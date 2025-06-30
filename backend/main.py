import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import auth
from routers import user
from routers import ai

app = FastAPI(debug=True)

# Create the database tables
Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:5174",
    # Add more origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(ai.router, prefix="/ai")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
