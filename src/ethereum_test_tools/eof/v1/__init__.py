"""
EVM Object Format Version 1 Library to generate bytecode for testing purposes
"""

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum
from functools import cached_property
from typing import Dict, List, Optional, Tuple

from ...common import Bytes
from ...common.types import CopyValidateModel
from ...exceptions import EOFException
from ...vm.opcode import Opcodes as Op
from ..constants import EOF_HEADER_TERMINATOR, EOF_MAGIC

VERSION_NUMBER = bytes([0x01])
VERSION_MAX_SECTION_KIND = 3


class SectionKind(IntEnum):
    """
    Enum class of V1 valid section kind values
    """

    TYPE = 1
    CODE = 2
    CONTAINER = 3
    DATA = 4


class AutoSection(Enum):
    """
    Enum class for auto section generation approach
    """

    AUTO = 1
    ONLY_HEADER = 2
    ONLY_BODY = 3
    NONE = 4


SUPPORT_MULTI_SECTION_HEADER = [SectionKind.CODE, SectionKind.CONTAINER]


class Section(CopyValidateModel):
    """
    Class that represents a section in an EOF V1 container.
    """

    data: Bytes = Bytes(b"")
    """
    Data to be contained by this section.
    Can be SupportsBytes, another EOF container or any other abstract data.
    """
    custom_size: int | None = None
    """
    Size value to be used in the header.
    If set to None, the header is built with length of the data.
    """
    kind: SectionKind | int
    """
    Kind of section that is represented by this object.
    Can be any `int` outside of the values defined by `SectionKind`
    for testing purposes.
    """
    force_type_listing: bool = False
    """
    Forces this section to appear in the TYPE section at the beginning of the
    container.
    """
    code_inputs: int = 0
    """
    Data stack items consumed by this code section (function)
    """
    code_outputs: int = 0
    """
    Data stack items produced by or expected at the end of this code section
    (function)
    """
    max_stack_height: int = 0
    """
    Maximum height data stack reaches during execution of code section.
    """
    auto_max_stack_height: bool = False
    """
    Whether to automatically compute the best suggestion for the
    max_stack_height value for this code section.
    """
    auto_code_inputs_outputs: bool = False
    """
    Whether to automatically compute the best suggestion for the code_inputs,
    code_outputs values for this code section.
    """

    @cached_property
    def header(self) -> bytes:
        """
        Get formatted header for this section according to its contents.
        """
        size = self.custom_size
        if size is None:
            if self.data is None:
                raise Exception("Attempted to build header without section data")
            size = len(Bytes(self.data))
        if self.kind == SectionKind.CODE:
            raise Exception("Need container-wide view of code sections to generate header")
        else:
            return self.kind.to_bytes(1, byteorder="big") + size.to_bytes(2, byteorder="big")

    def with_max_stack_height(self, max_stack_height) -> "Section":
        """
        Creates a copy of the section with `max_stack_height` set to the
        specified value.
        """
        return self.copy(max_stack_height=max_stack_height)

    def with_auto_max_stack_height(self) -> "Section":
        """
        Creates a copy of the section with `auto_max_stack_height` set to True.
        """
        return self.copy(auto_max_stack_height=True)

    def with_auto_code_inputs_outputs(self) -> "Section":
        """
        Creates a copy of the section with `auto_code_inputs_outputs` set to
        True.
        """
        return self.copy(auto_code_inputs_outputs=True)


class Bytecode:
    """Abstract class used to define a class that generates bytecode."""

    @property
    @abstractmethod
    def bytecode(self) -> bytes:
        """
        Converts the sections into bytecode.
        """
        raise NotImplementedError

    def __bytes__(self) -> bytes:
        """
        Returns the bytecode of the container.
        """
        return self.bytecode

    def __len__(self) -> int:
        """
        Returns the length of the container bytecode.
        """
        return len(self.bytecode)


