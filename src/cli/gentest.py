"""
Generate a Python blockchain test from a transaction hash.

This script can be used to generate Python source for a blockchain test case
that replays a mainnet or testnet transaction from its transaction hash.

Note:

Requirements:

1. Access to an archive node for the network where the transaction
    originates. A provider may be used.
2. A config file with the remote node data in JSON format

    ```json
    {
        "remote_nodes" : [
            {
                "name" : "mainnet_archive",
                "node_url" : "https://example.archive.node.url/v1
                "client_id" : "",
                "secret" : ""
            }
        ]
    }
    ```

    `client_id` and `secret` may be left empty if the node does not require
    them.
3. The transaction hash of a type 0 transaction (currently only legacy
    transactions are supported).

Example Usage:

1. Generate a test for a transaction with hash

    ```console
    gentest -c config.json \
    0xa41f343be7a150b740e5c939fa4d89f3a2850dbe21715df96b612fc20d1906be \
    tests/paris/test_0xa41f.py
    ```

2. Fill the test:

    ```console
    fill --fork=Paris tests/paris/test_0xa41f.py
    ```

Limitations:

1. Only legacy transaction types (type 0) are currently supported.
"""

import json
import os
import urllib
from dataclasses import asdict, dataclass
from sys import stderr
from typing import Dict, List, TextIO

import click
import requests

from ethereum_test_tools import Account, Address, Transaction, common
from ethereum_test_tools.rpc.rpc import EthRPC


@click.command()
@click.option(
    "--config-file",
    "-c",
    envvar="GENTEST_CONFIG_FILE",
    type=click.File("r"),
    default=os.path.expanduser("~/.eest/gentest"),
    help="Config file with remote node data.",
)
@click.argument("transaction_hash")
@click.argument("output_file", type=click.File("w", lazy=True))
def make_test(transaction_hash: str, output_file: TextIO, config_file: TextIO):
    """
    Extracts a transaction and required state from a network to make a blockchain test out of it.

    TRANSACTION_HASH is the hash of the transaction to be used.

    OUTPUT_FILE is the path to the output python script.
    """
    print("Load configs...", file=stderr)
    config = Config(config_file)
    request = RequestManager(config.remote_nodes[0])

    print(
        "Perform tx request: eth_get_transaction_by_hash(" + f"{transaction_hash}" + ")",
        file=stderr,
    )
    tr = request.eth_get_transaction_by_hash(transaction_hash)

    print("Perform debug_trace_call", file=stderr)
    state = request.debug_trace_call(tr)

    print("Perform eth_get_block_by_number", file=stderr)
    block = request.eth_get_block_by_number(tr.block_number)

    print("Generate py test", file=stderr)
    constructor = TestConstructor(PYTEST_TEMPLATE)
    test = constructor.make_test_template(block, tr, state)

    output_file.write(test)

    print("Finished", file=stderr)


class TestConstructor:
    """
    Construct .py file from test template, by replacing keywords with test data
    """

    test_template: str

    def __init__(self, test_template: str):
        """
        Initialize with template
        """
        self.test_template = test_template

    def _make_test_comments(self, test: str, tr_hash: str) -> str:
        test = test.replace(
            "$HEADLINE_COMMENT",
            "gentest autogenerated test with debug_traceCall of tx.hash " + tr_hash,
        )
        test = test.replace("$TEST_NAME", "test_transaction_" + tr_hash[2:])
        test = test.replace(
            "$TEST_COMMENT", "gentest autogenerated test for tx.hash " + tr_hash[2:]
        )
        return test

    def _make_test_environment(self, test: str, bl: "RequestManager.RemoteBlock") -> str:
        env_str = ""
        pad = "        "
        for field, value in asdict(bl).items():
            env_str += (
                f'{pad}{field}="{value}",\n' if field == "coinbase" else f"{pad}{field}={value},\n"
            )
        test = test.replace("$ENV", env_str)
        return test

    def _make_pre_state(
        self, test: str, tr: "RequestManager.RemoteTransaction", state: Dict[Address, Account]
    ) -> str:
        # Print a nice .py storage pre
        pad = "            "
        state_str = ""
        for address, account in state.items():
            if isinstance(account, dict):
                account_obj = Account(**account)
                state_str += f'        "{address}": Account(\n'
                state_str += f"{pad}balance={str(account_obj.balance)},\n"
                if address == tr.transaction.sender:
                    state_str += f"{pad}nonce={tr.transaction.nonce},\n"
                else:
                    state_str += f"{pad}nonce={str(account_obj.nonce)},\n"

                if account_obj.code is None:
                    state_str += f'{pad}code="0x",\n'
                else:
                    state_str += f'{pad}code="{str(account_obj.code)}",\n'
                state_str += pad + "storage={\n"

                if account_obj.storage is not None:
                    for record, value in account_obj.storage.root.items():
                        pad_record = common.ZeroPaddedHexNumber(record)
                        pad_value = common.ZeroPaddedHexNumber(value)
                        state_str += f'{pad}    "{pad_record}" : "{pad_value}",\n'

                state_str += pad + "}\n"
                state_str += "        ),\n"
        return test.replace("$PRE", state_str)

    def _make_transaction(self, test: str, tr: "RequestManager.RemoteTransaction") -> str:
        """
        Print legacy transaction in .py
        """
        pad = "            "
        tr_str = ""
        quoted_fields_array = ["data", "to"]
        hex_fields_array = ["v", "r", "s"]
        legacy_fields_array = [
            "ty",
            "chain_id",
            "nonce",
            "gas_price",
            "protected",
            "gas_limit",
            "value",
        ]
        for field, value in iter(tr.transaction):
            if value is None:
                continue

            if field in legacy_fields_array:
                tr_str += f"{pad}{field}={value},\n"

            if field in quoted_fields_array:
                tr_str += f'{pad}{field}="{value}",\n'

            if field in hex_fields_array:
                tr_str += f"{pad}{field}={hex(value)},\n"

        return test.replace("$TR", tr_str)

    def make_test_template(
        self,
        bl: "RequestManager.RemoteBlock",
        tr: "RequestManager.RemoteTransaction",
        state: Dict[Address, Account],
    ) -> str:
        """
        Prepare the .py file template
        """
        test = self.test_template
        test = self._make_test_comments(test, tr.tr_hash)
        test = self._make_test_environment(test, bl)
        test = self._make_pre_state(test, tr, state)
        test = self._make_transaction(test, tr)
        return test


