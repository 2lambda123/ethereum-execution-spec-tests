"""
A bytecode sequence that caused bug, calling to undefined opcode with filled stack
"""

import pytest

from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcode
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.valid_from("Frontier")
def test_bytecode(
    state_test: StateTestFiller,
    pre: Alloc,
):
    """
    Original bytecode: 0x67FFFFFFFFFFFFFFFF600160006000FB
    Original test: src/GeneralStateTestsFiller/stBugs/evmBytecodeFiller.json
    """
    code_worked = 1
    code_contract = pre.deploy_contract(
        balance=0,
        code=Op.PUSH8(0xFFFFFFFFFFFFFFFF)
        + Op.PUSH1(0x01)
        + Op.PUSH1(0x00)
        + Op.PUSH1(0x00)
        + Opcode(0xFB),
        storage={},
    )

    caller = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CALL(0, code_contract, 0, 0, 0, 0, 0)) + Op.SSTORE(code_worked, 1)
    )

    post = {
        caller: Account(storage={0: 0, code_worked: 1}),
    }

    tx = Transaction(
        sender=pre.fund_eoa(),
        gas_limit=120000,
        to=caller,
        data=b"",
        value=0,
        protected=False,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
