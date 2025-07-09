from datetime import datetime
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel


class FeedbackEntryBase(BaseModel):
    session_id: int
    sentence: str
    phoneme_analysis: Any
    feedback_text: str


class FeedbackEntryCreate(FeedbackEntryBase):
    pass


class FeedbackEntryOut(FeedbackEntryBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class AudioAnalysis(BaseModel):
    pronunciation_dataframe: pd.DataFrame
    problem_summary: dict
    per_summary: dict
    highest_per_word: dict

    class Config:
        arbitrary_types_allowed = True
