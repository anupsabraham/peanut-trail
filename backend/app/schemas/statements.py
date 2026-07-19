"""Schemas for non-persistent statement previews."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class StatementPreviewTransaction(BaseModel):
    """One parsed row the client can review before saving."""

    client_id: str
    source_row: int
    debit_date: date
    actual_date: date
    narration: str
    txn_number: str
    debit_amount: Decimal
    credit_amount: Decimal
    category: str = ""
    sub_category: str = ""
    notes: str = ""
    exclude: bool = False
    was_repaired: bool = False


class StatementParseIssue(BaseModel):
    """A file or row problem returned to the statement-review UI."""

    code: str
    message: str
    source_row: int | None = None
    raw_values: list[str] | None = None


class StatementPreviewResponse(BaseModel):
    """A statement preview with new rows and parsing feedback."""

    transactions: list[StatementPreviewTransaction]
    issues: list[StatementParseIssue]
    skipped_existing_count: int
