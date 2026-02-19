from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime, date, timedelta
import uuid

from db.database_utilities import get_db
from model.budget_schema import BudgetCreate, BudgetResponse, BudgetAlert
from utils.helpers import row_to_dict
from ml.algorithms import moving_average
from api.auth import get_current_user

router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)

# ==================== CREATE BUDGET ====================
@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(budget: BudgetCreate, user=Depends(get_current_user)):
    user_id = user["user_id"]

    with get_db() as conn:
        cursor = conn.cursor()

        # Prevent duplicate budget for same category
        cursor.execute("""
            SELECT budget_id FROM budgets
            WHERE user_id=? AND LOWER(category)=LOWER(?)
        """, (user_id, budget.category.value))

        if cursor.fetchone():
            raise HTTPException(400, "Budget already exists for this category")

        budget_id = str(uuid.uuid4())
        created_at = datetime.now()

        cursor.execute("""
            INSERT INTO budgets (budget_id, user_id, category, monthly_limit, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            budget_id,
            user_id,
            budget.category.value,
            budget.monthly_limit,
            created_at
        ))

    return BudgetResponse(
        budget_id=budget_id,
        user_id=user_id,
        category=budget.category,
        monthly_limit=budget.monthly_limit,
        created_at=created_at
    )


# ==================== GET BUDGETS ====================
@router.get("", response_model=List[BudgetResponse])
async def get_budgets(user=Depends(get_current_user)):
    user_id = user["user_id"]
    today = date.today()
    month_start = today.replace(day=1)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets WHERE user_id=?", (user_id,))
        budgets = cursor.fetchall()

        result = []

        for b in budgets:
            budget = row_to_dict(b)

            # Calculate current month spending dynamically
            cursor.execute("""
                SELECT COALESCE(SUM(amount),0) as total
                FROM expenses
                WHERE user_id=?
                AND LOWER(category)=LOWER(?)
                AND date>=?
                AND date<=?
            """, (
                user_id,
                budget["category"],
                month_start,
                today
            ))

            spent = cursor.fetchone()["total"]
            budget["amount_used"] = round(spent, 2)

            result.append(BudgetResponse(**budget))

    return result


# ==================== BUDGET ALERTS ====================
@router.get("/alerts", response_model=List[BudgetAlert])
async def get_budget_alerts(user=Depends(get_current_user)):
    user_id = user["user_id"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets WHERE user_id=?", (user_id,))
        budgets = [row_to_dict(row) for row in cursor.fetchall()]

        if not budgets:
            return []

        alerts = []
        today = date.today()
        month_start = today.replace(day=1)

        # Calculate month end
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)

        month_end = next_month - timedelta(days=1)
        days_remaining = month_end.day - today.day

        for budget in budgets:
            category = budget["category"]

            # Current month spending
            cursor.execute("""
                SELECT COALESCE(SUM(amount),0) as total
                FROM expenses
                WHERE user_id=?
                AND LOWER(category)=LOWER(?)
                AND date>=?
                AND date<=?
            """, (
                user_id,
                category,
                month_start,
                today
            ))

            current_spending = cursor.fetchone()["total"]

            # Last 30 days data for ML prediction
            cursor.execute("""
                SELECT amount FROM expenses
                WHERE user_id=?
                AND LOWER(category)=LOWER(?)
                AND date>=?
            """, (
                user_id,
                category,
                today - timedelta(days=30)
            ))

            daily_amounts = [r["amount"] for r in cursor.fetchall()]

            if daily_amounts and days_remaining > 0:
                avg_daily = moving_average(daily_amounts, window=7)
                predicted_month_end = current_spending + avg_daily * days_remaining
            else:
                predicted_month_end = current_spending

            budget_limit = budget["monthly_limit"]

            percentage_used = (
                (current_spending / budget_limit) * 100
                if budget_limit > 0 else 0
            )

            # Status logic
            if percentage_used >= 90 or predicted_month_end >= budget_limit:
                status_level = "danger"
            elif percentage_used >= 70:
                status_level = "warning"
            else:
                status_level = "safe"

            alerts.append(
                BudgetAlert(
                    category=category,
                    current_spending=round(current_spending, 2),
                    budget_limit=budget_limit,
                    percentage_used=round(percentage_used, 2),
                    status=status_level,
                    predicted_month_end=round(predicted_month_end, 2)
                )
            )

    return alerts
