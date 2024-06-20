"""
EOF v1 validation code
"""

import pytest
from ethereum_test_tools import EOFTestFiller
from ethereum_test_tools import EOFException, Opcodes as Op, UndefinedOpcodes as UOp
from ethereum_test_tools.eof.v1 import Container, ContainerKind, Section

@pytest.mark.parametrize(
    "eof_code,expected_hex_bytecode,exception",
    [
        
        pytest.param(
                Container(
                    name="EOF1V00001",
                    sections=[
                        Section.Code(code=Op.PUSH1[0x01] * 20 + Op.DUPN[0x00] + Op.STOP, max_stack_height=21),
                    ],
                    kind=ContainerKind.RUNTIME,
                ),
                "0xef0001010004020001002b040000000080001560016001600160016001600160016001600160016001600160016001600160016001600160016001e60000",
                None,
                id="dupn_stack_validation_1",
            ),
                
        pytest.param(
                Container(
                    name="EOF1V00002",
                    sections=[
                        Section.Code(code=Op.PUSH1[0x01] * 20 + Op.DUPN[0x13] + Op.STOP, max_stack_height=21),
                    ],
                    kind=ContainerKind.RUNTIME,
                ),
                "0xef0001010004020001002b040000000080001560016001600160016001600160016001600160016001600160016001600160016001600160016001e61300",
                None,
                id="dupn_stack_validation_2",
            ),
                
        pytest.param(
                Container(
                    name="EOF1V00003",
                    sections=[
                        Section.Code(code=Op.PUSH1[0x01] * 20 + Op.DUPN[0x14] + Op.STOP, max_stack_height=21),
                    ],
                    kind=ContainerKind.RUNTIME,
                ),
                "0xef0001010004020001002b040000000080001560016001600160016001600160016001600160016001600160016001600160016001600160016001e61400",
                EOFException.STACK_UNDERFLOW,
                id="dupn_stack_validation_3",
            ),
                
        pytest.param(
                Container(
                    name="EOF1V00004",
                    sections=[
                        Section.Code(code=Op.PUSH1[0x01] * 20 + Op.DUPN[0xd0] + Op.STOP, max_stack_height=21),
                    ],
                    kind=ContainerKind.RUNTIME,
                ),
                "0xef0001010004020001002b040000000080001560016001600160016001600160016001600160016001600160016001600160016001600160016001e6d000",
                EOFException.STACK_UNDERFLOW,
                id="dupn_stack_validation_4",
            ),
                
        pytest.param(
                Container(
                    name="EOF1V00005",
                    sections=[
                        Section.Code(code=Op.PUSH1[0x01] * 20 + Op.DUPN[0xfe] + Op.STOP, max_stack_height=21),
                    ],
                    kind=ContainerKind.RUNTIME,
                ),
                "0xef0001010004020001002b040000000080001560016001600160016001600160016001600160016001600160016001600160016001600160016001e6fe00",
                EOFException.STACK_UNDERFLOW,
                id="dupn_stack_validation_5",
            ),
                
        pytest.param(
                Container(
                    name="EOF1V00006",
                    sections=[
                        Section.Code(code=Op.PUSH1[0x01] * 20 + Op.DUPN[0xff] + Op.STOP, max_stack_height=21),
                    ],
                    kind=ContainerKind.RUNTIME,
                ),
                "0xef0001010004020001002b040000000080001560016001600160016001600160016001600160016001600160016001600160016001600160016001e6ff00",
                EOFException.STACK_UNDERFLOW,
                id="dupn_stack_validation_6",
            ),
                
    ]
)

def test_example_valid_invalid(
    eof_test: EOFTestFiller,
    eof_code: Container,
    expected_hex_bytecode: str,
    exception: EOFException | None,
):
    """
    Verify eof container construction and exception
    """
    if expected_hex_bytecode[0:2] == "0x":
        expected_hex_bytecode = expected_hex_bytecode[2:]
    assert bytes(eof_code) == bytes.fromhex(expected_hex_bytecode)

    eof_test(
        data=eof_code,
        expect_exception=exception,
    )
