"""Integration tests for statement preview and reviewed-transaction save endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Transaction
from tests.conftest import make_transaction

HEADER = "Date,Narration,Chq/Ref Number,Value Dat,Debit Amount,Credit Amount,Closing Balance"


def transaction_payload(txn_number: str) -> dict[str, object]:
    """Build a valid reviewed transaction payload."""
    return {
        "debit_date": "2026-06-01",
        "actual_date": "2026-06-01",
        "narration": "Supermarket",
        "txn_number": txn_number,
        "debit_amount": "100.00",
        "credit_amount": "0.00",
        "category": "Food",
        "sub_category": "Groceries",
        "notes": "",
        "exclude": False,
    }


class TestStatementPreview:
    def test_returns_only_new_rows_without_persisting_them(self, client: TestClient, db: Session) -> None:
        make_transaction(db, txn_number="EXISTING")
        content = f"""{HEADER}
01/06/26,Already saved,EXISTING,01/06/26,100.00,,1000.00
02/06/26,New row,NEW001,02/06/26,200.00,,800.00
""".encode()

        response = client.post(
            "/api/statements/preview",
            data={"bank": "hdfc", "statement_type": "savings"},
            files={"file": ("statement.csv", content, "text/csv")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["skipped_existing_count"] == 1
        assert [transaction["txn_number"] for transaction in body["transactions"]] == ["NEW001"]
        assert db.query(Transaction).count() == 1

    def test_rejects_an_unknown_statement_file_type(self, client: TestClient) -> None:
        response = client.post(
            "/api/statements/preview",
            data={"bank": "hdfc", "statement_type": "savings"},
            files={"file": ("statement.pptx", b"not a statement", "text/plain")},
        )

        assert response.status_code == 422

    def test_rejects_unsupported_bank_and_statement_type_combination(self, client: TestClient) -> None:
        content = f"{HEADER}\n01/06/26,Payment,REF001,01/06/26,100.00,,1000.00\n".encode()

        response = client.post(
            "/api/statements/preview",
            data={"bank": "hdfc", "statement_type": "credit_card"},
            files={"file": ("statement.csv", content, "text/csv")},
        )

        assert response.status_code == 422

    def test_returns_parse_issues_alongside_valid_transactions(self, client: TestClient) -> None:
        content = f"""{HEADER}
                    01/06/26,Valid row,VALID001,01/06/26,100.00,,1000.00
                    BADDATE,Broken row,BAD001,01/06/26,200.00,,800.00
                    """.encode()

        response = client.post(
            "/api/statements/preview",
            data={"bank": "hdfc", "statement_type": "savings"},
            files={"file": ("statement.csv", content, "text/csv")},
        )

        assert response.status_code == 200
        body = response.json()
        assert [t["txn_number"] for t in body["transactions"]] == ["VALID001"]
        assert len(body["issues"]) == 1
        assert body["issues"][0]["code"] == "invalid_transaction_data"
        assert body["issues"][0]["source_row"] == 3

    def test_client_id_is_prefixed_with_source_row(self, client: TestClient) -> None:
        content = f"{HEADER}\n01/06/26,Payment,REF001,01/06/26,100.00,,1000.00\n".encode()

        response = client.post(
            "/api/statements/preview",
            data={"bank": "hdfc", "statement_type": "savings"},
            files={"file": ("statement.csv", content, "text/csv")},
        )

        assert response.status_code == 200
        assert response.json()["transactions"][0]["client_id"] == "preview-2"


class TestReviewedTransactionSave:
    def test_saves_one_reviewed_transaction(self, client: TestClient, db: Session) -> None:
        response = client.post("/api/transactions", json=transaction_payload("SINGLE001"))

        assert response.status_code == 200
        assert response.json()["txn_number"] == "SINGLE001"
        assert db.query(Transaction).filter_by(txn_number="SINGLE001").one().category == "Food"

    def test_saves_a_split_preview_transaction_with_its_children(self, client: TestClient, db: Session) -> None:
        payload = transaction_payload("SPLIT001")
        payload["splits"] = [
            {"debit_amount": "60.00", "category": "Food", "sub_category": "Groceries", "notes": ""},
            {"debit_amount": "40.00", "category": "Household", "sub_category": "Cleaning", "notes": ""},
        ]

        response = client.post("/api/transactions", json=payload)

        assert response.status_code == 200
        parent = db.query(Transaction).filter_by(txn_number="SPLIT001").one()
        assert parent.exclude is True
        assert len(parent.children) == 2

    def test_bulk_save_is_atomic_when_one_row_is_invalid(self, client: TestClient, db: Session) -> None:
        invalid = transaction_payload("INVALID002")
        invalid["category"] = ""
        invalid["sub_category"] = ""

        response = client.post(
            "/api/transactions/bulk",
            json={"transactions": [transaction_payload("VALID001"), invalid]},
        )

        assert response.status_code == 422
        assert db.query(Transaction).count() == 0

    def test_bulk_save_rejects_existing_transaction_numbers(self, client: TestClient, db: Session) -> None:
        make_transaction(db, txn_number="EXISTING")

        response = client.post(
            "/api/transactions/bulk",
            json={"transactions": [transaction_payload("EXISTING")]},
        )

        assert response.status_code == 409
        assert db.query(Transaction).count() == 1
