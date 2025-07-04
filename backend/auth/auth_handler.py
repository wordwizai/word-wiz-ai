import jwt
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from database import get_db
from schemas import TokenData
from models import User, UserSettings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

load_dotenv()
secret_key = os.getenv("SECRET_KEY")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


router = APIRouter()


def verify_password(plain_password, hashed_password):
    """
    Verify a plain password against its hashed version.

    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hash a password using the configured password context.

    Args:
        password (str): The plain text password.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_user(db: Session, user: User):
    """
    Create a new user in the database.

    Args:
        db (Session): SQLAlchemy database session.
        user (User): The user object to create.

    Returns:
        User: The created user object.
    """
    db.add(user)
    db.flush()

    # add settings
    settings = UserSettings(user_id=user.id)
    db.add(settings)

    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, email: str):
    """
    Retrieve a user from the database by email.

    Args:
        db (Session): SQLAlchemy database session.
        email (str): The user's email address.

    Returns:
        User | None: The user object if found, else None.
    """
    db_user = db.query(User).filter(User.email == email).first()
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate a user by email and password.

    Args:
        db (Session): SQLAlchemy database session.
        email (str): The user's email address.
        password (str): The plain text password.

    Returns:
        User | bool: The user object if authentication is successful, else False.
    """
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create a JWT access token.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (timedelta, optional): Token expiration time delta.

    Returns:
        str: The encoded JWT token.

    Raises:
        HTTPException: If the secret key is not set.
    """
    if secret_key is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    Retrieve the current user based on the JWT token.

    Args:
        token (str): The JWT token from the request.
        db (Session): SQLAlchemy database session.

    Returns:
        User: The authenticated user.

    Raises:
        HTTPException: If credentials are invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if secret_key is None:
            raise credentials_exception
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Retrieve the current active user.

    Args:
        current_user (User): The current authenticated user.

    Returns:
        User: The current active user.
    """
    return current_user
