"""Endpoints for parsing statement files into non-persistent previews."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.models import Transaction
from app.parsers import resolve_parser
from app.parsers.resolver import detect_file_type
from app.parsers.types import Bank, StatementType, UnsupportedStatementError

router = APIRouter(prefix="/api/statements", tags=["Statements"])
DB = Annotated[Session, Depends(get_db)]


@router.post("/preview")
async def preview_statement(
    bank: Annotated[Bank, Form()],
    statement_type: Annotated[StatementType, Form()],
    file: Annotated[UploadFile, File()],
    db: DB,
) -> schemas.statements.StatementPreviewResponse:
    """Parse a statement and return only rows not already stored in the database."""
    try:
        file_type = detect_file_type(file.filename, file.content_type)
        parser = resolve_parser(bank, statement_type, file_type)
    except UnsupportedStatementError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error

    parse_result = parser.parse(await file.read())
    transaction_numbers = {transaction.txn_number for transaction in parse_result.transactions}
    existing_numbers = {
        number
        for (number,) in db.query(Transaction.txn_number).filter(Transaction.txn_number.in_(transaction_numbers)).all()
    }
    transactions = [
        schemas.statements.StatementPreviewTransaction(
            client_id=f"preview-{transaction.source_row}",
            source_row=transaction.source_row,
            debit_date=transaction.debit_date,
            actual_date=transaction.actual_date,
            narration=transaction.narration,
            txn_number=transaction.txn_number,
            debit_amount=transaction.debit_amount,
            credit_amount=transaction.credit_amount,
            was_repaired=transaction.was_repaired,
        )
        for transaction in parse_result.transactions
        if transaction.txn_number not in existing_numbers
    ]
    issues = [
        schemas.statements.StatementParseIssue(
            code=issue.code,
            message=issue.message,
            source_row=issue.source_row,
            raw_values=list(issue.raw_values) if issue.raw_values is not None else None,
        )
        for issue in parse_result.issues
    ]
    return schemas.statements.StatementPreviewResponse(
        transactions=transactions,
        issues=issues,
        skipped_existing_count=len(parse_result.transactions) - len(transactions),
    )
