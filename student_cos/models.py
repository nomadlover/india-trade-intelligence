"""
Data models and schemas for Student Chief of Staff.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN PROGRESS"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @classmethod
    def numeric_weight(cls, priority: "Priority | str") -> int:
        val = priority.value if isinstance(priority, Priority) else str(priority).upper()
        if val == "HIGH":
            return 3
        if val == "MEDIUM":
            return 2
        return 1


class ProjectCategory(str, Enum):
    ACADEMICS = "Academics"
    JOB_SEARCH = "Job Search"
    LEARNING = "Learning"
    SIDE_PROJECT = "Side Project"
    PERSONAL = "Personal"


class Project(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, description="Name of the project")
    category: str = Field(default=ProjectCategory.ACADEMICS.value)
    description: Optional[str] = ""
    status: str = Field(default="ACTIVE")  # ACTIVE, ON_HOLD, COMPLETED
    target_date: Optional[str] = None  # YYYY-MM-DD
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Project name cannot be empty or blank")
        return s


class Task(BaseModel):
    id: Optional[int] = None
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    title: str = Field(..., min_length=1, description="Title of the task")
    description: Optional[str] = ""
    deadline: Optional[str] = None  # YYYY-MM-DD or YYYY-MM-DD HH:MM
    priority: Priority = Field(default=Priority.MEDIUM)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    estimated_minutes: int = Field(default=30, ge=0)
    actual_minutes: int = Field(default=0, ge=0)
    notes: Optional[str] = ""
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Task title cannot be empty or whitespace only")
        return s

    @field_validator("priority", mode="before")
    @classmethod
    def parse_priority(cls, v: Any) -> Priority:
        if isinstance(v, Priority):
            return v
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in Priority._value2member_map_:
                return Priority(v_upper)
        return Priority.MEDIUM

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v: Any) -> TaskStatus:
        if isinstance(v, TaskStatus):
            return v
        if isinstance(v, str):
            v_upper = v.strip().upper()
            if v_upper in TaskStatus._value2member_map_:
                return TaskStatus(v_upper)
        return TaskStatus.TODO


class Commitment(BaseModel):
    id: Optional[int] = None
    title: str = Field(..., min_length=1)
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM (24h)
    end_time: str  # HH:MM (24h)
    notes: Optional[str] = ""


class ScheduleBlock(BaseModel):
    start_time: str
    end_time: str
    title: str
    task_id: Optional[int] = None
    block_type: str  # "TASK", "COMMITMENT", "BREAK", "BUFFER"
    priority: Optional[str] = None
    estimated_minutes: int = 0


class DailyPlan(BaseModel):
    date: str
    available_hours: float
    total_planned_minutes: int
    scheduled_blocks: List[ScheduleBlock]
    unscheduled_tasks: List[Task] = []
    top_recommendations: List[str] = []
    overload_warning: Optional[str] = None


class ExtractedTaskItem(BaseModel):
    title: str
    project_name: Optional[str] = None
    deadline: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    estimated_minutes: int = 45
    notes: Optional[str] = ""


class DocumentAnalysisResult(BaseModel):
    title: str = "Document Analysis"
    summary: str = ""
    key_points: List[str] = []
    decisions: List[str] = []
    action_items: List[str] = []
    extracted_tasks: List[ExtractedTaskItem] = []
    extracted_deadlines: List[Dict[str, Any]] = []
