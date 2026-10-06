import re
from typing import Optional

from models import ThemeMode
from pydantic import BaseModel, field_validator

# Deliberately loose: one @, something on each side, a dot in the domain.
# Catches typos like "jane.gmail.com" without rejecting unusual real addresses.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def normalize_email(email: str) -> str:
    """Emails compare case-insensitively, so "Jane@X.com" can't open a second account."""
    return email.strip().lower()


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

    # Messages are shown to parents as-is by the sign-up form.
    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        v = normalize_email(v)
        if not _EMAIL_RE.match(v) or len(v) > 254:
            raise ValueError("Please enter a valid email address.")
        return v

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Please choose a username.")
        if len(v) > 50:
            raise ValueError("Usernames can be at most 50 characters.")
        if "<" in v or ">" in v:
            raise ValueError("Usernames can't contain < or >.")
        return v

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Please enter your name.")
        if len(v) > 100:
            raise ValueError("Names can be at most 100 characters.")
        if "<" in v or ">" in v:
            raise ValueError("Names can't contain < or >.")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Please use a password with at least {MIN_PASSWORD_LENGTH} characters.")
        if len(v) > 128:
            raise ValueError("Passwords can be at most 128 characters.")
        return v


class UserResponse(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None


class UserInDB(UserResponse):
    hashed_password: str
