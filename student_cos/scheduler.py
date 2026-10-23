"""
Deterministic daily planning and scheduling engine in pure Python.
Calculates date intervals, free time slots, priority weights, and knapsack packing.
"""
from __future__ import annotations

from datetime import datetime, date, timedelta, time
from typing import List, Tuple, Optional, Dict, Any

from student_cos.models import Task, Commitment, ScheduleBlock, DailyPlan, Priority, TaskStatus
from student_cos.config import DEFAULT_WORK_START, DEFAULT_WORK_END, DEFAULT_BREAK_MINUTES


def parse_time_str(t_str: str) -> time:
    """Parse HH:MM string to time object."""
    parts = [int(p) for p in t_str.strip().split(":")]
    return time(hour=parts[0], minute=parts[1])


def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def minutes_to_time_str(m: int) -> str:
    h = (m // 60) % 24
    mins = m % 60
    return f"{h:02d}:{mins:02d}"


def calculate_task_priority_score(task: Task, target_date: date) -> float:
    """
    Deterministic scoring algorithm for student tasks:
    Score = Priority_Weight + Status_Weight + Deadline_Urgency_Weight
    """
    # 1. Base Priority Weight
    pri_weight = Priority.numeric_weight(task.priority) * 35  # HIGH=105, MEDIUM=70, LOW=35

    # 2. Status Weight: favor finishing in-progress work first to maintain flow
    if task.status == TaskStatus.IN_PROGRESS:
        status_weight = 40.0
    elif task.status == TaskStatus.BLOCKED:
        status_weight = -100.0  # Do not schedule blocked tasks
    else:
        status_weight = 0.0

    # 3. Deterministic Deadline Urgency
    deadline_weight = 0.0
    if task.deadline:
        try:
            # support both YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS
            deadline_str = task.deadline.split("T")[0].split(" ")[0]
            dl_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            diff_days = (dl_date - target_date).days

            if diff_days < 0:
                deadline_weight = 150.0  # Overdue! Urgent!
            elif diff_days == 0:
                deadline_weight = 120.0  # Due today
            elif diff_days == 1:
                deadline_weight = 85.0   # Due tomorrow
            elif diff_days <= 3:
                deadline_weight = 50.0   # Due within 3 days
            elif diff_days <= 7:
                deadline_weight = 25.0   # Due this week
            else:
                deadline_weight = 5.0
        except Exception:
            deadline_weight = 0.0

    return pri_weight + status_weight + deadline_weight


class DeterministicScheduler:
    """
    Schedules daily tasks around fixed student commitments (classes, labs, meetings).
    Ensures zero hallucinated time math and respects student capacity.
    """

    def __init__(
        self,
        work_start: str = DEFAULT_WORK_START,
        work_end: str = DEFAULT_WORK_END,
        break_minutes: int = DEFAULT_BREAK_MINUTES
    ):
        self.work_start = work_start
        self.work_end = work_end
        self.break_minutes = break_minutes

    def get_free_intervals(
        self,
        day_start_m: int,
        day_end_m: int,
        commitments: List[Commitment]
    ) -> List[Tuple[int, int]]:
        """
        Subtracts commitments from the working day to produce non-overlapping free time windows.
        """
        # Convert commitments to minute ranges
        busy: List[Tuple[int, int]] = []
        for c in commitments:
            c_start = time_to_minutes(parse_time_str(c.start_time))
            c_end = time_to_minutes(parse_time_str(c.end_time))
            # Clip to working hours
            c_start = max(day_start_m, min(day_end_m, c_start))
            c_end = max(day_start_m, min(day_end_m, c_end))
            if c_end > c_start:
                busy.append((c_start, c_end))

        # Merge overlapping busy periods
        busy.sort(key=lambda x: x[0])
        merged_busy: List[Tuple[int, int]] = []
        for b in busy:
            if not merged_busy:
                merged_busy.append(b)
            else:
                last_start, last_end = merged_busy[-1]
                if b[0] <= last_end:
                    merged_busy[-1] = (last_start, max(last_end, b[1]))
                else:
                    merged_busy.append(b)

        # Invert busy to get free intervals
        free_intervals: List[Tuple[int, int]] = []
        curr = day_start_m
        for b_start, b_end in merged_busy:
            if b_start > curr:
                free_intervals.append((curr, b_start))
            curr = max(curr, b_end)
        if curr < day_end_m:
            free_intervals.append((curr, day_end_m))

        return free_intervals

    def generate_daily_plan(
        self,
        tasks: List[Task],
        commitments: List[Commitment],
        target_date_str: Optional[str] = None
    ) -> DailyPlan:
        """
        Generates a deterministic schedule for the day.
        """
        if not target_date_str:
            target_date = date.today()
            target_date_str = target_date.isoformat()
        else:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

        day_start_m = time_to_minutes(parse_time_str(self.work_start))
        day_end_m = time_to_minutes(parse_time_str(self.work_end))
        total_day_capacity_m = max(0, day_end_m - day_start_m)

        # 1. Filter out already completed tasks
        eligible_tasks = [t for t in tasks if t.status != TaskStatus.DONE]

        # 2. Score and sort tasks deterministically
        scored_tasks: List[Tuple[float, Task]] = []
        for t in eligible_tasks:
            # Blocked tasks get negative score and will only be scheduled if unblocked
            score = calculate_task_priority_score(t, target_date)
            scored_tasks.append((score, t))

        # Sort: Highest score first, then earliest deadline, then shortest duration
        scored_tasks.sort(
            key=lambda x: (
                -x[0],
                x[1].deadline or "9999-99-99",
                x[1].estimated_minutes
            )
        )

        # 3. Calculate free intervals around commitments
        # Also prepare schedule blocks with commitments already placed
        scheduled_blocks: List[ScheduleBlock] = []

        # Add commitments as fixed blocks
        for c in sorted(commitments, key=lambda x: x.start_time):
            c_start_m = time_to_minutes(parse_time_str(c.start_time))
            c_end_m = time_to_minutes(parse_time_str(c.end_time))
            scheduled_blocks.append(ScheduleBlock(
                start_time=c.start_time,
                end_time=c.end_time,
                title=f"📅 {c.title}",
                block_type="COMMITMENT",
                estimated_minutes=max(0, c_end_m - c_start_m)
            ))

        free_intervals = self.get_free_intervals(day_start_m, day_end_m, commitments)
        total_free_minutes = sum(end - start for start, end in free_intervals)

        # 4. Pack tasks into free intervals
        scheduled_task_ids = set()
        unscheduled_tasks: List[Task] = []
        total_planned_minutes = sum(b.estimated_minutes for b in scheduled_blocks if b.block_type == "COMMITMENT")

        # Create mutable list of intervals
        intervals = [list(interval) for interval in free_intervals]

        for score, task in scored_tasks:
            if score < 0 or task.status == TaskStatus.BLOCKED:
                unscheduled_tasks.append(task)
                continue

            est = task.estimated_minutes if task.estimated_minutes > 0 else 30
            placed = False

            for interval in intervals:
                curr_start, curr_end = interval[0], interval[1]
                remaining_slot = curr_end - curr_start

                if remaining_slot >= min(est, 25):  # at least 25 min to be productive
                    block_dur = min(est, remaining_slot)
                    start_str = minutes_to_time_str(curr_start)
                    end_str = minutes_to_time_str(curr_start + block_dur)

                    scheduled_blocks.append(ScheduleBlock(
                        start_time=start_str,
                        end_time=end_str,
                        title=f"{task.title} ({task.project_name or 'General'})",
                        task_id=task.id,
                        block_type="TASK",
                        priority=task.priority.value if isinstance(task.priority, Priority) else str(task.priority),
                        estimated_minutes=block_dur
                    ))

                    total_planned_minutes += block_dur
                    scheduled_task_ids.add(task.id)

                    # Update interval start with small buffer/break
                    next_start = curr_start + block_dur + self.break_minutes
                    interval[0] = min(next_start, curr_end)
                    placed = True
                    break

            if not placed:
                unscheduled_tasks.append(task)

        # Sort all scheduled blocks by start_time
        scheduled_blocks.sort(key=lambda b: time_to_minutes(parse_time_str(b.start_time)))

        # 5. Overload warning and recommendations
        overload_warning = None
        if len(unscheduled_tasks) > 0 and total_free_minutes < sum(t.estimated_minutes for t in unscheduled_tasks):
            overload_warning = (
                f"Schedule capacity reached. {len(unscheduled_tasks)} pending tasks deferred "
                f"to protect cognitive capacity and avoid burnout."
            )

        recommendations = []
        if scheduled_blocks:
            top_task_block = next((b for b in scheduled_blocks if b.block_type == "TASK"), None)
            if top_task_block:
                recommendations.append(f"Primary Focus: Start your morning with **{top_task_block.title}**.")
        if any(t.status == TaskStatus.BLOCKED for t in tasks):
            blocked_count = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
            recommendations.append(f"Attention: You have {blocked_count} blocked task(s). Unblock dependencies before scheduling.")
        if total_free_minutes > 90 and len(unscheduled_tasks) == 0:
            recommendations.append("Good pacing today. Extra buffer time available for review or rest.")

        return DailyPlan(
            date=target_date_str,
            available_hours=round(total_free_minutes / 60.0, 1),
            total_planned_minutes=total_planned_minutes,
            scheduled_blocks=scheduled_blocks,
            unscheduled_tasks=unscheduled_tasks,
            top_recommendations=recommendations,
            overload_warning=overload_warning
        )
