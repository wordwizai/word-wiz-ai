from pydantic import BaseModel


class ActivityBase(BaseModel):
    title: str
    type = str  # e.g., 'story_mode', 'drill', etc.
    target_phoneme: str | None = None  # e.g., "/ʃ/"
    metadata: dict = {}


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(ActivityBase):
    id: int


class ActivityOut(ActivityBase):
    id: int

    class Config:
        orm_mode = True  # Enable ORM mode for compatibility with SQLAlchemy models
