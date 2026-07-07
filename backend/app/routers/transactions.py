from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app import schemas, services, utils
from app.database import get_db
from app.models import Transaction

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

DB = Annotated[Session, Depends(get_db)]
Filters = Annotated[schemas.filters.TransactionFilters, Depends()]


@router.get("")
def list_transactions(db: DB, filters: Filters) -> schemas.transactions.TransactionListResponse:
    """List all transactions.

    Returns the list of all transactions. Query strings contain filters if anything applied. The response is also
    paginated.
    """
    qs = (
        db.query(Transaction)
        .options(joinedload(Transaction.vendor), joinedload(Transaction.children))
        .filter(Transaction.parent_transaction_id.is_(None))
        .order_by(Transaction.actual_date.desc())
    )
    qs = services.transactions.apply_transaction_filters(qs, filters=filters)

    total = qs.count()
    page_size = 50
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(filters.page, pages)
    items = qs.offset((page - 1) * page_size).limit(page_size).all()

    transactions_response = [utils.get_transaction_out_obj(db, txn) for txn in items if txn]

    return schemas.transactions.TransactionListResponse(
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
def update_transaction(
    transaction_id: int, update: schemas.transactions.TransactionUpdate, db: DB
) -> schemas.transactions.TransactionOut:
    """Update a transaction identified by transaction id."""
    txn = db.query(Transaction).options(joinedload(Transaction.vendor)).filter(Transaction.id == transaction_id).first()

    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No transaction with id {transaction_id} found."
        )

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)

    utils.validate_transaction(txn)

    db.commit()
    db.refresh(txn)

    return utils.get_transaction_out_obj(db, txn)


@router.post("/{transaction_id}/split")
def split_transaction(
    transaction_id: int, request: schemas.transactions.TransactionSplitRequest, db: DB
) -> schemas.transactions.TransactionOut:
    """Split a transaction into multiple transaction to tag them into multiple categories.

    Eg: In case of an online purchase, there may be items from different categories
    """
    txn = (
        db.query(Transaction).options(joinedload(Transaction.children)).filter(Transaction.id == transaction_id).first()
    )

    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No transaction with id {transaction_id} found."
        )

    if txn.parent_transaction_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot splita child transaction.")

    if txn.children:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction is already split.")

    if txn.credit_amount > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credit transactions cannot be split.")

    total = sum(split.debit_amount for split in request.splits)

    if total != txn.debit_amount:
        if total > txn.debit_amount:
            message = f"Total amount({total}) exceeds transaction amount({txn.debit_amount})"
        else:
            message = f"Total amount({total}) is lesser than transaction amount({txn.debit_amount})"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    if len(request.splits) <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction must be split into at least 2 parts."
        )

    for index, split in enumerate(request.splits, start=1):
        if split.debit_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction amount should be greater than 0"
            )
        child = Transaction(
            debit_date=txn.debit_date,
            actual_date=txn.actual_date,
            narration=txn.narration,
            txn_number=utils.generate_split_txn_number(txn, index),
            debit_amount=split.debit_amount,
            credit_amount=Decimal("0.00"),
            vendor_id=txn.vendor_id,
            category=split.category,
            sub_category=split.sub_category,
            notes=split.notes,
            exclude=split.exclude,
            parent=txn,
        )

        utils.validate_transaction(child)

        db.add(child)

    txn.exclude = True

    db.commit()
    db.refresh(txn)

    return utils.get_transaction_out_obj(db, txn)


@router.get("/{transaction_id}/children")
def get_split_transactions(transaction_id: int, db: DB) -> list[schemas.transactions.TransactionOut]:
    """Get a list of split transactions under the parent transaction."""
    txn = (
        db.query(Transaction)
        .options(joinedload(Transaction.children).joinedload(Transaction.vendor))
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No transaction with id {transaction_id} found."
        )

    return [utils.get_transaction_out_obj(db, child) for child in txn.children]
