"""
Tests for ChiefOfStaffTools interface, parameter validation, and safety confirmations.
"""
import pytest
from student_cos.db import Database
from student_cos.tools import ChiefOfStaffTools


@pytest.fixture
def tools_instance(tmp_path):
    db_file = tmp_path / "test_tools.db"
    db = Database(str(db_file))
    return ChiefOfStaffTools(db)


def test_create_and_list_tasks(tools_instance):
    res = tools_instance.create_task(
        title="Prepare for LeetCode contest",
        project_name="Interviews",
        priority="HIGH",
        estimated_minutes=90
    )
    assert res.success is True
    assert res.data["title"] == "Prepare for LeetCode contest"
    assert res.data["priority"] == "HIGH"
    assert res.data["project_name"] == "Interviews"

    # List tasks
    list_res = tools_instance.list_tasks(priority="HIGH")
    assert list_res.success is True
    assert len(list_res.data) == 1


def test_invalid_task_inputs(tools_instance):
    # Empty title should fail
    res = tools_instance.create_task(title="")
    assert res.success is False
    assert "required" in res.error.lower()

    # Updating non-existent task should fail
    update_res = tools_instance.update_task(task_id=99999, title="Non-existent")
    assert update_res.success is False
    assert "not found" in update_res.error.lower()


def test_safety_confirmation_on_delete_task(tools_instance):
    # 1. Create a task
    created = tools_instance.create_task(title="Sensitive task to delete")
    tid = created.data["id"]

    # 2. Attempt deletion WITHOUT confirmation
    del_unconfirmed = tools_instance.delete_task(tid, confirmed=False)
    assert del_unconfirmed.success is False
    assert del_unconfirmed.requires_confirmation is True
    assert del_unconfirmed.confirmation_prompt is not None

    # Verify task still exists
    list_res = tools_instance.list_tasks()
    assert any(t["id"] == tid for t in list_res.data)

    # 3. Attempt deletion WITH confirmation
    del_confirmed = tools_instance.delete_task(tid, confirmed=True)
    assert del_confirmed.success is True

    # Verify task is now deleted
    list_res_after = tools_instance.list_tasks()
    assert not any(t["id"] == tid for t in list_res_after.data)


def test_safety_confirmation_on_delete_project(tools_instance):
    proj_res = tools_instance.create_project(name="Project to remove")
    pid = proj_res.data["id"]

    # Without confirmation
    del_unconfirmed = tools_instance.delete_project(pid, confirmed=False)
    assert del_unconfirmed.success is False
    assert del_unconfirmed.requires_confirmation is True

    # With confirmation
    del_confirmed = tools_instance.delete_project(pid, confirmed=True)
    assert del_confirmed.success is True
