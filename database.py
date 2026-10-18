"""SQLite persistence for StudyPlanner AI.

The database is created automatically on first launch. Every query uses
parameter binding and a short-lived connection so the app remains safe to rerun.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("STUDYPLANNER_DB", str(BASE_DIR / "data" / "studyplanner.db")))

COLORS = ["#2563eb", "#7c3aed", "#0891b2", "#d97706", "#059669", "#db2777"]
STATUSES = ("not-started", "in-progress", "completed")
MODES = ("Focus", "Lecture", "Revision", "Practice")

DEFAULT_SETTINGS: dict[str, Any] = {
    "study_start": "09:00",
    "focus_length": 50,
    "break_length": 10,
    "study_days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    "session_reminders": True,
    "exam_reminders": True,
    "revision_reminders": True,
    "weekly_summary": False,
    "compact_mode": False,
}


def _iso(offset: int = 0) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def _now() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _rows(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


def _row(cursor: sqlite3.Cursor) -> dict[str, Any] | None:
    result = cursor.fetchone()
    return dict(result) if result else None


SCHEMA = """
CREATE TABLE IF NOT EXISTS student_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    course TEXT NOT NULL DEFAULT '',
    university TEXT NOT NULL DEFAULT '',
    year TEXT NOT NULL DEFAULT '',
    student_id TEXT NOT NULL DEFAULT '',
    weekly_goal REAL NOT NULL DEFAULT 20,
    study_style TEXT NOT NULL DEFAULT '',
    timezone TEXT NOT NULL DEFAULT '',
    target_exam TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '#2563eb',
    instructor TEXT NOT NULL DEFAULT '',
    credits INTEGER NOT NULL DEFAULT 3,
    target_grade TEXT NOT NULL DEFAULT 'A',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    unit TEXT NOT NULL DEFAULT 'Unit 1',
    status TEXT NOT NULL DEFAULT 'not-started' CHECK (status IN ('not-started', 'in-progress', 'completed')),
    confidence INTEGER NOT NULL DEFAULT 2 CHECK (confidence BETWEEN 1 AND 5),
    due_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    session_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    duration INTEGER NOT NULL DEFAULT 60,
    mode TEXT NOT NULL DEFAULT 'Focus',
    completed INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'manual',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    exam_date TEXT NOT NULL,
    start_time TEXT NOT NULL DEFAULT '09:00 AM',
    location TEXT NOT NULL DEFAULT '',
    exam_type TEXT NOT NULL DEFAULT 'Midterm',
    readiness INTEGER NOT NULL DEFAULT 40 CHECK (readiness BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Study',
    due_date TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    priority TEXT NOT NULL DEFAULT 'Medium'
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER,
    subject_name TEXT NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    taken_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_topics_subject ON topics(subject_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_subject ON sessions(subject_id);
CREATE INDEX IF NOT EXISTS idx_exams_date ON exams(exam_date);
"""


# ---------------------------------------------------------------------------
# Initialisation and demonstration content
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create the database, ensure defaults, and seed a first-run workspace."""
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        for key, value in DEFAULT_SETTINGS.items():
            connection.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
        profile = connection.execute("SELECT id FROM student_profile WHERE id = 1").fetchone()
    if profile is None:
        seed_demo()


def seed_demo() -> None:
    """Populate a considered sample workspace for a helpful first visit."""
    today = date.today()

    def day(offset: int) -> str:
        return (today + timedelta(days=offset)).isoformat()

    profile = {
        "name": "Aanya Sharma",
        "email": "aanya.sharma@university.edu",
        "course": "B.Sc. Computer Science",
        "university": "Northfield University",
        "year": "Year 2",
        "student_id": "NU-2024-0186",
        "weekly_goal": 20,
        "study_style": "Visual + practice-led",
        "timezone": "GMT+05:30 · Asia/Kolkata",
        "target_exam": "Semester finals · May 2026",
        "bio": (
            "A curious computer science student who learns best through examples, diagrams, "
            "and a little healthy competition with yesterday's self."
        ),
    }

    subjects = [
        (
            "Advanced Mathematics", "MATH 204", "#2563eb", "Dr. Elena Park", 4, "A",
            [
                ("Limits and continuity", "Unit 1 · Foundations", "completed", 5, -14),
                ("Differentiation rules", "Unit 1 · Foundations", "completed", 4, -10),
                ("Applications of derivatives", "Unit 2 · Calculus", "completed", 4, -6),
                ("Integration techniques", "Unit 2 · Calculus", "in-progress", 3, 2),
                ("Definite integrals", "Unit 2 · Calculus", "in-progress", 2, 5),
                ("Sequences and series", "Unit 3 · Analysis", "not-started", 1, 9),
                ("Linear algebra essentials", "Unit 4 · Algebra", "completed", 4, -2),
                ("Eigenvalues and vectors", "Unit 4 · Algebra", "not-started", 1, 12),
            ],
        ),
        (
            "Data Structures & Algorithms", "CS 210", "#7c3aed", "Dr. Marcus Lee", 4, "A-",
            [
                ("Arrays and strings", "Unit 1 · Linear structures", "completed", 5, -18),
                ("Linked lists", "Unit 1 · Linear structures", "completed", 4, -12),
                ("Stacks and queues", "Unit 1 · Linear structures", "completed", 4, -7),
                ("Trees and traversals", "Unit 2 · Trees", "in-progress", 3, 1),
                ("Binary search trees", "Unit 2 · Trees", "in-progress", 2, 4),
                ("Graph algorithms", "Unit 3 · Graphs", "not-started", 1, 10),
                ("Hashing strategies", "Unit 4 · Optimisation", "completed", 4, -3),
                ("Dynamic programming", "Unit 5 · Advanced", "not-started", 1, 14),
            ],
        ),
        (
            "Applied Physics", "PHY 202", "#0891b2", "Prof. Nadia Rahman", 3, "B+",
            [
                ("Kinematics in 2D", "Unit 1 · Mechanics", "completed", 4, -13),
                ("Newton's laws", "Unit 1 · Mechanics", "completed", 4, -8),
                ("Work, energy and power", "Unit 2 · Energy", "in-progress", 3, 3),
                ("Rotational motion", "Unit 2 · Energy", "not-started", 1, 8),
                ("Electromagnetic induction", "Unit 3 · Electromagnetism", "completed", 3, -4),
                ("Optics and wave behaviour", "Unit 4 · Waves", "not-started", 1, 13),
            ],
        ),
        (
            "English Communication", "ENG 201", "#d97706", "Prof. James Miller", 2, "A",
            [
                ("Academic essay structure", "Unit 1 · Writing", "completed", 5, -15),
                ("Argument and evidence", "Unit 1 · Writing", "completed", 5, -9),
                ("Presentation storytelling", "Unit 2 · Speaking", "completed", 4, -5),
                ("Research citations", "Unit 3 · Research", "in-progress", 4, 4),
                ("Interview communication", "Unit 4 · Professional", "completed", 4, -1),
            ],
        ),
    ]

    past_blocks = [
        (-12, 0, "Focused review", 60, "Focus"),
        (-11, 1, "Practice problems", 75, "Practice"),
        (-10, 2, "Concept review", 45, "Revision"),
        (-9, 3, "Reading and notes", 60, "Focus"),
        (-8, 0, "Problem set", 90, "Practice"),
        (-7, 1, "Recall drill", 60, "Revision"),
        (-6, 0, "Calculus problem set", 90, "Practice"),
        (-6, 3, "Essay editing workshop", 60, "Focus"),
        (-5, 1, "Linked lists lab", 75, "Practice"),
        (-5, 2, "Mechanics recap", 45, "Lecture"),
        (-4, 0, "Derivatives deep dive", 60, "Focus"),
        (-4, 1, "Tree traversal drills", 90, "Practice"),
        (-3, 2, "Energy concepts", 60, "Focus"),
        (-3, 3, "Presentation rehearsal", 45, "Practice"),
        (-2, 0, "Integration practice", 90, "Practice"),
        (-2, 1, "Graphs: first pass", 60, "Focus"),
        (-1, 1, "Stack & queue quiz prep", 75, "Revision"),
        (-1, 2, "Induction notes", 60, "Focus"),
        (-1, 3, "Citation formatting", 30, "Focus"),
    ]

    with get_connection() as connection:
        # Clearing here means "reset" and first-run seeding share one reliable path.
        connection.executescript(
            """
            DELETE FROM quiz_attempts;
            DELETE FROM reminders;
            DELETE FROM exams;
            DELETE FROM sessions;
            DELETE FROM topics;
            DELETE FROM subjects;
            DELETE FROM student_profile;
            DELETE FROM settings;
            """
        )
        connection.execute(
            """
            INSERT INTO student_profile
            (id, name, email, course, university, year, student_id, weekly_goal, study_style, timezone, target_exam, bio)
            VALUES (1, :name, :email, :course, :university, :year, :student_id, :weekly_goal, :study_style, :timezone, :target_exam, :bio)
            """,
            profile,
        )
        for key, value in DEFAULT_SETTINGS.items():
            connection.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))

        subject_ids: list[int] = []
        for name, code, color, instructor, credits, target, topics in subjects:
            cursor = connection.execute(
                """
                INSERT INTO subjects (name, code, color, instructor, credits, target_grade, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, code, color, instructor, credits, target, _now()),
            )
            subject_id = int(cursor.lastrowid)
            subject_ids.append(subject_id)
            connection.executemany(
                """
                INSERT INTO topics (subject_id, title, unit, status, confidence, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [(subject_id, title, unit, status, confidence, day(offset)) for title, unit, status, confidence, offset in topics],
            )

        for index, (offset, subject_pos, label, minutes, mode) in enumerate(past_blocks):
            start = "09:00" if index % 2 == 0 else "16:00"
            connection.execute(
                """
                INSERT INTO sessions
                (subject_id, title, session_date, start_time, duration, mode, completed, source, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, 'manual', '', ?)
                """,
                (subject_ids[subject_pos], label, day(offset), start, minutes, mode, _now()),
            )

        today_blocks = [
            (0, "Morning formula recall", "07:30", 45, "Revision", 1, "manual"),
            (1, "Binary search trees", "10:00", 90, "Focus", 0, "plan"),
            (2, "Rotational motion problems", "13:30", 60, "Practice", 0, "plan"),
            (3, "Research citation review", "16:00", 45, "Revision", 0, "plan"),
        ]
        for subject_pos, title, start, minutes, mode, done, source in today_blocks:
            connection.execute(
                """
                INSERT INTO sessions
                (subject_id, title, session_date, start_time, duration, mode, completed, source, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', ?)
                """,
                (subject_ids[subject_pos], title, day(0), start, minutes, mode, done, source, _now()),
            )

        for subject_pos, title, start, offset, minutes, mode in [
            (0, "Definite integrals", "09:00", 1, 90, "Practice"),
            (1, "Graph traversal practice", "14:00", 1, 60, "Practice"),
            (2, "Optics reading", "10:30", 2, 60, "Focus"),
            (3, "Essay outline", "15:00", 2, 45, "Focus"),
            (0, "Sequences and series", "09:30", 3, 75, "Focus"),
            (1, "Hashing recap", "11:00", 4, 60, "Revision"),
        ]:
            connection.execute(
                """
                INSERT INTO sessions
                (subject_id, title, session_date, start_time, duration, mode, completed, source, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 'plan', '', ?)
                """,
                (subject_ids[subject_pos], title, day(offset), start, minutes, mode, _now()),
            )

        exams = [
            (0, "Calculus Midterm", 6, "09:00 AM", "Hall B · Seat 24", "Midterm", 68),
            (1, "DSA Concept Quiz", 10, "02:00 PM", "Lab 3 · Block C", "Quiz", 55),
            (2, "Physics Lab Assessment", 15, "11:30 AM", "Physics Lab 2", "Lab", 42),
            (3, "Research Presentation", 21, "10:00 AM", "Seminar Room 1", "Presentation", 76),
        ]
        for subject_pos, title, offset, start, location, kind, readiness in exams:
            connection.execute(
                """
                INSERT INTO exams (subject_id, title, exam_date, start_time, location, exam_type, readiness)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (subject_ids[subject_pos], title, day(offset), start, location, kind, readiness),
            )

        reminders = [
            ("Review integration formulas for 30 minutes", "Study", 0, 0, "High"),
            ("Submit DSA problem set #4", "Deadline", 1, 0, "High"),
            ("Book a physics lab practice slot", "Deadline", 3, 0, "Medium"),
            ("Take a 20-minute screen break", "Wellbeing", 0, 1, "Low"),
            ("Print research citation guide", "Study", 4, 0, "Low"),
        ]
        connection.executemany(
            "INSERT INTO reminders (text, category, due_date, done, priority) VALUES (?, ?, ?, ?, ?)",
            [(text, category, day(offset), done, priority) for text, category, offset, done, priority in reminders],
        )

        attempts = [
            (0, "Advanced Mathematics", 4, 5, day(-11)),
            (1, "Data Structures & Algorithms", 3, 5, day(-7)),
            (2, "Applied Physics", 3, 4, day(-4)),
            (0, "Advanced Mathematics", 5, 6, day(-2)),
            (1, "Data Structures & Algorithms", 4, 5, day(-1)),
        ]
        for subject_pos, name, score, total, taken_at in attempts:
            connection.execute(
                """
                INSERT INTO quiz_attempts (subject_id, subject_name, score, total, taken_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (subject_ids[subject_pos], name, score, total, taken_at),
            )


def reset_demo() -> None:
    seed_demo()


def clear_workspace() -> None:
    """Remove study content while keeping the student's profile and preferences."""
    with get_connection() as connection:
        connection.executescript(
            """
            DELETE FROM quiz_attempts;
            DELETE FROM reminders;
            DELETE FROM exams;
            DELETE FROM sessions;
            DELETE FROM topics;
            DELETE FROM subjects;
            """
        )


# ---------------------------------------------------------------------------
# Profile and settings
# ---------------------------------------------------------------------------

def get_profile() -> dict[str, Any]:
    with get_connection() as connection:
        record = _row(connection.execute("SELECT * FROM student_profile WHERE id = 1"))
    return record or {}


def update_profile(**changes: Any) -> None:
    allowed = {
        "name", "email", "course", "university", "year", "student_id",
        "weekly_goal", "study_style", "timezone", "target_exam", "bio",
    }
    values = {key: value for key, value in changes.items() if key in allowed}
    if not values:
        return
    assignments = ", ".join(f"{key} = ?" for key in values)
    with get_connection() as connection:
        connection.execute(
            f"UPDATE student_profile SET {assignments} WHERE id = 1",
            [*values.values()],
        )


def get_settings() -> dict[str, Any]:
    settings = dict(DEFAULT_SETTINGS)
    with get_connection() as connection:
        records = _rows(connection.execute("SELECT key, value FROM settings"))
    for record in records:
        if record["key"] in settings:
            try:
                settings[record["key"]] = json.loads(record["value"])
            except (TypeError, json.JSONDecodeError):
                settings[record["key"]] = record["value"]
    return settings


def update_settings(changes: dict[str, Any]) -> None:
    values = {key: value for key, value in changes.items() if key in DEFAULT_SETTINGS}
    if not values:
        return
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            [(key, json.dumps(value)) for key, value in values.items()],
        )


# ---------------------------------------------------------------------------
# Subjects and topics
# ---------------------------------------------------------------------------

def list_subjects() -> list[dict[str, Any]]:
    with get_connection() as connection:
        records = _rows(
            connection.execute(
                """
                SELECT s.*,
                       COUNT(t.id) AS topic_total,
                       COALESCE(SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END), 0) AS topic_completed,
                       COALESCE(SUM(CASE WHEN t.status = 'in-progress' THEN 1 ELSE 0 END), 0) AS topic_in_progress
                FROM subjects s
                LEFT JOIN topics t ON t.subject_id = s.id
                GROUP BY s.id
                ORDER BY s.created_at ASC, s.id ASC
                """
            )
        )
    for subject in records:
        total = int(subject["topic_total"] or 0)
        points = float(subject["topic_completed"] or 0) + 0.45 * float(subject["topic_in_progress"] or 0)
        subject["progress"] = round((points / total) * 100) if total else 0
    return records


def get_subject(subject_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        subject = _row(connection.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)))
        if not subject:
            return None
        subject["topics"] = _rows(
            connection.execute(
                "SELECT * FROM topics WHERE subject_id = ? ORDER BY due_date ASC, id ASC",
                (subject_id,),
            )
        )
    total = len(subject["topics"])
    completed = sum(1 for topic in subject["topics"] if topic["status"] == "completed")
    in_progress = sum(1 for topic in subject["topics"] if topic["status"] == "in-progress")
    subject["progress"] = round(((completed + 0.45 * in_progress) / total) * 100) if total else 0
    subject["topic_total"] = total
    subject["topic_completed"] = completed
    return subject


