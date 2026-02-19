from fastapi import Depends, FastAPI, HTTPException, status
from typing import List, Optional
from datetime import datetime, date
import uuid
from db.database_utilities import get_db
from model.expense_schema import ExpenseResponse, ExpenseCreate, ExpenseUpdate, ExpenseCategory
from utils.helpers import verify_user_exists, verify_expense_ownership, row_to_dict

# ------------------------------------------------------------------------
from fastapi import APIRouter

router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"]
)
# ------------------------------------------------------------------------

from api.auth import get_current_user   # ← pulls user_id from Bearer token
def row_dict(row): 
    return dict(zip(row.keys(), row))


@router.post("", response_model=ExpenseResponse, status_code=201)
async def add_expense(expense: ExpenseCreate, user=Depends(get_current_user)):
    """Add a new expense — user_id extracted from JWT automatically"""
    user_id = user["user_id"]
    with get_db() as conn:
        cur = conn.cursor()
        eid = str(uuid.uuid4())
        now = datetime.now()
        cur.execute("""
            INSERT INTO expenses
            (expense_id, user_id, amount, category, description, date, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (eid, user_id, expense.amount, expense.category.value,
              expense.description, expense.date, now, now))
    return ExpenseResponse(expense_id=eid, user_id=user_id, **expense.dict(), created_at=now, updated_at=now)

@router.get("", response_model=List[ExpenseResponse])
async def get_expenses(
    category:   Optional[ExpenseCategory] = None,
    start_date: Optional[date] = None,
    end_date:   Optional[date] = None,
    user=Depends(get_current_user)
):
    """Get all expenses for the logged-in user, with optional filters"""
    user_id = user["user_id"]
    with get_db() as conn:
        cur = conn.cursor()
        q = "SELECT * FROM expenses WHERE user_id = ?"
        p = [user_id]
        if category:    q += " AND category = ?";   p.append(category.value)
        if start_date:  q += " AND date >= ?";       p.append(str(start_date))
        if end_date:    q += " AND date <= ?";       p.append(str(end_date))
        q += " ORDER BY date DESC"
        cur.execute(q,p)
        return [ExpenseResponse(**row_dict(r)) for r in cur.fetchall()]

@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(expense_id: str, user=Depends(get_current_user)):
    """Get a single expense (must belong to the logged-in user)"""
    user_id = user["user_id"]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM expenses WHERE expense_id = ?", (expense_id,))
        exp = cur.fetchone()
    if not exp: raise HTTPException(404, "Expense not found")
    if exp["user_id"] != user_id: raise HTTPException(403, "Access denied")
    return ExpenseResponse(**row_dict(exp))

@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(expense_id: str, body: ExpenseUpdate, user=Depends(get_current_user)):
    """Update an expense"""
    user_id = user["user_id"]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM expenses WHERE expense_id = ?", (expense_id,))
        exp = cur.fetchone()
        if not exp: raise HTTPException(404, "Expense not found")
        if exp["user_id"] != user_id: raise HTTPException(403, "Access denied")

        fields, params = [], []
        if body.amount      is not None: fields.append("amount = ?");      params.append(body.amount)
        if body.category    is not None: fields.append("category = ?");    params.append(body.category.value)
        if body.description is not None: fields.append("description = ?"); params.append(body.description)
        if body.date        is not None: fields.append("date = ?");        params.append(str(body.date))
        fields.append("updated_at = ?"); params.append(datetime.now())
        params.append(expense_id)

        cur.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE expense_id = ?", params)
        cur.execute("SELECT * FROM expenses WHERE expense_id = ?", (expense_id,))
        return ExpenseResponse(**row_dict(cur.fetchone()))

@router.delete("/{expense_id}", status_code=204)
async def delete_expense(expense_id: str, user=Depends(get_current_user)):
    """Delete an expense"""
    user_id = user["user_id"]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM expenses WHERE expense_id = ?", (expense_id,))
        exp = cur.fetchone()
        if not exp: raise HTTPException(404, "Expense not found")
        if exp["user_id"] != user_id: raise HTTPException(403, "Access denied")
        cur.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))

# ─── SUMMARY ENDPOINTS ──────────────────────────────────────────────────
@router.get("/summary/monthly")
async def monthly_summary(month: int, year: int, user=Depends(get_current_user)):
    if month < 1 or month > 12: raise HTTPException(400, "Month must be 1-12")
    user_id = user["user_id"]
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as cnt, COALESCE(SUM(amount),0) as total, COALESCE(AVG(amount),0) as avg
            FROM expenses WHERE user_id=? AND strftime('%m',date)=? AND strftime('%Y',date)=?
        """, (user_id, f"{month:02d}", str(year)))
        row = cur.fetchone()
        cur.execute("""
            SELECT category, SUM(amount) as t FROM expenses
            WHERE user_id=? AND strftime('%m',date)=? AND strftime('%Y',date)=?
            GROUP BY category
        """, (user_id, f"{month:02d}", str(year)))
        breakdown = {r["category"]: round(r["t"], 2) for r in cur.fetchall()}
    return {
        "month": month, "year": year,
        "total_expenses": round(row["total"], 2),
        "expense_count":  row["cnt"],
        "category_breakdown": breakdown,
        "average_expense": round(row["avg"], 2)
    }
@router.get("/summary/category")
async def category_summary(user=Depends(get_current_user)):
    user_id = user["user_id"]

    today = datetime.today()
    month = f"{today.month:02d}"
    year = str(today.year)

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT COALESCE(SUM(amount),0) as t
            FROM expenses
            WHERE user_id=? 
            AND strftime('%m',date)=?
            AND strftime('%Y',date)=?
        """, (user_id, month, year))

        total = cur.fetchone()["t"]

        cur.execute("""
            SELECT category, SUM(amount) as t
            FROM expenses
            WHERE user_id=? 
            AND strftime('%m',date)=?
            AND strftime('%Y',date)=?
            GROUP BY category
        """, (user_id, month, year))

        rows = cur.fetchall()

    breakdown = {r["category"]: round(r["t"], 2) for r in rows}
    pcts = {k: round(v / total * 100, 2) if total else 0 for k, v in breakdown.items()}

    return {
        "total_expenses": round(total, 2),
        "category_breakdown": breakdown,
        "category_percentages": pcts
    }
