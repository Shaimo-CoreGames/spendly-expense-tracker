from pydantic import BaseModel, Field
from typing import Annotated, List, Optional
from datetime import datetime, date
from enum import Enum

class ExpensePrediction(BaseModel):
    category: str
    predicted_amount: float
    confidence: float
    trend: str  # "increasing", "decreasing", "stable"
    historical_average: float
    last_week_actual: float

class WeeklyForecast(BaseModel):
    start_date: date
    end_date: date
    total_predicted: float
    category_predictions: List[ExpensePrediction]
    recommendations: List[str]

