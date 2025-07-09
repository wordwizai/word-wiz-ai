from pydantic import BaseModel


class SessionBase(BaseModel):
    activity_id: int
    user_id: int
    metadata: dict = {}


class SessionCreate(SessionBase):
    pass


class SessionOut(SessionBase):
    id: int
    created_at: str  # ISO format date string

    class Config:
        orm_mode = True  # Enable ORM mode for compatibility with SQLAlchemy models
