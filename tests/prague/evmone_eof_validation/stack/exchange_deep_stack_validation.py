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
                        0x45,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x21,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0x60,
                        0x01,
                        0xe8,
                        0xff,
                        0x00,

                     ]),
            ),
            "0xef000101000402000100450400000000800021600160016001600160016001600160016001600160016001600160016001600160016001600160016001600160016001600160016001600160016001600160016001e8ff00",
            None,
            id="exchange_deep_stack_validation_0",
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
