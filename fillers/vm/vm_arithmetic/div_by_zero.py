"""
Test Div by Zero:
    # Original test by Ori Pomerantz qbzzt1@gmail.com
    # Port from ethereum/tests:
    #   - GeneralStateTestsFiller/VMTests/vmTest/divByZeroFiller.yml
    #   - Original test by Ori Pomerantz qbzzt1@gmail.com
    #
    # A standard location for division by zero tests.
    #
    # Opcodes where this is relevant:
    #   DIV
    #   SDIV
    #   MOD
    #   SMOD
    #   ADDMOD
    #   MULMOD
    #
    # Any division or mod by zero returns zero.
"""

from ethereum_test_tools import Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    StateTest,
    TestAddress,
    Transaction,
    Yul,
    test_from,
    to_address,
    to_hash,
)


@test_from("istanbul")
def test_div_by_zero(fork):
    """
    Test division by zero.
    Port from ethereum/tests:
      - GeneralStateTestsFiller/VMTests/vmTest/divByZeroFiller.yml
      - Original test by Ori Pomerantz qbzzt1@gmail.com
    """
    env = Environment()
    pre = {TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE)}
    txs = []

    div_params = [
        2,
        1,
        0,
        to_hash(-1),
        to_hash(-2),
        to_hash(2**255 - 1),
        to_hash(2**255),
    ]

    for i in range(0, len(div_params)):

        address = to_address(0x100 + i)
        a = div_params[i]
        print(a)

        code_div = (
            # Push 0
            # Push a
            # Div(a, 0)
            Op.PUSH1(0)
            + Op.PUSH1(a)
            + Op.DIV
            # Push 0
            # sstore(0, div(a,0))
            + Op.PUSH1(i)
            + Op.SSTORE
            + Op.STOP
        )

        pre[to_address(0x100)] = Account(code=code_div)

        tx = Transaction(
            nonce=i,
            to=address,
            gas_limit=100000000,
            gas_price=10,
        )
        txs.append(tx)

        post = {address: Account(storage={i: 0x00})}

    yield StateTest(env=env, pre=pre, post=post, txs=txs)
