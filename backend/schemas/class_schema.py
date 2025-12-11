from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ClassCreate(BaseModel):
    """Schema for creating a new class."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the class")


class ClassBase(BaseModel):
    """Base schema for class data."""
    name: str
    join_code: str
    teacher_id: int
    created_at: datetime


class ClassResponse(ClassBase):
    """Schema for class API responses."""
    id: int

    model_config = {"from_attributes": True}


class ClassWithStudentCount(ClassResponse):
    """Schema for class with student count."""
    student_count: int = Field(default=0, description="Number of students in the class")

    model_config = {"from_attributes": True}


class TeacherInfo(BaseModel):
    """Schema for teacher information."""
    id: int
    full_name: Optional[str]
    email: str

    model_config = {"from_attributes": True}


class ClassWithTeacher(ClassResponse):
    """Schema for class with teacher information (for students)."""
    teacher: TeacherInfo

    model_config = {"from_attributes": True}
