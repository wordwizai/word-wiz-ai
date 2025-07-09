from typing import Optional

from models import ThemeMode
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str


class UserResponse(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None


class UserInDB(UserResponse):
    hashed_password: str
