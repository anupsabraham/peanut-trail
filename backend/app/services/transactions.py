from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app import schemas, utils
from app.models import Transaction, Vendor


def create_import_transaction(db: Session, payload: schemas.transactions.TransactionImportCreate) -> Transaction:
    """Create one reviewed preview transaction and any requested split children.

    The caller controls the database transaction, allowing a bulk save to remain
    all-or-nothing.
    """
    _validate_import_splits(payload)
    transaction_data = payload.model_dump(exclude={"splits"})
    if payload.splits:
        transaction_data["exclude"] = True

    txn = Transaction(**transaction_data)
    utils.validate_transaction(txn)
    db.add(txn)
    db.flush()

    if payload.splits:
        utils.create_split_children(db, txn, payload.splits)
    return txn


def _validate_import_splits(payload: schemas.transactions.TransactionImportCreate) -> None:
    if not payload.splits:
        return
    if payload.credit_amount > Decimal(0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credit transactions cannot be split.")
    if len(payload.splits) == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction must be split into at least 2 parts.",
        )

    total = sum((split.debit_amount for split in payload.splits), start=Decimal(0))
    if total != payload.debit_amount:
        if total > payload.debit_amount:
            message = f"Total amount({total}) exceeds transaction amount({payload.debit_amount})"
        else:
            message = f"Total amount({total}) is lesser than transaction amount({payload.debit_amount})"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def apply_transaction_filters(qs: Query, filters: schemas.filters.TransactionFilters) -> Query:
    """Apply filters to a transaction query."""
    if filters.category:
        qs = qs.filter(Transaction.category.ilike(f"%{filters.category}%"))
    if filters.vendor:
        qs = qs.join(Transaction.vendor).filter(Vendor.name.ilike(f"%{filters.vendor}%"))
    if filters.start_date:
        qs = qs.filter(Transaction.actual_date >= filters.start_date)
    if filters.end_date:
        qs = qs.filter(Transaction.actual_date <= filters.end_date)
    if filters.search:
        qs = qs.filter(
            or_(
                Transaction.category.ilike(f"%{filters.search}%"),
                Transaction.sub_category.ilike(f"%{filters.search}%"),
                Transaction.narration.ilike(f"%{filters.search}%"),
                Transaction.notes.ilike(f"%{filters.search}%"),
                Transaction.vendor.has(Vendor.name.ilike(f"%{filters.search}%")),
            ),
        )
    if filters.min_amount is not None:
        qs = qs.filter(Transaction.debit_amount >= filters.min_amount)
    if filters.max_amount is not None:
        qs = qs.filter(Transaction.debit_amount <= filters.max_amount)
    if filters.exclude_filter.lower() == "true":
        qs = qs.filter(Transaction.exclude == True)  # noqa: E712
    elif filters.exclude_filter.lower() == "false":
        qs = qs.filter(Transaction.exclude == False)  # noqa: E712
    return qs
