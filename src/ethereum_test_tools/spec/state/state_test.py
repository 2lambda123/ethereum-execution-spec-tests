"""
Ethereum state test spec definition and filler.
"""

from typing import Any, Callable, ClassVar, Dict, Generator, List, Optional, Type

from pydantic import Field

from ethereum_test_forks import Fork
from evm_transition_tool import FixtureFormats, TransitionTool

from ...common import Account, Alloc, Environment, Transaction
from ...common.base_types import Bytes
from ...common.constants import EngineAPIError
from ...common.json import to_json
from ...common.types import TransitionToolOutput
from ..base.base_test import BaseFixture, BaseTest
from ..blockchain.blockchain_test import Block, BlockchainTest
from ..blockchain.types import Header
from ..debugging import print_traces
from .types import Fixture, FixtureEnvironment, FixtureForkPost, FixtureTransaction

TARGET_BLOB_GAS_PER_BLOCK = 393216


class StateTest(BaseTest):
    """
    Filler type that tests transactions over the period of a single block.
    """

    env: Environment
    pre: Alloc
    post: Alloc
    tx: Transaction
    engine_api_error_code: Optional[EngineAPIError] = None
    blockchain_test_header_verify: Optional[Header] = None
    blockchain_test_rlp_modifier: Optional[Header] = None
    chain_id: int = 1

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [
        FixtureFormats.BLOCKCHAIN_TEST,
        FixtureFormats.BLOCKCHAIN_TEST_HIVE,
        FixtureFormats.STATE_TEST,
    ]

    def _generate_blockchain_genesis_environment(self) -> Environment:
        """
        Generate the genesis environment for the BlockchainTest formatted test.
        """
        assert (
            self.env.number >= 1
        ), "genesis block number cannot be negative, set state test env.number to 1"

        # Modify values to the proper values for the genesis block
        # TODO: All of this can be moved to a new method in `Fork`
        updated_values: Dict[str, Any] = {
            "withdrawals": None,
            "parent_beacon_block_root": None,
            "number": self.env.number - 1,
        }
        if self.env.excess_blob_gas:
            # The excess blob gas environment value means the value of the context (block header)
            # where the transaction is executed. In a blockchain test, we need to indirectly
            # set the excess blob gas by setting the excess blob gas of the genesis block
            # to the expected value plus the TARGET_BLOB_GAS_PER_BLOCK, which is the value
            # that will be subtracted from the excess blob gas when the first block is mined.
            updated_values["excess_blob_gas"] = (
                self.env.excess_blob_gas + TARGET_BLOB_GAS_PER_BLOCK
            )

        return self.env.copy(**updated_values)

    def _generate_blockchain_blocks(self) -> List[Block]:
        """
        Generate the single block that represents this state test in a BlockchainTest format.
        """
        return [
            Block(
                number=self.env.number,
                timestamp=self.env.timestamp,
                fee_recipient=self.env.fee_recipient,
                difficulty=self.env.difficulty,
                gas_limit=self.env.gas_limit,
                extra_data=self.env.extra_data,
                withdrawals=self.env.withdrawals,
                parent_beacon_block_root=self.env.parent_beacon_block_root,
                txs=[self.tx],
                ommers=[],
                exception=self.tx.error,
                header_verify=self.blockchain_test_header_verify,
                rlp_modifier=self.blockchain_test_rlp_modifier,
            )
        ]

    def generate_blockchain_test(self) -> BlockchainTest:
        """
        Generate a BlockchainTest fixture from this StateTest fixture.
        """
        return BlockchainTest(
            genesis_environment=self._generate_blockchain_genesis_environment(),
            pre=self.pre,
            post=self.post,
            blocks=self._generate_blockchain_blocks(),
            t8n_dump_dir=self.t8n_dump_dir,
        )

    def make_state_test_fixture(
        self,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
    ) -> Fixture:
        """
        Create a fixture from the state test definition.
        """
        # We can't generate a state test fixture that names a transition fork,
        # so we get the fork at the block number and timestamp of the state test
        fork = fork.fork_at(self.env.number, self.env.timestamp)

        env = self.env.set_fork_requirements(fork)
        tx = self.tx.with_signature_and_sender(keep_secret_key=True)
        pre_alloc = Alloc.merge(
            Alloc.model_validate(fork.pre_allocation()),
            self.pre,
        )
        if empty_accounts := pre_alloc.empty_accounts():
            raise Exception(f"Empty accounts in pre state: {empty_accounts}")
        transition_tool_name = fork.transition_tool_name(
            block_number=self.env.number,
            timestamp=self.env.timestamp,
        )
        fork_name = (
            "+".join([transition_tool_name] + [str(eip) for eip in eips])
            if eips
            else transition_tool_name
        )
        transition_tool_output = TransitionToolOutput(
            **t8n.evaluate(
                alloc=to_json(pre_alloc),
                txs=[to_json(tx)],
                env=to_json(env),
                fork_name=fork_name,
                chain_id=self.chain_id,
                reward=0,  # Reward on state tests is always zero
                eips=eips,
                debug_output_path=self.get_next_transition_tool_output_path(),
            )
        )

        try:
            self.post.verify_post_alloc(transition_tool_output.alloc)
        except Exception as e:
            print_traces(t8n.get_traces())
            raise e

        return Fixture(
            env=FixtureEnvironment(**env.model_dump(exclude_none=True)),
            pre=pre_alloc,
            post={
                fork.blockchain_test_network_name(): [
                    FixtureForkPost(
                        state_root=transition_tool_output.result.state_root,
                        logs_hash=transition_tool_output.result.logs_hash,
                        tx_bytes=tx.rlp,
                        expect_exception=tx.error,
                    )
                ]
            },
            transaction=FixtureTransaction.from_transaction(tx),
        )

    def generate(
        self,
        t8n: TransitionTool,
        fork: Fork,
        fixture_format: FixtureFormats,
        eips: Optional[List[int]] = None,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        if fixture_format in BlockchainTest.supported_fixture_formats:
            return self.generate_blockchain_test().generate(
                t8n=t8n, fork=fork, fixture_format=fixture_format, eips=eips
            )
        elif fixture_format == FixtureFormats.STATE_TEST:
            return self.make_state_test_fixture(t8n, fork, eips)

        raise Exception(f"Unknown fixture format: {fixture_format}")


class StateTestOnly(StateTest):
    """
    StateTest filler that only generates a state test fixture.
    """

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [FixtureFormats.STATE_TEST]


StateTestSpec = Callable[[str], Generator[StateTest, None, None]]
StateTestFiller = Type[StateTest]


class SimpleStateTest(BaseTest):
    """
    Defines a simplified state test with a single contract interaction or a contract-creating
    transaction.
    """

    env: Environment = Field(default_factory=Environment)

    contract: Bytes | None = None
    contract_post: Account | None = Field(default_factory=Account)

    tx_type: int = 0
    tx_data: Bytes = Bytes(b"")
    tx_gas_limit: int = 10_000_000
    tx_sender_funding_amount: int = 1_000_000_000_000_000_000_000

    pre: Alloc | None = None

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [
        FixtureFormats.STATE_TEST,
        FixtureFormats.BLOCKCHAIN_TEST,
        FixtureFormats.BLOCKCHAIN_TEST_HIVE,
    ]

    def generate_state_test(self) -> StateTest:
        """
        Generate the StateTest filler.
        """
        assert self.pre is not None, "pre must be set to generate a StateTest."
        sender = self.pre.fund_eoa(amount=self.tx_sender_funding_amount)
        if self.contract is None:
            # Contract-creating transaction
            tx = Transaction(
                type=self.tx_type,
                to=None,
                gas_limit=self.tx_gas_limit,
                data=self.tx_data,
                sender=sender,
            )
            contract_address = tx.created_contract
        else:
            # Contract interaction transaction
            contract_address = self.pre.deploy_contract(self.contract)
            tx = Transaction(
                type=self.tx_type,
                to=contract_address,
                gas_limit=self.tx_gas_limit,
                data=self.tx_data,
                sender=sender,
            )

        post = Alloc({
            contract_address: self.contract_post,
        })
        return StateTest(
            pre=self.pre,
            tx=tx,
            env=self.env,
            post=post,
        )

    def generate(
        self,
        *,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
        fixture_format: FixtureFormats,
        **_,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        if fixture_format in (
            FixtureFormats.STATE_TEST,
            FixtureFormats.BLOCKCHAIN_TEST,
            FixtureFormats.BLOCKCHAIN_TEST_HIVE,
        ):
            return self.generate_state_test().generate(
                t8n=t8n, fork=fork, fixture_format=fixture_format, eips=eips
            )

        raise Exception(f"Unknown fixture format: {fixture_format}")


SimpleStateTestSpec = Callable[[str], Generator[SimpleStateTest, None, None]]
SimpleStateTestFiller = Type[SimpleStateTest]
