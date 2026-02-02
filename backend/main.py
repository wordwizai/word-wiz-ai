import uvicorn
from database import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from routers import ai, auth, google_auth, session, user, activities, feedback, health, classes
from starlette.middleware.sessions import SessionMiddleware
from core.logging_config import setup_logging, get_logger

# Initialize logging
log_level = os.getenv("LOG_LEVEL", "INFO")
enable_perf_logging = os.getenv("ENABLE_PERFORMANCE_LOGGING", "false").lower() == "true"
setup_logging(level=log_level, enable_performance_logging=enable_perf_logging)

logger = get_logger(__name__)
logger.info("Starting Word Wiz AI Backend")

app = FastAPI(debug=os.getenv("DEBUG", "false").lower() == "true")

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
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_middleware(SessionMiddleware, secret_key=google_auth.GOOGLE_CLIENT_SECRET or "")


app.include_router(user.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(ai.router, prefix="/ai")
app.include_router(google_auth.router, prefix="/auth/google")
app.include_router(session.router, prefix="/session")
app.include_router(activities.router, prefix="/activities")
app.include_router(feedback.router, prefix="/feedback")
app.include_router(classes.router, prefix="/classes")
app.include_router(health.router)  # Health check endpoints

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
