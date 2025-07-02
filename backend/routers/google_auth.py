from datetime import timedelta
from click import prompt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import os

from sqlalchemy.orm import Session

from auth.auth_handler import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_user
from database import get_db
from models import User

router = APIRouter()

# Load these from env for security
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

print("GOOGLE_CLIENT_ID:", GOOGLE_CLIENT_ID)
print("GOOGLE_CLIENT_SECRET:", GOOGLE_CLIENT_SECRET)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/login")
async def login_with_google(request: Request):
    redirect_uri = request.url_for("google_auth_callback")
    return await oauth.google.authorize_redirect(
        request, redirect_uri, prompt="select_account"
    )


@router.get("/callback", name="google_auth_callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(
            status_code=400, detail="Google login failed: user info missing"
        )

    email_verified = user_info.get("email_verified")
    if not email_verified:
        raise HTTPException(
            status_code=400, detail="Google login failed: email not verified"
        )

    # Example user_info fields: email, name, picture
    email = user_info.get("email")
    name = user_info.get("name")

    # Check your database: If user exists, log them in; if not, create a new one
    db_user = get_user(db, email)
    if db_user is None:
        # Create a new user if they don't exist
        db_user = User(
            email=email,
            full_name=name,
            username=email.split("@")[0],  # Use email prefix as username
            hashed_password=None,  # Password is not needed for OAuth
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # Generate a session or JWT for the frontend
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )

    # Send the token back to the frontend (e.g., in a redirect or JSON)
    response = RedirectResponse(
        url=f"http://localhost:5173/oauth-callback?token={jwt_token}"
    )
    return response
