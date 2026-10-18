"""Learning analytics for the student."""

from __future__ import annotations

import streamlit as st

import analytics
import database
import planner
from views import components


def render() -> None:
    subjects = database.list_subjects()
    sessions = database.list_sessions(status="completed")
    attempts = database.list_attempts()
    exams = database.list_exams()
    activity = planner.daily_activity(7)
    quiz = planner.quiz_stats()
    hours = planner.total_study_hours()
    streak = planner.study_streak()
    studied_week = planner.weekly_hours()
    readiness = round(sum(int(exam["readiness"]) for exam in exams) / len(exams)) if exams else 0
    focus_subject = planner.weakest_subject(subjects)
    strength_subject = planner.strongest_subject(subjects)
    profile = database.get_profile()

    header, actions = st.columns([2.5, 1.2], vertical_alignment="bottom")
    with header:
        components.page_header(
            "Performance Analysis",
            "A thoughtful look at your consistency, subject mastery, and recall — so your next study decision is an informed one.",
            "Patterns, not pressure",
        )
    with actions:
        if st.button("Take a quiz", type="primary", use_container_width=True):
            st.session_state.page = "Revision & Quiz"
            st.rerun()
        if st.button("Review weak topics", use_container_width=True):
            st.session_state.page = "Syllabus Tracker"
            if focus_subject:
                st.session_state.syllabus_subject_id = focus_subject["id"]
            st.rerun()

    if not subjects:
        components.empty_state(
            "Your insights will grow here",
            "Add subjects, complete study blocks, and take a short revision quiz. Small actions become a clear picture of your progress.",
            "chart",
        )
        if st.button("Add your first subject", type="primary"):
            st.session_state.page = "Subjects"
            st.rerun()
        return

    components.metric_grid(
        [
            {"label": "Syllabus mastery", "value": f"{planner.overall_progress(subjects)}%", "suffix": "", "icon": "target", "tone": "blue", "hint": f"across {len(subjects)} active subjects"},
            {"label": "Quiz accuracy", "value": f"{quiz['accuracy']}%" if quiz["total"] else "—", "suffix": "", "icon": "brain", "tone": "violet", "hint": f"{quiz['score']} of {quiz['total']} answers correct"},
            {"label": "Total study time", "value": f"{hours:g}h", "suffix": "", "icon": "clock", "tone": "green", "hint": f"{streak} day current streak"},
            {"label": "Exam readiness", "value": f"{readiness}%", "suffix": "", "icon": "calendar", "tone": "amber", "hint": f"{len(exams)} assessments ahead"},
        ]
    )

    st.write("")
    left, right = st.columns([1.7, 1], gap="medium")
    with left:
        with st.container(border=True):
            components.card_title("Weekly study rhythm", f"{studied_week:.1f}h this week · {planner.hours_label(sum(point['minutes'] for point in activity))} in the last 7 days", "chart")
            st.plotly_chart(
                analytics.study_activity_figure(activity),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            best = max(activity, key=lambda point: point["hours"])
            daily_target = round(float(profile.get("weekly_goal", 20) or 20) / 7, 1)
            st.caption(f"Your strongest recent day was {best['label']} with {best['hours']} focused hours. A daily target of {daily_target}h keeps your weekly goal within reach.")

        with st.container(border=True):
            components.card_title("Subject mastery", "Progress across the whole syllabus", "target")
            st.plotly_chart(
                analytics.subject_mastery_figure(subjects),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        with st.container(border=True):
            components.card_title("Assessment readiness", "How prepared each course feels right now", "calendar")
            if exams:
                st.plotly_chart(
                    analytics.exam_readiness_figure(exams),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                exam_columns = st.columns(len(exams[:3]))
                for column, exam in zip(exam_columns, exams[:3]):
                    with column:
                        st.markdown(
                            f'<div class="readiness-card"><span>{components.safe(exam.get("subject_code") or "Course")}</span>'
                            f'<strong>{int(exam["readiness"])}%</strong>'
                            f'<p>{components.safe(exam["title"])}</p>'
                            f'<small>{components.safe(planner.countdown_label(exam["exam_date"]))}</small></div>',
                            unsafe_allow_html=True,
                        )
            else:
                components.empty_state("No assessments scheduled", "Add an upcoming assessment so you can track your readiness over time.", "calendar")

    with right:
        with st.container(border=True):
            components.card_title("Mastery shape", "How balanced your learning is", "target")
            st.plotly_chart(
                analytics.mastery_radar_figure(subjects),
                use_container_width=True,
                config={"displayModeBar": False},
            )
            for subject in subjects[:4]:
                st.markdown(
                    f'<div class="radar-legend"><span><i style="background:{components.safe(subject["color"])}"></i>'
                    f'{components.safe(subject["code"])}</span><strong>{subject["progress"]}%</strong></div>',
                    unsafe_allow_html=True,
                )

        with st.container(border=True):
            components.card_title("Quiz accuracy", "Active recall across all attempts", "brain")
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.plotly_chart(
                    analytics.quiz_accuracy_figure(attempts),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with col_b:
                st.markdown(
                    f'<div class="quiz-summary"><div><span>Correct</span><strong>{quiz["score"]}</strong></div>'
                    f'<div><span>Attempts</span><strong>{quiz["attempts"]}</strong></div>'
                    f'<div><span>Best score</span><strong>{quiz["best"]}%</strong></div></div>',
                    unsafe_allow_html=True,
                )
            if st.button("Practise recall now", use_container_width=True):
                st.session_state.page = "Revision & Quiz"
                st.rerun()
            for attempt in attempts[:3]:
                percentage = round((attempt["score"] / max(1, attempt["total"])) * 100)
                st.markdown(
                    f'<div class="attempt-line"><span class="attempt-score {"good" if percentage >= 70 else "warm"}">{percentage}</span>'
                    f'<span class="attempt-name">{components.safe(attempt["subject_name"])}</span>'
                    f'<small>{attempt["score"]}/{attempt["total"]} · {components.safe(planner.format_date(attempt["taken_at"]))}</small></div>',
                    unsafe_allow_html=True,
                )

        components.insight_card(
            f"Spend 45 focused minutes on {focus_subject['name']}.",
            (
                f"It is your lowest-mastery subject at {focus_subject['progress']}%. "
                "Try active recall first, then a short problem set. "
                f"Your strongest area is {strength_subject['name']} at {strength_subject['progress']}%."
                if strength_subject
                else "A focused first step will start building your picture."
            )
            if focus_subject
            else "Add a subject to receive a personal next step.",
            "lightbulb",
        )
        st.caption(f"You have recorded {len(sessions)} completed study blocks. That is meaningful, consistent work.")
