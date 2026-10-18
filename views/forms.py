"""Shared Streamlit dialogs for creating and managing study data."""

from __future__ import annotations

from datetime import date, time, timedelta

import streamlit as st

import database
from views import components


def _go(page: str) -> None:
    st.session_state.page = page
    st.rerun()


@st.dialog("Add a study block")
def add_session_dialog(default_date: date | None = None, subject_id: int | None = None) -> None:
    subjects = database.list_subjects()
    if not subjects:
        st.warning("Add a subject before scheduling a study block.")
        if st.button("Go to Subjects", use_container_width=True, type="primary"):
            _go("Subjects")
        return

    ids = [subject["id"] for subject in subjects]
    names = {subject["id"]: subject["name"] for subject in subjects}
    default_index = ids.index(subject_id) if subject_id in ids else 0
    with st.form("study_block_form", clear_on_submit=False):
        title = st.text_input("What will you focus on?", placeholder="e.g. Integration practice")
        subject = st.selectbox("Subject", ids, index=default_index, format_func=lambda value: names.get(value, "Subject"))
        left, right = st.columns(2)
        with left:
            block_date = st.date_input("Date", value=default_date or date.today())
            start = st.time_input("Start time", value=time(9, 0))
        with right:
            duration = st.selectbox("Length", [25, 30, 45, 60, 75, 90, 120], index=3)
            mode = st.selectbox("Study mode", list(database.MODES))
        notes = st.text_area("Notes (optional)", placeholder="A small reminder for future you…", height=72)
        submitted = st.form_submit_button("Add block", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("Give your study block a short title.")
            return
        if start is None:
            st.error("Choose a start time for this study block.")
            return
        database.add_session(
            subject_id=int(subject),
            title=title,
            session_date=block_date.isoformat(),
            start_time=start.strftime("%H:%M"),
            duration=int(duration),
            mode=mode,
            notes=notes,
        )
        st.toast("Study block added to your timetable.")
        st.rerun()


@st.dialog("Add a subject")
def add_subject_dialog() -> None:
    with st.form("subject_form", clear_on_submit=False):
        name = st.text_input("Subject name", placeholder="e.g. Organic Chemistry")
        left, right = st.columns(2)
        with left:
            code = st.text_input("Course code", placeholder="e.g. CHEM 201")
            credits = st.selectbox("Credits", [1, 2, 3, 4, 5, 6], index=2)
        with right:
            instructor = st.text_input("Instructor", placeholder="e.g. Dr. Maya Chen")
            target_grade = st.selectbox("Target grade", ["A+", "A", "A-", "B+", "B", "B-", "C+", "Pass"])
        color = st.selectbox("Subject colour", database.COLORS, format_func=lambda value: value.upper())
        submitted = st.form_submit_button("Add subject", type="primary", use_container_width=True)
    if submitted:
        if not name.strip():
            st.error("Add a subject name to continue.")
            return
        database.add_subject(name, code, color, instructor, int(credits), target_grade)
        st.toast(f"{name.strip()} added to your subjects.")
        st.rerun()


@st.dialog("Edit subject")
def edit_subject_dialog(subject_id: int) -> None:
    subject = database.get_subject(subject_id)
    if not subject:
        st.error("This subject is no longer available.")
        return
    with st.form(f"edit_subject_{subject_id}"):
        name = st.text_input("Subject name", value=subject["name"])
        left, right = st.columns(2)
        with left:
            code = st.text_input("Course code", value=subject["code"])
            credits = st.selectbox("Credits", [1, 2, 3, 4, 5, 6], index=max(0, min(5, int(subject["credits"]) - 1)))
        with right:
            instructor = st.text_input("Instructor", value=subject["instructor"])
            grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "Pass"]
            target_grade = st.selectbox(
                "Target grade", grades, index=grades.index(subject["target_grade"]) if subject["target_grade"] in grades else 1
            )
        color = st.selectbox(
            "Subject colour",
            database.COLORS,
            index=database.COLORS.index(subject["color"]) if subject["color"] in database.COLORS else 0,
            format_func=lambda value: value.upper(),
        )
        submitted = st.form_submit_button("Save subject", type="primary", use_container_width=True)
    if submitted:
        if not name.strip():
            st.error("Your subject needs a name.")
            return
        database.update_subject(
            subject_id,
            name=name.strip(),
            code=code.strip() or "NEW 101",
            credits=int(credits),
            instructor=instructor.strip() or "Not set",
            target_grade=target_grade,
            color=color,
        )
        st.toast("Subject details updated.")
        st.rerun()


