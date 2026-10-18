"""Subject management for the semester."""

from __future__ import annotations

import streamlit as st

import database
import planner
from views import components
from views.forms import add_subject_dialog, confirm_dialog, edit_subject_dialog


def render() -> None:
    subjects = database.list_subjects()
    sessions = database.list_sessions()
    exams = database.list_exams(include_past=True)
    credits = sum(int(subject["credits"]) for subject in subjects)
    topics_total = sum(int(subject.get("topic_total", 0)) for subject in subjects)
    topics_done = sum(int(subject.get("topic_completed", 0)) for subject in subjects)

    header, actions = st.columns([2.5, 1.2], vertical_alignment="bottom")
    with header:
        components.page_header(
            "Subjects",
            "A clear view of every course, its pace, and what is coming next. Add subjects to keep your plan balanced.",
            "Your semester",
        )
    with actions:
        if st.button("＋ Add subject", type="primary", use_container_width=True):
            add_subject_dialog()
        if st.button("Open syllabus", use_container_width=True):
            st.session_state.page = "Syllabus Tracker"
            st.rerun()

    components.metric_grid(
        [
            {"label": "Active subjects", "value": len(subjects), "suffix": "courses", "icon": "book", "tone": "blue", "hint": "this semester"},
            {"label": "Overall progress", "value": f"{planner.overall_progress(subjects)}%", "suffix": "", "icon": "target", "tone": "green", "hint": f"{topics_done} of {topics_total} topics done"},
            {"label": "Credit load", "value": credits, "suffix": "credits", "icon": "layers", "tone": "violet", "hint": "academic credits"},
            {"label": "Next assessment", "value": planner.countdown_label(exams[0]["exam_date"]) if exams else "—", "suffix": "", "icon": "calendar", "tone": "amber", "hint": exams[0]["title"] if exams else "Nothing scheduled"},
        ]
    )

    st.write("")
    if not subjects:
        components.empty_state(
            "Add your first subject",
            "Subjects are the building blocks of your syllabus, timetable, progress tracking, and revision quizzes. Start with one course and add the rest when you are ready.",
            "book",
            "No subjects is a perfectly fine starting point.",
        )
        if st.button("＋ Add your first subject", type="primary"):
            add_subject_dialog()
        return

    columns = st.columns(2, gap="medium")
    for index, subject in enumerate(subjects):
        column = columns[index % 2]
        subject_sessions = [session for session in sessions if session["subject_id"] == subject["id"]]
        minutes = sum(int(session["duration"]) for session in subject_sessions if session["completed"])
        subject_exam = next((exam for exam in exams if exam["subject_id"] == subject["id"]), None)
        with column:
            st.markdown(
                f'<div class="subject-card"><div class="subject-accent" style="background:{components.safe(subject["color"])}"></div>'
                '<div class="subject-card-inner"><div class="subject-head">'
                f'<div class="subject-badge" style="background:{components.safe(subject["color"])}">{components.safe((subject["code"] or "SUB").split(" ")[0][:4])}</div>'
                '<div class="subject-head-copy">'
                f'<h3>{components.safe(subject["name"])}</h3>'
                f'<p>{components.safe(subject["code"])} · {int(subject["credits"])} credits</p></div>'
                + components.badge(f"Target {subject['target_grade']}", "slate")
                + '</div>'
                '<div class="subject-details">'
                f'<span>{components.icon("shield", 12)} {components.safe(subject["instructor"])}</span>'
                f'<span>{components.icon("clock", 12)} {planner.hours_label(minutes)} studied</span>'
                "</div>"
                f'<div class="subject-exam">{components.icon("calendar", 12)} '
                + (
                    f'{components.safe(subject_exam["title"])} · {components.safe(planner.format_date(subject_exam["exam_date"]))}'
                    if subject_exam
                    else "No assessment attached"
                )
                + "</div>"
                '<div class="subject-progress-top"><span>Syllabus progress</span>'
                f'<span style="color:#F8FAFC;font-weight:700">{subject["progress"]}%</span></div>'
                + components.progress_html(subject["progress"], subject["color"], 6)
                + f'<p class="subject-topic-count">{subject.get("topic_completed", 0)} of {subject.get("topic_total", 0)} topics complete</p>'
                "</div></div>",
                unsafe_allow_html=True,
            )
            button_a, button_b, button_c = st.columns([1.4, 1, 1])
            with button_a:
                if st.button("Open syllabus →", key=f"open_syllabus_{subject['id']}", use_container_width=True):
                    st.session_state.page = "Syllabus Tracker"
                    st.session_state.syllabus_subject_id = subject["id"]
                    st.rerun()
            with button_b:
                if st.button("Edit", key=f"edit_subject_{subject['id']}", use_container_width=True):
                    edit_subject_dialog(int(subject["id"]))
            with button_c:
                if st.button("Delete", key=f"delete_subject_{subject['id']}", use_container_width=True):
                    confirm_dialog("subject", int(subject["id"]), f"Remove {subject['name']}?")

    st.markdown('<div class="soft-note">Your progress percentages update as you complete syllabus topics. Every course is welcome — even the ones you are still getting to know.</div>', unsafe_allow_html=True)
