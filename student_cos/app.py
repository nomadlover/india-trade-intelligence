"""
Student Chief of Staff - Personal Operating System.
Streamlit application providing a local-first interface for task management,
deterministic daily planning, document intelligence, weekly reviews, and assistant workflows.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd

from student_cos.config import DEFAULT_DB_PATH, DEFAULT_WORK_START, DEFAULT_WORK_END, DEFAULT_BREAK_MINUTES
from student_cos.db import Database
from student_cos.models import Task, Project, Commitment, Priority, TaskStatus, ProjectCategory
from student_cos.tools import ChiefOfStaffTools
from student_cos.scheduler import DeterministicScheduler
from student_cos.ai.assistant import StudentChiefOfStaff
from student_cos.ai.doc_analyzer import DocumentAnalyzer


st.set_page_config(
    page_title="Student Chief of Staff | Personal OS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished Personal OS aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #0f172a;
    }
    .cos-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #1e293b;
        border-radius: 10px;
        border: 1px solid #334155;
        padding: 16px;
        text-align: center;
    }
    .badge-high {
        background-color: #ef4444;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-medium {
        background-color: #f59e0b;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-low {
        background-color: #10b981;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .schedule-item-task {
        background: #1e293b;
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    .schedule-item-comm {
        background: #1e293b;
        border-left: 4px solid #8b5cf6;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db():
    db = Database(DEFAULT_DB_PATH)
    db.seed_sample_data_if_empty()
    return db


def get_assistant(db: Database, provider_name: str):
    return StudentChiefOfStaff(db=db, provider_name=provider_name)


db = get_db()
tools = ChiefOfStaffTools(db)
doc_analyzer = DocumentAnalyzer()

# Session State Initialization
if "provider_name" not in st.session_state:
    st.session_state.provider_name = "offline"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "delete_confirmation" not in st.session_state:
    st.session_state.delete_confirmation = None

# Initialize assistant
assistant = get_assistant(db, st.session_state.provider_name)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.title("🎓 Chief of Staff")
    st.caption("Personal Operating System for Students")

    # Workflow indicator
    st.markdown("""
    **Core Loop:**  
    `CAPTURE` → `UNDERSTAND` → `PRIORITIZE` → `PLAN` → `EXECUTE` → `REVIEW`
    """)

    st.divider()

    st.subheader("⚡ Assistant Engine")
    provider_options = {
        "offline": "Deterministic Local (Offline / No API)",
        "gemini": "Google Gemini (Tool Calling)",
        "ollama": "Local Ollama (Local LLM)",
        "openrouter": "OpenRouter API"
    }
    selected_provider = st.selectbox(
        "Active AI Provider:",
        options=list(provider_options.keys()),
        format_func=lambda x: provider_options[x],
        index=list(provider_options.keys()).index(st.session_state.provider_name)
    )
    if selected_provider != st.session_state.provider_name:
        st.session_state.provider_name = selected_provider
        assistant.set_provider(selected_provider)
        st.rerun()

    st.divider()

    # Quick Stats in Sidebar
    upcoming_deadlines = db.get_upcoming_deadlines(days=7)
    st.markdown(f"**⏰ Due This Week:** `{len(upcoming_deadlines)} tasks`")
    active_tasks = db.list_tasks(status="IN PROGRESS")
    st.markdown(f"**⚡ In Progress:** `{len(active_tasks)} tasks`")

    st.divider()
    st.caption("Safety: Destructive operations require explicit confirmation.")


# ----------------- TOP METRIC BAR -----------------
all_tasks = db.list_tasks()
pending_tasks = [t for t in all_tasks if t.status != TaskStatus.DONE]
completed_tasks = [t for t in all_tasks if t.status == TaskStatus.DONE]
projects = db.list_projects()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Projects", len(projects))
with col2:
    st.metric("Pending Tasks", len(pending_tasks))
with col3:
    st.metric("In Progress", len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]))
with col4:
    st.metric("Completed", len(completed_tasks))
with col5:
    st.metric("Deadlines (14d)", len(db.get_upcoming_deadlines(days=14)))

st.write("")

# ----------------- MAIN NAVIGATION TABS -----------------
tabs = st.tabs([
    "📅 Today's Plan",
    "📋 Tasks & Projects",
    "📥 Capture & Analyze",
    "📊 Weekly Review",
    "🤖 Chief of Staff Chat",
    "⚙️ Settings & Audit"
])


# =========================================================
# TAB 1: TODAY'S PLAN (DETERMINISTIC SCHEDULER)
# =========================================================
with tabs[0]:
    st.header("📅 Daily Planner & Time-Blocked Agenda")
    st.caption("Deterministic Python scheduling based on fixed commitments, deadlines, priority, and capacity.")

    pcol1, pcol2, pcol3 = st.columns([2, 1, 1])
    with pcol1:
        target_date = st.date_input("Plan Date:", value=date.today())
    with pcol2:
        work_start = st.text_input("Day Start:", value=DEFAULT_WORK_START)
    with pcol3:
        work_end = st.text_input("Day End:", value=DEFAULT_WORK_END)

    target_date_str = target_date.isoformat()

    # Scheduler instance with user inputs
    scheduler = DeterministicScheduler(work_start=work_start, work_end=work_end)
    commitments = db.list_commitments(for_date=target_date_str)
    daily_plan = scheduler.generate_daily_plan(all_tasks, commitments, target_date_str)

    # Summary Pills
    m1, m2, m3 = st.columns(3)
    with m1:
        st.info(f"⏱️ **Focus Capacity:** {daily_plan.available_hours} hours available")
    with m2:
        st.info(f"📌 **Scheduled:** {daily_plan.total_planned_minutes} minutes")
    with m3:
        st.info(f"📅 **Fixed Commitments:** {len(commitments)}")

    if daily_plan.overload_warning:
        st.warning(f"⚠️ **Pacing Guard:** {daily_plan.overload_warning}")

    if daily_plan.top_recommendations:
        st.markdown("**Strategic Directives:**")
        for rec in daily_plan.top_recommendations:
            st.markdown(f"- {rec}")

    st.write("---")

    sched_col, side_col = st.columns([3, 2])

    with sched_col:
        st.subheader("Time-Blocked Timeline")
        if not daily_plan.scheduled_blocks:
            st.success("No blocks scheduled! You have full flexibility.")
        else:
            for b in daily_plan.scheduled_blocks:
                is_task = b.block_type == "TASK"
                css_class = "schedule-item-task" if is_task else "schedule-item-comm"
                with st.container():
                    st.markdown(f"""
                    <div class="{css_class}">
                        <strong>{b.start_time} - {b.end_time}</strong> | {b.title} 
                        {'<span class="badge-high">HIGH</span>' if b.priority == 'HIGH' else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    if is_task and b.task_id:
                        b_col1, b_col2 = st.columns([1, 4])
                        with b_col1:
                            if st.button("Mark Done", key=f"done_b_{b.task_id}"):
                                tools.complete_task(b.task_id)
                                st.rerun()

    with side_col:
        st.subheader("Add Fixed Commitment")
        st.caption("Lectures, labs, study groups, interviews")
        with st.form("add_commitment_form"):
            comm_title = st.text_input("Commitment Title", placeholder="e.g. CS 450 Lab Session")
            c_time1, c_time2 = st.columns(2)
            with c_time1:
                c_start = st.text_input("Start (HH:MM)", value="14:00")
            with c_time2:
                c_end = st.text_input("End (HH:MM)", value="15:30")
            c_notes = st.text_input("Notes", placeholder="Room, link, or notes")
            submitted = st.form_submit_button("Add to Schedule")
            if submitted and comm_title:
                db.create_commitment(Commitment(
                    title=comm_title,
                    date=target_date_str,
                    start_time=c_start,
                    end_time=c_end,
                    notes=c_notes
                ))
                st.success(f"Added commitment '{comm_title}'")
                st.rerun()

        if commitments:
            st.write("**Today's Commitments:**")
            for c in commitments:
                cc1, cc2 = st.columns([4, 1])
                with cc1:
                    st.write(f"• **{c.start_time}-{c.end_time}** {c.title}")
                with cc2:
                    if st.button("✕", key=f"del_c_{c.id}"):
                        db.delete_commitment(c.id)
                        st.rerun()


# =========================================================
# TAB 2: TASKS & PROJECTS (MANAGEMENT & KANBAN)
# =========================================================
with tabs[1]:
    st.header("📋 Task & Project Management")

    view_mode = st.radio("View Format:", ["Kanban Board", "Table / List", "Create New"], horizontal=True)

    if view_mode == "Create New":
        tc1, tc2 = st.columns(2)
        with tc1:
            st.subheader("➕ Create New Task")
            with st.form("new_task_form"):
                t_title = st.text_input("Task Title *", placeholder="e.g. Write Literature Review")
                t_proj = st.selectbox(
                    "Project",
                    options=["None"] + [p.name for p in projects]
                )
                t_deadline = st.date_input("Deadline", value=date.today() + timedelta(days=3))
                t_pri = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"], index=1)
                t_est = st.number_input("Estimated Minutes", min_value=5, max_value=600, value=45, step=15)
                t_notes = st.text_area("Notes / Details", placeholder="Checklist or reference links")
                btn_create_task = st.form_submit_button("Create Task")
                if btn_create_task:
                    if not t_title.strip():
                        st.error("Task title cannot be empty.")
                    else:
                        proj_id = None
                        if t_proj != "None":
                            p_match = next((p for p in projects if p.name == t_proj), None)
                            if p_match:
                                proj_id = p_match.id
                        res = tools.create_task(
                            title=t_title,
                            project_id=proj_id,
                            deadline=t_deadline.isoformat(),
                            priority=t_pri,
                            estimated_minutes=t_est,
                            notes=t_notes
                        )
                        if res.success:
                            st.success(f"Task '{t_title}' created successfully!")
                            st.rerun()
                        else:
                            st.error(res.error)

        with tc2:
            st.subheader("📁 Create New Project")
            with st.form("new_project_form"):
                p_name = st.text_input("Project Name *", placeholder="e.g. Distributed Systems Lab")
                p_cat = st.selectbox("Category", [c.value for c in ProjectCategory])
                p_target = st.date_input("Target Date", value=date.today() + timedelta(days=30))
                p_desc = st.text_area("Description / Objectives")
                btn_create_proj = st.form_submit_button("Create Project")
                if btn_create_proj:
                    if not p_name.strip():
                        st.error("Project name cannot be empty.")
                    else:
                        p_res = tools.create_project(
                            name=p_name,
                            category=p_cat,
                            description=p_desc,
                            target_date=p_target.isoformat()
                        )
                        if p_res.success:
                            st.success(f"Project '{p_name}' created!")
                            st.rerun()
                        else:
                            st.error(p_res.error)

    elif view_mode == "Kanban Board":
        k_cols = st.columns(4)
        statuses = [
            ("TODO", "📝", k_cols[0]),
            ("IN PROGRESS", "⚡", k_cols[1]),
            ("DONE", "✅", k_cols[2]),
            ("BLOCKED", "⛔", k_cols[3])
        ]

        for status_val, icon, col in statuses:
            with col:
                status_tasks = [t for t in all_tasks if t.status == status_val]
                col.subheader(f"{icon} {status_val} ({len(status_tasks)})")
                for t in status_tasks:
                    with st.expander(f"{t.title}", expanded=True):
                        st.caption(f"📁 {t.project_name or 'General'} | ⏱️ {t.estimated_minutes}m")
                        badge_color = "badge-high" if t.priority == Priority.HIGH else ("badge-medium" if t.priority == Priority.MEDIUM else "badge-low")
                        st.markdown(f'<span class="{badge_color}">{t.priority}</span> Due: <b>{t.deadline or "None"}</b>', unsafe_allow_html=True)
                        if t.notes:
                            st.write(f"_{t.notes}_")

                        # Actions
                        act_col1, act_col2 = st.columns(2)
                        with act_col1:
                            if status_val != "IN PROGRESS" and status_val != "DONE":
                                if st.button("Start", key=f"start_{t.id}"):
                                    tools.update_task(t.id, status="IN PROGRESS")
                                    st.rerun()
                            elif status_val == "IN PROGRESS":
                                if st.button("Done", key=f"done_{t.id}"):
                                    tools.complete_task(t.id)
                                    st.rerun()
                        with act_col2:
                            if st.button("Delete", key=f"del_kb_{t.id}"):
                                st.session_state.delete_confirmation = ("TASK", t.id, t.title)
                                st.rerun()

    elif view_mode == "Table / List":
        # Filters
        f1, f2, f3 = st.columns(3)
        with f1:
            filter_status = st.selectbox("Filter Status", ["ALL"] + [s.value for s in TaskStatus])
        with f2:
            filter_pri = st.selectbox("Filter Priority", ["ALL", "HIGH", "MEDIUM", "LOW"])
        with f3:
            search_kw = st.text_input("Search Tasks", placeholder="Keyword...")

        filtered = db.list_tasks(
            status=None if filter_status == "ALL" else filter_status,
            priority=None if filter_pri == "ALL" else filter_pri,
            search=search_kw if search_kw.strip() else None
        )

        if filtered:
            data = []
            for t in filtered:
                data.append({
                    "ID": t.id,
                    "Title": t.title,
                    "Project": t.project_name or "General",
                    "Priority": t.priority,
                    "Status": t.status,
                    "Deadline": t.deadline or "",
                    "Est (min)": t.estimated_minutes,
                    "Actual (min)": t.actual_minutes
                })
            df = pd.DataFrame(data)
            st.dataframe(df, width="stretch")

            # Quick edit / action box
            sel_id = st.number_input("Task ID for Quick Action:", min_value=1, step=1)
            qa1, qa2, qa3 = st.columns(3)
            with qa1:
                if st.button("Complete Task"):
                    tools.complete_task(int(sel_id))
                    st.success(f"Completed task #{sel_id}")
                    st.rerun()
            with qa2:
                if st.button("Set In Progress"):
                    tools.update_task(int(sel_id), status="IN PROGRESS")
                    st.rerun()
            with qa3:
                if st.button("Delete Task (Confirm)"):
                    st.session_state.delete_confirmation = ("TASK", int(sel_id), f"Task #{sel_id}")
                    st.rerun()
        else:
            st.info("No tasks match the filter criteria.")

    # Safety Confirmation Banner
    if st.session_state.delete_confirmation:
        entity_type, entity_id, entity_name = st.session_state.delete_confirmation
        st.warning(f"⚠️ **CONFIRM DELETION:** Are you sure you want to permanently delete {entity_type} '{entity_name}'?")
        conf1, conf2 = st.columns([1, 4])
        with conf1:
            if st.button("✅ Yes, Delete", key="confirm_delete_btn"):
                if entity_type == "TASK":
                    tools.delete_task(entity_id, confirmed=True)
                elif entity_type == "PROJECT":
                    tools.delete_project(entity_id, confirmed=True)
                st.session_state.delete_confirmation = None
                st.rerun()
        with conf2:
            if st.button("❌ Cancel", key="cancel_delete_btn"):
                st.session_state.delete_confirmation = None
                st.rerun()


# =========================================================
# TAB 3: DOCUMENT ANALYSIS & CAPTURE
# =========================================================
with tabs[2]:
    st.header("📥 Document Analysis & Intelligence Capture")
    st.caption("Paste course syllabi, lecture notes, assignment instructions, or meeting notes to extract structured tasks and deadlines.")

    sample_doc = (
        "CS 450: Distributed Systems Final Milestone\n"
        "Important: Class attendance is recommended for final presentations.\n"
        "Decision: Team agreed to use Go and gRPC for RPC benchmarks.\n\n"
        "Deliverables and Schedule:\n"
        "- Implement Raft election timeout and heartbeat due 2026-10-25 urgent\n"
        "- Submit Project Architecture Proposal by tomorrow\n"
        "- Write unit tests for log replication and state machine recovery\n"
        "- Optional bonus: Benchmark throughput with 5 replica nodes\n"
    )

    doc_title = st.text_input("Document / Source Title:", value="CS 450 Project Deliverables")
    doc_text = st.text_area("Document Content / Notes:", value=sample_doc, height=220)

    if st.button("🔍 Analyze Document", type="primary"):
        analysis = doc_analyzer.analyze(doc_text, title=doc_title)
        st.session_state.last_analysis = analysis

    if "last_analysis" in st.session_state:
        analysis = st.session_state.last_analysis
        st.success(f"Analyzed: {analysis.summary}")

        a_col1, a_col2 = st.columns(2)
        with a_col1:
            st.subheader("💡 Key Points & Decisions")
            if analysis.decisions:
                st.markdown("**Decisions:**")
                for d in analysis.decisions:
                    st.write(f"• {d}")
            if analysis.key_points:
                st.markdown("**Key Takeaways:**")
                for kp in analysis.key_points:
                    st.write(f"• {kp}")

            if analysis.extracted_deadlines:
                st.markdown("**Detected Deadlines:**")
                for dl in analysis.extracted_deadlines:
                    st.write(f"📅 **{dl['date']}** — _{dl['context']}_")

        with a_col2:
            st.subheader(f"⚡ Extracted Tasks ({len(analysis.extracted_tasks)})")
            for i, task_item in enumerate(analysis.extracted_tasks):
                st.markdown(f"**{i+1}. {task_item.title}**")
                st.caption(f"Priority: `{task_item.priority}` | Due: `{task_item.deadline or 'None'}` | Est: `{task_item.estimated_minutes} min`")

            if st.button("🚀 Import All Extracted Tasks into Database"):
                created_count = 0
                for task_item in analysis.extracted_tasks:
                    res = tools.create_task(
                        title=task_item.title,
                        deadline=task_item.deadline,
                        priority=task_item.priority.value,
                        estimated_minutes=task_item.estimated_minutes,
                        notes=f"Extracted from '{doc_title}'"
                    )
                    if res.success:
                        created_count += 1
                # Also save the document record
                db.save_document(
                    title=doc_title,
                    content=doc_text,
                    summary=analysis.summary,
                    key_points=analysis.key_points,
                    decisions=analysis.decisions,
                    action_items=analysis.action_items
                )
                st.success(f"Successfully imported {created_count} tasks and archived document!")
                st.rerun()


# =========================================================
# TAB 4: WEEKLY REVIEW & ANALYTICS
# =========================================================
with tabs[3]:
    st.header("📊 Executive Weekly Review")
    st.caption("Consolidated review of completed milestones, bottlenecks, project velocity, and suggested priorities.")

    stats = db.get_weekly_review_stats(days_back=7)

    w1, w2, w3 = st.columns(3)
    with w1:
        st.metric("Tasks Completed This Week", stats["completed_count"])
    with w2:
        st.metric("Focus Time Logged", f"{stats['total_time_spent_minutes']} min")
    with w3:
        st.metric("Unfinished Backlog", stats["unfinished_count"])

    st.write("---")

    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.subheader("📁 Project Progress & Velocity")
        for p in stats["project_stats"]:
            total = p["total_tasks"]
            done = p["done_tasks"] or 0
            pct = p["completion_pct"]
            st.write(f"**{p['name']}** `[{p['category']}]`")
            st.progress(pct / 100.0)
            st.caption(f"{done}/{total} tasks complete ({pct}%) | {p['total_actual_minutes'] or 0} min logged")

        st.write("")
        st.subheader("⏰ Upcoming Deadlines (Next 14 Days)")
        upcoming = db.get_upcoming_deadlines(days=14)
        if not upcoming:
            st.write("_No upcoming deadlines in the next 14 days._")
        else:
            for u in upcoming:
                st.write(f"• **{u.deadline}** — {u.title} `[{u.priority}]` *({u.project_name or 'General'})*")

    with r_col2:
        st.subheader("✅ Completed Tasks This Week")
        if not stats["completed_tasks"]:
            st.write("_No tasks marked complete yet this week._")
        else:
            for ct in stats["completed_tasks"]:
                st.write(f"✓ **{ct['title']}** *({ct['project_name'] or 'General'})* — {ct.get('actual_minutes', 0)} min")

        st.write("")
        st.subheader("🎯 Suggested Next Week Priorities")
        st.markdown("""
        1. **Clear bottlenecks:** Address any blocked tasks before committing to new work.
        2. **Capstone & High Priority First:** Schedule 90-minute morning deep work blocks.
        3. **Protect Buffer Time:** Leave 15% daily capacity unallocated to handle unexpected academic or interview requests.
        """)

    # Export weekly review
    st.write("---")
    report_md = f"""# Student Weekly Review ({stats['window_start']} to {stats['window_end']})
- Completed Tasks: {stats['completed_count']}
- Total Focus Time Logged: {stats['total_time_spent_minutes']} minutes
- Remaining Backlog: {stats['unfinished_count']} tasks

## Project Summary:
""" + "\n".join([f"- {p['name']}: {p['completion_pct']}% complete ({p['done_tasks']}/{p['total_tasks']} tasks)" for p in stats['project_stats']])

    st.download_button(
        "📥 Export Weekly Review Report (Markdown)",
        data=report_md,
        file_name=f"weekly_review_{date.today().isoformat()}.md",
        mime="text/markdown"
    )


# =========================================================
# TAB 5: CHIEF OF STAFF ASSISTANT (CHAT & TOOL CALLS)
# =========================================================
with tabs[4]:
    st.header("🤖 Chief of Staff Conversational Assistant")
    st.caption("Interact with your student operating system using natural language. Always grounded in local deterministic tools.")

    # Quick Prompt Chips
    st.markdown("**Quick Directives:**")
    q1, q2, q3, q4, q5 = st.columns(5)
    prompt_to_send = None
    with q1:
        if st.button("📅 Plan my day"):
            prompt_to_send = "Plan my day."
    with q2:
        if st.button("⚡ What first?"):
            prompt_to_send = "What should I work on first?"
    with q3:
        if st.button("📊 Project Progress"):
            prompt_to_send = "Summarize my project progress."
    with q4:
        if st.button("⏰ Deadlines"):
            prompt_to_send = "What deadlines are coming up?"
    with q5:
        if st.button("📝 Turn notes to tasks"):
            prompt_to_send = "Turn these notes into tasks: Implement unit tests due tomorrow urgent; write documentation."

    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tools_called"):
                with st.expander("🛠️ Deterministic Tool Execution Trace"):
                    for tc in msg["tools_called"]:
                        st.code(f"Tool: {tc.get('tool')}\nParams: {tc.get('params')}")

    user_input = st.chat_input("Ask Chief of Staff (e.g. 'Plan my day' or 'What deadlines are coming up?')...")
    if prompt_to_send:
        user_input = prompt_to_send

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Executing deterministic tools..."):
                response = assistant.process_message(user_input)
                st.markdown(response.text)
                if response.tools_called:
                    with st.expander("🛠️ Deterministic Tool Execution Trace"):
                        for tc in response.tools_called:
                            st.code(f"Tool: {tc.get('tool')}\nParams: {tc.get('params')}")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.text,
                    "tools_called": response.tools_called
                })
        st.rerun()