@st.dialog("Add a syllabus topic")
def add_topic_dialog(subject_id: int | None = None) -> None:
    subjects = database.list_subjects()
    if not subjects:
        st.warning("Add a subject before building a syllabus.")
        if st.button("Go to Subjects", use_container_width=True, type="primary"):
            _go("Subjects")
        return
    ids = [subject["id"] for subject in subjects]
    names = {subject["id"]: subject["name"] for subject in subjects}
    index = ids.index(subject_id) if subject_id in ids else 0
    with st.form("topic_form"):
        subject = st.selectbox("Subject", ids, index=index, format_func=lambda value: names.get(value, "Subject"))
        title = st.text_input("Topic", placeholder="e.g. Integration by parts")
        left, right = st.columns(2)
        with left:
            unit = st.text_input("Unit or module", value="Unit 1")
            status = st.selectbox("Current status", ["Not started", "In progress", "Completed"])
        with right:
            confidence = st.slider("Confidence", 1, 5, 2, help="1 = needs a lot of work · 5 = exam ready")
            due_date = st.date_input("Target review date", value=date.today() + timedelta(days=7))
        submitted = st.form_submit_button("Add topic", type="primary", use_container_width=True)
    if submitted:
        if not title.strip():
            st.error("Give this syllabus topic a name.")
            return
        status_value = {"Not started": "not-started", "In progress": "in-progress", "Completed": "completed"}[status]
        database.add_topic(int(subject), title, unit, status_value, int(confidence), due_date.isoformat())
        st.toast("Topic added to your syllabus.")
        st.rerun()


@st.dialog("Add an assessment")
def add_exam_dialog() -> None:
    subjects = database.list_subjects()
    if not subjects:
        st.warning("Add a subject first, then attach an assessment to it.")
        if st.button("Go to Subjects", use_container_width=True, type="primary"):
            _go("Subjects")
        return
    ids = [subject["id"] for subject in subjects]
    names = {subject["id"]: subject["name"] for subject in subjects}
    with st.form("exam_form"):
        title = st.text_input("Assessment title", placeholder="e.g. Statistics midterm")
        left, right = st.columns(2)
        with left:
            subject = st.selectbox("Subject", ids, format_func=lambda value: names.get(value, "Subject"))
            exam_type = st.selectbox("Type", ["Midterm", "Quiz", "Lab", "Presentation", "Final"])
            readiness = st.slider("Current readiness", 0, 100, 40, step=5)
        with right:
            exam_date = st.date_input("Date", value=date.today() + timedelta(days=14))
            start_time = st.text_input("Time", value="09:00 AM")
            location = st.text_input("Location", placeholder="e.g. Hall B · Seat 24")
        submitted = st.form_submit_button("Add assessment", type="primary", use_container_width=True)
    if submitted:
        if not title.strip():
            st.error("Add an assessment title to continue.")
            return
        database.add_exam(
            int(subject), title, exam_date.isoformat(), start_time, location, exam_type, int(readiness)
        )
        st.toast("Assessment added to your exam outlook.")
        st.rerun()


@st.dialog("Add a reminder")
def add_reminder_dialog() -> None:
    with st.form("reminder_form"):
        text = st.text_input("Reminder", placeholder="e.g. Review chapter 4 summary")
        left, right = st.columns(2)
        with left:
            category = st.selectbox("Category", ["Study", "Deadline", "Wellbeing"])
            priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)
        with right:
            due_date = st.date_input("Due date", value=date.today())
        submitted = st.form_submit_button("Add reminder", type="primary", use_container_width=True)
    if submitted:
        if not text.strip():
            st.error("Write a reminder first.")
            return
        database.add_reminder(text, category, due_date.isoformat(), priority)
        st.toast("Reminder added to your dashboard.")
        st.rerun()


@st.dialog("Please confirm")
def confirm_dialog(kind: str, record_id: int | None = None, label: str = "") -> None:
    copy = {
        "subject": "Related topics, study sessions, and assessments will also be removed from your workspace.",
        "topic": "This topic will be removed from your syllabus progress. Your subject and history stay intact.",
        "exam": "It will disappear from your assessment outlook and timetable.",
        "session": "This entry will be removed from your study history and progress calculations.",
        "reminder": "This reminder will be removed from your dashboard.",
        "reset": "The sample subjects, study history, assessments, and reminders will replace your current workspace.",
        "clear": "Every subject, session, assessment, reminder, and quiz attempt will be removed. Your profile and preferences stay.",
    }.get(kind, "This action updates your workspace.")
    st.markdown(f"**{components.safe(label) or 'Are you sure?'}**")
    st.caption(copy)
    left, right = st.columns(2)
    with left:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with right:
        confirm_label = "Clear workspace" if kind == "clear" else "Load sample workspace" if kind == "reset" else "Remove"
        if st.button(confirm_label, use_container_width=True, type="primary"):
            if kind == "subject" and record_id:
                database.delete_subject(record_id)
                st.toast("Subject removed.", icon="✅")
            elif kind == "topic" and record_id:
                database.delete_topic(record_id)
                st.toast("Topic removed.", icon="✅")
            elif kind == "exam" and record_id:
                database.delete_exam(record_id)
                st.toast("Assessment removed.", icon="✅")
            elif kind == "session" and record_id:
                database.delete_session(record_id)
                st.toast("Study session removed.", icon="✅")
            elif kind == "reminder" and record_id:
                database.delete_reminder(record_id)
                st.toast("Reminder removed.", icon="✅")
            elif kind == "reset":
                database.reset_demo()
                st.toast("Sample workspace loaded.", icon="✨")
            elif kind == "clear":
                database.clear_workspace()
                st.toast("Your workspace is clear.", icon="🧹")
            st.rerun()
