"""
Pytest fixtures for the `consume engine` simulator.

Configures the hive back-end & EL clients for each individual test execution.
"""

from pathlib import Path

import pytest
from hive.client import Client

from ethereum_test_fixtures import BlockchainHiveFixture
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream
from ethereum_test_fixtures.file import BlockchainHiveFixtures
from ethereum_test_tools.rpc import EngineRPC
from pytest_plugins.consume.common import JsonSource

TestCase = TestCaseIndexFile | TestCaseStream


@pytest.fixture(scope="function")
def engine_rpc(client: Client) -> EngineRPC:
    """
    Initialize engine RPC client for the execution client under test.
    """
    return EngineRPC(ip=client.ip)


@pytest.fixture(scope="session")
def test_suite_name() -> str:
    """
    The name of the hive test suite used in this simulator.
    """
    return "eest-engine"


@pytest.fixture(scope="session")
def test_suite_description() -> str:
    """
    The description of the hive test suite used in this simulator.
    """
    return "Execute blockchain tests by against clients using the Engine API."


@pytest.fixture(scope="function")
def blockchain_fixture(fixture_source: JsonSource, test_case: TestCase) -> BlockchainHiveFixture:
    """
    Create the blockchain engine fixture pydantic model for the current test case.

    The fixture is either already available within the test case (if consume
    is taking input on stdin) or loaded from the fixture json file if taking
    input from disk (fixture directory with index file).
    """
    if fixture_source == "stdin":
        assert isinstance(test_case, TestCaseStream), "Expected a stream test case"
        assert isinstance(
            test_case.fixture, BlockchainHiveFixture
        ), "Expected a blockchain engine test fixture"
        fixture = test_case.fixture
    else:
        assert isinstance(test_case, TestCaseIndexFile), "Expected an index file test case"
        # TODO: Optimize, json files will be loaded multiple times. This pytest fixture
        # is executed per test case, and a fixture json will contain multiple test cases.
        fixtures = BlockchainHiveFixtures.from_file(Path(fixture_source) / test_case.json_path)
        fixture = fixtures[test_case.id]
    return fixture
