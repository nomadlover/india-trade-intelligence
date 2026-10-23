"""
SQLite database engine, schemas, and persistence operations.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple

from student_cos.config import DEFAULT_DB_PATH
from student_cos.models import Task, Project, Commitment, TaskStatus, Priority, ProjectCategory


class Database:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, autocommit=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        with self.get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL DEFAULT 'Academics',
                description TEXT,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                target_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                description TEXT,
                deadline TEXT,
                priority TEXT NOT NULL DEFAULT 'MEDIUM',
                status TEXT NOT NULL DEFAULT 'TODO',
                estimated_minutes INTEGER NOT NULL DEFAULT 30,
                actual_minutes INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS commitments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                key_points TEXT,
                decisions TEXT,
                action_items TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                details TEXT,
                timestamp TEXT NOT NULL
            );
            """)

    # ----------------- Projects -----------------

    def create_project(self, project: Project) -> Project:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO projects (name, category, description, status, target_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                project.name.strip(),
                project.category,
                project.description or "",
                project.status,
                project.target_date,
                now,
                now
            ))
            project_id = cur.lastrowid
        self.log_audit("CREATE", "PROJECT", project_id, f"Created project '{project.name}'")
        res = self.get_project(project_id)
        if not res:
            raise RuntimeError(f"Could not retrieve project {project_id}")
        return res

    def get_project(self, project_id: int) -> Optional[Project]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Project(**dict(row))

    def get_project_by_name(self, name: str) -> Optional[Project]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM projects WHERE LOWER(name) = LOWER(?)", (name.strip(),))
            row = cur.fetchone()
            if not row:
                return None
            return Project(**dict(row))

    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            if status:
                cur.execute("SELECT * FROM projects WHERE status = ? ORDER BY name ASC", (status,))
            else:
                cur.execute("SELECT * FROM projects ORDER BY name ASC")
            return [Project(**dict(r)) for r in cur.fetchall()]

    def update_project(self, project_id: int, updates: Dict[str, Any]) -> Optional[Project]:
        allowed = {"name", "category", "description", "status", "target_date"}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return self.get_project(project_id)

        filtered["updated_at"] = datetime.now().isoformat()
        set_clauses = [f"{k} = ?" for k in filtered.keys()]
        values = list(filtered.values()) + [project_id]

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ?", values)
            if cur.rowcount > 0:
                self.log_audit("UPDATE", "PROJECT", project_id, f"Updated fields: {list(filtered.keys())}")
                return self.get_project(project_id)
            return None

    def delete_project(self, project_id: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            if cur.rowcount > 0:
                self.log_audit("DELETE", "PROJECT", project_id, "Deleted project and detached tasks")
                return True
            return False

    # ----------------- Tasks -----------------

    def create_task(self, task: Task) -> Task:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO tasks (project_id, title, description, deadline, priority, status,
                                   estimated_minutes, actual_minutes, notes, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.project_id,
                task.title.strip(),
                task.description or "",
                task.deadline,
                task.priority.value if isinstance(task.priority, Priority) else str(task.priority),
                task.status.value if isinstance(task.status, TaskStatus) else str(task.status),
                task.estimated_minutes,
                task.actual_minutes,
                task.notes or "",
                now,
                now if task.status == TaskStatus.DONE else None
            ))
            task_id = cur.lastrowid
        self.log_audit("CREATE", "TASK", task_id, f"Created task '{task.title}'")
        res = self.get_task(task_id)
        if not res:
            raise RuntimeError(f"Could not retrieve task {task_id}")
        return res

    def get_task(self, task_id: int) -> Optional[Task]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT t.*, p.name AS project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.id = ?
            """, (task_id,))
            row = cur.fetchone()
            if not row:
                return None
            return Task(**dict(row))

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        project_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Task]:
        query = """
            SELECT t.*, p.name AS project_name
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE 1=1
        """
        params: List[Any] = []

        if status:
            query += " AND t.status = ?"
            params.append(status.upper())
        if priority:
            query += " AND t.priority = ?"
            params.append(priority.upper())
        if project_id:
            query += " AND t.project_id = ?"
            params.append(project_id)
        if search:
            query += " AND (t.title LIKE ? OR t.description LIKE ? OR t.notes LIKE ?)"
            term = f"%{search.strip()}%"
            params.extend([term, term, term])

        # Order by priority weight descending and deadline ascending
        query += """
            ORDER BY 
                CASE t.status 
                    WHEN 'IN PROGRESS' THEN 1 
                    WHEN 'TODO' THEN 2 
                    WHEN 'BLOCKED' THEN 3 
                    ELSE 4 
                END,
                CASE t.priority 
                    WHEN 'HIGH' THEN 1 
                    WHEN 'MEDIUM' THEN 2 
                    ELSE 3 
                END,
                t.deadline ASC NULLS LAST
        """

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return [Task(**dict(r)) for r in cur.fetchall()]

    def update_task(self, task_id: int, updates: Dict[str, Any]) -> Optional[Task]:
        allowed = {
            "project_id", "title", "description", "deadline", "priority",
            "status", "estimated_minutes", "actual_minutes", "notes", "completed_at"
        }
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return self.get_task(task_id)

        # Handle status transitions
        if "status" in filtered:
            status_val = filtered["status"].value if isinstance(filtered["status"], TaskStatus) else str(filtered["status"]).upper()
            filtered["status"] = status_val
            if status_val == "DONE" and "completed_at" not in filtered:
                filtered["completed_at"] = datetime.now().isoformat()
            elif status_val != "DONE":
                filtered["completed_at"] = None

        if "priority" in filtered:
            pri_val = filtered["priority"].value if isinstance(filtered["priority"], Priority) else str(filtered["priority"]).upper()
            filtered["priority"] = pri_val

        set_clauses = [f"{k} = ?" for k in filtered.keys()]
        values = list(filtered.values()) + [task_id]

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?", values)
            if cur.rowcount > 0:
                self.log_audit("UPDATE", "TASK", task_id, f"Updated fields: {list(filtered.keys())}")
                return self.get_task(task_id)
            return None

    def complete_task(self, task_id: int, actual_minutes: Optional[int] = None) -> Optional[Task]:
        updates: Dict[str, Any] = {
            "status": TaskStatus.DONE.value,
            "completed_at": datetime.now().isoformat()
        }
        if actual_minutes is not None:
            updates["actual_minutes"] = max(0, actual_minutes)
        return self.update_task(task_id, updates)

    def delete_task(self, task_id: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            if cur.rowcount > 0:
                self.log_audit("DELETE", "TASK", task_id, "Deleted task")
                return True
            return False

    def get_upcoming_deadlines(self, days: int = 14) -> List[Task]:
        today_str = date.today().isoformat()
        cutoff_str = (date.today() + timedelta(days=days)).isoformat() + " 23:59:59"

        query = """
            SELECT t.*, p.name AS project_name
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.deadline IS NOT NULL 
              AND t.status != 'DONE'
              AND t.deadline >= ?
              AND t.deadline <= ?
            ORDER BY t.deadline ASC, 
                     CASE t.priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, (today_str, cutoff_str))
            return [Task(**dict(r)) for r in cur.fetchall()]

    # ----------------- Commitments -----------------

    def create_commitment(self, commitment: Commitment) -> Commitment:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO commitments (title, date, start_time, end_time, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                commitment.title.strip(),
                commitment.date,
                commitment.start_time,
                commitment.end_time,
                commitment.notes or ""
            ))
            cid = cur.lastrowid
            commitment.id = cid
            return commitment

    def list_commitments(self, for_date: Optional[str] = None) -> List[Commitment]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            if for_date:
                cur.execute("SELECT * FROM commitments WHERE date = ? ORDER BY start_time ASC", (for_date,))
            else:
                cur.execute("SELECT * FROM commitments ORDER BY date ASC, start_time ASC")
            return [Commitment(**dict(r)) for r in cur.fetchall()]

    def delete_commitment(self, commitment_id: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM commitments WHERE id = ?", (commitment_id,))
            return cur.rowcount > 0

    # ----------------- Documents -----------------

    def save_document(
        self,
        title: str,
        content: str,
        summary: str = "",
        key_points: Optional[List[str]] = None,
        decisions: Optional[List[str]] = None,
        action_items: Optional[List[str]] = None
    ) -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO documents (title, content, summary, key_points, decisions, action_items, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                title.strip(),
                content,
                summary,
                json.dumps(key_points or []),
                json.dumps(decisions or []),
                json.dumps(action_items or []),
                now
            ))
            doc_id = cur.lastrowid
            self.log_audit("SAVE", "DOCUMENT", doc_id, f"Saved document '{title}'")
            return doc_id

    def list_documents(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, title, summary, created_at, key_points, decisions, action_items FROM documents ORDER BY id DESC")
            docs = []
            for r in cur.fetchall():
                d = dict(r)
                d["key_points"] = json.loads(d["key_points"] or "[]")
                d["decisions"] = json.loads(d["decisions"] or "[]")
                d["action_items"] = json.loads(d["action_items"] or "[]")
                docs.append(d)
            return docs

    # ----------------- Audit Log & Analytics -----------------

    def log_audit(self, action: str, entity_type: str, entity_id: Optional[int], details: str) -> None:
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO audit_log (action, entity_type, entity_id, details, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (action, entity_type, entity_id, details, datetime.now().isoformat()))
        except Exception:
            pass

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]

    def get_weekly_review_stats(self, days_back: int = 7) -> Dict[str, Any]:
        start_date = (date.today() - timedelta(days=days_back)).isoformat()
        today_date = date.today().isoformat()

        with self.get_connection() as conn:
            cur = conn.cursor()

            # Completed tasks in window
            cur.execute("""
                SELECT t.*, p.name as project_name, p.category as project_category
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.status = 'DONE' AND t.completed_at >= ?
            """, (start_date,))
            completed_tasks = [dict(r) for r in cur.fetchall()]

            # Pending/Unfinished tasks
            cur.execute("""
                SELECT t.*, p.name as project_name, p.category as project_category
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.status != 'DONE'
            """)
            unfinished_tasks = [dict(r) for r in cur.fetchall()]

            # Project Progress summary
            cur.execute("""
                SELECT 
                    p.id, 
                    p.name, 
                    p.category, 
                    p.status,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.status = 'DONE' THEN 1 ELSE 0 END) as done_tasks,
                    SUM(COALESCE(t.actual_minutes, 0)) as total_actual_minutes,
                    SUM(COALESCE(t.estimated_minutes, 0)) as total_estimated_minutes
                FROM projects p
                LEFT JOIN tasks t ON p.id = t.project_id
                GROUP BY p.id
            """)
            project_stats = [dict(r) for r in cur.fetchall()]
            for ps in project_stats:
                total = ps["total_tasks"]
                done = ps["done_tasks"] or 0
                ps["completion_pct"] = round((done / total * 100), 1) if total > 0 else 0.0

            total_actual_minutes = sum(t.get("actual_minutes", 0) for t in completed_tasks)
            total_estimated_minutes = sum(t.get("estimated_minutes", 0) for t in completed_tasks)

            return {
                "window_start": start_date,
                "window_end": today_date,
                "completed_count": len(completed_tasks),
                "completed_tasks": completed_tasks,
                "unfinished_count": len(unfinished_tasks),
                "unfinished_tasks": unfinished_tasks,
                "project_stats": project_stats,
                "total_time_spent_minutes": total_actual_minutes,
                "total_estimated_minutes": total_estimated_minutes,
            }

    def seed_sample_data_if_empty(self) -> None:
        """Seed realistic student projects and tasks if database is empty."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as cnt FROM projects")
            count = cur.fetchone()["cnt"]
            if count > 0:
                return

        today = date.today()
        # Seed Projects
        p1 = self.create_project(Project(
            name="CS Capstone: Distributed Key-Value Store",
            category=ProjectCategory.ACADEMICS.value,
            description="Senior year capstone project building a Raft-consensus replicated KV database in Go/Python.",
            target_date=(today + timedelta(days=30)).isoformat()
        ))
        p2 = self.create_project(Project(
            name="Fall 2026 Software Internship Search",
            category=ProjectCategory.JOB_SEARCH.value,
            description="Applying to 50 tech companies, leetcode grinding, technical mock interviews.",
            target_date=(today + timedelta(days=45)).isoformat()
        ))
        p3 = self.create_project(Project(
            name="Machine Learning & Deep Learning Specialization",
            category=ProjectCategory.LEARNING.value,
            description="Self-study on Transformer architectures, attention mechanisms, and fine-tuning.",
            target_date=(today + timedelta(days=60)).isoformat()
        ))

        # Seed Tasks
        self.create_task(Task(
            project_id=p1.id,
            title="Implement Raft Election Timeout & Heartbeat",
            priority=Priority.HIGH,
            status=TaskStatus.IN_PROGRESS,
            deadline=(today + timedelta(days=2)).isoformat(),
            estimated_minutes=90,
            notes="Handle split vote corner cases and election timer randomization."
        ))
        self.create_task(Task(
            project_id=p1.id,
            title="Write Capstone Architecture Milestone Document",
            priority=Priority.MEDIUM,
            status=TaskStatus.TODO,
            deadline=(today + timedelta(days=4)).isoformat(),
            estimated_minutes=60,
            notes="Include system diagram, RPC protocols, and state machine replication flowchart."
        ))
        self.create_task(Task(
            project_id=p2.id,
            title="Tailor Resume for Distributed Systems & Backend Roles",
            priority=Priority.HIGH,
            status=TaskStatus.TODO,
            deadline=(today + timedelta(days=1)).isoformat(),
            estimated_minutes=45,
            notes="Quantify impact, add GitHub links and tech keywords (Go, Docker, gRPC)."
        ))
        self.create_task(Task(
            project_id=p2.id,
            title="Solve 3 LeetCode Mediums on Graphs / BFS",
            priority=Priority.MEDIUM,
            status=TaskStatus.TODO,
            deadline=(today + timedelta(days=3)).isoformat(),
            estimated_minutes=75,
            notes="Focus on Topological Sort, Course Schedule II, and Shortest Path."
        ))
        self.create_task(Task(
            project_id=p3.id,
            title="Read 'Attention Is All You Need' Paper Section 3",
            priority=Priority.LOW,
            status=TaskStatus.TODO,
            deadline=(today + timedelta(days=6)).isoformat(),
            estimated_minutes=40,
            notes="Derive Scaled Dot-Product Attention formula manually."
        ))

        # Seed a completed task
        done_task = Task(
            project_id=p1.id,
            title="Setup Go module and CI pipeline with GitHub Actions",
            priority=Priority.MEDIUM,
            status=TaskStatus.DONE,
            deadline=(today - timedelta(days=2)).isoformat(),
            estimated_minutes=45,
            actual_minutes=50,
            completed_at=(today - timedelta(days=1)).isoformat(),
            notes="Passing unit test runs and lint checks."
        )
        self.create_task(done_task)

        # Seed Today Commitments (classes/meetings)
        self.create_commitment(Commitment(
            title="CS 450 Distributed Systems Lecture",
            date=today.isoformat(),
            start_time="10:00",
            end_time="11:30",
            notes="Lecture on Paxos vs Raft consensus."
        ))
        self.create_commitment(Commitment(
            title="Peer Coding / Mock Interview Session",
            date=today.isoformat(),
            start_time="14:00",
            end_time="15:00",
            notes="Practice mock graph traversal problem on Coderpad."
        ))