class Container(CopyValidateModel, Bytecode):
    """
    Class that represents an EOF V1 container.
    """

    name: Optional[str] = None
    """
    Name of the container
    """
    sections: Optional[List[Section]] = None
    """
    List of sections in the container
    """
    custom_magic: Optional[int] = None
    """
    Custom magic value used to override the mandatory EOF value for testing
    purposes.
    """
    custom_version: Optional[int] = None
    """
    Custom version value used to override the mandatory EOF V1 value
    for testing purposes.
    """
    custom_terminator: Optional[Bytes] = None
    """
    Custom terminator bytes used to terminate the header.
    """
    extra: Optional[Bytes] = None
    """
    Extra data to be appended at the end of the container, which will
    not be considered part of any of the sections, for testing purposes.
    """
    auto_type_section: AutoSection = AutoSection.AUTO
    """
    Automatically generate a `TYPE` section based on the
    included `CODE` kind sections.
    """
    auto_data_section: bool = True
    """
    Automatically generate a `DATA` section.
    """
    auto_sort_sections: AutoSection = AutoSection.AUTO
    """
    Automatically sort sections for the header and body:
    Headers: type section first, all code sections, container sections, last
                data section(s)
    Body: type section first, all code sections, data section(s), last
                container sections
    """
    validity_error: EOFException | None = None
    """
    Optional error expected for the container.
    """
    raw_bytes: Optional[Bytes] = None
    """
    Optional raw bytes that represent the container.
    Used to have a cohesive type among all test cases, even those that do not
    resemble a valid EOF V1 container.
    """

    @cached_property
    def bytecode(self) -> bytes:
        """
        Converts the EOF V1 Container into bytecode.
        """
        if self.raw_bytes is not None:
            assert self.sections is None or len(self.sections) == 0
            return self.raw_bytes

        assert self.sections is not None

        c = bytes([0xEF])

        c += EOF_MAGIC if self.custom_magic is None else self.custom_magic.to_bytes(1, "big")

        c += (
            VERSION_NUMBER
            if self.custom_version is None
            else self.custom_version.to_bytes(1, "big")
        )

        # Copy the sections so we can add the `type` section
        sections = self.sections.copy()

        auto_type_section = self.auto_type_section in (
            AutoSection.AUTO,
            AutoSection.ONLY_BODY,
            AutoSection.ONLY_HEADER,
        )
        if auto_type_section and count_sections(sections, SectionKind.TYPE) == 0:
            type_section_data: bytes = bytes()
            for s in sections:
                if s.kind == SectionKind.CODE or s.force_type_listing:
                    code_inputs, code_outputs, max_stack_height = (
                        s.code_inputs,
                        s.code_outputs,
                        s.max_stack_height,
                    )
                    if s.auto_max_stack_height or s.auto_code_inputs_outputs:
                        (
                            auto_code_inputs,
                            auto_code_outputs,
                            auto_max_height,
                        ) = compute_code_stack_values(s.data)
                        if s.auto_max_stack_height:
                            max_stack_height = auto_max_height
                        if s.auto_code_inputs_outputs:
                            code_inputs, code_outputs = (
                                auto_code_inputs,
                                auto_code_outputs,
                            )

                    type_section_data += make_type_def(code_inputs, code_outputs, max_stack_height)

            sections = [Section(kind=SectionKind.TYPE, data=type_section_data)] + sections

        if self.auto_data_section:
            if count_sections(sections, SectionKind.DATA) > 0:
                pass  # already exists
            else:
                sections.append(Section(kind=SectionKind.DATA, data="0x"))

        original_sections = sections
        if self.auto_sort_sections in (AutoSection.AUTO, AutoSection.ONLY_HEADER):
            # Sort sections for the header
            sections = (
                [s for s in sections if s.kind == SectionKind.TYPE]
                + [s for s in sections if s.kind == SectionKind.CODE]
                + [s for s in sections if s.kind == SectionKind.CONTAINER]
                + [s for s in sections if s.kind == SectionKind.DATA]
                + [
                    s
                    for s in sections
                    if s.kind
                    not in [
                        SectionKind.TYPE,
                        SectionKind.CODE,
                        SectionKind.DATA,
                        SectionKind.CONTAINER,
                    ]
                ]
            )

        # Add headers
        concurrent_kind_sections: List[Section] = []
        for s in sections:
            if s.kind == SectionKind.TYPE and self.auto_type_section == AutoSection.ONLY_BODY:
                continue

            if len(concurrent_kind_sections) == 0:
                concurrent_kind_sections.append(s)
                continue
            if s.kind == concurrent_kind_sections[0].kind:
                concurrent_kind_sections.append(s)
                continue
            else:
                c += create_sections_header(
                    concurrent_kind_sections[0].kind, concurrent_kind_sections
                )
                concurrent_kind_sections = [s]

        if len(concurrent_kind_sections) > 0:
            c += create_sections_header(concurrent_kind_sections[0].kind, concurrent_kind_sections)

        # Add header terminator
        if self.custom_terminator is not None:
            c += self.custom_terminator
        else:
            c += EOF_HEADER_TERMINATOR

        sections = original_sections
        if self.auto_sort_sections in (AutoSection.AUTO, AutoSection.ONLY_BODY):
            # Sort sections for the body
            sections = (
                [s for s in sections if s.kind == SectionKind.TYPE]
                + [s for s in sections if s.kind == SectionKind.CODE]
                + [s for s in sections if s.kind == SectionKind.DATA]
                + [s for s in sections if s.kind == SectionKind.CONTAINER]
                + [
                    s
                    for s in sections
                    if s.kind
                    not in [
                        SectionKind.TYPE,
                        SectionKind.CODE,
                        SectionKind.DATA,
                        SectionKind.CONTAINER,
                    ]
                ]
            )

        # Add section bodies
        for s in sections:
            if s.kind == SectionKind.TYPE and self.auto_type_section == AutoSection.ONLY_HEADER:
                continue
            if s.data:
                c += s.data

        # Add extra (garbage)
        if self.extra is not None:
            c += self.extra

        return c


