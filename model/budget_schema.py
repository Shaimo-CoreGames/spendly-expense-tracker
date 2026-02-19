from pydantic import BaseModel, Field
from typing import Annotated, Optional
from datetime import datetime
from model.expense_schema import ExpenseCategory

class BudgetCreate(BaseModel):
    category: ExpenseCategory
    monthly_limit: Annotated[float, Field(..., gt=0)]

class BudgetResponse(BaseModel):
    budget_id: str
    user_id: str
    category: ExpenseCategory
    monthly_limit: float
    created_at: datetime



class BudgetAlert(BaseModel):
    category: str
    current_spending: float
    budget_limit: float
    percentage_used: float
    status: str  # "safe", "warning", "danger"
    predicted_month_end: float
