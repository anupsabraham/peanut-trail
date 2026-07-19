"""Shared types used by statement parsers."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum


class Bank(StrEnum):
    """Supported financial institutions."""

    HDFC = "hdfc"
    ICICI = "icici"


class StatementType(StrEnum):
    """Kinds of statements a bank can provide."""

    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"


class FileType(StrEnum):
    """Supported statement file formats."""

    CSV = "csv"
    XLS = "xls"
    PDF = "pdf"


class UnsupportedStatementError(ValueError):
    """Raised when no parser supports a selected statement format."""


@dataclass(frozen=True)
class ParsedTransaction:
    """A valid, non-persistent transaction extracted from a statement."""

    source_row: int
    debit_date: date
    actual_date: date
    narration: str
    txn_number: str
    debit_amount: Decimal
    credit_amount: Decimal
    raw_values: tuple[str, ...]
    was_repaired: bool = False


@dataclass(frozen=True)
class ParseIssue:
    """A file- or row-level problem that prevents reliable parsing."""

    code: str
    message: str
    source_row: int | None = None
    raw_values: tuple[str, ...] | None = None


@dataclass
class ParseResult:
    """The successful rows and issues found while parsing one statement."""

    transactions: list[ParsedTransaction] = field(default_factory=list)
    issues: list[ParseIssue] = field(default_factory=list)
