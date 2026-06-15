from sqlalchemy import or_
from sqlalchemy.orm import Query

from app.models import Transaction, Vendor
from app.schemas.filters import TransactionFilters


def apply_transaction_filters(qs: Query, filters: TransactionFilters) -> Query:
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
