from fastapi import FastAPI, HTTPException, status,Depends
from typing import List, Optional
from model.user_schema import UserResponse, UserCreate
from db.database_utilities import get_db    
from utils.helpers import row_to_dict
import uuid
from datetime import datetime   

# ------------------------------------------------------------------------
from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)
# ------------------------------------------------------------------------

from api.auth import get_current_user   # ← pulls user_id from Bearer token

# ==================== USER ENDPOINTS ====================
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """Register a new user"""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (user.username,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        cursor.execute("""
            INSERT INTO users (user_id, username, email, password, full_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, user.username, user.email, user.password, user.full_name, created_at))
        
        return UserResponse(
            user_id=user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=created_at
        )

@router.get("/users/{username}", response_model=UserResponse)
async def get_user(username: str):
    """Get user information by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, email, full_name, created_at FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**row_to_dict(user))