@dataclass(kw_only=True)
class Initcode(Bytecode):
    """
    Helper class used to generate initcode for the specified deployment code,
    using EOF V1 container as init code.
    """

    name: str = "EOF V1 Initcode"
    """
    Name used to identify the initcode.
    """
    deploy_container: Container
    """
    Container to be deployed.
    """

    @cached_property
    def init_container(self) -> Container:
        """
        Generate a container that will be used as the initcode.
        """
        return Container(
            sections=[
                Section(
                    kind=SectionKind.CODE,
                    data=Op.RETURNCONTRACT(0, 0, 0),
                    max_stack_height=2,
                ),
                Section(
                    kind=SectionKind.CONTAINER,
                    data=bytes(self.deploy_container),
                ),
            ],
        )

    @cached_property
    def bytecode(self) -> bytes:
        """
        Generate legacy initcode that inits a contract with the specified code.
        The initcode can be padded to a specified length for testing purposes.
        """
        initcode = Container(
            sections=[
                Section(
                    data=Op.CREATE3(0, 0, 0, 0, len(self.deploy_container)) + Op.STOP(),
                    kind=SectionKind.CODE,
                    max_stack_height=4,
                ),
                Section(
                    kind=SectionKind.CONTAINER,
                    data=self.init_container,
                ),
            ]
        )

        return bytes(initcode)


def create_sections_header(kind: SectionKind | int, sections: List[Section]) -> bytes:
    """
    Creates the single code header for all code sections contained in
    the list.
    """
    h = bytes()
    if sections[0].kind in SUPPORT_MULTI_SECTION_HEADER:
        h += kind.to_bytes(1, "big")
        h += len(sections).to_bytes(2, "big")
        for cs in sections:
            if cs.custom_size:
                h += cs.custom_size.to_bytes(2, "big")
            else:
                if isinstance(cs.data, Container):
                    h += len(cs.data).to_bytes(2, "big")
                else:
                    h += len(cs.data).to_bytes(2, "big")
    else:
        for s in sections:
            h += s.header

    return h


def count_sections(sections: List[Section], kind: SectionKind | int) -> int:
    """
    Counts sections from a list that match a specific kind
    """
    return len([s for s in sections if s.kind == kind])


def make_type_def(inputs, outputs, max_stack_height) -> bytes:
    """
    Returns a serialized type section entry for the given values.
    """
    out = bytes()
    out += inputs.to_bytes(
        length=((inputs.bit_length() - 1) // 8 + 1) if inputs > 0 else 1,
        byteorder="big",
    )
    out += outputs.to_bytes(
        length=((outputs.bit_length() - 1) // 8 + 1) if outputs > 0 else 1,
        byteorder="big",
    )
    out += max_stack_height.to_bytes(
        length=((outputs.bit_length() - 1) // 8 + 1) if outputs > 255 else 2,
        byteorder="big",
    )
    return out


OPCODE_MAP: Dict[int, Op] = {x.int(): x for x in Op}


def compute_code_stack_values(code: bytes) -> Tuple[int, int, int]:
    """
    Computes the stack values for the given bytecode.

    TODO: THIS DOES NOT WORK WHEN THE RJUMP* JUMPS BACKWARDS (and many other
    things).
    """
    i = 0
    stack_height = 0
    min_stack_height = 0
    max_stack_height = 0

    # compute type annotation
    while i < len(code):
        op = OPCODE_MAP.get(code[i])
        if op is None:
            return (0, 0, 0)
        elif op == Op.RJUMPV:
            i += 1
            if i < len(code):
                count = code[i]
                i += count * 2
        else:
            i += 1 + op.data_portion_length

        stack_height -= op.popped_stack_items
        min_stack_height = min(stack_height, min_stack_height)
        stack_height += op.pushed_stack_items
        max_stack_height = max(stack_height, max_stack_height)
    if stack_height < 0:
        stack_height = 0
    return (abs(min_stack_height), stack_height, max_stack_height)
