"""
Deterministic tool interface and safety enforcement layer.
AI and automation layers interact with database ONLY through these validated tools.
"""
from __future__ import annotations

from datetime import date
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

from student_cos.db import Database
from student_cos.models import Task, Project, Priority, TaskStatus, ProjectCategory
from student_cos.scheduler import DeterministicScheduler


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None


class ChiefOfStaffTools:
    """
    Standard toolset exposed to both AI agents and the UI.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.scheduler = DeterministicScheduler()

    # 1. create_task
    def create_task(
        self,
        title: str,
        project_id: Optional[int] = None,
        project_name: Optional[str] = None,
        deadline: Optional[str] = None,
        priority: str = "MEDIUM",
        estimated_minutes: int = 30,
        notes: str = ""
    ) -> ToolResult:
        try:
            if not title or not title.strip():
                return ToolResult(success=False, error="Task title is required.")

            resolved_pid = project_id
            if resolved_pid is None and project_name:
                p = self.db.get_project_by_name(project_name)
                if p:
                    resolved_pid = p.id
                else:
                    # Automatically create the project if named
                    new_p = self.db.create_project(Project(name=project_name.strip()))
                    resolved_pid = new_p.id

            task = Task(
                title=title.strip(),
                project_id=resolved_pid,
                deadline=deadline,
                priority=priority,  # validated by model
                status=TaskStatus.TODO,
                estimated_minutes=max(5, estimated_minutes),
                notes=notes
            )
            created = self.db.create_task(task)
            return ToolResult(success=True, data=created.model_dump())
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create task: {str(e)}")

    # 2. update_task
    def update_task(self, task_id: int, **updates) -> ToolResult:
        try:
            existing = self.db.get_task(task_id)
            if not existing:
                return ToolResult(success=False, error=f"Task with ID {task_id} not found.")

            updated = self.db.update_task(task_id, updates)
            if updated:
                return ToolResult(success=True, data=updated.model_dump())
            return ToolResult(success=False, error="No changes applied.")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to update task: {str(e)}")

    # 3. complete_task
    def complete_task(self, task_id: int, actual_minutes: Optional[int] = None) -> ToolResult:
        try:
            task = self.db.get_task(task_id)
            if not task:
                return ToolResult(success=False, error=f"Task with ID {task_id} not found.")

            completed = self.db.complete_task(task_id, actual_minutes)
            return ToolResult(success=True, data=completed.model_dump() if completed else None)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to complete task: {str(e)}")

    # 4. list_tasks
    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> ToolResult:
        try:
            tasks = self.db.list_tasks(status=status, priority=priority, project_id=project_id, search=search)
            return ToolResult(success=True, data=[t.model_dump() for t in tasks])
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to list tasks: {str(e)}")

    # 5. get_deadlines
    def get_deadlines(self, days: int = 14) -> ToolResult:
        try:
            deadlines = self.db.get_upcoming_deadlines(days=days)
            return ToolResult(success=True, data=[t.model_dump() for t in deadlines])
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to fetch deadlines: {str(e)}")

    # 6. get_project
    def get_project(self, project_identifier: str | int) -> ToolResult:
        try:
            if isinstance(project_identifier, int) or (isinstance(project_identifier, str) and project_identifier.isdigit()):
                p = self.db.get_project(int(project_identifier))
            else:
                p = self.db.get_project_by_name(str(project_identifier))

            if not p:
                return ToolResult(success=False, error=f"Project '{project_identifier}' not found.")

            # Attach project tasks
            tasks = self.db.list_tasks(project_id=p.id)
            data = p.model_dump()
            data["tasks"] = [t.model_dump() for t in tasks]
            return ToolResult(success=True, data=data)
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get project: {str(e)}")

    # 7. create_project
    def create_project(
        self,
        name: str,
        category: str = "Academics",
        description: str = "",
        target_date: Optional[str] = None
    ) -> ToolResult:
        try:
            existing = self.db.get_project_by_name(name)
            if existing:
                return ToolResult(success=False, error=f"Project '{name}' already exists (ID: {existing.id}).")

            proj = Project(
                name=name.strip(),
                category=category,
                description=description,
                target_date=target_date
            )
            created = self.db.create_project(proj)
            return ToolResult(success=True, data=created.model_dump())
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create project: {str(e)}")

    # 8. delete_task (Safety guarded)
    def delete_task(self, task_id: int, confirmed: bool = False) -> ToolResult:
        task = self.db.get_task(task_id)
        if not task:
            return ToolResult(success=False, error=f"Task with ID {task_id} does not exist.")

        if not confirmed:
            return ToolResult(
                success=False,
                requires_confirmation=True,
                confirmation_prompt=f"Are you sure you want to permanently delete task '{task.title}' (ID {task.id})? Pass confirmed=True to proceed."
            )

        success = self.db.delete_task(task_id)
        return ToolResult(success=success, data={"deleted_task_id": task_id, "title": task.title})

    # 9. delete_project (Safety guarded)
    def delete_project(self, project_id: int, confirmed: bool = False) -> ToolResult:
        proj = self.db.get_project(project_id)
        if not proj:
            return ToolResult(success=False, error=f"Project with ID {project_id} does not exist.")

        if not confirmed:
            return ToolResult(
                success=False,
                requires_confirmation=True,
                confirmation_prompt=f"Destructive Action: Are you sure you want to delete project '{proj.name}'? Existing tasks will be detached. Pass confirmed=True to proceed."
            )

        success = self.db.delete_project(project_id)
        return ToolResult(success=success, data={"deleted_project_id": project_id, "name": proj.name})

    # 10. plan_day
    def plan_day(self, date_str: Optional[str] = None) -> ToolResult:
        try:
            target_date = date_str or date.today().isoformat()
            tasks = self.db.list_tasks()
            commitments = self.db.list_commitments(for_date=target_date)
            daily_plan = self.scheduler.generate_daily_plan(tasks, commitments, target_date)
            return ToolResult(success=True, data=daily_plan.model_dump())
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to generate daily plan: {str(e)}")

    # 11. get_project_summary
    def get_project_summary(self) -> ToolResult:
        try:
            stats = self.db.get_weekly_review_stats()
            return ToolResult(success=True, data=stats["project_stats"])
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get project summary: {str(e)}")


# Tool definitions formatted for LLM Function Calling schemas
TOOL_DEFINITIONS = [
    {
        "name": "create_task",
        "description": "Create a new task with project, deadline, priority, and estimated time.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The clear, actionable task title"},
                "project_name": {"type": "string", "description": "Name of the project this task belongs to"},
                "deadline": {"type": "string", "description": "Deadline in YYYY-MM-DD or YYYY-MM-DD HH:MM format"},
                "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"], "description": "Priority level"},
                "estimated_minutes": {"type": "integer", "description": "Estimated time to complete in minutes"},
                "notes": {"type": "string", "description": "Additional notes or subtasks"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "update_task",
        "description": "Update fields of an existing task by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "Task ID"},
                "title": {"type": "string"},
                "status": {"type": "string", "enum": ["TODO", "IN PROGRESS", "DONE", "BLOCKED"]},
                "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                "deadline": {"type": "string"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task as completed (DONE) and optionally record actual minutes spent.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "ID of the completed task"},
                "actual_minutes": {"type": "integer", "description": "Actual minutes taken"}
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "list_tasks",
        "description": "List or filter tasks by status, priority, or search term.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["TODO", "IN PROGRESS", "DONE", "BLOCKED"]},
                "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                "search": {"type": "string", "description": "Search keyword"}
            }
        }
    },
    {
        "name": "get_deadlines",
        "description": "Retrieve all upcoming tasks sorted chronologically by due date.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Window in days (default 14)"}
            }
        }
    },
    {
        "name": "get_project",
        "description": "Get detailed info and tasks for a specific project by name or ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_identifier": {"type": "string", "description": "Project ID or Project Name"}
            },
            "required": ["project_identifier"]
        }
    },
    {
        "name": "create_project",
        "description": "Create a new project entity for tracking coursework, internships, or learning.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project title"},
                "category": {"type": "string", "enum": ["Academics", "Job Search", "Learning", "Side Project", "Personal"]},
                "description": {"type": "string"},
                "target_date": {"type": "string", "description": "Target completion date (YYYY-MM-DD)"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "plan_day",
        "description": "Run the deterministic scheduling algorithm to generate today's agenda.",
        "parameters": {
            "type": "object",
            "properties": {
                "date_str": {"type": "string", "description": "Target date in YYYY-MM-DD format (defaults to today)"}
            }
        }
    },
    {
        "name": "get_project_summary",
        "description": "Get high level progress percentage and status across all active student projects.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
