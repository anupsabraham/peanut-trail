"""Integration tests for /api/transactions endpoints."""

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Transaction
from tests.conftest import make_transaction, make_vendor


class TestListTransactions:
    def test_empty_db_returns_empty_list(self, client: Session) -> None:
        resp = client.get("/api/transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["pages"] == 1

    def test_returns_existing_transaction(self, client: TestClient, db: Session) -> None:
        make_transaction(db, txn_number="LIST001")
        db.flush()

        resp = client.get("/api/transactions")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["txn_number"] == "LIST001"

    def test_pagination_page_size_is_50(self, client: TestClient, db: Session) -> None:
        for i in range(55):
            make_transaction(db, txn_number=f"PAGE{i:03d}")
        db.flush()

        resp = client.get("/api/transactions?page=1")
        data = resp.json()
        assert data["total"] == 55
        assert len(data["items"]) == 50
        assert data["pages"] == 2

    def test_second_page_returns_remaining(self, client: TestClient, db: Session) -> None:
        for i in range(55):
            make_transaction(db, txn_number=f"PG2{i:03d}")
        db.flush()

        resp = client.get("/api/transactions?page=2")
        data = resp.json()
        assert len(data["items"]) == 5

    def test_results_ordered_by_date_desc(self, client: TestClient, db: Session) -> None:
        make_transaction(db, actual_date=date(2026, 1, 1), txn_number="OLD001")
        make_transaction(db, actual_date=date(2026, 6, 1), txn_number="NEW001")
        db.flush()

        resp = client.get("/api/transactions")
        data = resp.json()
        dates = [item["actual_date"] for item in data["items"]]
        assert dates == sorted(dates, reverse=True)

    def test_transaction_includes_suggestion_fields(self, client: TestClient, db: Session) -> None:
        make_transaction(db, txn_number="SUG001")
        db.flush()

        resp = client.get("/api/transactions")
        item = resp.json()["items"][0]
        assert "suggestion1" in item
        assert "suggestion2" in item


class TestFilterByCategory:
    def test_category_filter_returns_matching(self, client: TestClient, db: Session) -> None:
        make_transaction(db, category="Food", sub_category="Groceries", txn_number="CAT001")
        make_transaction(db, category="Transport", sub_category="Fuel", txn_number="CAT002")
        db.flush()

        resp = client.get("/api/transactions?category=Food")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "Food"

    def test_category_filter_is_case_insensitive(self, client: TestClient, db: Session) -> None:
        make_transaction(db, category="Food", sub_category="Groceries", txn_number="CATI001")
        db.flush()

        resp = client.get("/api/transactions?category=food")
        assert resp.json()["total"] == 1

    def test_category_filter_no_match_returns_empty(self, client: TestClient, db: Session) -> None:
        make_transaction(db, category="Food", sub_category="Groceries", txn_number="CATNM001")
        db.flush()

        resp = client.get("/api/transactions?category=Nonexistent")
        assert resp.json()["total"] == 0


class TestFilterByVendor:
    def test_vendor_filter_returns_matching(self, client: TestClient, db: Session) -> None:
        v1 = make_vendor(db, "SuperMart")
        v2 = make_vendor(db, "PetrolStation")
        make_transaction(db, vendor_id=v1.id, txn_number="VEN001")
        make_transaction(db, vendor_id=v2.id, txn_number="VEN002")
        db.flush()

        resp = client.get("/api/transactions?vendor=SuperMart")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["vendor_name"] == "SuperMart"

    def test_vendor_filter_partial_match(self, client: TestClient, db: Session) -> None:
        v = make_vendor(db, "SuperMartExpress")
        make_transaction(db, vendor_id=v.id, txn_number="VENP001")
        db.flush()

        resp = client.get("/api/transactions?vendor=Super")
        assert resp.json()["total"] == 1


class TestFilterByDate:
    def test_start_date_filters_older_transactions(self, client: TestClient, db: Session) -> None:
        make_transaction(db, actual_date=date(2026, 1, 1), txn_number="DATE001")
        make_transaction(db, actual_date=date(2026, 6, 1), txn_number="DATE002")
        db.flush()

        resp = client.get("/api/transactions?start_date=2026-03-01")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["txn_number"] == "DATE002"

    def test_end_date_filters_newer_transactions(self, client: TestClient, db: Session) -> None:
        make_transaction(db, actual_date=date(2026, 1, 1), txn_number="EDATE001")
        make_transaction(db, actual_date=date(2026, 6, 1), txn_number="EDATE002")
        db.flush()

        resp = client.get("/api/transactions?end_date=2026-03-01")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["txn_number"] == "EDATE001"

    def test_date_range_both_bounds(self, client: TestClient, db: Session) -> None:
        make_transaction(db, actual_date=date(2026, 1, 1), txn_number="RANGE001")
        make_transaction(db, actual_date=date(2026, 4, 1), txn_number="RANGE002")
        make_transaction(db, actual_date=date(2026, 7, 1), txn_number="RANGE003")
        db.flush()

        resp = client.get("/api/transactions?start_date=2026-03-01&end_date=2026-05-01")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["txn_number"] == "RANGE002"


class TestFilterByAmount:
    def test_min_amount_filter(self, client: TestClient, db: Session) -> None:
        make_transaction(db, debit_amount=10.00, txn_number="AMT001")
        make_transaction(db, debit_amount=500.00, txn_number="AMT002")
        db.flush()

        resp = client.get("/api/transactions?min_amount=100")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["txn_number"] == "AMT002"

    def test_max_amount_filter(self, client: TestClient, db: Session) -> None:
        make_transaction(db, debit_amount=10.00, txn_number="AMTX001")
        make_transaction(db, debit_amount=500.00, txn_number="AMTX002")
        db.flush()

        resp = client.get("/api/transactions?max_amount=100")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["txn_number"] == "AMTX001"


class TestFilterByExclude:
    def test_exclude_true_returns_only_excluded(self, client: TestClient, db: Session) -> None:
        make_transaction(db, exclude=False, txn_number="EXC001")
        make_transaction(db, exclude=True, txn_number="EXC002")
        db.flush()

        resp = client.get("/api/transactions?exclude_filter=true")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["exclude"] is True

    def test_exclude_false_returns_only_non_excluded(self, client: TestClient, db: Session) -> None:
        make_transaction(db, exclude=False, txn_number="EXCF001")
        make_transaction(db, exclude=True, txn_number="EXCF002")
        db.flush()

        resp = client.get("/api/transactions?exclude_filter=false")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["exclude"] is False

    def test_exclude_all_returns_both(self, client: TestClient, db: Session) -> None:
        make_transaction(db, exclude=False, txn_number="EXCA001")
        make_transaction(db, exclude=True, txn_number="EXCA002")
        db.flush()

        # Default (no exclude_filter param) returns all
        resp = client.get("/api/transactions")
        data = resp.json()
        assert data["total"] == 2


class TestSearchFilter:
    def test_search_matches_narration(self, client: TestClient, db: Session) -> None:
        make_transaction(db, narration="Amazon Prime subscription", txn_number="SRCH001")
        make_transaction(db, narration="Petrol refill", txn_number="SRCH002")
        db.flush()

        resp = client.get("/api/transactions?search=Amazon")
        data = resp.json()
        assert data["total"] == 1

    def test_search_matches_category(self, client: TestClient, db: Session) -> None:
        make_transaction(db, category="Entertainment", sub_category="Streaming", txn_number="SRCHC001")
        db.flush()

        resp = client.get("/api/transactions?search=Entertainment")
        assert resp.json()["total"] == 1

    def test_search_matches_vendor_name(self, client: TestClient, db: Session) -> None:
        v = make_vendor(db, "CoffeeBeans Inc")
        make_transaction(db, vendor_id=v.id, txn_number="SRCHV001")
        db.flush()

        resp = client.get("/api/transactions?search=CoffeeBeans")
        assert resp.json()["total"] == 1


class TestMetaEndpoints:
    def test_categories_list_returns_categories(self, client: TestClient, db: Session) -> None:
        make_transaction(db, category="Food", sub_category="Groceries", txn_number="META001")
        make_transaction(db, category="Transport", sub_category="Fuel", txn_number="META002")
        db.flush()

        resp = client.get("/api/transactions/meta/categories/list")
        assert resp.status_code == 200
        cats = resp.json()
        assert "Food" in cats
        assert "Transport" in cats

    def test_categories_excludes_excluded_transactions(self, client: TestClient, db: Session) -> None:
        make_transaction(db, category="HiddenCat", sub_category="X", exclude=True, txn_number="METAEX001")
        db.flush()

        resp = client.get("/api/transactions/meta/categories/list")
        assert "HiddenCat" not in resp.json()

    def test_subcategories_list_all(self, client: TestClient, db: Session) -> None:
        make_transaction(db, category="Food", sub_category="Groceries", txn_number="MSUB001")
        make_transaction(db, category="Food", sub_category="Dining", txn_number="MSUB002")
        db.flush()

        resp = client.get("/api/transactions/meta/subcategories/list")
        assert resp.status_code == 200
        subs = resp.json()
        assert "Groceries" in subs
        assert "Dining" in subs

    def test_subcategories_filtered_by_category(self, client: TestClient, db: Session) -> None:
        make_transaction(db, category="Food", sub_category="Groceries", txn_number="MSUBC001")
        make_transaction(db, category="Transport", sub_category="Fuel", txn_number="MSUBC002")
        db.flush()

        resp = client.get("/api/transactions/meta/subcategories/list?category=Food")
        subs = resp.json()
        assert "Groceries" in subs
        assert "Fuel" not in subs


class TestHealthCheck:
    def test_health_endpoint(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestDeleteTransaction:
    def test_delete_transaction_success(self, client: TestClient, db: Session) -> None:
        new_txn = make_transaction(db, category="Food", sub_category="Groceries", txn_number="TEST123")
        resp = client.delete(f"/api/transactions/{new_txn.id}")
        assert resp.status_code == 204

        deleted_txn = db.query(Transaction).filter(Transaction.id == new_txn.id).first()
        assert deleted_txn is None

    def test_delete_transaction_wrong_id_returns_404(self, client: TestClient, db: Session) -> None:
        new_txn = make_transaction(db, category="Food", sub_category="Groceries", txn_number="TEST123")
        client.delete(f"/api/trnsactions/{new_txn.id}")

        # Try to delete it again to get a failure.
        resp = client.delete(f"/api/trnsactions/{new_txn.id}")
        assert resp.status_code == 404


class TestUpdateTransaction:
    def test_update_transaction_success(self, client: TestClient, db: Session) -> None:
        new_txn = make_transaction(db, txn_number="TEST001", category="Groceries", sub_category="Supermarket")

        new_sub_category = "Fresh Produce"

        updated_data = {"sub_category": new_sub_category}
        resp = client.patch(f"/api/transactions/{new_txn.id}", json=updated_data)

        assert resp.status_code == 200
        assert resp.json()["sub_category"] == new_sub_category

        updated_txn = db.query(Transaction).filter(Transaction.txn_number == "TEST001").first()
        assert updated_txn.sub_category == new_sub_category

    def test_non_existing_transaction_returns_404(self, client: TestClient, db: Session) -> None:
        new_txn = make_transaction(db, txn_number="TEST002", category="Groceries", sub_category="Supermarket")

        client.delete(f"/api/transactions/{new_txn.id}")

        # Try to update the deleted transaction
        updated_data = {"sub_category": "Fresh Produce"}
        resp = client.patch(f"/api/transactions/{new_txn.id}", json=updated_data)
        assert resp.status_code == 404

    def test_id_and_vendor_cannot_be_updated(self, client: TestClient, db: Session) -> None:
        vendor = make_vendor(db, "Test Vendor")
        new_txn = make_transaction(
            db, txn_number="TEST003", category="Groceries", sub_category="Supermarket", vendor_id=vendor.id
        )

        update_vendor = make_vendor(db, "Updated Vendor")
        update_id = new_txn.id + 1

        client.patch(f"/api/transactions/{new_txn.id}", json={"id": update_id, "vendor_id": update_vendor.id})

        updated_txn = db.query(Transaction).filter(Transaction.txn_number == "TEST003").first()
        assert updated_txn.id == new_txn.id
        assert updated_txn.vendor_id == vendor.id

    def test_non_excluded_without_category_raises_422(self, client: TestClient, db: Session) -> None:
        txn = make_transaction(db, txn_number="TEST004", category="Groceries", sub_category="Supermarket", exclude=True)

        update_value = {"exclude": False, "category": "", "sub_category": ""}

        resp = client.patch(f"/api/transactions/{txn.id}", json=update_value)

        assert resp.status_code == 422
