"""
EOF validation tests for EIP-3540 migrated from
ethereum/tests/src/EOFTestsFiller/EIP3540/validInvalidFiller.yml
"""

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, Section

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "eof_code,exception",
    [
        pytest.param(
            # Deployed code without data section
            Container(
                name="EOF1V3540_0001",
                sections=[
                    Section.Code(code=Op.PUSH1[0] + Op.POP + Op.STOP),
                ],
            ),
            None,
            id="EOF1V3540_0001",
        ),
        pytest.param(
            # Deployed code with data section
            Container(
                name="EOF1V3540_0002",
                sections=[
                    Section.Code(code=Op.PUSH1[0] + Op.POP + Op.STOP),
                    Section.Data("aabbccdd"),
                ],
            ),
            None,
            id="EOF1V3540_0002",
        ),
        pytest.param(
            # No data section contents
            Container(
                name="EOF1V3540_0003",
                sections=[
                    Section.Code(code=Op.INVALID),
                    Section.Data(custom_size=2),
                ],
            ),
            EOFException.TOPLEVEL_CONTAINER_TRUNCATED,
            id="EOF1V3540_0003",
        ),
        pytest.param(
            # Data section contents incomplete
            Container(
                name="EOF1V3540_0004",
                sections=[
                    Section.Code(code=Op.INVALID),
                    Section.Data("aa", custom_size=2),
                ],
            ),
            EOFException.TOPLEVEL_CONTAINER_TRUNCATED,
            id="EOF1V3540_0004",
        ),
        pytest.param(
            # Type section size incomplete
            bytes.fromhex("ef00010100"),
            EOFException.INCOMPLETE_SECTION_SIZE,
            id="EOF1I3540_0011",
        ),
        pytest.param(
            # Empty code section with non-empty data section
            Container(
                sections=[Section.Code(code_outputs=0), Section.Data("aabb")],
                expected_bytecode="ef000101000402000100000400020000000000aabb",
            ),
            EOFException.ZERO_SECTION_SIZE,
            id="EOF1I3540_0012",
        ),
        pytest.param(
            # No data section after code section size
            bytes.fromhex("ef00010100040200010001"),
            EOFException.MISSING_HEADERS_TERMINATOR,
            id="EOF1I3540_0017",
        ),
        pytest.param(
            # No data size
            bytes.fromhex("ef0001010004020001000104"),
            EOFException.MISSING_HEADERS_TERMINATOR,
            id="EOF1I3540_0018",
        ),
        pytest.param(
            # Data size incomplete
            bytes.fromhex("ef000101000402000100010400"),
            EOFException.INCOMPLETE_SECTION_SIZE,
            id="EOF1I3540_0019",
        ),
        pytest.param(
            # No section terminator after data section size
            bytes.fromhex("ef00010100040200010001040002"),
            EOFException.MISSING_HEADERS_TERMINATOR,
            id="EOF1I3540_0020",
        ),
        pytest.param(
            # No type section contents
            bytes.fromhex("ef0001010004020001000104000200"),
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="EOF1I3540_0021",
        ),
        pytest.param(
            # Type section contents (no outputs and max stack)
            bytes.fromhex("ef000101000402000100010400020000"),
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="EOF1I3540_0022",
        ),
        pytest.param(
            # Type section contents (no max stack)
            bytes.fromhex("ef00010100040200010001040002000000"),
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="EOF1I3540_0023",
        ),
        pytest.param(
            # Type section contents (max stack incomplete)
            bytes.fromhex("ef0001010004020001000104000200000000"),
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="EOF1I3540_0024",
        ),
        pytest.param(
            # No code section contents
            bytes.fromhex("ef000101000402000100010400020000000000"),
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="EOF1I3540_0025",
        ),
        pytest.param(
            # Code section contents incomplete
            bytes.fromhex("ef0001010004020001002904000000000000027f"),
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="EOF1I3540_0026",
        ),
        pytest.param(
            # Trailing bytes after code section
            bytes.fromhex("ef0001 010004 0200010001 040000 00 00800000 fe aabbcc"),
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="EOF1I3540_0027",
        ),
        pytest.param(
            # Trailing bytes after code section with wrong first section type
            bytes.fromhex("ef0001 010004 0200010001 040000 00 00000000 fe aabbcc"),
            EOFException.INVALID_FIRST_SECTION_TYPE,
            id="EOF1I3540_0027_orig",
        ),
        pytest.param(
            # Empty code section
            bytes.fromhex("ef000101000402000100000400000000000000"),
            EOFException.ZERO_SECTION_SIZE,
            id="EOF1I3540_0028",
        ),
        pytest.param(
            # Code section preceding type section
            bytes.fromhex("ef000102000100010100040400020000000000feaabb"),
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1I3540_0030",
        ),
        pytest.param(
            # Data section preceding type section
            bytes.fromhex("ef000104000201000402000100010000000000feaabb"),
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1I3540_0031",
        ),
        pytest.param(
            # Data section preceding code section
            bytes.fromhex("ef000101000404000202000100010000000000feaabb"),
            EOFException.MISSING_CODE_HEADER,
            id="EOF1I3540_0032",
        ),
        pytest.param(
            # Data section without code section
            bytes.fromhex("ef00010100040400020000000000aabb"),
            EOFException.MISSING_CODE_HEADER,
            id="EOF1I3540_0033",
        ),
        pytest.param(
            # No data section
            bytes.fromhex("ef000101000402000100010000000000fe"),
            EOFException.MISSING_DATA_SECTION,
            id="EOF1I3540_0034",
        ),
        pytest.param(
            # Trailing bytes after data section
            Container(
                sections=[
                    Section.Code(Op.INVALID),
                    Section.Data("aabb"),
                ],
                extra="ccdd",
                expected_bytecode="ef0001 010004 0200010001 040002 00 00800000 fe aabbccdd",
            ),
            EOFException.INVALID_SECTION_BODIES_SIZE,
            id="EOF1I3540_0035",
        ),
        pytest.param(
            # Trailing bytes after data section with wrong first section type
            bytes.fromhex("ef0001 010004 0200010001 040002 00 00000000 fe aabbccdd"),
            EOFException.INVALID_FIRST_SECTION_TYPE,
            id="EOF1I3540_0035_orig",
        ),
        pytest.param(
            # Multiple data sections
            bytes.fromhex("ef000101000402000100010400020400020000000000feaabbaabb"),
            EOFException.MISSING_TERMINATOR,
            id="EOF1I3540_0036",
        ),
        pytest.param(
            # Multiple code and data sections
            bytes.fromhex("ef000101000802000200010001040002040002000000000000000000fefeaabbaabb"),
            EOFException.MISSING_TERMINATOR,
            id="EOF1I3540_0037",
        ),
        pytest.param(
            # Unknown section ID (at the beginning)
            bytes.fromhex("ef000105000101000402000100010400000000000000fe"),
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1I3540_0038",
        ),
        pytest.param(
            # Unknown section ID (at the beginning)
            bytes.fromhex("ef000106000101000402000100010400000000000000fe"),
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1I3540_0039",
        ),
        pytest.param(
            # Unknown section ID (at the beginning)
            bytes.fromhex("ef0001ff000101000402000100010400000000000000fe"),
            EOFException.MISSING_TYPE_HEADER,
            id="EOF1I3540_0040",
        ),
        pytest.param(
            # Unknown section ID (after types section)
            bytes.fromhex("ef000101000405000102000100010400000000000000fe"),
            EOFException.MISSING_CODE_HEADER,
            id="EOF1I3540_0041",
        ),
        pytest.param(
            # Unknown section ID (after types section)
            bytes.fromhex("ef000101000406000102000100010400000000000000fe"),
            EOFException.MISSING_CODE_HEADER,
            id="EOF1I3540_0042",
        ),
        pytest.param(
            # Unknown section ID (after types section)
            bytes.fromhex("ef0001010004ff000102000100010400000000000000fe"),
            EOFException.MISSING_CODE_HEADER,
            id="EOF1I3540_0043",
        ),
        pytest.param(
            # Unknown section ID (after code section)
            bytes.fromhex("ef000101000402000100010500010400000000000000fe"),
            EOFException.MISSING_DATA_SECTION,
            id="EOF1I3540_0044",
        ),
        pytest.param(
            # Unknown section ID (after code section)
            bytes.fromhex("ef000101000402000100010600010400000000000000fe"),
            EOFException.MISSING_DATA_SECTION,
            id="EOF1I3540_0045",
        ),
        pytest.param(
            # Unknown section ID (after code section)
            bytes.fromhex("ef00010100040200010001ff00010400000000000000fe"),
            EOFException.MISSING_DATA_SECTION,
            id="EOF1I3540_0046",
        ),
        pytest.param(
            # Unknown section ID (after data section)
            bytes.fromhex("ef000101000402000100010400000500010000000000fe"),
            EOFException.MISSING_TERMINATOR,
            id="EOF1I3540_0047",
        ),
        pytest.param(
            # Unknown section ID (after data section)
            bytes.fromhex("ef000101000402000100010400000600010000000000fe"),
            EOFException.MISSING_TERMINATOR,
            id="EOF1I3540_0048",
        ),
        pytest.param(
            # Unknown section ID (after data section)
            bytes.fromhex("ef00010100040200010001040000ff00010000000000fe"),
            EOFException.MISSING_TERMINATOR,
            id="EOF1I3540_0049",
        ),
        # TODO: Duplicated tests
        # The following test cases are duplicates but added to confirm test coverage is retained.
        pytest.param(
            Container(
                name="EOF1I3540_0001 (Invalid) No magic",
                raw_bytes="ef",
            ),
            EOFException.INVALID_MAGIC,
        ),
        pytest.param(
            Container(
                name="EOF1I3540_0002 (Invalid) Invalid magic",
                raw_bytes="ef010101000402000100010400000000000000fe",
            ),
            EOFException.INVALID_MAGIC,
        ),
        pytest.param(
            Container(
                name="EOF1I3540_0003",
                raw_bytes="ef020101000402000100010400000000000000fe",
            ),
            EOFException.INVALID_MAGIC,
        ),
        pytest.param(
            Container(
                name="EOF1I3540_0004",
                raw_bytes="efff0101000402000100010400000000000000fe",
            ),
            EOFException.INVALID_MAGIC,
        ),
        pytest.param(
            Container(
                name="EOF1I3540_0005 (Invalid) No version",
                raw_bytes="ef00",
            ),
            EOFException.INVALID_VERSION,
        ),
        pytest.param(
            Container(
                name="EOF1I3540_0006 (Invalid) Invalid version",
                raw_bytes="ef000001000402000100010400000000000000fe",
            ),
            EOFException.INVALID_VERSION,
        ),
        pytest.param(
            Container(
                name="EOF1I3540_0007",
                raw_bytes="ef000201000402000100010400000000000000fe",
            ),
            EOFException.INVALID_VERSION,
        ),
        pytest.param(
            Container(
                name="EOF1I3540_0008",
                raw_bytes="ef00ff01000402000100010400000000000000fe",
            ),
            EOFException.INVALID_VERSION,
        ),
    ],
)
def test_migrated_valid_invalid(
    eof_test: EOFTestFiller,
    eof_code: Container | bytes,
    exception: EOFException | None,
):
    """
    Verify EOF container construction and exception
    """
    eof_test(
        data=eof_code,
        expect_exception=exception,
    )
