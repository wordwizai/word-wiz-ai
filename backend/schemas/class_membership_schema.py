from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class JoinClassRequest(BaseModel):
    """Schema for joining a class."""
    join_code: str = Field(..., min_length=6, max_length=10, description="Join code for the class")


class ClassMembershipCreate(BaseModel):
    """Schema for creating a class membership."""
    class_id: int
    student_id: int


class ClassMembershipResponse(BaseModel):
    """Schema for class membership API responses."""
    id: int
    class_id: int
    student_id: int
    joined_at: datetime

    model_config = {"from_attributes": True}


class StudentStatistics(BaseModel):
    """Schema for student statistics."""
    total_sessions: int = Field(default=0, description="Total number of sessions completed")
    words_read: int = Field(default=0, description="Total number of words read")
    average_per: float = Field(default=0.0, description="Average Phoneme Error Rate")
    last_session_date: Optional[datetime] = Field(default=None, description="Date of last session")
    current_streak: int = Field(default=0, description="Current streak of consecutive days")


class StudentInfo(BaseModel):
    """Schema for student basic information."""
    id: int
    full_name: Optional[str]
    email: str

    model_config = {"from_attributes": True}


class StudentWithStats(StudentInfo):
    """Schema for student with statistics."""
    joined_at: datetime = Field(description="Date when student joined the class")
    statistics: StudentStatistics

    model_config = {"from_attributes": True}


class ClassStudentsResponse(BaseModel):
    """Schema for class students API response."""
    class_id: int
    class_name: str
    join_code: str
    students: list[StudentWithStats]


class SessionActivity(BaseModel):
    """Individual session activity record."""
    session_id: int
    date: datetime
    sentence_count: int = Field(description="Number of sentences practiced")
    accuracy: float = Field(description="Session accuracy percentage (0-100)")
    per: float = Field(description="Session Phoneme Error Rate")


class PhonemeInsight(BaseModel):
    """Phoneme-level insight with error analysis."""
    phoneme: str = Field(description="IPA phoneme symbol")
    error_count: int = Field(description="Number of times this phoneme was mispronounced")
    error_types: dict = Field(description="Breakdown by substitution, deletion, insertion")
    description: Optional[str] = Field(default=None, description="How to pronounce this phoneme")
    difficulty_level: Optional[int] = Field(default=None, description="Difficulty level 1-5")


class StudentInsightsResponse(BaseModel):
    """Comprehensive student insights for teacher view."""
    student_id: int
    recent_sessions: list[SessionActivity] = Field(description="Last 20 sessions")
    recent_accuracy: float = Field(description="Average accuracy from recent sessions (0-100)")
    recent_per: float = Field(description="Average PER from recent sessions")
    total_sentences_practiced: int = Field(description="Total sentences in recent window")
    phoneme_insights: list[PhonemeInsight] = Field(description="Top problematic phonemes")
    recommendations: list[str] = Field(description="Actionable teaching recommendations")
    calculation_window: str = Field(description="E.g., 'Last 15 sessions' or 'Last 7 days'")