def add_subject(name: str, code: str, color: str, instructor: str, credits: int, target_grade: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO subjects (name, code, color, instructor, credits, target_grade, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name.strip(), code.strip(), color, instructor.strip(), int(credits), target_grade, _now()),
        )
        return int(cursor.lastrowid)


def update_subject(subject_id: int, **changes: Any) -> None:
    allowed = {"name", "code", "color", "instructor", "credits", "target_grade"}
    values = {key: value for key, value in changes.items() if key in allowed}
    if not values:
        return
    assignments = ", ".join(f"{key} = ?" for key in values)
    with get_connection() as connection:
        connection.execute(
            f"UPDATE subjects SET {assignments} WHERE id = ?",
            [*values.values(), subject_id],
        )


def delete_subject(subject_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))


def list_topics(subject_id: int | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT t.*, s.name AS subject_name, s.code AS subject_code, s.color AS subject_color
        FROM topics t JOIN subjects s ON s.id = t.subject_id
    """
    params: tuple[Any, ...] = ()
    if subject_id is not None:
        query += " WHERE t.subject_id = ?"
        params = (subject_id,)
    query += " ORDER BY t.due_date ASC, t.id ASC"
    with get_connection() as connection:
        return _rows(connection.execute(query, params))


def add_topic(subject_id: int, title: str, unit: str, status: str, confidence: int, due_date: str) -> int:
    if status not in STATUSES:
        status = "not-started"
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO topics (subject_id, title, unit, status, confidence, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (subject_id, title.strip(), unit.strip(), status, max(1, min(5, int(confidence))), due_date),
        )
        return int(cursor.lastrowid)


def update_topic(topic_id: int, **changes: Any) -> None:
    allowed = {"title", "unit", "status", "confidence", "due_date"}
    values = {key: value for key, value in changes.items() if key in allowed}
    if not values:
        return
    if "status" in values and values["status"] not in STATUSES:
        values["status"] = "not-started"
    if "confidence" in values:
        values["confidence"] = max(1, min(5, int(values["confidence"])))
    assignments = ", ".join(f"{key} = ?" for key in values)
    with get_connection() as connection:
        connection.execute(
            f"UPDATE topics SET {assignments} WHERE id = ?",
            [*values.values(), topic_id],
        )


def delete_topic(topic_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM topics WHERE id = ?", (topic_id,))


def toggle_topic_complete(topic_id: int) -> None:
    with get_connection() as connection:
        record = connection.execute("SELECT status FROM topics WHERE id = ?", (topic_id,)).fetchone()
        if not record:
            return
        new_status = "completed" if record["status"] != "completed" else "in-progress"
        connection.execute(
            "UPDATE topics SET status = ?, confidence = CASE WHEN ? = 'completed' THEN 4 ELSE confidence END WHERE id = ?",
            (new_status, new_status, topic_id),
        )


# ---------------------------------------------------------------------------
# Sessions, exams, reminders, quiz attempts
# ---------------------------------------------------------------------------

def list_sessions(
    start_date: str | None = None,
    end_date: str | None = None,
    subject_id: int | None = None,
    status: str | None = None,
    order: str = "asc",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT s.*, sub.name AS subject_name, sub.code AS subject_code, sub.color AS subject_color
        FROM sessions s LEFT JOIN subjects sub ON sub.id = s.subject_id
        WHERE 1 = 1
    """
    params: list[Any] = []
    if start_date:
        query += " AND s.session_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND s.session_date <= ?"
        params.append(end_date)
    if subject_id is not None:
        query += " AND s.subject_id = ?"
        params.append(subject_id)
    if status == "completed":
        query += " AND s.completed = 1"
    elif status == "planned":
        query += " AND s.completed = 0"
    direction = "DESC" if order.lower() == "desc" else "ASC"
    query += f" ORDER BY s.session_date {direction}, s.start_time {direction}"
    if limit:
        query += " LIMIT ?"
        params.append(int(limit))
    with get_connection() as connection:
        return _rows(connection.execute(query, params))


def add_session(
    subject_id: int,
    title: str,
    session_date: str,
    start_time: str,
    duration: int,
    mode: str,
    source: str = "manual",
    notes: str = "",
) -> int:
    if mode not in MODES:
        mode = "Focus"
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO sessions
            (subject_id, title, session_date, start_time, duration, mode, completed, source, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (subject_id, title.strip(), session_date, start_time, int(duration), mode, source, notes.strip(), _now()),
        )
        return int(cursor.lastrowid)


def toggle_session(session_id: int) -> None:
    with get_connection() as connection:
        connection.execute("UPDATE sessions SET completed = 1 - completed WHERE id = ?", (session_id,))


def delete_session(session_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))


