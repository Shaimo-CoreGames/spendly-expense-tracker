from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import date, timedelta
from collections import defaultdict
import statistics

from model.prediction_schema import WeeklyForecast, ExpensePrediction
from model.expense_schema import SpendingPattern
from db.database_utilities import get_db
from utils.helpers import row_to_dict, verify_user_exists
from ml.algorithms import predict_next_week_expenses, calculate_confidence, calculate_trend, calculate_volatility
from api.auth import get_current_user  # JWT helper

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"]
)

# ==================== ML PREDICTION ENDPOINTS ====================

@router.get("/next-week", response_model=WeeklyForecast)
async def predict_next_week(current_user: dict = Depends(get_current_user)):
    """
    🤖 ML: Predict next week's expenses using Linear Regression, Moving Average & Exponential Smoothing
    User is identified via JWT.
    """
    user_id = current_user["user_id"]
    verify_user_exists(user_id)

    with get_db() as conn:
        cursor = conn.cursor()

        # Get last 90 days of expenses
        lookback_date = date.today() - timedelta(days=90)
        cursor.execute("""
            SELECT category, amount, date
            FROM expenses
            WHERE user_id = ?
            AND date >= ?
            ORDER BY date
        """, (user_id, lookback_date))

        historical_expenses = [row_to_dict(row) for row in cursor.fetchall()]

        if len(historical_expenses) < 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough historical data for prediction. Add at least 7 days of expenses."
            )

        # Get last week's actual expenses
        last_week_start = date.today() - timedelta(days=7)
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = ?
            AND date >= ?
            GROUP BY category
        """, (user_id, last_week_start))
        last_week_data = {row["category"]: row["total"] for row in cursor.fetchall()}

        # Predict next week's expenses
        predictions_dict = predict_next_week_expenses(historical_expenses)

        # Build category predictions
        category_predictions = []
        total_predicted = 0.0
        category_history = defaultdict(list)
        for exp in historical_expenses:
            category_history[exp['category']].append(exp['amount'])

        for category, predicted_amount in predictions_dict.items():
            historical_amounts = category_history[category]
            category_pred = ExpensePrediction(
                category=category,
                predicted_amount=round(predicted_amount, 2),
                confidence=calculate_confidence(historical_amounts),
                trend=calculate_trend(historical_amounts),
                historical_average=round(statistics.mean(historical_amounts), 2) if historical_amounts else 0.0,
                last_week_actual=round(last_week_data.get(category, 0.0), 2)
            )
            category_predictions.append(category_pred)
            total_predicted += predicted_amount
            
        # Forecast period
        start_date = date.today() + timedelta(days=1)
        end_date = start_date + timedelta(days=6)

        return WeeklyForecast(
            start_date=start_date,
            end_date=end_date,
            total_predicted=round(total_predicted, 2),
            category_predictions=category_predictions,
            recommendations=[]  

        )


@router.get("/patterns", response_model=List[SpendingPattern])
async def analyze_spending_patterns(current_user: dict = Depends(get_current_user)):
    """
    📊 ML: Analyze spending patterns with trend detection & volatility analysis
    """
    user_id = current_user["user_id"]
    verify_user_exists(user_id)

    with get_db() as conn:
        cursor = conn.cursor()

        lookback_date = date.today() - timedelta(days=60)
        cursor.execute("""
            SELECT category, amount, date
            FROM expenses
            WHERE user_id = ?
            AND date >= ?
            ORDER BY date
        """, (user_id, lookback_date))

        expenses = [row_to_dict(row) for row in cursor.fetchall()]

        if not expenses:
            return []

        # Group by category
        category_data = defaultdict(list)
        for exp in expenses:
            category_data[exp['category']].append(exp['amount'])

        patterns = []
        for category, amounts in category_data.items():
            total = sum(amounts)
            days_tracked = (date.today() - lookback_date).days

            pattern = SpendingPattern(
                category=category,
                average_daily=round(total / days_tracked, 2),
                average_weekly=round(total / (days_tracked / 7), 2),
                average_monthly=round(total / (days_tracked / 30), 2),
                trend_direction=calculate_trend(amounts),
                volatility=calculate_volatility(amounts)
            )
            patterns.append(pattern)

        return patterns
