from pydantic import BaseModel, Field,EmailStr
from typing import Annotated, Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=50)]
    email: Annotated[EmailStr, Field(...)]
    password: Annotated[str, Field(..., min_length=6)]
    full_name: Optional[Annotated[str, Field(..., min_length=1, max_length=100)]] = None

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str]
    created_at: datetime