class Config:
    """
    Main class to manage Pyspec config
    """

    @dataclass
    class RemoteNode:
        """
        Remote node structure
        """

        name: str
        node_url: str
        client_id: str
        secret: str

    remote_nodes: List["Config.RemoteNode"]

    def __init__(self, file: TextIO):
        """
        Initialize pyspec config from file
        """
        data = json.load(file)
        self.remote_nodes = [Config.RemoteNode(**node) for node in data["remote_nodes"]]


class RequestManager:
    """
    Interface for the RPC interaction with remote node
    """

    @dataclass()
    class RemoteTransaction:
        """
        Remote transaction structure
        """

        block_number: str
        tr_hash: str
        transaction: Transaction

    @dataclass
    class RemoteBlock:
        """
        Remote block header information structure
        """

        coinbase: str
        difficulty: str
        gas_limit: str
        number: str
        timestamp: str

    node_url: str
    headers: dict[str, str]

    @staticmethod
    def _get_ip_from_url(node_url):
        return urllib.parse.urlsplit(node_url).netloc.split(":")[0]

    def __init__(self, node_config: Config.RemoteNode):
        """
        Initialize the RequestManager with specific client config.
        """
        self.node_url = node_config.node_url
        client_ip = self._get_ip_from_url(node_config.node_url)
        self.rpc = EthRPC(client_ip)
        self.headers = {
            "CF-Access-Client-Id": node_config.client_id,
            "CF-Access-Client-Secret": node_config.secret,
            "Content-Type": "application/json",
        }

    def eth_get_transaction_by_hash(self, transaction_hash: str) -> RemoteTransaction:
        """
        Get transaction data.
        """
        response = self.rpc.get_transaction_by_hash(transaction_hash)
        res = response.json().get("result", None)

        assert (
            res["type"] == "0x0"
        ), f"Transaction has type {res['type']}: Currently only type 0 transactions are supported."

        return RequestManager.RemoteTransaction(
            block_number=res["blockNumber"],
            tr_hash=res["hash"],
            transaction=Transaction(
                ty=int(res["type"], 16),
                gas_limit=int(res["gas"], 16),
                gas_price=int(res["gasPrice"], 16),
                data=res["input"],
                nonce=int(res["nonce"], 16),
                sender=res["from"],
                to=res["to"],
                value=int(res["value"], 16),
                v=int(res["v"], 16),
                r=int(res["r"], 16),
                s=int(res["s"], 16),
                protected=True if int(res["v"], 16) > 30 else False,
            ),
        )

    def eth_get_block_by_number(self, block_number: str) -> RemoteBlock:
        """
        Get block by number
        """
        response = self.rpc.get_block_by_number(block_number)
        res = response.json().get("result", None)

        return RequestManager.RemoteBlock(
            coinbase=res["miner"],
            number=res["number"],
            difficulty=res["difficulty"],
            gas_limit=res["gasLimit"],
            timestamp=res["timestamp"],
        )

    def debug_trace_call(self, tr: RemoteTransaction) -> Dict[Address, Account]:
        """
        Get pre state required for transaction
        """
        response = self.rpc.debug_trace_call(tr)
        if "error" in response:
            raise Exception(response["error"]["message"])
        assert "result" in response, "No result in response on debug_traceCall"
        return response["result"]


PYTEST_TEMPLATE = """
\"\"\"
$HEADLINE_COMMENT
\"\"\"

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Block,
    Environment,
    BlockchainTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.fixture
def env():  # noqa: D103
    return Environment(
$ENV
    )


@pytest.mark.valid_from("Paris")
def $TEST_NAME(
    env: Environment,
    blockchain_test: BlockchainTestFiller,
):
    \"\"\"
    $TEST_COMMENT
    \"\"\"

    pre = {
$PRE
    }

    post = {
    }

    tx = Transaction(
$TR
    )

    blockchain_test(genesis_environment=env, pre=pre, post=post, blocks=[Block(txs=[tx])])

"""
