"""Global parser resolver."""

from importlib import import_module
from pathlib import Path
from typing import Protocol

from app.parsers.types import Bank, FileType, ParseResult, StatementType, UnsupportedStatementError


class StatementParser(Protocol):
    """Contract implemented by every statement parser."""

    def parse(self, file_content: bytes) -> ParseResult:
        """Parse statement content without writing to the database."""


def detect_file_type(filename: str | None, content_type: str | None) -> FileType:
    """Detect the file type from the filename and content type."""
    if not filename or not content_type:
        message = "Unsupported file: No filename or content-type"
        raise UnsupportedStatementError(message)
    file_type_from_extension = _infer_from_extension(filename)
    file_type_from_content_type = _infer_from_content_type(content_type)

    if file_type_from_extension != file_type_from_content_type:
        message = (
            f"Unsupported file: Extension {Path(filename).suffix.lstrip('.')} doesn't match the "
            f"content-type: {content_type}."
        )
        raise UnsupportedStatementError(message)

    return file_type_from_extension


def _infer_from_extension(filename: str) -> FileType:
    """Infer the file type from the extension of the filename."""
    extension = Path(filename).suffix.lower().lstrip(".")
    match extension:
        case "csv" | "txt":
            return FileType.CSV
        case "xls" | "xlsx":
            return FileType.XLS
        case "pdf":
            return FileType.PDF
        case _:
            message = f"Unsupported file: Extension: {extension}"
            raise UnsupportedStatementError(message)


def _infer_from_content_type(content_type: str) -> FileType:
    """Infer the file type from the content-type of the file."""
    match content_type.lower():
        case "text/csv" | "text/plain":
            return FileType.CSV
        case "application/vnd.ms-excel" | "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return FileType.XLS
        case "application/pdf":
            return FileType.PDF
        case _:
            message = f"Unsupported file type: {content_type}"
            raise UnsupportedStatementError(message)


def resolve_parser(bank: Bank, statement_type: StatementType, file_type: FileType) -> StatementParser:
    """Return the parser supported by the selected bank and statement format."""
    try:
        bank_module = import_module(f"app.parsers.{bank.value}")
    except ModuleNotFoundError as e:
        message = f"Unsupported bank: {bank.value}"
        raise UnsupportedStatementError(message) from e

    return bank_module.resolve_parser(statement_type, file_type)
