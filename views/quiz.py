"""Revision and active-recall quiz experience."""

from __future__ import annotations

import streamlit as st

import database
import planner
import quiz as quiz_engine
from views import components


def _start_quiz(subject: dict, mode: str) -> None:
    questions = quiz_engine.generate_quiz(subject["name"], mode)
    st.session_state.quiz_questions = questions
    st.session_state.quiz_subject = {"id": subject["id"], "name": subject["name"], "color": subject["color"]}
    st.session_state.quiz_index = 0
    st.session_state.quiz_answers = []
    st.session_state.quiz_checked = False
    st.session_state.quiz_result = None
    st.session_state.quiz_token = st.session_state.get("quiz_token", 0) + 1
    st.session_state.quiz_stage = "active"
    st.rerun()


def _reset_quiz() -> None:
    st.session_state.quiz_stage = "setup"
    st.session_state.quiz_questions = []
    st.session_state.quiz_answers = []
    st.session_state.quiz_checked = False
    st.session_state.quiz_result = None
    st.session_state.quiz_index = 0
    st.rerun()


def _history_card(attempts: list[dict]) -> None:
    with st.container(border=True):
        components.card_title("Recent attempts", f"{len(attempts)} quizzes recorded", "brain")
        if attempts:
            for attempt in attempts[:4]:
                percentage = round((attempt["score"] / max(1, attempt["total"])) * 100)
                st.markdown(
                    f'<div class="attempt-line"><span class="attempt-score {"good" if percentage >= 70 else "warm"}">{percentage}</span>'
                    f'<span class="attempt-name">{components.safe(attempt["subject_name"])}</span>'
                    f'<small>{attempt["score"]}/{attempt["total"]} · {components.safe(planner.format_date(attempt["taken_at"]))}</small></div>',
                    unsafe_allow_html=True,
                )
        else:
            components.empty_state("No quiz attempts yet", "Complete a short quiz to start your recall history.", "brain")


