"""The student dashboard — the first and main view of StudyPlanner AI."""

from __future__ import annotations

from datetime import date

import streamlit as st

import analytics
import database
import planner
from views import components
from views.forms import add_reminder_dialog, add_session_dialog


def _greeting() -> str:
    hour = __import__("datetime").datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def _end_time(start: str, duration: int) -> str:
    return planner.end_time(start, duration)


def render() -> None:
    profile = database.get_profile()
    subjects = database.list_subjects()
    sessions = database.list_sessions()
    today_sessions = [session for session in sessions if session["session_date"] == date.today().isoformat()]
    today_sessions.sort(key=lambda session: session["start_time"])
    exams = database.list_exams()
    reminders = database.list_reminders()
    attempts = database.list_attempts(limit=5)

    hours = planner.weekly_hours()
    goal = float(profile.get("weekly_goal", 20) or 20)
    percent = min(100, round((hours / goal) * 100)) if goal else 0
    streak = planner.study_streak()
    completed_today = sum(1 for session in today_sessions if session["completed"])
    total_minutes_today = sum(int(session["duration"]) for session in today_sessions)
    progress = planner.overall_progress(subjects)
    first_name = (profile.get("name") or "Student").split(" ")[0]

    header_left, header_right = st.columns([3.2, 1.1], vertical_alignment="bottom")
    with header_left:
        components.page_header(
            f"{_greeting()}, {first_name} 👋",
            (
                f"You have {len(today_sessions)} study blocks today and {len(exams)} assessments on the horizon. "
                "One focused step at a time."
                if today_sessions
                else "Your day is clear. A small, thoughtful plan is the best place to begin."
            ),
            date.today().strftime("%A, %B %-d"),
        )
    with header_right:
        if st.button("＋ Add study block", type="primary", use_container_width=True):
            add_session_dialog()
        if st.button("View timetable", use_container_width=True):
            st.session_state.page = "AI Timetable"
            st.rerun()

    next_exam = exams[0] if exams else None
    components.metric_grid(
        [
            {
                "label": "Study streak",
                "value": streak,
                "suffix": "days",
                "icon": "flame",
                "tone": "amber",
                "hint": "Keep the momentum alive today" if streak else "Complete a block to begin",
            },
            {
                "label": "Hours this week",
                "value": f"{hours:.1f}",
                "suffix": "hrs",
                "icon": "clock",
                "tone": "blue",
                "hint": f"{len([session for session in sessions if session['completed']])} completed blocks in your history",
            },
            {
                "label": "Weekly goal",
                "value": f"{percent}%",
                "suffix": f"of {int(goal)}h",
                "icon": "target",
                "tone": "violet",
                "hint": f"{max(0, round(goal - hours, 1))} hours remaining this week",
            },
            {
                "label": "Upcoming assessments",
                "value": len(exams),
                "suffix": "scheduled",
                "icon": "calendar",
                "tone": "rose",
                "hint": f"Next: {next_exam['title']} · {planner.countdown_label(next_exam['exam_date'])}"
                if next_exam
                else "No assessments added yet",
            },
        ]
    )

    left, right = st.columns([2.08, 1], gap="medium")

    with left:
        with st.container(border=True):
            components.card_title(
                "Today's study plan",
                f"{date.today().strftime('%A, %b %-d')} · {planner.hours_label(total_minutes_today) if today_sessions else 'Nothing scheduled yet'}",
                "calendar",
            )
            if today_sessions:
                for session in today_sessions:
                    time_col, body_col, badge_col, done_col = st.columns([0.75, 4.4, 1.0, 0.9], vertical_alignment="center")
                    with time_col:
                        st.markdown(
                            f'<div class="time-cell"><strong>{components.safe(session["start_time"])}</strong>'
                            f'<span>{components.safe(_end_time(session["start_time"], session["duration"]))}</span></div>',
                            unsafe_allow_html=True,
                        )
                    with body_col:
                        st.markdown(
                            f'<div class="session-title">{components.safe(session["title"])}</div>'
                            f'<div class="session-meta"><span class="dot" style="background:{components.safe(session.get("subject_color") or "#2563eb")}"></span>'
                            f'{components.safe(session.get("subject_name") or "General study")} · '
                            f'{planner.hours_label(session["duration"])}</div>',
                            unsafe_allow_html=True,
                        )
                    with badge_col:
                        st.markdown(
                            components.badge(session["mode"], "blue" if session["mode"] == "Focus" else "amber"),
                            unsafe_allow_html=True,
                        )
                    with done_col:
                        checked = st.checkbox(
                            f"Mark {session['title']} complete",
                            value=bool(session["completed"]),
                            key=f"dash_done_{session['id']}",
                            label_visibility="collapsed",
                        )
                        if checked != bool(session["completed"]):
                            database.toggle_session(int(session["id"]))
                            st.toast("Study block completed. That's progress." if checked else "Study block moved back to your plan.")
                            st.rerun()
                st.markdown(
                    f'<div class="list-footer"><span>{completed_today} of {len(today_sessions)} blocks complete</span>'
                    f'<span class="soft-badge">{planner.completion_rate()}% overall completion</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                components.empty_state(
                    "A clear day, ready for a plan",
                    "Put one meaningful study block on the calendar. Your future self will thank you.",
                    "calendar",
                )
                block_col, plan_col = st.columns(2)
                with block_col:
                    if st.button("Add study block", type="primary", use_container_width=True):
                        add_session_dialog()
                with plan_col:
                    if st.button("Build my plan", use_container_width=True):
                        result = planner.generate_plan()
                        st.toast(result["message"])
                        st.rerun()

        with st.container(border=True):
            components.card_title("Subject progress", f"{progress}% overall syllabus confidence", "target")
            st.markdown(components.subject_progress_rows(subjects), unsafe_allow_html=True)
            if subjects:
                if st.button("Open syllabus tracker", use_container_width=False):
                    st.session_state.page = "Syllabus Tracker"
                    st.rerun()
            else:
                components.empty_state(
                    "Your subjects will live here",
                    "Add a subject to unlock progress bars, syllabus tracking, and a tailored timetable.",
                    "book",
                )
                if st.button("Add your first subject", type="primary"):
                    st.session_state.page = "Subjects"
                    st.rerun()

        with st.container(border=True):
            components.card_title("Study activity", "Your focused time over the last seven days", "chart")
            st.plotly_chart(
                analytics.study_activity_figure(planner.daily_activity(7)),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            activity = planner.daily_activity(7)
            best = max(activity, key=lambda point: point["hours"]) if activity else {"label": "—", "hours": 0}
            average = round(sum(point["hours"] for point in activity) / max(1, len(activity)), 1)
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f'<div class="mini-stat"><span>Best day</span><strong>{best["label"]} · {best["hours"]}h</strong></div>', unsafe_allow_html=True)
            with col_b:
                st.markdown(f'<div class="mini-stat"><span>Daily average</span><strong>{average}h</strong></div>', unsafe_allow_html=True)
            with col_c:
                st.markdown(f'<div class="mini-stat"><span>Consistency</span><strong>{streak} day streak</strong></div>', unsafe_allow_html=True)

        weakest = planner.weakest_subject(subjects)
        strongest = planner.strongest_subject(subjects)
        if weakest:
            insight = (
                f"{weakest['name']} is at {weakest['progress']}% complete. "
                + (
                    f"Your next assessment is {planner.countdown_label(next_exam['exam_date']).lower()}. "
                    if next_exam
                    else ""
                )
                + "Two focused blocks this week could make the biggest difference."
            )
            components.insight_card("A focused next step", insight)
            if strongest and attempts:
                st.caption(
                    f"{strongest['name']} is your strongest subject at {strongest['progress']}%. "
                    f"Your latest quiz: {attempts[0]['score']}/{attempts[0]['total']}."
                )
        else:
            components.insight_card(
                "Your study story starts with one subject",
                "Add a subject and the planner will turn your syllabus into a realistic weekly study plan.",
            )

    with right:
        components.focus_card(profile, hours, percent)
        if st.button("✦ Build this week's plan", type="primary", use_container_width=True):
            result = planner.generate_plan()
            st.toast(result["message"])
            st.rerun()

        with st.container(border=True):
            components.card_title("Upcoming examinations", f"{len(exams)} assessments ahead", "calendar")
            st.markdown(components.exam_outlook(exams, 3), unsafe_allow_html=True)
            if st.button("Manage assessments", use_container_width=True):
                st.session_state.page = "AI Timetable"
                st.rerun()

        with st.container(border=True):
            components.card_title("Reminders", f"{sum(1 for reminder in reminders if not reminder['done'])} things need a look", "bell")
            for reminder in reminders[:5]:
                checked = st.checkbox(
                    reminder["text"],
                    value=bool(reminder["done"]),
                    key=f"dash_reminder_{reminder['id']}",
                    help=f"{reminder['category']} · {planner.countdown_label(reminder['due_date'])}",
                )
                if checked != bool(reminder["done"]):
                    database.toggle_reminder(int(reminder["id"]))
                    st.rerun()
            if not reminders:
                st.caption("No reminders right now. Capture the small things so your mind can stay on studying.")
            if st.button("＋ Add a reminder", use_container_width=True):
                add_reminder_dialog()