def clear_future_plan() -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE source = 'plan' AND completed = 0 AND session_date > ?",
            (date.today().isoformat(),),
        )


def list_exams(include_past: bool = False) -> list[dict[str, Any]]:
    query = """
        SELECT e.*, s.name AS subject_name, s.code AS subject_code, s.color AS subject_color
        FROM exams e LEFT JOIN subjects s ON s.id = e.subject_id
    """
    params: tuple[Any, ...] = ()
    if not include_past:
        query += " WHERE e.exam_date >= ?"
        params = (date.today().isoformat(),)
    query += " ORDER BY e.exam_date ASC"
    with get_connection() as connection:
        return _rows(connection.execute(query, params))


def add_exam(
    subject_id: int,
    title: str,
    exam_date: str,
    start_time: str,
    location: str,
    exam_type: str,
    readiness: int,
) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO exams (subject_id, title, exam_date, start_time, location, exam_type, readiness)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (subject_id, title.strip(), exam_date, start_time, location.strip(), exam_type, max(0, min(100, int(readiness)))),
        )
        return int(cursor.lastrowid)


def delete_exam(exam_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM exams WHERE id = ?", (exam_id,))


def list_reminders(include_done: bool = True) -> list[dict[str, Any]]:
    query = "SELECT * FROM reminders"
    if not include_done:
        query += " WHERE done = 0"
    query += " ORDER BY done ASC, due_date ASC, priority ASC"
    with get_connection() as connection:
        return _rows(connection.execute(query))


def add_reminder(text: str, category: str, due_date: str, priority: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO reminders (text, category, due_date, done, priority) VALUES (?, ?, ?, 0, ?)",
            (text.strip(), category, due_date, priority),
        )
        return int(cursor.lastrowid)


def toggle_reminder(reminder_id: int) -> None:
    with get_connection() as connection:
        connection.execute("UPDATE reminders SET done = 1 - done WHERE id = ?", (reminder_id,))


def delete_reminder(reminder_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))


