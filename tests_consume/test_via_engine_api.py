"""
A hive simulator that executes blocks against clients using the
`engine_newPayloadVX` method from the Engine API, verifying
the appropriate VALID/INVALID responses.

Implemented using the pytest framework as a pytest plugin.
"""

import io
import json
import pprint
from typing import Generator, List, Mapping, Tuple, cast

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from ethereum_test_base_types import Account, to_json
from ethereum_test_fixtures.blockchain import FixtureHeader, HiveFixture
from ethereum_test_tools.rpc import EngineRPC, EthRPC
from pytest_plugins.consume.hive_ruleset import ruleset


@pytest.fixture(scope="function")
def client_genesis(fixture: HiveFixture) -> dict:
    """
    Convert the fixture's genesis block header and pre-state to a client genesis state.
    """
    genesis = to_json(fixture.genesis)
    alloc = to_json(fixture.pre)
    # NOTE: nethermind requires account keys without '0x' prefix
    genesis["alloc"] = {k.replace("0x", ""): v for k, v in alloc.items()}
    return genesis


@pytest.fixture(scope="function")
def buffered_genesis(client_genesis: dict) -> io.BufferedReader:
    """
    Create a buffered reader for the genesis block header of the current test
    fixture.
    """
    genesis_json = json.dumps(client_genesis)
    genesis_bytes = genesis_json.encode("utf-8")
    return io.BufferedReader(cast(io.RawIOBase, io.BytesIO(genesis_bytes)))


@pytest.fixture(scope="function")
def client_files(buffered_genesis: io.BufferedReader) -> Mapping[str, io.BufferedReader]:
    """
    Define the files that hive will start the client with.
    """
    files = {}
    files["/genesis.json"] = buffered_genesis
    return files


@pytest.fixture
def environment(fixture: HiveFixture) -> dict:
    """
    Define the environment that hive will start the client with using the fork
    rules specific for the simulator.
    """
    assert fixture.fork in ruleset, f"fork '{fixture.fork}' missing in hive ruleset"
    return {
        "HIVE_CHAIN_ID": "1",
        "HIVE_FORK_DAO_VOTE": "1",
        "HIVE_NODETYPE": "full",
        **{k: f"{v:d}" for k, v in ruleset[fixture.fork].items()},
    }


@pytest.fixture(scope="function")
def client(
    hive_test: HiveTest,
    client_files: dict,
    environment: dict,
    client_type: ClientType,
) -> Generator[Client, None, None]:
    """
    Initialize the client with the appropriate files and environment variables.
    """
    client = hive_test.start_client(
        client_type=client_type, environment=environment, files=client_files
    )
    error_message = (
        f"Unable to connect to the client container ({client_type.name}) via Hive during test "
        "setup. Check the client or Hive server logs for more information."
    )
    assert client is not None, error_message
    yield client
    client.stop()


@pytest.fixture(scope="function")
def eth_rpc(client: Client) -> EthRPC:
    """
    Initialize ethereum RPC client for the execution client under test.
    """
    return EthRPC(ip=client.ip)


@pytest.fixture(scope="function")
def engine_rpc(client: Client) -> EngineRPC:
    """
    Initialize engine RPC client for the execution client under test.
    """
    return EngineRPC(ip=client.ip)


def compare_models(expected: FixtureHeader, got: FixtureHeader) -> dict:
    """
    Compare two FixtureHeader model instances and return their differences.
    """
    differences = {}
    for (exp_name, exp_value), (_, got_value) in zip(expected, got):
        if exp_value != got_value:
            differences[exp_name] = {
                "expected     ": str(exp_value),
                "got (via rpc)": str(got_value),
            }
    return differences


class GenesisBlockMismatchException(Exception):
    """
    Used when the client's genesis block hash does not match the fixture.
    """

    def __init__(self, *, expected_header: FixtureHeader, got_header: FixtureHeader):
        message = (
            "Genesis block hash mismatch.\n"
            f"Expected: {expected_header.block_hash}\n"
            f"     Got: {got_header.block_hash}."
        )
        differences = compare_models(expected_header, got_header)
        if differences:
            message += (
                "\n\nAdditionally, there are differences between the expected and received "
                "genesis block header fields:\n"
                f"{pprint.pformat(differences, indent=4)}"
            )
        else:
            message += (
                "There were no differences in the expected and received genesis block headers."
            )
        super().__init__(message)


@pytest.fixture(scope="function")
def engine_new_payloads(fixture: HiveFixture) -> List[Tuple[list, int, bool]]:
    """
    Engine new payloads extracted from the hive fixture.
    """
    engine_new_payloads: List[Tuple[list, int, bool]] = []
    for payload in fixture.payloads:
        payload_json = to_json(payload)
        version = payload_json.pop("version")
        execution_payload = payload_json["executionPayload"]
        blob_hashes = payload_json["expectedBlobVersionedHashes"]
        beacon_root = payload_json["parentBeaconBlockRoot"]
        valid = True
        if payload.validation_error is not None:
            valid = False
        engine_new_payloads.append(
            ([execution_payload, blob_hashes, beacon_root], version, valid),
        )
    return engine_new_payloads


def test_via_engine_api(
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    fixture: HiveFixture,
    engine_new_payloads: List[Tuple[list, int, bool]],
):
    """
    1) Checks that the genesis block hash of the client matches that of the fixture.
    2) Executes the test case fixture blocks against the client under test using the
    `engine_newPayloadVX` method from the Engine API, verifying the appropriate
    VALID/INVALID responses.
    3) Performs a forkchoice update to finalize the chain and verify the post state.
    4) Checks that the post state of the client matches that of the fixture.
    """
    genesis_block = eth_rpc.get_block_by_number(0)
    if genesis_block["hash"] != str(fixture.genesis.block_hash):
        raise GenesisBlockMismatchException(
            expected_header=fixture.genesis, got_header=FixtureHeader(**genesis_block)
        )

    skip_fcu = False
    for payload in engine_new_payloads:
        payload_response = engine_rpc.new_payload(
            engine_new_payload=payload[0],
            version=payload[1],
        )
        assert payload_response["status"] == (
            "VALID" if payload[2] else "INVALID"
        ), f"unexpected status: {payload_response} "
        if not payload[2]:
            skip_fcu = True

    if not skip_fcu:
        forkchoice_response = engine_rpc.forkchoice_updated(
            forkchoice_state={"headBlockHash": engine_new_payloads[-1][0][0]["blockHash"]},
            payload_attributes=None,
            version=fixture.fcu_version,
        )
        assert forkchoice_response["payloadStatus"]["status"] == (
            "VALID"
        ), f"unexpected status: {forkchoice_response} "

    for address, account in fixture.post_state.root.items():
        verify_account_state_and_storage(eth_rpc, address.hex(), account)


def verify_account_state_and_storage(eth_rpc, address, account: Account):
    """
    Verify the account state and storage matches the expected account state and storage.
    """
    # Check final nonce matches expected in fixture
    nonce = eth_rpc.get_transaction_count(address)
    assert account.nonce == int(nonce, 16), f"Nonce mismatch for account {address}."

    # Check final balance
    balance = eth_rpc.get_balance(address)
    assert account.balance == int(balance, 16), f"Balance mismatch for account {address}."

    # Check final storage
    # TODO: Fix this
    # if len(account.storage.root) > 0:
    # keys = list(account.storage.keys())
    # storage = eth_rpc.storage_at_keys(address, keys)
    # for key in keys:
    # assert int(account.storage[key]) == int(
    # storage[key], 16
    # ), f"Storage mismatch for account {address}, key {key}."
