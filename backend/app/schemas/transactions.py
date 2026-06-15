from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SuggestionOut(BaseModel):
    category: str | None = None
    sub_category: str | None = None
    notes: str | None = None
    confidence: float = 0.0
    auto_prefill: bool = False


class TransactionBase(BaseModel):
    debit_date: date
    actual_date: date
    narration: str
    txn_number: str
    debit_amount: Decimal = Decimal(0)
    credit_amount: Decimal = Decimal(0)
    category: str = ""
    sub_category: str = ""
    notes: str = ""
    exclude: bool = False


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    debit_date: date | None = None
    actual_date: date | None = None
    narration: str | None = None
    txn_number: str | None = None
    debit_amount: Decimal | None = None
    credit_amount: Decimal | None = None
    category: str | None = None
    sub_category: str | None = None
    notes: str | None = None
    exclude: bool | None = None


class TransactionOut(TransactionBase):
    id: int
    vendor_id: int | None = None
    vendor_name: str | None = None
    suggestion1: SuggestionOut | None = None
    suggestion2: SuggestionOut | None = None
    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    pages: int
