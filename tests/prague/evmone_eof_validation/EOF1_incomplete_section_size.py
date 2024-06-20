"""
EOF v1 validation code
"""

import pytest
from ethereum_test_tools import EOFTestFiller
from ethereum_test_tools import EOFException
from ethereum_test_tools.eof.v1 import Container, ContainerKind

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

                     ]),
                ),
                "0xef000101",
                EOFException.MISSING_HEADERS_TERMINATOR,
                id="EOF1_incomplete_section_size_1",
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

                     ]),
                ),
                "0xef00010100",
                EOFException.INCOMPLETE_SECTION_SIZE,
                id="EOF1_incomplete_section_size_2",
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

                     ]),
                ),
                "0xef00010100040200",
                EOFException.INCOMPLETE_SECTION_NUMBER,
                id="EOF1_incomplete_section_size_3",
            ),
            pytest.param(
            Container(
                name="EOF1V00004",
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

                     ]),
                ),
                "0xef000101000402000100",
                EOFException.INCOMPLETE_SECTION_SIZE,
                id="EOF1_incomplete_section_size_4",
            ),
            pytest.param(
            Container(
                name="EOF1V00005",
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
                        0x01,

                     ]),
                ),
                "0xef00010100040200010001",
                EOFException.MISSING_HEADERS_TERMINATOR,
                id="EOF1_incomplete_section_size_5",
            ),
            pytest.param(
            Container(
                name="EOF1V00006",
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
                        0x01,
                        0x04,

                     ]),
                ),
                "0xef0001010004020001000104",
                EOFException.MISSING_HEADERS_TERMINATOR,
                id="EOF1_incomplete_section_size_6",
            ),
            pytest.param(
            Container(
                name="EOF1V00007",
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
                        0x01,
                        0x04,
                        0x00,

                     ]),
                ),
                "0xef000101000402000100010400",
                EOFException.INCOMPLETE_SECTION_SIZE,
                id="EOF1_incomplete_section_size_7",
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
