from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.schemas import TransactionListResponse, TransactionOut, SuggestionOut
from app.database import get_db
from app.models import Transaction, Vendor
from app.utils import get_category_suggestions

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

@router.get("", response_model=TransactionListResponse)
def list_transactions(
    page: int = Query(1, ge=1),
    category: str = Query(""),
    vendor: str = Query(""),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    search: str = Query(""),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    exclude_filter: str = Query(""),
    db: Session = Depends(get_db),
):
    qs = db.query(Transaction).options(joinedload(Transaction.vendor)).order_by(Transaction.actual_date.desc())

    if category:
        qs = qs.filter(Transaction.category.ilike(f"%{category}%"))
    if vendor:
        qs = qs.join(Transaction.vendor).filter(Vendor.name.ilike(f"%{vendor}%"))
    if start_date:
        qs = qs.filter(Transaction.actual_date >= start_date)
    if end_date:
        qs = qs.filter(Transaction.actual_date <= end_date)
    if search:
        qs = qs.filter(
            or_(
                Transaction.category.ilike(f"%{search}%"),
                Transaction.sub_category.ilike(f"%{search}%"),
                Transaction.narration.ilike(f"%{search}%"),
                Transaction.notes.ilike(f"%{search}%"),
                Transaction.vendor.has(Vendor.name.ilike(f"%{search}%")),
            )
        )
    if min_amount is not None:
        qs = qs.filter(Transaction.debit_amount >= min_amount)
    if max_amount is not None:
        qs = qs.filter(Transaction.debit_amount <= max_amount)
    if exclude_filter.lower() == "true":
        qs = qs.filter(Transaction.exclude == True)
    elif exclude_filter.lower() == "false":
        qs = qs.filter(Transaction.exclude == False)

    total = qs.count()
    page_size = 50
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, pages)
    items = qs.offset((page - 1) * page_size).limit(page_size).all()

    transactions_response = []
    for txn in items:
        s1, s2 = get_category_suggestions(db, txn.vendor)
        transactions_response.append(
            TransactionOut(
                id=txn.id,
                debit_date=txn.debit_date,
                actual_date=txn.actual_date,
                narration=txn.narration,
                txn_number=txn.txn_number,
                debit_amount=txn.debit_amount,
                credit_amount=txn.credit_amount,
                category=txn.category or "",
                sub_category=txn.sub_category or "",
                notes=txn.notes or "",
                exclude=txn.exclude,
                vendor_id=txn.vendor_id,
                vendor_name=txn.vendor.name if txn.vendor else None,
                suggestion1=SuggestionOut(**s1),
                suggestion2=SuggestionOut(**s2),
            )
        )
    return TransactionListResponse(
        items=transactions_response,
        total=total,
        page=page,
        pages=pages,
    )
