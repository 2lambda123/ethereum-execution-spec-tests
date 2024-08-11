"""
EOF Container, test custom_size field for sections
"""

from enum import IntEnum

import pytest

from ethereum_test_tools import EOFException, EOFTestFiller
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools.eof.v1 import Container, Section, SectionKind

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


class SectionSize(IntEnum):
    """
    Enum for the section size
    """

    NORMAL = -1
    ZERO = 0
    UNDERSIZE = 2
    OVERSIZE = 100
    HUGE = 0x8000
    MAX = 0xFFFF

    def __str__(self) -> str:
        """
        Returns the string representation of the section kind
        """
        return self.name


@pytest.mark.parametrize(
    "section_kind, section_size, exception",
    [
        (SectionKind.DATA, SectionSize.NORMAL, None),
        (SectionKind.DATA, SectionSize.ZERO, EOFException.INVALID_SECTION_BODIES_SIZE),
        (SectionKind.DATA, SectionSize.UNDERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE),
        (SectionKind.DATA, SectionSize.OVERSIZE, EOFException.TOPLEVEL_CONTAINER_TRUNCATED),
        (SectionKind.DATA, SectionSize.HUGE, EOFException.TOPLEVEL_CONTAINER_TRUNCATED),
        (SectionKind.DATA, SectionSize.MAX, EOFException.TOPLEVEL_CONTAINER_TRUNCATED),
        (SectionKind.CODE, SectionSize.NORMAL, None),
        (SectionKind.CODE, SectionSize.ZERO, EOFException.ZERO_SECTION_SIZE),
        (SectionKind.CODE, SectionSize.UNDERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE),
        (SectionKind.CODE, SectionSize.OVERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE),
        (SectionKind.CODE, SectionSize.HUGE, EOFException.INVALID_SECTION_BODIES_SIZE),
        (SectionKind.CODE, SectionSize.MAX, EOFException.INVALID_SECTION_BODIES_SIZE),
        (SectionKind.TYPE, SectionSize.NORMAL, None),
        (SectionKind.TYPE, SectionSize.ZERO, EOFException.ZERO_SECTION_SIZE),
        (SectionKind.TYPE, SectionSize.UNDERSIZE, EOFException.INVALID_TYPE_SECTION_SIZE),
        (SectionKind.TYPE, SectionSize.OVERSIZE, EOFException.INVALID_SECTION_BODIES_SIZE),
        (SectionKind.TYPE, SectionSize.HUGE, EOFException.INVALID_SECTION_BODIES_SIZE),
        (SectionKind.TYPE, SectionSize.MAX, EOFException.INVALID_SECTION_BODIES_SIZE),
    ],
)
def test_section_size(
    eof_test: EOFTestFiller,
    section_size: SectionSize,
    section_kind: SectionKind,
    exception: EOFException,
):
    """
    Test custom_size is auto, more or less then the actual size of the section
    """
    eof_code = Container()

    if section_size != SectionSize.NORMAL and section_kind == SectionKind.TYPE:
        eof_code.sections.append(
            Section(
                kind=SectionKind.TYPE,
                data="0x00800001",
                custom_size=section_size,
            ),
        )

    if section_size != SectionSize.NORMAL and section_kind == SectionKind.CODE:
        eof_code.sections.append(
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                max_stack_height=1,
                custom_size=section_size,
            )
        )
    else:
        eof_code.sections.append(
            Section.Code(
                code=Op.ADDRESS + Op.POP + Op.STOP,
                max_stack_height=1,
            )
        )

    if section_size != SectionSize.NORMAL and section_kind == SectionKind.DATA:
        eof_code.sections.append(Section.Data("0x00daaa", custom_size=section_size))
    else:
        eof_code.sections.append(Section.Data("0x00aaaa"))

    eof_test(
        data=eof_code,
        expect_exception=exception,
    )


@pytest.mark.parametrize(
    "truncation_len, exception",
    [
        # The original container is not valid by itself because its 2-byte code section
        # starts with the terminating instruction: INVALID.
        pytest.param(0, EOFException.UNREACHABLE_INSTRUCTIONS),
        pytest.param(1, EOFException.INVALID_SECTION_BODIES_SIZE, id="EOF1_truncated_section_2"),
        pytest.param(3, EOFException.INVALID_SECTION_BODIES_SIZE, id="EOF1_truncated_section_1"),
        pytest.param(6, EOFException.INVALID_SECTION_BODIES_SIZE, id="EOF1_truncated_section_0"),
    ],
)
def test_truncated_container_without_data(
    eof_test: EOFTestFiller,
    truncation_len: int,
    exception: EOFException,
):
    """
    This test takes a semi-valid container and removes some bytes from its tail.
    Migrated from EOFTests/efValidation/EOF1_truncated_section_.json (cases without data section).
    """
    container = Container(sections=[Section.Code(Op.INVALID + Op.INVALID)])
    bytecode = bytes(container)
    eof_test(
        data=bytecode[: len(bytecode) - truncation_len],
        expect_exception=exception,
    )


@pytest.mark.parametrize(
    "truncation_len, exception",
    [
        pytest.param(0, None),
        pytest.param(1, EOFException.TOPLEVEL_CONTAINER_TRUNCATED, id="EOF1_truncated_section_4"),
        pytest.param(2, EOFException.TOPLEVEL_CONTAINER_TRUNCATED, id="EOF1_truncated_section_3"),
    ],
)
def test_truncated_container_with_data(
    eof_test: EOFTestFiller,
    truncation_len: int,
    exception: EOFException,
):
    """
    This test takes a valid container with data and removes some bytes from its tail.
    Migrated from EOFTests/efValidation/EOF1_truncated_section_.json (cases with data section).
    """
    container = Container(sections=[Section.Code(Op.INVALID), Section.Data("aabb")])
    bytecode = bytes(container)
    eof_test(
        data=bytecode[: len(bytecode) - truncation_len],
        expect_exception=exception,
    )
