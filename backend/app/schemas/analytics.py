from pydantic import BaseModel
from typing import Optional


class DashboardCategoryRow(BaseModel):
    category: str
    total_amount: float


class ChartDataset(BaseModel):
    label: str
    data: list[Optional[float]]
    borderColor: str
    borderWidth: int
    borderDash: Optional[list[int]] = None
    pointRadius: Optional[int] = None


class CategoryExpenseResponse(BaseModel):
    categories: list[DashboardCategoryRow]
    total_expense: float

class ProgressionChartResponse(BaseModel):
    progression_datasets: list[ChartDataset]
    days: list[int]