def render() -> None:
    if "quiz_stage" not in st.session_state:
        st.session_state.quiz_stage = "setup"

    subjects = database.list_subjects()
    attempts = database.list_attempts()
    stats = planner.quiz_stats()

    header, actions = st.columns([2.5, 1.1], vertical_alignment="bottom")
    with header:
        components.page_header(
            "Revision & Quiz",
            "Short retrieval practice beats long rereading. Choose a subject, answer a few questions, and learn from every attempt.",
            "Practise remembering",
        )
    with actions:
        if st.button("View performance", use_container_width=True):
            st.session_state.page = "Performance Analysis"
            st.rerun()
        if st.session_state.quiz_stage != "setup":
            if st.button("Start over", use_container_width=True):
                _reset_quiz()

    if not subjects:
        components.empty_state(
            "A quiz needs something to revise",
            "Add your first subject and its syllabus topics. Then you can practise active recall with short, subject-specific quizzes.",
            "brain",
        )
        if st.button("Add your first subject", type="primary"):
            st.session_state.page = "Subjects"
            st.rerun()
        return

    if st.session_state.quiz_stage == "setup":
        components.metric_grid(
            [
                {"label": "Quiz accuracy", "value": f"{stats['accuracy']}%" if stats["total"] else "—", "suffix": "", "icon": "brain", "tone": "blue", "hint": f"{stats['score']}/{stats['total']} total answers"},
                {"label": "Quizzes taken", "value": stats["attempts"], "suffix": "", "icon": "check", "tone": "violet", "hint": "every attempt counts"},
                {"label": "Personal best", "value": f"{stats['best']}%" if stats["attempts"] else "—", "suffix": "", "icon": "trophy", "tone": "amber", "hint": "your highest score so far"},
                {"label": "Topics to revisit", "value": len([topic for subject in subjects for topic in (database.get_subject(int(subject["id"])) or {}).get("topics", []) if topic["status"] != "completed"]), "suffix": "", "icon": "lightbulb", "tone": "green", "hint": "from your syllabus"},
            ]
        )
        st.write("")
        left, right = st.columns([1.8, 1], gap="medium")
        with left:
            with st.container(border=True):
                st.markdown(
                    '<div class="quiz-hero"><div class="quiz-hero-icon">' + components.icon("brain", 19) + "</div>"
                    '<div><p class="planning-eyebrow">Active recall session</p>'
                    "<h2>Test yourself, not your notes.</h2>"
                    "<p>Each quiz mixes topic-specific questions with transferable study skills. "
                    "Every answer comes with a short explanation. No timer, no pressure — understanding is the goal.</p>"
                    "</div></div>",
                    unsafe_allow_html=True,
                )
                names = {int(subject["id"]): subject["name"] for subject in subjects}
                subject_id = st.selectbox(
                    "Choose a subject",
                    list(names.keys()),
                    format_func=lambda value: names.get(value, "Subject"),
                )
                mode = st.radio(
                    "Pick your depth",
                    list(quiz_engine.DIFFICULTY_COUNTS.keys()),
                    horizontal=True,
                    index=1,
                    help="More questions means a deeper recall session.",
                )
                weeks_note = st.empty()
                selected_subject = next(subject for subject in subjects if int(subject["id"]) == int(subject_id))
                st.markdown(
                    f'<div class="inline-note">{components.icon("sparkles", 13)} '
                    f'<span>{components.safe(selected_subject["name"])} · {selected_subject["topic_total"]} syllabus topics · '
                    f'{selected_subject["progress"]}% mastery</span></div>',
                    unsafe_allow_html=True,
                )
                weeks_note.caption(f"About {quiz_engine.DIFFICULTY_COUNTS[mode] * 2} minutes. Questions are drawn from your subject and general study skills.")
                if st.button("Start quiz →", type="primary", use_container_width=False):
                    _start_quiz(selected_subject, mode)
        with right:
            with st.container(border=True):
                components.card_title("Make it stick", "Three habits for durable recall", "sparkles")
                for step, title, copy in [
                    ("01", "Recall before you peek", "Try answering without notes. The effort is where learning happens."),
                    ("02", "Read the explanation", "Even correct guesses deserve a clear reason. Connect it to what you know."),
                    ("03", "Revisit tomorrow", "A short second attempt a day later is stronger than a long one today."),
                ]:
                    st.markdown(
                        f'<div class="tip-row"><span>{step}</span><div><strong>{title}</strong><p>{copy}</p></div></div>',
                        unsafe_allow_html=True,
                    )
            _history_card(attempts)

    elif st.session_state.quiz_stage == "active":
        questions = st.session_state.get("quiz_questions", [])
        index = int(st.session_state.get("quiz_index", 0))
        subject = st.session_state.get("quiz_subject", {})
        checked = bool(st.session_state.get("quiz_checked", False))
        answers = list(st.session_state.get("quiz_answers", []))
        if not questions or index >= len(questions):
            _reset_quiz()
            return
        question = questions[index]
        token = st.session_state.get("quiz_token", 0)
        option_key = f"quiz_option_{token}_{index}"

        left, right = st.columns([1.8, 1], gap="medium")
        with left:
            with st.container(border=True):
                components.card_title(
                    subject.get("name", "Revision"),
                    f"{len(questions)}-question recall session",
                    "brain",
                    components.badge(f"Question {index + 1} of {len(questions)}", "blue"),
                )
                st.markdown(components.progress_html(((index + (1 if checked else 0)) / len(questions)) * 100, "#2563eb", 5), unsafe_allow_html=True)
                st.markdown(
                    f'<p class="question-topic">{components.safe(question["topic"])}</p>'
                    f'<h2 class="quiz-question">{components.safe(question["question"])}</h2>',
                    unsafe_allow_html=True,
                )
                selection = st.radio(
                    "Choose your answer",
                    question["options"],
                    index=None,
                    key=option_key,
                    label_visibility="collapsed",
                    disabled=checked,
                )
                if checked and answers:
                    selected_index = answers[-1]
                    correct = selected_index == question["answer"]
                    feedback_class = "correct" if correct else "wrong"
                    feedback_headline = "That's right." if correct else "Not quite — here's the reasoning."
                    explanation = components.safe(question["explanation"])
                    st.markdown(
                        f'<div class="answer-feedback {feedback_class}">'
                        f"<strong>{feedback_headline}</strong>"
                        f"<p>{explanation}</p></div>",
                        unsafe_allow_html=True,
                    )
                    st.button(
                        "See results" if index == len(questions) - 1 else "Next question →",
                        type="primary",
                        key=f"quiz_next_{token}_{index}",
                        on_click=lambda: _advance_quiz(questions, answers, subject),
                    )
                else:
                    if st.button("Check answer", type="primary"):
                        if selection is None:
                            st.warning("Choose an answer before checking.")
                        else:
                            st.session_state.quiz_answers = answers + [question["options"].index(selection)]
                            st.session_state.quiz_checked = True
                            st.rerun()
                st.caption("Tip: say your reasoning out loud before choosing.")
        with right:
            with st.container(border=True):
                components.card_title("Session progress", "You are doing the work", "chart")
                correct_so_far = sum(1 for answer_index, answer in enumerate(answers) if answer == questions[answer_index]["answer"])
                st.markdown(
                    f'<div class="session-score">{components.ring_html(round((correct_so_far / max(1, len(answers))) * 100), 56, "#7c3aed", "#eef2f8", f"{correct_so_far}/{len(answers)}")}'
                    f'<div><strong>Correct so far</strong><span>{len(answers)} checked · {len(questions) - len(answers)} remaining</span></div></div>',
                    unsafe_allow_html=True,
                )
                for number, item in enumerate(questions):
                    if number < len(answers):
                        state = "correct" if answers[number] == item["answer"] else "wrong"
                        symbol = "✓" if state == "correct" else "×"
                    else:
                        state = "current" if number == index else ""
                        symbol = str(number + 1)
                    st.markdown(
                        f'<div class="quiz-step {state}"><span>{symbol}</span>{components.safe(item["topic"])}</div>',
                        unsafe_allow_html=True,
                    )
            _history_card(attempts)

    else:
        result = st.session_state.get("quiz_result")
        subject = st.session_state.get("quiz_subject", {})
        if not result:
            _reset_quiz()
            return
        header_col, action_col = st.columns([2.2, 1])
        with header_col:
            st.markdown(
                f'<div class="result-banner"><div>{components.ring_html(result["percent"], 90, "#7dd3fc", "rgba(255,255,255,.14)")}</div>'
                '<div><p class="planning-eyebrow">Quiz complete</p>'
                f'<h2>{components.safe(result["message"])}</h2>'
                f'<p>You answered {result["score"]} of {result["total"]} questions correctly in {components.safe(subject.get("name", "your subject"))}. '
                f'{components.safe(quiz_engine.feedback_for(result["percent"]))}</p></div></div>',
                unsafe_allow_html=True,
            )
        with action_col:
            if st.button("Start a new quiz", type="primary", use_container_width=True):
                _reset_quiz()
            if st.button("Review weak topics", use_container_width=True):
                st.session_state.page = "Syllabus Tracker"
                st.rerun()

        st.write("")
        left, right = st.columns([1.8, 1], gap="medium")
        with left:
            with st.container(border=True):
                components.card_title("Answer review", "Understanding the why matters more than the score", "list")
                for index, item in enumerate(result["review"], start=1):
                    st.markdown(
                        f'<div class="review-card {"correct" if item["correct"] else "wrong"}">'
                        f'<div class="review-head"><span>{"✓" if item["correct"] else "×"}</span>'
                        f'<p>{index}. {components.safe(item["question"])}</p></div>'
                        f'<p class="review-answer">Correct: {components.safe(item["correct_text"])}'
                        + ("" if item["correct"] else f' · You chose: {components.safe(item["selected_text"])}')
                        + "</p>"
                        f'<p class="review-explanation">{components.safe(item["explanation"])}</p></div>',
                        unsafe_allow_html=True,
                    )
        with right:
            st.markdown(
                '<div class="sp-card"><p class="eyebrow-small">KEEP THE THREAD</p>'
                '<h3 class="card-heading">Revisit tomorrow</h3>'
                '<p class="muted-copy">Come back to these questions in a day without looking at the explanations first. '
                "Spacing your recall turns a good quiz into lasting knowledge.</p></div>",
                unsafe_allow_html=True,
            )
            _history_card(attempts)


def _advance_quiz(questions: list[dict], answers: list[int], subject: dict) -> None:
    """Advance or finish a quiz. Used as a Streamlit button callback."""
    index = int(st.session_state.get("quiz_index", 0))
    if index >= len(questions) - 1:
        result = quiz_engine.score_quiz(questions, answers)
        database.add_quiz_attempt(subject.get("id"), subject.get("name", "Study quiz"), result["score"], result["total"])
        st.session_state.quiz_result = result
        st.session_state.quiz_stage = "results"
        st.session_state.quiz_checked = False
    else:
        st.session_state.quiz_index = index + 1
        st.session_state.quiz_checked = False
