from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app import schemas, services, utils
from app.database import get_db
from app.models import Transaction

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

DB = Annotated[Session, Depends(get_db)]
Filters = Annotated[schemas.filters.TransactionFilters, Depends()]


@router.post("")
def create_transaction(
    payload: schemas.transactions.TransactionImportCreate, db: DB
) -> schemas.transactions.TransactionOut:
    """Save one reviewed transaction from a statement preview."""
    try:
        txn = services.transactions.create_import_transaction(db, payload)
        db.commit()
        db.refresh(txn)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A transaction with this transaction number already exists.",
        ) from error
    return utils.get_transaction_out_obj(db, txn)


@router.post("/bulk")
def create_transactions_bulk(
    request: schemas.transactions.TransactionBulkCreateRequest, db: DB
) -> schemas.transactions.TransactionBulkCreateResponse:
    """Atomically save all selected and reviewed statement-preview rows."""
    transaction_numbers = [transaction.txn_number for transaction in request.transactions]
    duplicate_numbers = {number for number in transaction_numbers if transaction_numbers.count(number) > 1}
    if duplicate_numbers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate transaction number in request: {sorted(duplicate_numbers)[0]}.",
        )

    existing_numbers = {
        number
        for (number,) in db.query(Transaction.txn_number).filter(Transaction.txn_number.in_(transaction_numbers)).all()
    }
    if existing_numbers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transaction already exists: {sorted(existing_numbers)[0]}.",
        )

    try:
        transactions = [
            services.transactions.create_import_transaction(db, transaction) for transaction in request.transactions
        ]
        db.commit()
        for transaction in transactions:
            db.refresh(transaction)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more transactions already exist.",
        ) from error

    return schemas.transactions.TransactionBulkCreateResponse(
        items=[utils.get_transaction_out_obj(db, transaction) for transaction in transactions]
    )


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


@router.get("/categories")
def get_categories(db: DB) -> schemas.transactions.CategoryListResponse:
    """Get existing categories and subcategories list."""
    category_rows = (
        db.query(
            Transaction.category,
            func.sum(Transaction.debit_amount).label("total"),
        )
        .filter(Transaction.category != "")
        .filter(Transaction.exclude == False)  # noqa: E712
        .group_by(Transaction.category)
        .order_by(
            func.sum(Transaction.debit_amount).desc(),
        )
        .all()
    )

    subcategory_rows = (
        db.query(Transaction.category, Transaction.sub_category, func.sum(Transaction.debit_amount).label("total"))
        .filter(Transaction.sub_category != "")
        .filter(Transaction.exclude == False)  # noqa: E712
        .group_by(Transaction.category, Transaction.sub_category)
        .order_by(Transaction.category, func.sum(Transaction.debit_amount).desc())
        .all()
    )

    subcategories_by_category: dict[str, list[schemas.transactions.SubCategoryOut]] = {}

    for category, sub_category, _ in subcategory_rows:
        subcategories_by_category.setdefault(category, []).append(
            schemas.transactions.SubCategoryOut(name=sub_category)
        )

    return schemas.transactions.CategoryListResponse(
        categories=[
            schemas.transactions.CategoryOut(
                name=category,
                subcategories=subcategories_by_category.get(category, []),
            )
            for category, _ in category_rows
        ]
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: DB) -> None:
    """Delete a transaction using transaction id."""
    txn = utils.get_txn_object_by_id(db, transaction_id)
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
    txn = utils.get_txn_object_by_id(db, transaction_id, joinedload(Transaction.vendor))

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)

    utils.validate_transaction(txn)

    db.commit()
    db.refresh(txn)

    return utils.get_transaction_out_obj(db, txn)


@router.post("/{transaction_id}/split")
def update_transaction_splits(
    transaction_id: int, request: schemas.transactions.TransactionSplitRequest, db: DB
) -> schemas.transactions.TransactionOut:
    """Split a transaction into multiple transaction to tag them into multiple categories.

    Eg: In case of an online purchase, there may be items from different categories
    """
    txn = utils.get_txn_object_by_id(db, transaction_id, joinedload(Transaction.children))

    utils.validate_transaction(txn)

    if txn.parent_transaction_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot split a child transaction.")

    if txn.credit_amount > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Credit transactions cannot be split.")

    if request.splits:
        total = sum(split.debit_amount for split in request.splits)

        if total != txn.debit_amount:
            if total > txn.debit_amount:
                message = f"Total amount({total}) exceeds transaction amount({txn.debit_amount})"
            else:
                message = f"Total amount({total}) is lesser than transaction amount({txn.debit_amount})"
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    if len(request.splits) == 1:
        # Either there needs to be more than 1 split txn or none (delete splits)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction must be split into at least 2 parts."
        )

    if txn.children:
        for child in txn.children:
            db.delete(child)

    db.flush()

    utils.create_split_children(db, txn, request.splits)

    db.commit()
    db.refresh(txn)

    return utils.get_transaction_out_obj(db, txn)


@router.get("/{transaction_id}/children")
def get_split_transactions(transaction_id: int, db: DB) -> list[schemas.transactions.TransactionOut]:
    """Get a list of split transactions under the parent transaction."""
    txn = utils.get_txn_object_by_id(
        db, transaction_id, joinedload(Transaction.children).joinedload(Transaction.vendor)
    )

    return [utils.get_transaction_out_obj(db, child) for child in txn.children]
