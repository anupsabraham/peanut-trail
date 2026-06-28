from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Transaction
from app.schemas import TransactionFilters, TransactionListResponse, TransactionOut, TransactionUpdate
from app.services.transactions import apply_transaction_filters
from app.utils import get_transaction_out_obj

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

DB = Annotated[Session, Depends(get_db)]
Filters = Annotated[TransactionFilters, Depends()]


@router.get("")
def list_transactions(db: DB, filters: Filters) -> TransactionListResponse:
    """List all transactions.

    Returns the list of all transactions. Query strings contain filters if anything applied. The response is also
    paginated.
    """
    qs = db.query(Transaction).options(joinedload(Transaction.vendor)).order_by(Transaction.actual_date.desc())
    qs = apply_transaction_filters(qs, filters=filters)

    total = qs.count()
    page_size = 50
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(filters.page, pages)
    items = qs.offset((page - 1) * page_size).limit(page_size).all()

    transactions_response = [get_transaction_out_obj(db, txn) for txn in items if txn]

    return TransactionListResponse(
        items=transactions_response,
        total=total,
        page=page,
        pages=pages,
    )


@router.get("/meta/categories/list")
def get_categories(db: DB) -> list[str]:
    """Return all the categories saved in db."""
    rows = (
        db.query(Transaction.category, func.sum(Transaction.debit_amount).label("total"))
        .filter(Transaction.category != "")
        .filter(Transaction.exclude == False)  # noqa: E712
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.debit_amount).desc())
        .all()
    )

    return [r[0] for r in rows]


@router.get("/meta/subcategories/list")
def get_subcategories(db: DB, category: Annotated[str, Query()] = "") -> list[str]:
    """Return all the subcategories, optionally filtered by category."""
    qs = (
        db.query(Transaction.sub_category, func.sum(Transaction.debit_amount).label("total"))
        .filter(Transaction.sub_category != "")
        .filter(Transaction.exclude == False)  # noqa: E712
    )
    if category:
        qs = qs.filter(Transaction.category == category)

    rows = (
        qs.group_by(Transaction.category, Transaction.sub_category)
        .order_by(func.sum(Transaction.debit_amount).desc())
        .all()
    )
    return [r[0] for r in rows]


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: DB) -> None:
    """Delete a transaction using transaction id."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No transaction with id {transaction_id} found."
        )

    db.delete(txn)
    db.commit()


@router.patch("/{transaction_id}")
def update_transaction(transaction_id: int, update: TransactionUpdate, db: DB) -> TransactionOut:
    """Update a transaction identified by transaction id."""
    txn = db.query(Transaction).options(joinedload(Transaction.vendor)).filter(Transaction.id == transaction_id).first()

    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No transaction with id {transaction_id} found."
        )

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)

    db.commit()
    db.refresh(txn)

    return get_transaction_out_obj(db, txn)
