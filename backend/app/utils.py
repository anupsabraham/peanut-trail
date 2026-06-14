import math
from datetime import date, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.models import Transaction


def compute_trend(data_points: list[Optional[float]], days_in_month: int) -> list[Optional[float]]:
    x_points = []
    y_points = []
    for i, val in enumerate(data_points):
        if val is not None:
            x_points.append(i + 1)
            y_points.append(val)

    n = len(x_points)
    if n > 1:
        sum_x = sum(x_points)
        sum_y = sum(y_points)
        sum_xy = sum(x * y for x, y in zip(x_points, y_points))
        sum_xx = sum(x * x for x in x_points)
        denominator = n * sum_xx - sum_x**2
        if denominator != 0:
            m = (n * sum_xy - sum_x * sum_y) / denominator
            c = (sum_y - m * sum_x) / n
        else:
            m, c = 0, 0
    elif n == 1:
        m = y_points[0] / x_points[0]
        c = 0
    else:
        m, c = 0, 0

    trend = []
    for day in range(1, 32):
        if day <= days_in_month:
            val = m * day + c
            trend.append(float(max(0, val)))
        else:
            trend.append(None)

    return trend

def days_in_month(year: int, month: int) -> int:
    if month == 12:
        return (date(year + 1, 1, 1) - timedelta(days=1)).day
    return (date(year, month + 1, 1) - timedelta(days=1)).day


def get_confidence_score(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    z = 1
    p = count / total
    numerator = p + z**2 / (2 * total) - z * math.sqrt(
        (p * (1 - p) + z**2 / (4 * total)) / total
    )
    denominator = 1 + z**2 / total
    return numerator / denominator * 100


def get_category_suggestions(db: Session, vendor) -> tuple[dict, dict]:
    if not vendor:
        empty = {
            "category": None, "sub_category": None, "notes": None,
            "confidence": 0.0, "auto_prefill": False,
        }
        return empty, {**empty}

    rows = (
        db.query(
            Transaction.category,
            Transaction.sub_category,
            Transaction.notes,
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.vendor_id == vendor.id,
            Transaction.category != "",
            Transaction.sub_category != "",
        )
        .group_by(Transaction.category, Transaction.sub_category, Transaction.notes)
        .order_by(func.count(Transaction.id).desc())
        .all()
    )

    total_count = sum(r.count for r in rows)

    def make_suggestion(row) -> dict:
        return {
            "category": row.category,
            "sub_category": row.sub_category,
            "notes": row.notes or "",
            "confidence": get_confidence_score(row.count, total_count),
            "auto_prefill": False,
        }

    empty = {
        "category": None, "sub_category": None, "notes": None,
        "confidence": 0.0, "auto_prefill": False,
    }

    suggestion1 = make_suggestion(rows[0]) if len(rows) > 0 else {**empty}
    suggestion2 = make_suggestion(rows[1]) if len(rows) > 1 else {**empty}

    if suggestion1["confidence"] > 25:
        suggestion1["auto_prefill"] = True

    return suggestion1, suggestion2
