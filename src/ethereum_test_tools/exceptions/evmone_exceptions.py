"""
Evmone eof exceptions ENUM -> str mapper
"""
from dataclasses import dataclass

from bidict import frozenbidict

from .exceptions import EOFException


@dataclass
class ExceptionMessage:
    """Defines a mapping between an exception and a message."""

    exception: EOFException
    message: str


class EvmoneExceptionParser:
    """
    Translate between EEST exceptions and error strings returned by evmone.
    """

    _mapping_data = (
        # TODO EVMONE needs to differentiate when the section is missing in the header or body
        ExceptionMessage(EOFException.MISSING_STOP_OPCODE, "err: no_terminating_instruction"),
        ExceptionMessage(EOFException.MISSING_CODE_HEADER, "err: code_section_missing"),
        ExceptionMessage(EOFException.MISSING_TYPE_HEADER, "err: type_section_missing"),
        # TODO EVMONE these exceptions are too similar, this leeds to ambiguity
        ExceptionMessage(EOFException.MISSING_TERMINATOR, "err: header_terminator_missing"),
        ExceptionMessage(
            EOFException.MISSING_HEADERS_TERMINATOR, "err: section_headers_not_terminated"
        ),
        ExceptionMessage(EOFException.INVALID_VERSION, "err: eof_version_unknown"),
        ExceptionMessage(EOFException.INVALID_MAGIC, "err: invalid_prefix"),
        ExceptionMessage(
            EOFException.INVALID_FIRST_SECTION_TYPE, "err: invalid_first_section_type"
        ),
        ExceptionMessage(
            EOFException.INVALID_SECTION_BODIES_SIZE, "err: invalid_section_bodies_size"
        ),
        ExceptionMessage(EOFException.INVALID_TYPE_SIZE, "err: invalid_type_section_size"),
        ExceptionMessage(EOFException.INCOMPLETE_SECTION_SIZE, "err: incomplete_section_size"),
        ExceptionMessage(EOFException.INCOMPLETE_SECTION_NUMBER, "err: incomplete_section_number"),
        ExceptionMessage(EOFException.TOO_MANY_CODE_SECTIONS, "err: too_many_code_sections"),
        ExceptionMessage(EOFException.ZERO_SECTION_SIZE, "err: zero_section_size"),
    )

    def __init__(self) -> None:
        assert len(set(entry.exception for entry in self._mapping_data)) == len(
            self._mapping_data
        ), "Duplicate exception in _mapping_data"
        assert len(set(entry.message for entry in self._mapping_data)) == len(
            self._mapping_data
        ), "Duplicate message in _mapping_data"
        self.exception_to_message: frozenbidict = frozenbidict(
            {entry.exception: entry.message for entry in self._mapping_data}
        )

    def parse_exception(self, exception: EOFException) -> str:
        """Takes an EOFException and returns a formatted string."""
        message = self.exception_to_message.get(
            exception, f"EvmoneExceptionParser: Missing string for {exception}"
        )
        return message

    def rev_parse_exception(self, exception_string: str) -> EOFException:
        """Takes a string and tires to find matching exception"""
        exception = self.exception_to_message.inverse.get(
            exception_string, EOFException.UNDEFINED_EXCEPTION
        )
        return exception
