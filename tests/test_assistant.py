"""
Tests for StudentChiefOfStaff assistant orchestrator and natural language requests.
"""
from student_cos.db import Database
from student_cos.ai.assistant import StudentChiefOfStaff


def test_natural_language_queries(tmp_path):
    db_file = tmp_path / "test_assistant.db"
    db = Database(str(db_file))
    db.seed_sample_data_if_empty()

    assistant = StudentChiefOfStaff(db=db, provider_name="offline")

    # 1. "Plan my day"
    r1 = assistant.process_message("Plan my day.")
    assert "Daily Plan" in r1.text or "Time-Blocked Agenda" in r1.text
    assert len(r1.tools_called) >= 1
    assert r1.tools_called[0]["tool"] == "plan_day"

    # 2. "What should I work on first?"
    r2 = assistant.process_message("What should I work on first?")
    assert "Focus" in r2.text or "Task" in r2.text

    # 3. "Summarize my project progress"
    r3 = assistant.process_message("Summarize my project progress.")
    assert "Project Progress" in r3.text
    assert "%" in r3.text

    # 4. "What deadlines are coming up?"
    r4 = assistant.process_message("What deadlines are coming up?")
    assert "Deadlines" in r4.text

    # 5. "Create task: Review Chapter 4 of OS book"
    r5 = assistant.process_message("Create task Review Chapter 4 of OS book")
    assert "Created task" in r5.text or "Review Chapter 4" in r5.text
