from datetime import date
from decimal import Decimal

import pytest

from app.parsers.hdfc import HDFCSavingsCsvParser
from app.parsers.registry import resolve_parser
from app.parsers.types import Bank, FileType, ParseResult, StatementType, UnsupportedStatementError

HEADER = "Date,Narration,Chq/Ref Number,Value Dat,Debit Amount,Credit Amount,Closing Balance"


def parse(content: bytes) -> ParseResult:
    """Parse test content with a fresh HDFC savings parser."""
    return HDFCSavingsCsvParser().parse(content)


def test_parses_hdfc_savings_csv_rows() -> None:
    content = f"""HDFC Bank Statement
{HEADER}
01/06/26,UPI-GROCERY,REF001,01/06/26,"1,250.50",,10000.00
02/06/26,SALARY,REF002,02/06/26,,50000.00,60000.00
""".encode()

    result = parse(content)

    assert result.issues == []
    assert len(result.transactions) == 2
    assert result.transactions[0].debit_date == date(2026, 6, 1)
    assert result.transactions[0].debit_amount == Decimal("1250.50")
    assert result.transactions[0].credit_amount == Decimal(0)
    assert result.transactions[1].credit_amount == Decimal("50000.00")


def test_repairs_an_unquoted_comma_in_narration() -> None:
    content = f"""{HEADER}
01/06/26,UPI-GOMATHY, PRASAD,REF001,01/06/26,125.00,,10000.00
""".encode()

    result = parse(content)

    assert result.issues == []
    assert len(result.transactions) == 1
    transaction = result.transactions[0]
    assert transaction.narration == "UPI-GOMATHY, PRASAD"
    assert transaction.txn_number == "REF001"
    assert transaction.actual_date == date(2026, 6, 1)
    assert transaction.was_repaired is True


def test_reports_a_row_that_cannot_be_safely_repaired() -> None:
    content = f"""{HEADER}
01/06/26,UPI-GROCERY,REF001,01/06/26,125.00
""".encode()

    result = parse(content)

    assert result.transactions == []
    assert result.issues[0].code == "column_count_mismatch"
    assert result.issues[0].source_row == 2


def test_reports_missing_required_columns() -> None:
    content = b"Date,Narration,Value Dat,Debit Amount\n01/06/26,Coffee,01/06/26,100\n"

    result = parse(content)

    assert result.transactions == []
    assert result.issues[0].code == "required_columns_missing"
    assert "Chq/Ref Number" in result.issues[0].message


def test_reports_invalid_dates_without_discarding_valid_rows() -> None:
    content = f"""{HEADER}
01/06/26,Coffee,REF001,01/06/26,100.00,,1000.00
not-a-date,Bad row,REF002,01/06/26,100.00,,900.00
""".encode()

    result = parse(content)

    assert len(result.transactions) == 1
    assert result.issues[0].code == "invalid_transaction_data"
    assert result.issues[0].source_row == 3


def test_registry_resolves_the_hdfc_savings_csv_parser() -> None:
    parser = resolve_parser(Bank.HDFC, StatementType.SAVINGS, FileType.CSV)

    assert isinstance(parser, HDFCSavingsCsvParser)


def test_registry_rejects_an_unsupported_hdfc_format() -> None:
    with pytest.raises(UnsupportedStatementError, match="credit_card"):
        resolve_parser(Bank.HDFC, StatementType.CREDIT_CARD, FileType.CSV)
