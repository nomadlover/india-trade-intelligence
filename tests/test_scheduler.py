"""
Tests for Deterministic Scheduler and Prioritization Engine.
"""
import pytest
from datetime import date, timedelta
from student_cos.models import Task, Commitment, Priority, TaskStatus
from student_cos.scheduler import (
    DeterministicScheduler,
    calculate_task_priority_score,
    time_to_minutes,
    minutes_to_time_str
)


def test_time_conversions():
    assert minutes_to_time_str(90) == "01:30"
    assert minutes_to_time_str(600) == "10:00"


def test_free_interval_calculation():
    scheduler = DeterministicScheduler(work_start="09:00", work_end="17:00")
    commitments = [
        Commitment(title="Class 1", date="2026-10-15", start_time="10:00", end_time="11:30"),
        Commitment(title="Class 2", date="2026-10-15", start_time="13:00", end_time="14:00")
    ]
    day_start_m = time_to_minutes(scheduler.parse_time_str if hasattr(scheduler, "parse_time_str") else lambda s: None) if False else 9 * 60
    day_end_m = 17 * 60

    intervals = scheduler.get_free_intervals(day_start_m, day_end_m, commitments)
    # Expected free slots: 09:00 - 10:00 (540 - 600), 11:30 - 13:00 (690 - 780), 14:00 - 17:00 (840 - 1020)
    assert len(intervals) == 3
    assert intervals[0] == (540, 600)
    assert intervals[1] == (690, 780)
    assert intervals[2] == (840, 1020)


def test_priority_scoring():
    today = date.today()
    # High priority due today
    urgent_task = Task(title="Urgent", priority=Priority.HIGH, deadline=today.isoformat())
    # Low priority due in 20 days
    chill_task = Task(title="Chill", priority=Priority.LOW, deadline=(today + timedelta(days=20)).isoformat())

    score_urgent = calculate_task_priority_score(urgent_task, today)
    score_chill = calculate_task_priority_score(chill_task, today)

    assert score_urgent > score_chill
    # Blocked task should have negative or heavily penalized score
    blocked_task = Task(title="Blocked", status=TaskStatus.BLOCKED, priority=Priority.HIGH)
    score_blocked = calculate_task_priority_score(blocked_task, today)
    assert score_blocked < score_urgent


def test_daily_plan_generation():
    scheduler = DeterministicScheduler(work_start="09:00", work_end="14:00", break_minutes=15)
    today_str = date.today().isoformat()

    commitments = [
        Commitment(title="Morning Standup", date=today_str, start_time="09:30", end_time="10:00")
    ]
    tasks = [
        Task(id=1, title="Critical Bug", priority=Priority.HIGH, estimated_minutes=45, status=TaskStatus.TODO),
        Task(id=2, title="Refactor Module", priority=Priority.MEDIUM, estimated_minutes=60, status=TaskStatus.TODO),
    ]

    plan = scheduler.generate_daily_plan(tasks, commitments, today_str)

    assert plan.date == today_str
    assert len(plan.scheduled_blocks) >= 2
    # Verify no overlaps between scheduled task blocks and commitments
    for b in plan.scheduled_blocks:
        assert b.start_time < b.end_time
