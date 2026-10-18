"""Study history, filters, exports, and habit snapshots."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st

import database
import planner
from views import components
from views.forms import add_session_dialog, confirm_dialog

MODE_TONES = {"Focus": "blue", "Lecture": "violet", "Revision": "green", "Practice": "amber"}


def render() -> None:
    sessions = database.list_sessions(order="desc")
    subjects = database.list_subjects()
    completed = [session for session in sessions if session["completed"]]
    hours = planner.total_study_hours()
    streak = planner.study_streak()
    week_hours = planner.weekly_hours()
    completion = planner.completion_rate()

    header, actions = st.columns([2.5, 1.2], vertical_alignment="bottom")
    with header:
        components.page_header(
            "Study History",
            "See the work behind your progress. Review, reflect, and keep the habits that are serving you.",
            "Every minute tells a story",
        )
    with actions:
        if st.button("＋ Log study time", type="primary", use_container_width=True):
            add_session_dialog()
        if st.button("Open performance", use_container_width=True):
            st.session_state.page = "Performance Analysis"
            st.rerun()

    components.metric_grid(
        [
            {"label": "Total study time", "value": f"{hours:g}h", "suffix": "", "icon": "clock", "tone": "blue", "hint": f"{len(completed)} completed blocks"},
            {"label": "This week", "value": f"{week_hours:.1f}h", "suffix": "", "icon": "chart", "tone": "green", "hint": "last seven days"},
            {"label": "Completion rate", "value": f"{completion}%", "suffix": "", "icon": "check", "tone": "violet", "hint": f"{len(sessions) - len(completed)} blocks still planned"},
            {"label": "Current streak", "value": f"{streak}d", "suffix": "", "icon": "flame", "tone": "amber", "hint": "keep showing up"},
        ]
    )

    st.write("")
    with st.container(border=True):
        components.card_title("Find a study session", "Filter your history to understand a particular week or subject.", "list")
        filter_cols = st.columns([1.1, 1, 1, 1])
        with filter_cols[0]:
            query = st.text_input("Search", placeholder="Block or subject")
        with filter_cols[1]:
            subject_id = st.selectbox(
                "Subject",
                [None, *[int(subject["id"]) for subject in subjects]],
                format_func=lambda value: "All subjects" if value is None else next(
                    subject["name"] for subject in subjects if int(subject["id"]) == value
                ),
            )
        with filter_cols[2]:
            status = st.selectbox("Status", ["All", "Completed", "Planned"])
        with filter_cols[3]:
            period = st.selectbox("Period", ["All time", "Last 7 days", "Last 30 days", "Upcoming", "Past only"])

        filtered = []
        for session in sessions:
            haystack = f"{session['title']} {session.get('subject_name') or ''}".lower()
            if query and query.lower() not in haystack:
                continue
            if subject_id is not None and session["subject_id"] != subject_id:
                continue
            if status == "Completed" and not session["completed"]:
                continue
            if status == "Planned" and session["completed"]:
                continue
            session_date = date.fromisoformat(session["session_date"])
            if period == "Last 7 days" and not (date.today() - timedelta(days=6) <= session_date <= date.today()):
                continue
            if period == "Last 30 days" and not (date.today() - timedelta(days=29) <= session_date <= date.today()):
                continue
            if period == "Upcoming" and session_date <= date.today():
                continue
            if period == "Past only" and session_date >= date.today():
                continue
            filtered.append(session)

        if filtered:
            rows = [
                {
                    "Date": planner.format_date(session["session_date"]),
                    "Study block": session["title"],
                    "Subject": session.get("subject_name") or "General",
                    "Mode": session["mode"],
                    "Start": session["start_time"],
                    "Length": planner.hours_label(session["duration"]),
                    "Status": "Completed" if session["completed"] else "Planned",
                }
                for session in filtered
            ]
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Date": st.column_config.TextColumn("Date", width="small"),
                },
            )
            st.download_button(
                "Export this view (.csv)",
                data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
                file_name="studyplanner-history.csv",
                mime="text/csv",
            )
        else:
            components.empty_state(
                "Nothing in this view",
                "Try another subject, status, or period to find the study session you are looking for.",
                "list",
            )

    st.write("")
    left, right = st.columns([1.7, 1], gap="medium")
    with left:
        with st.container(border=True):
            components.card_title("Study mix", "Where your completed time goes.", "target")
            mix = planner.subject_study_minutes()
            for subject in mix:
                st.markdown(
                    '<div class="balance-row"><div class="balance-top">'
                    f'<span><i style="background:{components.safe(subject["color"])}"></i>{components.safe(subject["name"])}</span>'
                    f'<strong>{planner.hours_label(subject["minutes"]) if subject["minutes"] else "—"}</strong></div>'
                    + components.progress_html(min(subject["minutes"] * 2, 100), subject["color"], 4)
                    + "</div>",
                    unsafe_allow_html=True,
                )
            if not mix:
                st.caption("Your subject mix appears after a completed block.")

        if sessions:
            with st.container(border=True):
                components.card_title("Manage a session", "Keep your log accurate for better insights.", "shield")
                options = [session["id"] for session in sessions]
                selected = st.selectbox(
                    "Choose a study block",
                    options,
                    format_func=lambda value: next(
                        f"{session['session_date']} · {session['start_time']} · {session['title']}"
                        for session in sessions
                        if session["id"] == value
                    ),
                )
                session = next(item for item in sessions if item["id"] == selected)
                action_a, action_b = st.columns(2)
                with action_a:
                    if st.button("Mark complete / reopen", use_container_width=True):
                        database.toggle_session(int(session["id"]))
                        st.rerun()
                with action_b:
                    if st.button("Remove from history", use_container_width=True):
                        confirm_dialog("session", int(session["id"]), f"Remove {session['title']}?")

    with right:
        with st.container(border=True):
            components.card_title("Last 14 days", "A little colour for every effort.", "flame")
            completed_sessions = [session for session in completed]
            cells = []
            for offset in range(13, -1, -1):
                current = date.today() - timedelta(days=offset)
                minutes = sum(
                    int(session["duration"]) for session in completed_sessions if session["session_date"] == current.isoformat()
                )
                level = "empty" if minutes == 0 else "soft" if minutes < 60 else "mid" if minutes < 120 else "full"
                cells.append(
                    f'<div class="heat-day"><div class="heat-cell {level}" title="{current.isoformat()} · {minutes} minutes"></div>'
                    f'<span>{current.day}</span></div>'
                )
            st.markdown('<div class="heat-grid">' + "".join(cells) + "</div>", unsafe_allow_html=True)
            st.caption("Darker squares mean more focused minutes. Rest days are allowed.")

        with st.container(border=True):
            components.card_title("Your history belongs to you", "Download a complete copy of your study data at any time.", "download")
            st.download_button(
                "Download my data (.json)",
                data=json.dumps(database.export_workspace(), indent=2, default=str),
                file_name="studyplanner-my-data.json",
                mime="application/json",
                use_container_width=True,
            )
            st.caption("Includes subjects, syllabus topics, sessions, assessments, reminders, and quiz attempts.")
