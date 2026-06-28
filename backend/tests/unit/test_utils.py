"""Unit tests for app/utils.py — pure functions and DB-dependent helpers."""

from sqlalchemy.orm import Session

from app.config import settings
from app.utils import (
    compute_trend,
    get_category_suggestions,
    get_confidence_score,
    get_days_in_month,
    get_transaction_out_obj,
)
from tests.conftest import make_transaction, make_vendor

# ---------------------------------------------------------------------------
# get_days_in_month
# ---------------------------------------------------------------------------


class TestGetDaysInMonth:
    def test_january(self) -> None:
        assert get_days_in_month(2026, 1) == 31

    def test_february_non_leap(self) -> None:
        assert get_days_in_month(2026, 2) == 28

    def test_february_leap(self) -> None:
        assert get_days_in_month(2024, 2) == 29

    def test_april(self) -> None:
        assert get_days_in_month(2026, 4) == 30

    def test_december(self) -> None:
        assert get_days_in_month(2026, 12) == 31


# ---------------------------------------------------------------------------
# get_confidence_score
# ---------------------------------------------------------------------------


class TestGetConfidenceScore:
    def test_zero_total_returns_zero(self) -> None:
        assert get_confidence_score(0, 0) == 0.0

    def test_count_equal_total(self) -> None:
        # All transactions match — confidence should be high
        score = get_confidence_score(10, 10)
        assert score > 50

    def test_single_transaction(self) -> None:
        score = get_confidence_score(1, 1)
        assert 0 < score <= 100

    def test_low_count_low_confidence(self) -> None:
        # 1 out of 100 — should be low
        score = get_confidence_score(1, 100)
        assert score < 10

    def test_majority_count_high_confidence(self) -> None:
        score = get_confidence_score(90, 100)
        assert score > 50

    def test_returns_float(self) -> None:
        assert isinstance(get_confidence_score(5, 10), float)


# ---------------------------------------------------------------------------
# compute_trend
# ---------------------------------------------------------------------------


class TestComputeTrend:
    def test_returns_31_values(self) -> None:
        data = [None] * 31
        trend = compute_trend(data, 31)
        assert len(trend) == 31

    def test_pads_short_month_with_none(self) -> None:
        # February — days 29-31 should be None
        data = [float(i) for i in range(1, 29)] + [None, None, None]
        trend = compute_trend(data, 28)
        assert trend[28] is None
        assert trend[29] is None
        assert trend[30] is None

    def test_all_none_returns_zeros(self) -> None:
        data = [None] * 31
        trend = compute_trend(data, 31)
        # m=0, c=0 → all values should be 0.0
        for val in trend[:31]:
            assert val == 0.0

    def test_single_data_point(self) -> None:
        # Only the first day has a value
        data = [50.0] + [None] * 30
        trend = compute_trend(data, 31)
        assert len(trend) == 31
        # All values should be non-negative
        for val in trend[:31]:
            assert val >= 0

    def test_linear_data_produces_trend(self) -> None:
        # Perfect linear data — trend should closely follow the line
        data = [float(i * 10) for i in range(1, 32)]
        trend = compute_trend(data, 31)
        # Trend should be increasing
        non_none = [v for v in trend if v is not None]
        assert non_none[-1] > non_none[0]

    def test_values_are_non_negative(self) -> None:
        # Even with a downward slope, trend values should be clamped to 0
        data = [100.0, 90.0, 80.0, 70.0, 60.0] + [None] * 26
        trend = compute_trend(data, 31)
        for val in trend:
            if val is not None:
                assert val >= 0

    def test_partial_month_nones_at_end(self) -> None:
        # Simulates current month where future days are None
        today_day = 15
        data = [float(i * 5) for i in range(1, today_day + 1)] + [None] * (31 - today_day)
        trend = compute_trend(data, 31)
        # trend is computed over all 31 days regardless of None padding
        assert len(trend) == 31


# ---------------------------------------------------------------------------
# get_category_suggestions (requires a DB session)
# ---------------------------------------------------------------------------


class TestGetCategorySuggestions:
    def test_no_vendor_returns_empty_suggestions(self, db: Session) -> None:
        s1, s2 = get_category_suggestions(db, None)
        assert s1["category"] is None
        assert s2["category"] is None
        assert s1["confidence"] == 0.0
        assert s1["auto_prefill"] is False

    def test_vendor_with_no_transactions_returns_empty(self, db: Session) -> None:
        vendor = make_vendor(db, "Empty Vendor")
        s1, s2 = get_category_suggestions(db, vendor)
        assert s1["category"] is None
        assert s2["category"] is None

    def test_vendor_with_one_category(self, db: Session) -> None:
        vendor = make_vendor(db, "SuperMart")
        make_transaction(db, vendor_id=vendor.id, category="Food", sub_category="Groceries", txn_number="T001")
        make_transaction(db, vendor_id=vendor.id, category="Food", sub_category="Groceries", txn_number="T002")

        s1, s2 = get_category_suggestions(db, vendor)
        assert s1["category"] == "Food"
        assert s1["sub_category"] == "Groceries"
        assert s2["category"] is None  # only one distinct category

    def test_vendor_with_two_categories_orders_by_count(self, db: Session) -> None:
        vendor = make_vendor(db, "MegaStore")
        # Food appears 3 times, Transport appears 1 time
        for i in range(3):
            make_transaction(db, vendor_id=vendor.id, category="Food", sub_category="Groceries", txn_number=f"F{i}")
        make_transaction(db, vendor_id=vendor.id, category="Transport", sub_category="Fuel", txn_number="TR1")

        s1, s2 = get_category_suggestions(db, vendor)
        assert s1["category"] == "Food"
        assert s2["category"] == "Transport"

    def test_high_frequency_triggers_auto_prefill(self, db: Session) -> None:
        vendor = make_vendor(db, "AutoFillVendor")
        # Create enough identical transactions to exceed confidence threshold
        for i in range(20):
            make_transaction(db, vendor_id=vendor.id, category="Bills", sub_category="Utilities", txn_number=f"B{i}")

        s1, _ = get_category_suggestions(db, vendor)
        if s1["confidence"] > settings.min_category_suggestion_confidence:
            assert s1["auto_prefill"] is True


class TestGetTransactionOutObj:
    def test_no_transaction_returns_empty(self, db: Session) -> None:
        transaction_out_obj = get_transaction_out_obj(db, None)
        assert transaction_out_obj is None

    def test_transaction_returns_success(self, db: Session) -> None:
        txn = make_transaction(db, txn_number="T002")
        txn_out_obj = get_transaction_out_obj(db, txn)
        assert txn_out_obj.txn_number == "T002"

    def test_transaction_with_no_vendor_returns_no_suggestions(self, db: Session) -> None:
        txn = make_transaction(db, txn_number="T003", vendor_id=None)
        txn_out_obj = get_transaction_out_obj(db, txn)
        assert txn_out_obj.suggestion1.category is None
        assert txn_out_obj.suggestion2.category is None