def list_attempts(limit: int | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM quiz_attempts ORDER BY taken_at DESC, id DESC"
    params: tuple[Any, ...] = ()
    if limit:
        query += " LIMIT ?"
        params = (int(limit),)
    with get_connection() as connection:
        return _rows(connection.execute(query, params))


def add_quiz_attempt(subject_id: int | None, subject_name: str, score: int, total: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO quiz_attempts (subject_id, subject_name, score, total, taken_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (subject_id, subject_name, int(score), int(total), date.today().isoformat()),
        )


# ---------------------------------------------------------------------------
# Export and aggregate helpers
# ---------------------------------------------------------------------------

def export_workspace() -> dict[str, Any]:
    """Return the full workspace as a JSON-serialisable dictionary."""
    with get_connection() as connection:
        return {
            "exported_at": _now(),
            "profile": _row(connection.execute("SELECT * FROM student_profile WHERE id = 1")) or {},
            "settings": get_settings(),
            "subjects": _rows(connection.execute("SELECT * FROM subjects ORDER BY id")),
            "topics": _rows(connection.execute("SELECT * FROM topics ORDER BY id")),
            "sessions": _rows(connection.execute("SELECT * FROM sessions ORDER BY session_date, start_time")),
            "exams": _rows(connection.execute("SELECT * FROM exams ORDER BY exam_date")),
            "reminders": _rows(connection.execute("SELECT * FROM reminders ORDER BY id")),
            "quiz_attempts": _rows(connection.execute("SELECT * FROM quiz_attempts ORDER BY id")),
        }