# =========================================================
# TAB 6: SETTINGS & AUDIT LOG
# =========================================================
with tabs[5]:
    st.header("⚙️ Settings, Telegram Setup & Safety Console")

    s1, s2 = st.columns(2)
    with s1:
        st.subheader("🤖 Telegram Bot Configuration")
        st.markdown("""
        To connect the optional Telegram interface:
        1. Open Telegram and message `@BotFather` to create a bot and get a bot token.
        2. Set the environment variable:
           ```bash
           export TELEGRAM_BOT_TOKEN="your_token_here"
           ```
        3. Launch the gateway service:
           ```bash
           python -m student_cos.telegram_bot
           ```
        """)
        st.caption("The Telegram interface queries the exact same SQLite database and tools.")

    with s2:
        st.subheader("🛡️ Safety & System Reset")
        st.markdown("**Safety Policy:** Destructive actions (deletions, purges) require dual-confirmation.")
        if st.button("🔄 Reload Sample Seed Data"):
            db.seed_sample_data_if_empty()
            st.success("Sample projects and tasks re-verified.")
            st.rerun()

    st.write("---")
    st.subheader("📜 Audit & Execution Log")
    st.caption("Immutable record of actions, tool invocations, and database mutations.")
    logs = db.get_audit_logs(limit=30)
    if logs:
        st.dataframe(pd.DataFrame(logs), width="stretch")
    else:
        st.write("No audit records found.")
