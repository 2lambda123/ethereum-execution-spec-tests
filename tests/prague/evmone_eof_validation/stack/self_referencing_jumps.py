"""
EOF v1 validation code
"""

import pytest
from ethereum_test_tools import EOFTestFiller
from ethereum_test_tools.eof.v1 import Container, EOFException

@pytest.mark.parametrize(
    "eof_code,expected_hex_bytecode,exception",
    [
        pytest.param(
            Container(
                name="EOF1V00001",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x01,
                        0x00,
                        0x04,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x03,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0xe0,
                        0xff,
                        0xfd,

                     ]),
            ),
            "0xef000101000402000100030400000000800000e0fffd",
            None,
            id="rjump",
        ),
        pytest.param(
            Container(
                name="EOF1V00002",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x01,
                        0x00,
                        0x04,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x06,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0x60,
                        0x00,
                        0xe1,
                        0xff,
                        0xfd,
                        0x00,

                     ]),
            ),
            "0xef0001010004020001000604000000008000006000e1fffd00",
            EOFException.INVALID_STACK_HEIGHT,
            id="rjumpi",
        ),
        pytest.param(
            Container(
                name="EOF1V00003",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x01,
                        0x00,
                        0x04,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x07,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0x60,
                        0x00,
                        0xe2,
                        0x00,
                        0xff,
                        0xfc,
                        0x00,

                     ]),
            ),
            "0xef0001010004020001000704000000008000006000e200fffc00",
            EOFException.INVALID_STACK_HEIGHT,
            id="rjumpv",
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
