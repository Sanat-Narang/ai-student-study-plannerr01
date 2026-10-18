"""Student preferences, reminders, help and data controls."""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

import database
import planner
from views import components
from views.forms import confirm_dialog

FAQS = [
    (
        "How does the AI timetable build my week?",
        "Your plan is created from the subjects you are studying, how close each assessment is, and the topics still waiting for attention. "
        "It distributes focused blocks across your chosen study days and respects your preferred session length. Generate a fresh plan whenever priorities change.",
    ),
    (
        "How is subject progress calculated?",
        "Each syllabus topic counts toward subject progress. Completed topics count fully, topics in progress count partially, and topics not started do not count yet. "
        "This is why your percentage moves when you change a topic's status.",
    ),
    (
        "What makes a good weekly study goal?",
        "Choose a goal you can meet in an ordinary week, not an ideal one. A realistic target of 10–20 focused hours works for many students. "
        "Include breaks and one lighter day. You can change your goal at any time.",
    ),
    (
        "How should I use reminders?",
        "Keep reminders specific and small: 'review integration formulas for 30 minutes' beats 'study maths'. Use deadlines for submissions and wellbeing reminders for breaks. "
        "Mark them complete as you go so your dashboard stays useful.",
    ),
    (
        "Can I export or reset my study data?",
        "Yes. Download a copy of your study data, export your study history as a spreadsheet, load the sample workspace, or clear your workspace. "
        "Each option is available on this page.",
    ),
    (
        "Where is my planner data kept?",
        "Your work is stored in your StudyPlanner workspace and used only to power your timetable, progress, reminders, and revision experience. "
        "You can export a personal copy at any time. Your study data is never sold.",
    ),
]


