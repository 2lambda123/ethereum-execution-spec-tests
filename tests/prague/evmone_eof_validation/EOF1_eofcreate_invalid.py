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
                        0x09,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x14,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x04,
                        0x60,
                        0x00,
                        0x60,
                        0xff,
                        0x60,
                        0x00,
                        0x60,
                        0x00,
                        0xec,
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
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0xfe,

                     ]),
            ),
            "0xef0001010004020001000903000100140400000000800004600060ff60006000ecef000101000402000100010400000000800000fe",
            EOFException.TRUNCATED_INSTRUCTION,
            id="EOF1_eofcreate_invalid_0",
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
                        0x0a,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x14,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x04,
                        0x60,
                        0x00,
                        0x60,
                        0xff,
                        0x60,
                        0x00,
                        0x60,
                        0x00,
                        0xec,
                        0x00,
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
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0xfe,

                     ]),
            ),
            "0xef0001010004020001000a03000100140400000000800004600060ff60006000ec00ef000101000402000100010400000000800000fe",
            EOFException.MISSING_STOP_OPCODE,
            id="EOF1_eofcreate_invalid_1",
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
                        0x0c,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x14,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x04,
                        0x60,
                        0x00,
                        0x60,
                        0xff,
                        0x60,
                        0x00,
                        0x60,
                        0x00,
                        0xec,
                        0x01,
                        0x50,
                        0x00,
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
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0xfe,

                     ]),
            ),
            "0xef0001010004020001000c03000100140400000000800004600060ff60006000ec015000ef000101000402000100010400000000800000fe",
            EOFException.INVALID_CONTAINER_SECTION_INDEX,
            id="EOF1_eofcreate_invalid_2",
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
                        0x0c,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x14,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x04,
                        0x60,
                        0x00,
                        0x60,
                        0xff,
                        0x60,
                        0x00,
                        0x60,
                        0x00,
                        0xec,
                        0xff,
                        0x50,
                        0x00,
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
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0xfe,

                     ]),
            ),
            "0xef0001010004020001000c03000100140400000000800004600060ff60006000ecff5000ef000101000402000100010400000000800000fe",
            EOFException.INVALID_CONTAINER_SECTION_INDEX,
            id="EOF1_eofcreate_invalid_3",
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
                        0x0c,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x16,
                        0x04,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x04,
                        0x60,
                        0x00,
                        0x60,
                        0xff,
                        0x60,
                        0x00,
                        0x60,
                        0x00,
                        0xec,
                        0x00,
                        0x50,
                        0x00,
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
                        0x03,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0xfe,
                        0xaa,
                        0xbb,

                     ]),
            ),
            "0xef0001010004020001000c03000100160400000000800004600060ff60006000ec005000ef000101000402000100010400030000800000feaabb",
            EOFException.EOF_CREATE_WITH_TRUNCATED_CONTAINER,
            id="EOF1_eofcreate_invalid_4",
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
