from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from typing import Optional


class SuggestionOut(BaseModel):
    category: Optional[str] = None
    sub_category: Optional[str] = None
    notes: Optional[str] = None
    confidence: float = 0.0
    auto_prefill: bool = False


class TransactionBase(BaseModel):
    debit_date: date
    actual_date: date
    narration: str
    txn_number: str
    debit_amount: Decimal = Decimal("0")
    credit_amount: Decimal = Decimal("0")
    category: str = ""
    sub_category: str = ""
    notes: str = ""
    exclude: bool = False


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    debit_date: Optional[date] = None
    actual_date: Optional[date] = None
    narration: Optional[str] = None
    txn_number: Optional[str] = None
    debit_amount: Optional[Decimal] = None
    credit_amount: Optional[Decimal] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    notes: Optional[str] = None
    exclude: Optional[bool] = None


class TransactionOut(TransactionBase):
    id: int
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None
    suggestion1: Optional[SuggestionOut] = None
    suggestion2: Optional[SuggestionOut] = None
    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    pages: int