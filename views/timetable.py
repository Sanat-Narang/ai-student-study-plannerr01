"""A balanced, editable weekly study timetable."""

from __future__ import annotations

from datetime import date

import streamlit as st

import database
import planner
from views import components
from views.forms import add_exam_dialog, add_session_dialog, confirm_dialog


def render() -> None:
    subjects = database.list_subjects()
    sessions = database.list_sessions()
    exams = database.list_exams()
    days = planner.week_plan()
    week_sessions = [session for day in days for session in day["sessions"]]
    week_minutes = sum(int(session["duration"]) for session in week_sessions)
    week_completed = sum(1 for session in week_sessions if session["completed"])

    header, actions = st.columns([2.4, 1.4], vertical_alignment="bottom")
    with header:
        components.page_header(
            "AI Timetable",
            "A realistic week built around your subjects, deadlines, and the amount of time you actually have.",
            "Intelligent planning",
        )
    with actions:
        if st.button("✦ Generate plan", type="primary", use_container_width=True):
            result = planner.generate_plan()
            st.toast(result["message"])
            st.rerun()
        left_action, right_action = st.columns(2)
        with left_action:
            if st.button("＋ Block", use_container_width=True):
                add_session_dialog()
        with right_action:
            if st.button("＋ Assessment", use_container_width=True):
                add_exam_dialog()

    if not subjects:
        components.empty_state(
            "Your timetable needs a starting point",
            "Add at least one subject and the planner can begin building a balanced week of focused study blocks.",
            "calendar",
        )
        if st.button("Add your first subject", type="primary"):
            st.session_state.page = "Subjects"
            st.rerun()
        return

    components.weekly_focus_banner(len(week_sessions), week_minutes, week_completed)
    if st.button("Replan this week", use_container_width=False):
        result = planner.generate_plan()
        st.toast(result["message"])
        st.rerun()

    st.write("")
    week_start = days[0]["date"] if days else date.today().isoformat()
    week_end = days[-1]["date"] if days else date.today().isoformat()
    components.card_title(
        "This week at a glance",
        f"{planner.format_date(week_start)} – {planner.format_date(week_end)} · {planner.hours_label(week_minutes)} planned",
        "calendar",
    )

    day_columns = st.columns(7, gap="small")
    for column, day in zip(day_columns, days):
        with column:
            is_today = day["date"] == date.today().isoformat()
            st.markdown(
                f'<div class="day-head {"is-today" if is_today else ""}"><span>{components.safe(day["weekday"])}</span>'
                f'<strong>{day["day"]}</strong>'
                f'<small>{planner.hours_label(sum(int(item["duration"]) for item in day["sessions"])) if day["sessions"] else "Open"}</small></div>',
                unsafe_allow_html=True,
            )
            if day["sessions"]:
                for session in day["sessions"]:
                    st.markdown(
                        f'<div class="week-session {"is-complete" if session["completed"] else ""}" '
                        f'style="border-left-color:{components.safe(session.get("subject_color") or "#2563eb")}">'
                        f'<span class="week-time">{components.safe(session["start_time"])}</span>'
                        f'<p>{components.safe(session["title"])}</p>'
                        f'<small>{components.safe(session.get("subject_code") or "Study")}</small></div>',
                        unsafe_allow_html=True,
                    )
                    checked = st.checkbox(
                        f"Mark {session['title']} complete",
                        value=bool(session["completed"]),
                        key=f"tt_done_{session['id']}",
                        label_visibility="collapsed",
                    )
                    if checked != bool(session["completed"]):
                        database.toggle_session(int(session["id"]))
                        st.rerun()
            else:
                st.markdown('<p class="day-open">No blocks yet</p>', unsafe_allow_html=True)
            if st.button("＋", key=f"add_block_{day['date']}", help=f"Add a block on {day['date']}"):
                add_session_dialog(default_date=date.fromisoformat(day["date"]))

    st.markdown(
        '<p class="caption-row">' + " &nbsp; ".join(
            f'<span class="legend-dot" style="background:{components.safe(subject["color"])}"></span>{components.safe(subject["code"])}'
            for subject in subjects
        ) + "</p>",
        unsafe_allow_html=True,
    )

    st.write("")
    left, right = st.columns([1.4, 1], gap="medium")
    with left:
        with st.container(border=True):
            components.card_title("Assessment outlook", "Prepare calmly, well before each date.", "calendar")
            st.markdown(components.exam_outlook(exams, 5), unsafe_allow_html=True)
            if exams:
                selected_exam = st.selectbox(
                    "Select an assessment",
                    [exam["id"] for exam in exams],
                    format_func=lambda value: next(exam["title"] for exam in exams if exam["id"] == value),
                )
                remove_col, add_col = st.columns(2)
                with remove_col:
                    if st.button("Remove assessment", use_container_width=True):
                        exam = next(item for item in exams if item["id"] == selected_exam)
                        confirm_dialog("exam", int(exam["id"]), f"Remove {exam['title']}?")
                with add_col:
                    if st.button("Add another", use_container_width=True):
                        add_exam_dialog()
            else:
                if st.button("＋ Add an assessment", type="primary"):
                    add_exam_dialog()

        st.markdown(
            '<div class="sp-card"><h3 class="card-heading">Keep your calendar close</h3>'
            '<p class="muted-copy">Download the week as a calendar file and keep your study blocks beside your classes.</p></div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "Download this week (.ics)",
            data=planner.build_ics(),
            file_name="studyplanner-week.ics",
            mime="text/calendar",
            use_container_width=False,
        )

    with right:
        with st.container(border=True):
            components.card_title("This week's balance", f"{planner.hours_label(week_minutes)} scheduled this week", "target")
            balance = planner.subject_study_minutes()
            if balance:
                for subject in balance:
                    st.markdown(
                        '<div class="balance-row"><div class="balance-top">'
                        f'<span><i style="background:{components.safe(subject["color"])}"></i>{components.safe(subject["name"])}</span>'
                        f'<strong>{planner.hours_label(subject["minutes"]) if subject["minutes"] else "—"}</strong></div>'
                        + components.progress_html(min(subject["minutes"] * 2, 100), subject["color"], 4)
                        + "</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Your subject balance appears once study time is scheduled.")
            st.markdown(
                '<div class="inline-note soft">' + components.icon("lightbulb", 13) +
                " <span>Your plan prioritises subjects with nearer assessments while rotating unfinished topics.</span></div>",
                unsafe_allow_html=True,
            )

    st.write("")
    with st.container(border=True):
        components.card_title("Manage planned blocks", "Adjust the plan so it stays realistic.", "list")
        if sessions:
            selected_session = st.selectbox(
                "Select a study block",
                [session["id"] for session in sessions],
                format_func=lambda value: next(
                    f"{session['session_date']} · {session['start_time']} · {session['title']}" for session in sessions if session["id"] == value
                ),
            )
            session = next(item for item in sessions if item["id"] == selected_session)
            action_a, action_b = st.columns(2)
            with action_a:
                if st.button("Mark complete / reopen", use_container_width=True):
                    database.toggle_session(int(session["id"]))
                    st.rerun()
            with action_b:
                if st.button("Remove this block", use_container_width=True):
                    confirm_dialog("session", int(session["id"]), f"Remove {session['title']}?")
        else:
            st.caption("No study blocks yet. Generate a plan or add one above.")
