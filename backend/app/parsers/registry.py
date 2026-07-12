"""Global parser selection."""

from app.parsers import hdfc
from app.parsers.types import Bank, FileType, StatementParser, StatementType, UnsupportedStatementError


def resolve_parser(bank: Bank, statement_type: StatementType, file_type: FileType) -> StatementParser:
    """Return the parser supported by the selected bank and statement format."""
    if bank is Bank.HDFC:
        return hdfc.resolve_parser(statement_type, file_type)

    message = f"Unsupported bank: {bank.value}"
    raise UnsupportedStatementError(message)
