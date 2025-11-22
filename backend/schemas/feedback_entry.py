from datetime import datetime
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel, Json


class FeedbackEntryBase(BaseModel):
    session_id: int
    sentence: str
    phoneme_analysis: dict
    gpt_response: dict


class FeedbackEntryCreate(FeedbackEntryBase):
    pass


class FeedbackEntryOut(FeedbackEntryBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AudioAnalysis(BaseModel):
    pronunciation_dataframe: pd.DataFrame
    problem_summary: dict
    per_summary: dict
    highest_per_word: dict

    class Config:
        arbitrary_types_allowed = True


class UserStatistics(BaseModel):
    """User statistics for dashboard display"""
    total_sessions: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    words_read: int = 0
    
    model_config = {"from_attributes": True}
