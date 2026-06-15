from pydantic import BaseModel, Field


class DashboardCategoryRow(BaseModel):
    category: str
    total_amount: float


class ChartDataset(BaseModel):
    model_config = {"populate_by_name": True, "serialize_by_alias": True}

    label: str
    data: list[float | None]
    border_color: str = Field(alias="borderColor")
    border_width: int = Field(alias="borderWidth")
    border_dash: list[int] | None = Field(None, alias="borderDash")
    point_radius: int | None = Field(None, alias="pointRadius")


class CategoryExpenseResponse(BaseModel):
    categories: list[DashboardCategoryRow]
    total_expense: float


class ProgressionChartResponse(BaseModel):
    progression_datasets: list[ChartDataset]
    days: list[int]
