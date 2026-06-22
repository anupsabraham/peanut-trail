from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction
from app.schemas import CategoryExpenseResponse, ChartDataset, DashboardCategoryRow, ProgressionChartResponse
from app.utils import compute_trend, get_days_in_month

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
DB = Annotated[Session, Depends(get_db)]


@router.get("/expenses/by-category/current-month")
def get_current_month_expenses(db: DB) -> CategoryExpenseResponse:
    """Get the current month's category-wise expenses."""
    today = datetime.now(tz=UTC).date()

    # Category summary for current month
    cat_rows = (
        db.query(
            Transaction.category,
            func.sum(Transaction.debit_amount).label("total_amount"),
        )
        .filter(
            Transaction.exclude == False,  # noqa: E712
            extract("year", Transaction.actual_date) == today.year,
            extract("month", Transaction.actual_date) == today.month,
        )
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.debit_amount).desc())
        .all()
    )

    total_expense = sum(float(r.total_amount or 0) for r in cat_rows)
    categories = [
        DashboardCategoryRow(category=r.category or "Uncategorized", total_amount=float(r.total_amount or 0))
        for r in cat_rows
    ]

    return CategoryExpenseResponse(
        total_expense=total_expense,
        categories=categories,
    )


@router.get("/chart/progression/current-month")
def get_current_month_progression(db: DB) -> ProgressionChartResponse:
    """Get the current month progression for the chart.

    Get the current month's expense progression chart along with the previous 2 months'. Also create a trend line
    for the current month based on the progression.
    """

    def _get_month_cumulative(db: Session, year: int, month: int, today: date) -> list:
        days_in_m = get_days_in_month(year, month)

        daily_rows = (
            db.query(
                extract("day", Transaction.actual_date).label("day"),
                func.sum(Transaction.debit_amount).label("daily_sum"),
            )
            .filter(
                extract("year", Transaction.actual_date) == year,
                extract("month", Transaction.actual_date) == month,
                Transaction.exclude == False,  # noqa: E712
            )
            .group_by(extract("day", Transaction.actual_date))
            .order_by(extract("day", Transaction.actual_date))
            .all()
        )

        daily_dict = {int(r.day): float(r.daily_sum or 0) for r in daily_rows}

        data = []
        cumulative = 0.0
        for day in range(1, 32):
            if day <= days_in_m:
                if year == today.year and month == today.month and day > today.day:
                    data.append(None)
                else:
                    cumulative += daily_dict.get(day, 0.0)
                    data.append(cumulative)
            else:
                data.append(None)
        return data

    today = datetime.now(tz=UTC).date()

    current_month_data = _get_month_cumulative(db, today.year, today.month, today)
    days_in_current = get_days_in_month(today.year, today.month)
    trend_data = compute_trend(current_month_data, days_in_current)

    datasets = [
        ChartDataset(
            label=today.strftime("%B %Y"),
            data=current_month_data,
            borderColor="rgba(75, 192, 192, 1)",
            borderWidth=3,
        ),
        ChartDataset(
            label="Trend (Current Month)",
            data=trend_data,
            borderColor="rgba(75, 192, 192, 0.3)",
            borderWidth=2,
            borderDash=[7, 2],
            pointRadius=0,
        ),
    ]

    colors = [
        "rgba(255, 99, 132, 1)",
        "rgba(54, 162, 235, 1)",
        "rgba(255, 206, 86, 1)",
    ]

    for i in range(1, 4):
        prev_month = today.month - i
        prev_year = today.year
        if prev_month <= 0:
            prev_month = 12
            prev_year -= 1
        m_date = date(prev_year, prev_month, 1)
        datasets.append(
            ChartDataset(
                label=m_date.strftime("%B %Y"),
                data=_get_month_cumulative(db, prev_year, prev_month, today),
                borderColor=colors[i - 1],
                borderWidth=1,
                borderDash=[2, 1],
            ),
        )

    return ProgressionChartResponse(
        progression_datasets=datasets,
        days=list(range(1, 32)),
    )
