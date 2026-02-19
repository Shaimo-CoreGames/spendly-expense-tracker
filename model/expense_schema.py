from pydantic import BaseModel, Field
from typing import Annotated, Optional
from datetime import datetime, date
from enum import Enum

class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRAVEL = "travel"
    BILLS = "bills"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    OTHER = "other"

class ExpenseCreate(BaseModel):
    amount: Annotated[float, Field(..., gt=0, description="Expense amount must be positive")]
    category: ExpenseCategory
    description: Annotated[str, Field(..., min_length=1, max_length=200)]
    date: Annotated[date, Field(default_factory=date.today)]

class ExpenseUpdate(BaseModel):
    amount: Optional[Annotated[float, Field(None, gt=0)]] = None
    category: Optional[ExpenseCategory] = None
    description: Optional[Annotated[str, Field(None, min_length=1, max_length=200)]] = None
    date: Optional[Annotated[date, Field(None)]] = None

class ExpenseResponse(BaseModel):
    expense_id: str
    user_id: str
    amount: float
    category: ExpenseCategory
    description: str
    date: date
    created_at: datetime
    updated_at: datetime

class MonthlySummary(BaseModel):
    month: int
    year: int
    total_expenses: float
    expense_count: int
    category_breakdown: dict[str, float]
    average_expense: float

class SpendingPattern(BaseModel):
    category: str
    average_daily: float
    average_weekly: float
    average_monthly: float
    trend_direction: str
    volatility: str  # "high", "medium", "low"