def render() -> None:
    settings = database.get_settings()
    profile = database.get_profile()
    weekly_hours = planner.weekly_hours()
    weekly_percent = min(
        100,
        round(weekly_hours / max(1.0, float(profile.get("weekly_goal", 20) or 20)) * 100),
    )

    header, actions = st.columns([2.5, 1.0], vertical_alignment="bottom")
    with header:
        components.page_header(
            "Settings & Help",
            "Tune your study rhythm, manage your data, and find a clear answer when you need one.",
            "Your space, your way",
        )
    with actions:
        st.markdown(
            f'<div class="inline-note">{components.icon("shield", 13)} <span>Changes save to your planner</span></div>',
            unsafe_allow_html=True,
        )

    preferences_tab, notifications_tab, help_tab = st.tabs(
        ["Study preferences", "Notifications", "Help & data"]
    )

    with preferences_tab:
        left, right = st.columns([1.7, 1], gap="medium")
        with left:
            with st.container(border=True):
                components.card_title("Study rhythm", "The cadence your timetable is built around.", "target")
                with st.form("study_rhythm_form"):
                    row_one, row_two = st.columns(2)
                    with row_one:
                        start_value = datetime.strptime(settings.get("study_start", "09:00"), "%H:%M").time()
                        study_start = st.time_input("Preferred study start", value=start_value)
                    with row_two:
                        weekly_goal = st.number_input(
                            "Weekly study goal",
                            min_value=1.0,
                            max_value=80.0,
                            value=float(profile.get("weekly_goal", 20) or 20),
                            step=0.5,
                            help="A realistic target you can meet in an ordinary week.",
                        )
                    row_three, row_four = st.columns(2)
                    with row_three:
                        focus_options = [25, 30, 40, 45, 50, 60, 75, 90]
                        focus_length = st.selectbox(
                            "Focused session length",
                            focus_options,
                            index=focus_options.index(settings.get("focus_length", 50)) if settings.get("focus_length") in focus_options else 4,
                        )
                    with row_four:
                        break_options = [5, 10, 15, 20, 25, 30]
                        break_length = st.selectbox(
                            "Break length",
                            break_options,
                            index=break_options.index(settings.get("break_length", 10)) if settings.get("break_length") in break_options else 1,
                        )
                    study_days = st.multiselect(
                        "Study days",
                        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                        default=settings.get("study_days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]),
                        help="Your timetable will only place new study blocks on these days.",
                    )
                    compact_mode = st.toggle("Compact study lists", value=bool(settings.get("compact_mode", False)))
                    save_preferences = st.form_submit_button("Save study preferences", type="primary", use_container_width=True)
                if save_preferences:
                    if not study_days:
                        st.error("Choose at least one study day so your plan has room to grow.")
                    else:
                        database.update_settings(
                            {
                                "study_start": study_start.strftime("%H:%M"),
                                "focus_length": int(focus_length),
                                "break_length": int(break_length),
                                "study_days": study_days,
                                "compact_mode": bool(compact_mode),
                            }
                        )
                        database.update_profile(weekly_goal=float(weekly_goal))
                        st.toast("Study preferences saved.")
                        st.rerun()
        with right:
            components.focus_card(profile, weekly_hours, weekly_percent)
            st.markdown(
                '<div class="sp-card"><p class="eyebrow-small">A GENTLE NUDGE</p>'
                '<h3 class="card-heading">Build the week you can actually live</h3>'
                '<p class="muted-copy">Shorter sessions with real breaks protect attention better than marathon study. '
                "If a session feels heavy, make it one small, specific outcome. You can always plan another block tomorrow.</p></div>",
                unsafe_allow_html=True,
            )

    with notifications_tab:
        left, right = st.columns([1.7, 1], gap="medium")
        with left:
            with st.container(border=True):
                components.card_title("Reminders & check-ins", "Choose the nudges that help, and leave the noise behind.", "bell")
                with st.form("notification_form"):
                    session_reminders = st.toggle(
                        "Study session reminders",
                        value=bool(settings.get("session_reminders", True)),
                        help="A gentle heads-up before your planned focus blocks.",
                    )
                    exam_reminders = st.toggle(
                        "Assessment countdowns",
                        value=bool(settings.get("exam_reminders", True)),
                        help="Keep upcoming quizzes, labs, and exams in view.",
                    )
                    revision_reminders = st.toggle(
                        "Revision nudges",
                        value=bool(settings.get("revision_reminders", True)),
                        help="Short prompts when a topic is ready for another recall attempt.",
                    )
                    weekly_summary = st.toggle(
                        "Weekly reflection",
                        value=bool(settings.get("weekly_summary", False)),
                        help="A calm summary of your effort, streaks, and upcoming priorities.",
                    )
                    saved = st.form_submit_button("Save notification preferences", type="primary", use_container_width=True)
                if saved:
                    database.update_settings(
                        {
                            "session_reminders": bool(session_reminders),
                            "exam_reminders": bool(exam_reminders),
                            "revision_reminders": bool(revision_reminders),
                            "weekly_summary": bool(weekly_summary),
                        }
                    )
                    st.toast("Notification preferences saved.")
                    st.rerun()
            st.markdown(
                '<div class="soft-note">Your reminders live on the dashboard and in the bell menu. '
                "The best reminder is one that helps you begin, not one that makes you feel behind.</div>",
                unsafe_allow_html=True,
            )
        with right:
            st.markdown(
                '<div class="sp-card"><p class="eyebrow-small">CURRENT CADENCE</p>'
                '<h3 class="card-heading">A quieter kind of reminder</h3>'
                f'<p class="muted-copy">Session reminders are {"on" if settings.get("session_reminders") else "off"}. '
                f'Assessment countdowns are {"on" if settings.get("exam_reminders") else "off"}. '
                f'Revision nudges are {"on" if settings.get("revision_reminders") else "off"}.</p></div>',
                unsafe_allow_html=True,
            )

    with help_tab:
        left, right = st.columns([1.6, 1], gap="medium")
        with left:
            with st.container(border=True):
                components.card_title("Questions students ask", "Clear answers to help you get the most from your planner.", "lightbulb")
                for question, answer in FAQS:
                    with st.expander(question):
                        st.write(answer)
        with right:
            st.markdown(
                '<div class="sp-card"><p class="eyebrow-small">YOUR DATA, YOUR COPY</p>'
                '<h3 class="card-heading">Take your study record with you</h3>'
                '<p class="muted-copy">Export a personal copy of your subjects, syllabus, sessions, assessments, reminders, and quiz history.</p></div>',
                unsafe_allow_html=True,
            )
            st.download_button(
                "Download my study data (.json)",
                data=json.dumps(database.export_workspace(), indent=2, default=str),
                file_name="studyplanner-my-data.json",
                mime="application/json",
                use_container_width=True,
            )
            from planner import build_ics

            st.download_button(
                "Download my week (.ics)",
                data=build_ics(),
                file_name="studyplanner-week.ics",
                mime="text/calendar",
                use_container_width=True,
            )

            with st.container(border=True):
                components.card_title("Workspace", "Start fresh or restore the sample workspace.", "layers")
                if st.button("Load sample workspace", use_container_width=True):
                    confirm_dialog("reset", label="Load the sample workspace?")
                if st.button("Clear my workspace", use_container_width=True):
                    confirm_dialog("clear", label="Clear your workspace?")
                st.caption("Your profile and study preferences remain when you clear the workspace.")

            st.markdown(
                '<div class="sp-card"><p class="eyebrow-small">NEED A HAND?</p>'
                '<h3 class="card-heading">We are here to help</h3>'
                '<p class="muted-copy">Share what is not working and we will help you get back to studying with confidence.</p>'
                '<a class="support-link" href="mailto:help@studyplanner.ai">help@studyplanner.ai</a></div>',
                unsafe_allow_html=True,
            )
