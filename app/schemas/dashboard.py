from pydantic import BaseModel


class DashboardSummary(BaseModel):
    completed: int
    in_progress: int
    overdue: int
    completed_previous_week: int
    in_progress_previous_week: int
    overdue_previous_week: int


class DailyDistribution(BaseModel):
    date: str
    completed: int
    created: int


class CategoryDistribution(BaseModel):
    category: str
    color: str
    count: int


class MonthlyEvolution(BaseModel):
    month: str
    completion_rate: float


class DashboardCharts(BaseModel):
    daily_distribution: list[DailyDistribution]
    category_distribution: list[CategoryDistribution]
    monthly_evolution: list[MonthlyEvolution]


class DashboardKPIs(BaseModel):
    completion_rate: float
    punctuality_rate: float
    streak: int
