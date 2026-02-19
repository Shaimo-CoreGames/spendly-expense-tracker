from contextlib import contextmanager
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "expense_tracker.db")

@contextmanager
def get_db():
    """Context manager for database connection"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize database tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """)
        
        # Create expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                expense_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                date DATE NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Create budgets table for ML predictions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                monthly_limit REAL NOT NULL CHECK(monthly_limit > 0),
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, category)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_user_id 
            ON expenses(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_date 
            ON expenses(date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_category 
            ON expenses(category)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expenses_user_date 
            ON expenses(user_id, date)
        """)

