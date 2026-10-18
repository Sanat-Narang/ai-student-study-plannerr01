"""Syllabus progress, one specific topic at a time."""

from __future__ import annotations

import streamlit as st

import database
import planner
from views import components
from views.forms import add_topic_dialog, confirm_dialog

STATUS_OPTIONS = {"Not started": "not-started", "In progress": "in-progress", "Completed": "completed"}
STATUS_REVERSE = {value: key for key, value in STATUS_OPTIONS.items()}


def render() -> None:
    subjects = database.list_subjects()

    header, actions = st.columns([2.5, 1.2], vertical_alignment="bottom")
    with header:
        components.page_header(
            "Syllabus Tracker",
            "Turn a long syllabus into specific topics. A topic you can name is a topic you can finish.",
            "Make the syllabus feel smaller",
        )
    with actions:
        add_disabled = not subjects
        if st.button("＋ Add topic", type="primary", use_container_width=True, disabled=add_disabled):
            preferred = st.session_state.get("syllabus_subject_id")
            add_topic_dialog(int(preferred) if preferred else None)
        if st.button("Plan study time", use_container_width=True):
            st.session_state.page = "AI Timetable"
            st.rerun()

    if not subjects:
        components.empty_state(
            "Your syllabus will appear here",
            "Start with a subject, then add each unit and topic. Mark topics in progress or complete to see your confidence grow.",
            "list",
        )
        if st.button("Add your first subject", type="primary"):
            st.session_state.page = "Subjects"
            st.rerun()
        return

    ids = [int(subject["id"]) for subject in subjects]
    if st.session_state.get("syllabus_subject_id") in ids:
        st.session_state["syllabus_subject_select"] = st.session_state.pop("syllabus_subject_id")
    if st.session_state.get("syllabus_subject_select") not in ids:
        st.session_state.pop("syllabus_subject_select", None)

    names = {int(subject["id"]): subject["name"] for subject in subjects}
    select_col, note_col = st.columns([1.3, 2.4])
    with select_col:
        selected_id = st.selectbox(
            "Subject",
            ids,
            format_func=lambda value: names.get(value, "Subject"),
            key="syllabus_subject_select",
        )
    subject = database.get_subject(int(selected_id))
    if not subject:
        st.error("This subject could not be found. Choose another from the list.")
        return

    topics = subject.get("topics", [])
    counts = {
        "all": len(topics),
        "not-started": sum(1 for topic in topics if topic["status"] == "not-started"),
        "in-progress": sum(1 for topic in topics if topic["status"] == "in-progress"),
        "completed": sum(1 for topic in topics if topic["status"] == "completed"),
    }
    confidence = round(sum(topic["confidence"] for topic in topics) / len(topics), 1) if topics else 0
    next_review = next((topic for topic in topics if topic["status"] != "completed"), None)
    total_topics = sum(int(item.get("topic_total", 0)) for item in subjects)
    completed_topics = sum(int(item.get("topic_completed", 0)) for item in subjects)

    with note_col:
        st.markdown(
            f'<div class="inline-note">{components.icon("sparkles", 14)} '
            f'<span>{components.safe(subject["instructor"])} · {subject["credits"]} credits · Target grade {components.safe(subject["target_grade"])}</span></div>',
            unsafe_allow_html=True,
        )

    components.metric_grid(
        [
            {"label": "Total topics", "value": total_topics, "suffix": "", "icon": "list", "tone": "blue", "hint": f"across {len(subjects)} subjects"},
            {"label": "Completed", "value": completed_topics, "suffix": "", "icon": "check", "tone": "green", "hint": f"{round((completed_topics / total_topics) * 100) if total_topics else 0}% of the full syllabus"},
            {"label": "In progress", "value": counts["in-progress"], "suffix": "topics", "icon": "clock", "tone": "amber", "hint": subject["name"]},
            {"label": "Confidence", "value": f"{confidence}/5", "suffix": "", "icon": "target", "tone": "violet", "hint": "for this subject"},
        ]
    )

    st.write("")
    with st.container(border=True):
        components.card_title(
            subject["name"],
            f"{subject['code']} · {counts['completed']} of {counts['all']} topics complete",
            "book",
            components.badge(f"{subject['progress']}% complete", "green" if subject["progress"] >= 70 else "blue"),
        )
        st.markdown(components.progress_html(subject["progress"], subject["color"], 6), unsafe_allow_html=True)
        st.markdown(
            f'<p class="topic-next">{components.icon("clock3", 12)} Next review: '
            f'{components.safe(next_review["title"] if next_review else "Everything is reviewed")}'
            f'{" · " + components.safe(planner.format_date(next_review["due_date"])) if next_review else ""}</p>',
            unsafe_allow_html=True,
        )

        filter_label = st.radio(
            "Filter topics",
            [
                f"All ({counts['all']})",
                f"Learning ({counts['in-progress']})",
                f"Not started ({counts['not-started']})",
                f"Completed ({counts['completed']})",
            ],
            horizontal=True,
            label_visibility="collapsed",
            key="syllabus_filter",
        )
        selected_filter = {
            "All": "all",
            "Learning": "in-progress",
            "Not started": "not-started",
            "Completed": "completed",
        }[filter_label.split(" (")[0]]
        filtered = [
            topic for topic in topics if selected_filter == "all" or topic["status"] == selected_filter
        ]

        if filtered:
            for topic in filtered:
                check_col, title_col, confidence_col, status_col, delete_col = st.columns(
                    [0.35, 4.1, 1.15, 1.25, 0.5], vertical_alignment="center"
                )
                with check_col:
                    checked = st.checkbox(
                        f"Mark {topic['title']} complete",
                        value=topic["status"] == "completed",
                        key=f"topic_done_{topic['id']}",
                        label_visibility="collapsed",
                    )
                    if checked != (topic["status"] == "completed"):
                        database.toggle_topic_complete(int(topic["id"]))
                        st.rerun()
                with title_col:
                    st.markdown(
                        f'<p class="topic-title {"is-done" if topic["status"] == "completed" else ""}">{components.safe(topic["title"])}</p>'
                        f'<p class="topic-meta">{components.safe(topic["unit"])} · Review {components.safe(planner.format_date(topic["due_date"]))}</p>',
                        unsafe_allow_html=True,
                    )
                with confidence_col:
                    st.markdown(
                        '<div class="confidence"><span>Confidence</span><div class="confidence-dots">'
                        + "".join(
                            f'<i class="{"is-on" if level <= topic["confidence"] else ""}"></i>' for level in range(1, 6)
                        )
                        + f"</div><strong>{topic['confidence']}/5</strong></div>",
                        unsafe_allow_html=True,
                    )
                with status_col:
                    current = STATUS_REVERSE.get(topic["status"], "Not started")
                    new_status = st.selectbox(
                        f"Status for {topic['title']}",
                        list(STATUS_OPTIONS.keys()),
                        index=list(STATUS_OPTIONS.keys()).index(current),
                        key=f"topic_status_{topic['id']}",
                        label_visibility="collapsed",
                    )
                    if STATUS_OPTIONS[new_status] != topic["status"]:
                        database.update_topic(int(topic["id"]), status=STATUS_OPTIONS[new_status])
                        st.rerun()
                with delete_col:
                    if st.button("🗑", key=f"delete_topic_{topic['id']}", help=f"Remove {topic['title']}"):
                        confirm_dialog("topic", int(topic["id"]), f"Remove {topic['title']}?")
                st.markdown('<div class="row-divider"></div>', unsafe_allow_html=True)
        else:
            components.empty_state(
                "No topics in this view",
                "Change the filter to see the rest of your syllabus, or add a new topic.",
                "list",
            )

        if st.button("＋ Add a topic", use_container_width=False):
            add_topic_dialog(int(subject["id"]))

    st.markdown(
        '<div class="soft-note">A topic you understand deeply is worth more than three you skimmed. '
        "Use the confidence dots to notice where an extra review would help.</div>",
        unsafe_allow_html=True,
    )
