"""Student profile and personal study preferences."""

from __future__ import annotations

import streamlit as st

import database
import planner
from views import components

STYLES = [
    "Visual + practice-led",
    "Reading + note-taking",
    "Discussion + group study",
    "Video-first learner",
    "Practice problems first",
    "Flashcards + spaced repetition",
]
TIMEZONES = [
    "GMT+05:30 · Asia/Kolkata",
    "GMT+00:00 · Europe/London",
    "GMT+01:00 · Europe/Berlin",
    "GMT-05:00 · America/New_York",
    "GMT-08:00 · America/Los_Angeles",
    "GMT+08:00 · Asia/Singapore",
    "GMT+10:00 · Australia/Sydney",
]


def render() -> None:
    profile = database.get_profile()
    subjects = database.list_subjects()
    sessions = database.list_sessions()
    attempts = database.list_attempts()
    topics_completed = sum(subject.get("topic_completed", 0) for subject in subjects)
    hours = planner.total_study_hours()
    streak = planner.study_streak()
    mastery = planner.overall_progress(subjects)

    components.page_header(
        "Student Profile",
        f"{(profile.get('name') or 'Student').split(' ')[0]}, this is your study home. Keeping it accurate makes every plan more personal.",
        "Your learning identity",
    )

    left, right = st.columns([1, 1.85], gap="medium")

    with left:
        st.markdown(
            '<div class="profile-card">'
            '<div class="profile-banner"><span>STUDENT PROFILE</span></div>'
            f'<div class="profile-card-body"><div class="profile-avatar-wrap">{components.avatar_html(profile.get("name", "Student"), 64)}'
            '<span class="active-pill">● Active student</span></div>'
            f'<h2>{components.safe(profile.get("name"))}</h2>'
            f'<p class="profile-course">{components.safe(profile.get("course"))}</p>'
            f'<p class="profile-university">{components.safe(profile.get("university"))} · {components.safe(profile.get("year"))}</p>'
            '<div class="profile-stats">'
            f'<div><strong>{len(subjects)}</strong><span>Subjects</span></div>'
            f'<div><strong>{hours:g}</strong><span>Hours</span></div>'
            f'<div><strong>{streak}</strong><span>Day streak</span></div>'
            "</div>"
            f'<p class="profile-line">{components.icon("shield", 13)} &nbsp;{components.safe(profile.get("student_id") or "Student ID not set")}</p>'
            f'<p class="profile-line">{components.icon("layers", 13)} &nbsp;{components.safe(profile.get("study_style") or "Learning style not set")}</p>'
            f'<p class="profile-line">{components.icon("target", 13)} &nbsp;{components.safe(profile.get("target_exam") or "Next goal not set")}</p>'
            '<div class="profile-mastery"><div><span>Overall syllabus</span><strong>' + str(mastery) + '%</strong></div>'
            + components.progress_html(mastery, "#3B82F6", 5)
            + f'<p>{topics_completed} completed topics across {len(subjects)} subjects.</p></div>'
            "</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sp-card"><p class="eyebrow-small">MILESTONES</p>'
            '<h3 class="card-heading">Your learning wins</h3><div class="achievement-grid">'
            + "".join(
                '<div class="achievement ' + ("" if earned else "is-locked") + '">'
                f'<span class="achievement-icon {tone}">{components.icon(icon_name, 14)}</span>'
                f'<p>{title}</p><span>{description}</span></div>'
                for title, description, earned, tone, icon_name in [
                    ("Seven-day rhythm", "Studied seven days in a row", streak >= 7, "amber", "flame"),
                    ("Syllabus explorer", "Completed 10 or more topics", topics_completed >= 10, "blue", "book"),
                    ("Curious mind", "Completed your first quiz", len(attempts) > 0, "violet", "sparkles"),
                    ("Goal getter", "Set a personal weekly goal", float(profile.get("weekly_goal", 0) or 0) > 0, "green", "target"),
                ]
            )
            + "</div></div>",
            unsafe_allow_html=True,
        )

    with right:
        with st.container(border=True):
            components.card_title("Personal details", "Used to make your study space feel like yours.", "shield")
            with st.form("profile_personal_form"):
                left_a, right_a = st.columns(2)
                with left_a:
                    name = st.text_input("Full name", value=profile.get("name", ""))
                    course = st.text_input("Course or programme", value=profile.get("course", ""))
                with right_a:
                    email = st.text_input("University email", value=profile.get("email", ""))
                    university = st.text_input("University", value=profile.get("university", ""))
                left_b, right_b = st.columns(2)
                with left_b:
                    years = ["Year 1", "Year 2", "Year 3", "Year 4", "Postgraduate", "Foundation"]
                    year = st.selectbox("Year of study", years, index=years.index(profile.get("year")) if profile.get("year") in years else 1)
                with right_b:
                    student_id = st.text_input("Student ID", value=profile.get("student_id", ""))
                bio = st.text_area("About you", value=profile.get("bio", ""), height=84)
                saved = st.form_submit_button("Save personal details", type="primary", use_container_width=True)
            if saved:
                if not name.strip() or not email.strip():
                    st.error("Your name and email help personalise the planner.")
                else:
                    database.update_profile(
                        name=name.strip(),
                        email=email.strip(),
                        course=course.strip(),
                        university=university.strip(),
                        year=year,
                        student_id=student_id.strip(),
                        bio=bio.strip(),
                    )
                    st.toast("Profile saved.")
                    st.rerun()

        with st.container(border=True):
            components.card_title("Study preferences", "The planner shapes your week around these choices.", "chart")
            with st.form("profile_preferences_form"):
                pref_left, pref_right = st.columns(2)
                with pref_left:
                    weekly_goal = st.number_input(
                        "Weekly study goal (hours)", min_value=1.0, max_value=80.0,
                        value=float(profile.get("weekly_goal", 20) or 20), step=0.5,
                    )
                    styles = list(dict.fromkeys([profile.get("study_style") or STYLES[0], *STYLES]))
                    study_style = st.selectbox("Learning style", styles)
                with pref_right:
                    zones = list(dict.fromkeys([profile.get("timezone") or TIMEZONES[0], *TIMEZONES]))
                    timezone = st.selectbox("Timezone", zones)
                    target_exam = st.text_input("Next major goal", value=profile.get("target_exam", ""))
                saved_preferences = st.form_submit_button("Save study preferences", type="primary", use_container_width=True)
            if saved_preferences:
                database.update_profile(
                    weekly_goal=float(weekly_goal),
                    study_style=study_style,
                    timezone=timezone,
                    target_exam=target_exam.strip(),
                )
                st.toast("Study preferences saved.")
                st.rerun()

        quick_cols = st.columns(3)
        quick = [
            ("Active reminders", sum(1 for reminder in database.list_reminders() if not reminder["done"]), "bell", "blue"),
            ("Revision attempts", len(attempts), "brain", "violet"),
            ("Planner member", components.member_since(), "shield", "green"),
        ]
        for column, (label, value, icon_name, tone) in zip(quick_cols, quick):
            with column:
                st.markdown(
                    f'<div class="quick-card">{components.icon_tile(icon_name, tone, 30)}'
                    f'<div><span>{components.safe(label)}</span><strong>{components.safe(value)}</strong></div></div>',
                    unsafe_allow_html=True,
                )
