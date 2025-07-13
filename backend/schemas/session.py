from datetime import datetime

from pydantic import BaseModel
from schemas.activity import ActivityOut


class SessionCreateRequest(BaseModel):
    activity_id: int


class SessionBase(BaseModel):
    activity_id: int
    user_id: int


class SessionCreate(SessionBase):
    pass


class SessionOut(SessionBase):
    id: int
    created_at: datetime  # ISO format date string
    is_completed: bool  # True for completed, False for not completed
    activity: ActivityOut

    model_config = {"from_attributes": True}


class SessionInDB(SessionBase):
    id: int
    created_at: datetime  # ISO format date string
    is_completed: bool  # True for completed, False for not completed

    model_config = {"from_attributes": True}
