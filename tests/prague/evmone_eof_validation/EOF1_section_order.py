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
                        0x06,
                        0x04,
                        0x00,
                        0x02,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x01,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,
                        0xaa,
                        0xbb,

                     ]),
            ),
            "0xef0001010004020001000604000200008000016000e0000000aabb",
            None,
            id="EOF1_section_order_0",
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
                        0x04,
                        0x00,
                        0x02,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x06,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0xaa,
                        0xbb,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,

                     ]),
            ),
            "0xef000101000404000202000100060000800000aabb6000e0000000",
            EOFException.MISSING_CODE_HEADER,
            id="EOF1_section_order_1",
        ),
        pytest.param(
            Container(
                name="EOF1V00003",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x06,
                        0x01,
                        0x00,
                        0x04,
                        0x04,
                        0x00,
                        0x02,
                        0x00,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0xaa,
                        0xbb,

                     ]),
            ),
            "0xef00010200010006010004040002006000e000000000800000aabb",
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1_section_order_2",
        ),
        pytest.param(
            Container(
                name="EOF1V00004",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x06,
                        0x04,
                        0x00,
                        0x02,
                        0x01,
                        0x00,
                        0x04,
                        0x00,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,
                        0xaa,
                        0xbb,
                        0x00,
                        0x80,
                        0x00,
                        0x00,

                     ]),
            ),
            "0xef00010200010006040002010004006000e0000000aabb00800000",
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1_section_order_3",
        ),
        pytest.param(
            Container(
                name="EOF1V00005",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x04,
                        0x00,
                        0x02,
                        0x01,
                        0x00,
                        0x04,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x06,
                        0x00,
                        0xaa,
                        0xbb,
                        0x00,
                        0x80,
                        0x00,
                        0x00,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,

                     ]),
            ),
            "0xef0001040002010004020001000600aabb008000006000e0000000",
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1_section_order_4",
        ),
        pytest.param(
            Container(
                name="EOF1V00006",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x04,
                        0x00,
                        0x02,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x06,
                        0x01,
                        0x00,
                        0x04,
                        0x00,
                        0xaa,
                        0xbb,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x00,

                     ]),
            ),
            "0xef0001040002020001000601000400aabb6000e000000000800000",
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1_section_order_5",
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
                        0x06,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x14,
                        0x04,
                        0x00,
                        0x02,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x01,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
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
                        0xaa,
                        0xbb,

                     ]),
            ),
            "0xef00010100040200010006030001001404000200008000016000e0000000ef000101000402000100010400000000800000feaabb",
            None,
            id="EOF1_section_order_6",
        ),
        pytest.param(
            Container(
                name="EOF1V00008",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x14,
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
                        0x02,
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
                        0x00,
                        0x80,
                        0x00,
                        0x01,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,
                        0xaa,
                        0xbb,

                     ]),
            ),
            "0xef00010300010014010004020001000604000200ef000101000402000100010400000000800000fe008000016000e0000000aabb",
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1_section_order_7",
        ),
        pytest.param(
            Container(
                name="EOF1V00009",
                raw_bytes=bytes(
                     [
                        0xef,
                        0x00,
                        0x01,
                        0x01,
                        0x00,
                        0x04,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x14,
                        0x02,
                        0x00,
                        0x01,
                        0x00,
                        0x06,
                        0x04,
                        0x00,
                        0x02,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x01,
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
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,
                        0xaa,
                        0xbb,

                     ]),
            ),
            "0xef0001010004030001001402000100060400020000800001ef000101000402000100010400000000800000fe6000e0000000aabb",
            EOFException.MISSING_CODE_HEADER,
            id="EOF1_section_order_8",
        ),
        pytest.param(
            Container(
                name="EOF1V00010",
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
                        0x02,
                        0x03,
                        0x00,
                        0x01,
                        0x00,
                        0x14,
                        0x00,
                        0x00,
                        0x80,
                        0x00,
                        0x01,
                        0x60,
                        0x00,
                        0xe0,
                        0x00,
                        0x00,
                        0x00,
                        0xaa,
                        0xbb,
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
            "0xef00010100040200010006040002030001001400008000016000e0000000aabbef000101000402000100010400000000800000fe",
            EOFException.MISSING_TERMINATOR,
            id="EOF1_section_order_9",
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
