from fastapi import FastAPI, HTTPException, status
from datetime import datetime, date, timedelta

from db.database_utilities import get_db
# ==================== HELPER FUNCTIONS ====================
def row_to_dict(row):
    """Convert sqlite3.Row to dictionary"""
    return dict(zip(row.keys(), row))

def verify_user_exists(user_id: str):
    """Verify user exists"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

def verify_expense_ownership(expense_id: str, user_id: str):
    """Verify expense exists and belongs to user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM expenses WHERE expense_id = ?",
            (expense_id,)
        )
        expense = cursor.fetchone()
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        if expense["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this expense"
            )
        
        return row_to_dict(expense)

