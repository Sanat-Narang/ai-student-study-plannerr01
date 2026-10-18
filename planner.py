"""Study planning and progress calculations for StudyPlanner AI."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import database

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MODE_ROTATION = ["Focus", "Practice", "Revision"]


def _days_ago(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def _minutes_to_hours(minutes: int | float) -> float:
    return round(float(minutes) / 60, 1)


def hours_label(minutes: int | float) -> str:
    minutes = int(minutes or 0)
    hours, remainder = divmod(minutes, 60)
    if hours and remainder:
        return f"{hours}h {remainder}m"
    if hours:
        return f"{hours}h"
    return f"{remainder}m"


def add_minutes(start_time: str, minutes: int) -> str:
    try:
        base = datetime.strptime(start_time, "%H:%M")
    except (TypeError, ValueError):
        base = datetime.strptime("09:00", "%H:%M")
    result = base + timedelta(minutes=minutes)
    return result.strftime("%H:%M")


def end_time(start_time: str, duration: int) -> str:
    return add_minutes(start_time, int(duration or 60))


def format_date(value: str, include_weekday: bool = False) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return value or ""
    return parsed.strftime("%a, %b %-d" if include_weekday else "%b %-d")


def relative_days(value: str) -> int:
    try:
        return (datetime.strptime(value, "%Y-%m-%d").date() - date.today()).days
    except (TypeError, ValueError):
        return 9999


def countdown_label(value: str) -> str:
    days = relative_days(value)
    if days == 0:
        return "Today"
    if days == 1:
        return "Tomorrow"
    if days < 0:
        return f"{abs(days)}d ago"
    return f"In {days} days"


def overall_progress(subjects: list[dict] | None = None) -> int:
    subjects = subjects if subjects is not None else database.list_subjects()
    if not subjects:
        return 0
    return round(sum(int(subject.get("progress", 0)) for subject in subjects) / len(subjects))


def total_study_hours() -> float:
    sessions = database.list_sessions(status="completed")
    return _minutes_to_hours(sum(int(session["duration"]) for session in sessions))


def weekly_hours() -> float:
    sessions = database.list_sessions(start_date=_days_ago(-6), end_date=date.today().isoformat(), status="completed")
    return _minutes_to_hours(sum(int(session["duration"]) for session in sessions))


def study_streak() -> int:
    sessions = database.list_sessions(status="completed")
    dates = {session["session_date"] for session in sessions}
    streak = 0
    for offset in range(0, 366):
        current = _days_ago(-offset)
        if current in dates:
            streak += 1
        elif offset == 0:
            continue
        else:
            break
    return streak


def completion_rate() -> int:
    sessions = database.list_sessions()
    if not sessions:
        return 0
    completed = sum(1 for session in sessions if session["completed"])
    return round((completed / len(sessions)) * 100)


def daily_activity(days: int = 7) -> list[dict]:
    sessions = database.list_sessions(start_date=_days_ago(-(days - 1)), status="completed")
    activity = []
    for offset in range(days - 1, -1, -1):
        current = _days_ago(-offset)
        minutes = sum(int(session["duration"]) for session in sessions if session["session_date"] == current)
        activity.append(
            {
                "date": current,
                "label": datetime.strptime(current, "%Y-%m-%d").strftime("%a")[:2],
                "hours": _minutes_to_hours(minutes),
                "minutes": minutes,
            }
        )
    return activity


def subject_study_minutes() -> list[dict]:
    subjects = database.list_subjects()
    sessions = database.list_sessions(status="completed")
    result = []
    for subject in subjects:
        minutes = sum(int(session["duration"]) for session in sessions if session["subject_id"] == subject["id"])
        result.append({**subject, "minutes": minutes, "hours": _minutes_to_hours(minutes)})
    return sorted(result, key=lambda item: item["minutes"], reverse=True)


def quiz_stats() -> dict:
    attempts = database.list_attempts()
    score = sum(int(attempt["score"]) for attempt in attempts)
    total = sum(int(attempt["total"]) for attempt in attempts)
    best = 0
    for attempt in attempts:
        if attempt["total"]:
            best = max(best, round((attempt["score"] / attempt["total"]) * 100))
    return {
        "attempts": len(attempts),
        "score": score,
        "total": total,
        "accuracy": round((score / total) * 100) if total else 0,
        "best": best,
    }


def next_exams(limit: int | None = None) -> list[dict]:
    exams = database.list_exams()
    return exams[:limit] if limit else exams


def weakest_subject(subjects: list[dict] | None = None) -> dict | None:
    subjects = subjects if subjects is not None else database.list_subjects()
    return min(subjects, key=lambda subject: subject.get("progress", 0)) if subjects else None


def strongest_subject(subjects: list[dict] | None = None) -> dict | None:
    subjects = subjects if subjects is not None else database.list_subjects()
    return max(subjects, key=lambda subject: subject.get("progress", 0)) if subjects else None


def pending_topics(subject: dict) -> list[dict]:
    topics = subject.get("topics") or database.get_subject(int(subject["id"])) or {}
    rows = topics.get("topics", []) if isinstance(topics, dict) else topics
    return [topic for topic in rows if topic.get("status") != "completed"]


def generate_plan(replace_future: bool = True) -> dict:
    """Build a balanced seven-day plan and store it as study sessions.

    Priority is a blend of assessment proximity and unfinished syllabus work.
    The generator never schedules a subject twice in one day's first two blocks
    when there is an alternative, and it respects the student's study days.
    """
    subjects = database.list_subjects()
    if not subjects:
        return {"count": 0, "message": "Add a subject before generating a plan."}

    settings = database.get_settings()
    exams = {exam["subject_id"]: exam for exam in database.list_exams()}
    ranked = sorted(
        subjects,
        key=lambda subject: (
            exams.get(subject["id"], {}).get("exam_date", "9999-12-31"),
            subject.get("progress", 0),
        ),
    )

    study_days = settings.get("study_days") or WEEKDAYS[:5]
    focus_length = max(30, min(90, int(settings.get("focus_length", 50))))
    start_time = settings.get("study_start", "09:00")
    slots = [0, 240, 420]
    generated = 0
    rotation = 0

    if replace_future:
        database.clear_future_plan()

    for offset in range(1, 8):
        current = date.today() + timedelta(days=offset)
        if current.strftime("%a") not in study_days:
            continue
        block_count = 2 if offset % 3 else 3
        used_today: set[int] = set()
        for block in range(block_count):
            candidates = [subject for subject in ranked if subject["id"] not in used_today] or ranked
            subject = candidates[rotation % len(candidates)]
            rotation += 1
            used_today.add(subject["id"])
            full_subject = database.get_subject(int(subject["id"])) or subject
            pending = pending_topics(full_subject)
            in_progress = [topic for topic in pending if topic.get("status") == "in-progress"]
            topic = (in_progress or pending or [None])[0]
            title = topic["title"] if topic else f"{subject['name']} · focused practice"
            database.add_session(
                subject_id=int(subject["id"]),
                title=title,
                session_date=current.isoformat(),
                start_time=add_minutes(start_time, slots[block] if block < len(slots) else block * 180),
                duration=focus_length if block != 1 else max(45, focus_length - 10),
                mode=MODE_ROTATION[block % len(MODE_ROTATION)],
                source="plan",
            )
            generated += 1

    return {
        "count": generated,
        "message": f"{generated} study blocks added across the next seven days."
        if generated
        else "Your selected study days did not leave room for new blocks.",
    }


def week_plan() -> list[dict]:
    """Return the current week's sessions grouped by ISO date."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    sessions = database.list_sessions(start_date=monday.isoformat(), end_date=sunday.isoformat())
    grouped: dict[str, list[dict]] = {}
    for offset in range(7):
        grouped[(monday + timedelta(days=offset)).isoformat()] = []
    for session in sessions:
        grouped.setdefault(session["session_date"], []).append(session)
    return [
        {
            "date": current,
            "weekday": datetime.strptime(current, "%Y-%m-%d").strftime("%a"),
            "day": datetime.strptime(current, "%Y-%m-%d").day,
            "sessions": sorted(grouped.get(current, []), key=lambda item: item["start_time"]),
        }
        for current in grouped
    ]


def build_ics() -> bytes:
    """Produce a calendar file for the next seven days."""
    sessions = database.list_sessions(
        start_date=date.today().isoformat(),
        end_date=(date.today() + timedelta(days=7)).isoformat(),
    )
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//StudyPlanner AI//Study Week//EN",
        "CALSCALE:GREGORIAN",
    ]
    for session in sessions:
        start = session["start_time"].replace(":", "")
        end = end_time(session["start_time"], session["duration"]).replace(":", "")
        compact_date = session["session_date"].replace("-", "")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:studyplanner-{session['id']}@local",
                f"DTSTART:{compact_date}T{start}00",
                f"DTEND:{compact_date}T{end}00",
                f"SUMMARY:{session['title']}",
                f"DESCRIPTION:{session.get('subject_name') or 'Study'} · {session['mode']}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines).encode("utf-8")
