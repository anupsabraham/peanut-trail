"""Integration tests for /api/analytics endpoints."""

from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import make_transaction


def today() -> date:

    return datetime.now(tz=UTC).date()


class TestGetCurrentMonthExpenses:
    def test_empty_db_returns_zero(self, client: TestClient) -> None:
        resp = client.get("/api/analytics/expenses/by-category/current-month")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_expense"] == 0.0
        assert data["categories"] == []

    def test_current_month_transaction_appears(self, client: TestClient, db: Session) -> None:
        t = today()
        make_transaction(
            db,
            actual_date=t,
            debit_date=t,
            category="Food",
            sub_category="Groceries",
            debit_amount=50.00,
            txn_number="ANA001",
        )
        db.flush()

        resp = client.get("/api/analytics/expenses/by-category/current-month")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_expense"] == pytest.approx(50.0)
        assert len(data["categories"]) == 1
        assert data["categories"][0]["category"] == "Food"

    def test_excluded_transactions_not_counted(self, client: TestClient, db: Session) -> None:
        t = today()
        make_transaction(
            db,
            actual_date=t,
            debit_date=t,
            category="Food",
            sub_category="Groceries",
            debit_amount=200.00,
            exclude=True,
            txn_number="ANA002",
        )
        db.flush()

        resp = client.get("/api/analytics/expenses/by-category/current-month")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_expense"] == 0.0

    def test_previous_month_transactions_not_included(self, client: TestClient, db: Session) -> None:
        t = today()
        # Use a date clearly in the previous month
        prev_month_date = date(t.year if t.month > 1 else t.year - 1, t.month - 1 if t.month > 1 else 12, 1)
        make_transaction(
            db,
            actual_date=prev_month_date,
            debit_date=prev_month_date,
            category="Transport",
            sub_category="Fuel",
            debit_amount=300.00,
            txn_number="ANA003",
        )
        db.flush()

        resp = client.get("/api/analytics/expenses/by-category/current-month")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_expense"] == 0.0

    def test_multiple_categories_summed_separately(self, client: TestClient, db: Session) -> None:
        t = today()
        make_transaction(
            db,
            actual_date=t,
            debit_date=t,
            category="Food",
            sub_category="Groceries",
            debit_amount=100.00,
            txn_number="ANA004",
        )
        make_transaction(
            db,
            actual_date=t,
            debit_date=t,
            category="Transport",
            sub_category="Fuel",
            debit_amount=50.00,
            txn_number="ANA005",
        )
        make_transaction(
            db,
            actual_date=t,
            debit_date=t,
            category="Food",
            sub_category="Dining",
            debit_amount=75.00,
            txn_number="ANA006",
        )
        db.flush()

        resp = client.get("/api/analytics/expenses/by-category/current-month")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_expense"] == pytest.approx(225.0)
        categories = {c["category"]: c["total_amount"] for c in data["categories"]}
        assert categories["Food"] == pytest.approx(175.0)
        assert categories["Transport"] == pytest.approx(50.0)

    def test_categories_ordered_by_amount_descending(self, client: TestClient, db: Session) -> None:
        t = today()
        make_transaction(
            db, actual_date=t, debit_date=t, category="Cheap", sub_category="X", debit_amount=10.00, txn_number="ANA007"
        )
        make_transaction(
            db,
            actual_date=t,
            debit_date=t,
            category="Expensive",
            sub_category="Y",
            debit_amount=500.00,
            txn_number="ANA008",
        )
        db.flush()

        resp = client.get("/api/analytics/expenses/by-category/current-month")
        data = resp.json()
        amounts = [c["total_amount"] for c in data["categories"]]
        assert amounts == sorted(amounts, reverse=True)


class TestGetCurrentMonthProgression:
    def test_empty_db_returns_structure(self, client: TestClient) -> None:
        resp = client.get("/api/analytics/chart/progression/current-month")
        assert resp.status_code == 200
        data = resp.json()
        assert "progression_datasets" in data
        assert "days" in data
        assert data["days"] == list(range(1, 32))
        # 4 datasets: current month + trend + 3 previous months
        assert len(data["progression_datasets"]) == 5

    def test_each_dataset_has_31_data_points(self, client: TestClient) -> None:
        resp = client.get("/api/analytics/chart/progression/current-month")
        data = resp.json()
        for dataset in data["progression_datasets"]:
            assert len(dataset["data"]) == 31

    def test_current_month_dataset_is_cumulative(self, client: TestClient, db: Session) -> None:
        t = today()
        # Two transactions on day 1 of current month
        d1 = date(t.year, t.month, 1)
        make_transaction(
            db,
            actual_date=d1,
            debit_date=d1,
            category="Food",
            sub_category="Groceries",
            debit_amount=100.00,
            txn_number="PROG001",
        )
        make_transaction(
            db,
            actual_date=d1,
            debit_date=d1,
            category="Food",
            sub_category="Groceries",
            debit_amount=50.00,
            txn_number="PROG002",
        )
        db.flush()

        resp = client.get("/api/analytics/chart/progression/current-month")
        data = resp.json()
        current_dataset = data["progression_datasets"][0]
        # Day 1 (index 0) should be the sum of both transactions
        assert current_dataset["data"][0] == pytest.approx(150.0)

    def test_future_days_are_none_in_current_month(self, client: TestClient) -> None:
        t = today()
        resp = client.get("/api/analytics/chart/progression/current-month")
        data = resp.json()
        current_dataset = data["progression_datasets"][0]
        # Days after today should be None
        for day_idx in range(t.day, 31):
            assert current_dataset["data"][day_idx] is None

    def test_trend_dataset_labeled_correctly(self, client: TestClient) -> None:
        resp = client.get("/api/analytics/chart/progression/current-month")
        data = resp.json()
        labels = [ds["label"] for ds in data["progression_datasets"]]
        assert any("Trend" in label for label in labels)
