"""
api/auth.py
JWT Authentication router — handles login, token verification, /auth/me
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import hashlib, hmac, base64, json, sqlite3
from contextlib import contextmanager
from db.database_utilities import get_db,DATABASE_NAME

# ─── CONFIG ──────────────────────────────────────────────────────────
SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION_USE_ENV_VAR"   # ← swap with env var
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# ─── SIMPLE JWT (no PyJWT dep) ────────────────────────────────────────
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def create_token(user_id: str, username: str) -> str:
    header  = _b64url(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    expire  = (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
    payload = _b64url(json.dumps({"sub": user_id, "username": username, "exp": expire}).encode())
    sig     = _b64url(hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"

def verify_token(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3: raise ValueError
        header, payload, sig = parts
        expected_sig = _b64url(hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected_sig): raise ValueError("Invalid signature")
        padding = 4 - len(payload) % 4
        data = json.loads(base64.urlsafe_b64decode(payload + '=' * padding))
        if datetime.fromisoformat(data['exp']) < datetime.utcnow():
            raise ValueError("Token expired")
        return data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

# ─── DB HELPER (reuse same db) ────────────────────────────────────────

from fastapi import Depends, HTTPException, status
from db.database_utilities import get_db
from utils.helpers import row_to_dict

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    user_id = payload["sub"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        return row_to_dict(user)

# ─── RESPONSE MODELS ──────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str]

# ─── ROUTES ──────────────────────────────────────────────────────────
@auth_router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """Login with username + password → returns JWT token"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, username, password FROM users WHERE username = ?",
            (form.username,)
        )
        user = cur.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Compare hashed password
    if user["password"] != hash_password(form.password):
        # Also allow plain text for backwards compat with existing test data
        if user["password"] != form.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

    token = create_token(user["user_id"], user["username"])
    return TokenResponse(access_token=token)

@auth_router.get("/me", response_model=MeResponse)
async def me(current_user: dict = Depends(get_current_user)):
    """Get the currently authenticated user's info"""
    return MeResponse(**current_user)
