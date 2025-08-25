import uvicorn
from database import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from routers import ai, auth, google_auth, session, user, activities, feedback
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(debug=True)

# Create the database tables
Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:5173",
    "https://wordwizai.com",
    "https://www.wordwizai.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=google_auth.GOOGLE_CLIENT_SECRET or "")


app.include_router(user.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(ai.router, prefix="/ai")
app.include_router(google_auth.router, prefix="/auth/google")
app.include_router(session.router, prefix="/session")
app.include_router(activities.router, prefix="/activities")
app.include_router(feedback.router, prefix="/feedback")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
