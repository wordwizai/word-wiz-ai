import uvicorn
from database import Base, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from routers import ai, auth, google_auth, session, user, activities, feedback, health, classes, guest, assignments, phonics
from starlette.middleware.sessions import SessionMiddleware

# debug=True returns full tracebacks (SQL, parameters, file paths) in 500
# responses, so it stays off unless explicitly enabled for local work.
app = FastAPI(debug=os.getenv("FASTAPI_DEBUG") == "1")

# Create the database tables
Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:5173",
    "https://wordwizai.com",
    "https://www.wordwizai.com",
]
# Comma-separated extras for local work (dev_server.py sets this); unset in prod.
origins += [o for o in os.getenv("EXTRA_CORS_ORIGINS", "").split(",") if o]

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
app.include_router(classes.router, prefix="/classes")
# Teacher assignments of phonics patterns (see routers/assignments.py)
app.include_router(assignments.router, prefix="/classes")
app.include_router(phonics.router, prefix="/phonics")
# Public "try it" analysis, no account (see routers/guest.py)
app.include_router(guest.router, prefix="/guest")
app.include_router(health.router)  # Health check endpoints

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
