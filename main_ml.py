from fastapi import FastAPI
from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Annotated, Optional, List, Dict
from datetime import datetime, date, timedelta
from enum import Enum
import uuid
import statistics
from collections import defaultdict
from db.database_utilities import get_db, init_database
from model.user_schema import UserCreate, UserResponse
from model.expense_schema import ExpenseCreate, ExpenseResponse, ExpenseUpdate, ExpenseCategory,MonthlySummary,SpendingPattern
from model.budget_schema import BudgetCreate, BudgetResponse, BudgetAlert
from model.prediction_schema import WeeklyForecast, ExpensePrediction
from ml.algorithms import predict_next_week_expenses, calculate_confidence, calculate_trend, calculate_volatility, moving_average
from utils.helpers import row_to_dict, verify_user_exists, verify_expense_ownership
from db.database_utilities import DATABASE_NAME

app = FastAPI(title="Personal Expense Tracker API with ML", version="2.0.0")

# ------------------------------------------------------------------
from api.users import router as users_router
app.include_router(users_router)
# ------------------------------------------------------------------
from api.expenses import router as expenses_router
app.include_router(expenses_router)
# ------------------------------------------------------------------
from api.predictions import router as predictions_router
app.include_router(predictions_router)
# ------------------------------------------------------------------
from api.budgets import router as budgets_router
app.include_router(budgets_router)
# ------------------------------------------------------------------

from api.auth import auth_router
app.include_router(auth_router)

# ==================== DATABASE CONNECTION ====================
# Initialize database on startup
init_database()

# ==================== ROOT ENDPOINT ====================
@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        users_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM expenses")
        expenses_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM budgets")
        budgets_count = cursor.fetchone()["count"]
    
    return {
        "status": "healthy",
        "database": "SQLite",
        "ml_enabled": True,
        "timestamp": datetime.now(),
        "users_count": users_count,
        "expenses_count": expenses_count,
        "budgets_count": budgets_count
    }

# ==================== STARTUP/SHUTDOWN EVENTS ====================
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 Expense Tracker API with ML Started")
    print(f"📁 Database: {DATABASE_NAME}")
    print("🤖 ML Features: Enabled")
    print("📊 Prediction Models: Linear Regression, Moving Average, Exponential Smoothing")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 Expense Tracker API Shutting Down")
