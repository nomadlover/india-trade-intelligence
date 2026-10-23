"""
Tests for SQLite Database layer, persistence, and migrations.
"""
import pytest
from datetime import date, timedelta
from student_cos.db import Database
from student_cos.models import Task, Project, Commitment, TaskStatus, Priority, ProjectCategory


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_student_cos.db"
    return Database(str(db_file))


def test_project_crud(temp_db):
    # Create project
    proj = Project(
        name="CS 450 Operating Systems",
        category=ProjectCategory.ACADEMICS.value,
        description="Operating system kernel programming in C",
        target_date="2026-12-15"
    )
    created = temp_db.create_project(proj)
    assert created.id is not None
    assert created.name == "CS 450 Operating Systems"

    # Get project by ID and by Name
    fetched_by_id = temp_db.get_project(created.id)
    assert fetched_by_id is not None
    assert fetched_by_id.name == created.name

    fetched_by_name = temp_db.get_project_by_name("cs 450 operating systems")
    assert fetched_by_name is not None
    assert fetched_by_name.id == created.id

    # Update project
    updated = temp_db.update_project(created.id, {"description": "Updated OS description"})
    assert updated.description == "Updated OS description"

    # List projects
    all_projs = temp_db.list_projects()
    assert len(all_projs) == 1

    # Delete project
    deleted = temp_db.delete_project(created.id)
    assert deleted is True
    assert temp_db.get_project(created.id) is None


def test_task_creation_and_completion(temp_db):
    proj = temp_db.create_project(Project(name="Algorithms"))

    task = Task(
        project_id=proj.id,
        title="Implement Dijkstra Algorithm",
        priority=Priority.HIGH,
        estimated_minutes=60,
        deadline="2026-10-20"
    )
    created = temp_db.create_task(task)
    assert created.id is not None
    assert created.status == TaskStatus.TODO
    assert created.project_name == "Algorithms"

    # Complete task with actual minutes
    completed = temp_db.complete_task(created.id, actual_minutes=55)
    assert completed is not None
    assert completed.status == TaskStatus.DONE
    assert completed.actual_minutes == 55
    assert completed.completed_at is not None


def test_deadlines_filtering(temp_db):
    today = date.today()
    dl_soon = (today + timedelta(days=2)).isoformat()
    dl_far = (today + timedelta(days=30)).isoformat()

    temp_db.create_task(Task(title="Due Soon Task", deadline=dl_soon, priority=Priority.HIGH))
    temp_db.create_task(Task(title="Due Far Task", deadline=dl_far, priority=Priority.LOW))
    temp_db.create_task(Task(title="No Deadline Task", deadline=None))

    upcoming = temp_db.get_upcoming_deadlines(days=7)
    assert len(upcoming) == 1
    assert upcoming[0].title == "Due Soon Task"


def test_commitments(temp_db):
    c = Commitment(
        title="Distributed Systems Lecture",
        date="2026-10-15",
        start_time="10:00",
        end_time="11:30",
        notes="Room 304"
    )
    saved = temp_db.create_commitment(c)
    assert saved.id is not None

    list_c = temp_db.list_commitments("2026-10-15")
    assert len(list_c) == 1
    assert list_c[0].title == "Distributed Systems Lecture"


def test_document_saving(temp_db):
    doc_id = temp_db.save_document(
        title="Syllabus CS 450",
        content="Final project due Dec 10. Grade breakdown: 40% projects.",
        summary="Course syllabus overview",
        key_points=["40% projects weight"],
        decisions=["Use C99"],
        action_items=["Form teams by Friday"]
    )
    assert doc_id > 0
    docs = temp_db.list_documents()
    assert len(docs) == 1
    assert docs[0]["title"] == "Syllabus CS 450"
    assert "40% projects weight" in docs[0]["key_points"]


def test_weekly_review_stats(temp_db):
    proj = temp_db.create_project(Project(name="Thesis"))
    t1 = temp_db.create_task(Task(project_id=proj.id, title="Write Abstract", status=TaskStatus.TODO))
    t2 = temp_db.create_task(Task(project_id=proj.id, title="Lit Review", status=TaskStatus.DONE, actual_minutes=120))

    stats = temp_db.get_weekly_review_stats(days_back=7)
    assert stats["completed_count"] >= 1
    assert stats["total_time_spent_minutes"] >= 120
    assert len(stats["project_stats"]) == 1
    assert stats["project_stats"][0]["completion_pct"] == 50.0
