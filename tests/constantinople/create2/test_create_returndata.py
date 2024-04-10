"""
Return data management around create2
Port call_outsize_then_create2_successful_then_returndatasizeFiller.json test
Port call_then_create2_successful_then_returndatasizeFiller.json test
"""

import pytest
from ethereum.crypto.hash import keccak256

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    TestAddress,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op


@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize("call_return_size", [35, 32, 0])
@pytest.mark.parametrize("create_type", [Op.CREATE, Op.CREATE2])
def test_create2_return_data(
    call_return_size: int,
    create_type: Op,
    state_test: StateTestFiller,
):
    """
    Validate that create2 return data does not interfere with previously existing memory
    """
    # Storage vars
    slot_returndatasize_before_create = 0
    slot_returndatasize_after_create = 1
    slot_return_data_hash_before_create = 2
    slot_return_data_hash_after_create = 3
    slot_code_worked = 4

    # Pre-Existing Addresses
    address_to = Address(0x0600)
    address_call = Address(0x0601)

    # CREATE2 Initcode
    create2_salt = 1
    initcode = Op.MSTORE(0, 0x112233) + Op.RETURN(0, 32) + Op.STOP()

    def make_create() -> bytes:
        if create_type == Op.CREATE2:
            return Op.CREATE2(0, 0x100, Op.CALLDATASIZE(), create2_salt)
        elif create_type == Op.CREATE:
            return Op.CREATE(0, 0x100, Op.CALLDATASIZE())
        raise NotImplementedError

    call_return_data_value = 0x0000111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF
    call_return_data = int.to_bytes(call_return_data_value, 32, byteorder="big").ljust(
        call_return_size, b"\0"
    )[0:call_return_size]
    empty_data = int.to_bytes(call_return_data_value, 32, byteorder="big").ljust(
        call_return_size, b"\0"
    )[0:0]

    pre = {
        address_to: Account(
            balance=100_000_000,
            nonce=0,
            code=Op.JUMPDEST()
            + Op.MSTORE(0x100, Op.CALLDATALOAD(0))
            + Op.CALL(0x0900000000, address_call, 0, 0, 0, 0, call_return_size)
            + Op.SSTORE(slot_returndatasize_before_create, Op.RETURNDATASIZE())
            + Op.SSTORE(slot_return_data_hash_before_create, Op.SHA3(0, call_return_size))
            + make_create()
            + Op.SSTORE(slot_returndatasize_after_create, Op.RETURNDATASIZE())
            + Op.SSTORE(slot_return_data_hash_after_create, Op.SHA3(0, Op.RETURNDATASIZE()))
            + Op.SSTORE(slot_code_worked, 1)
            + Op.STOP(),
            storage={
                slot_returndatasize_before_create: 0xFF,
                slot_returndatasize_after_create: 0xFF,
                slot_return_data_hash_before_create: 0xFF,
                slot_return_data_hash_after_create: 0xFF,
            },
        ),
        address_call: Account(
            balance=0,
            nonce=0,
            code=Op.JUMPDEST()
            + Op.MSTORE(0, call_return_data_value)
            + Op.RETURN(0, call_return_size),
            storage={},
        ),
        TestAddress: Account(
            balance=7_000_000_000_000_000_000,
            nonce=0,
            code="0x",
            storage={},
        ),
    }

    post = {
        address_to: Account(
            storage={
                slot_code_worked: 1,
                slot_returndatasize_before_create: call_return_size,
                slot_returndatasize_after_create: 0,
                slot_return_data_hash_before_create: keccak256(call_return_data),
                slot_return_data_hash_after_create: keccak256(empty_data),
            }
        )
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to=address_to,
        gas_price=10,
        protected=False,
        data=initcode,
        gas_limit=0x0A00000000,
        value=0,
    )

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
