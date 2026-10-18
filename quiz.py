"""Revision quiz engine for StudyPlanner AI.

The bank covers the sample subjects and broader study-skills topics. Questions
are selected at random, then scored locally so quiz attempts can be stored in
SQLite without any external service.
"""

from __future__ import annotations

import random

QUIZ_BANK: list[dict] = [
    {
        "key": "math",
        "topic": "Integration techniques",
        "question": "What is ∫ 2x dx?",
        "options": ["x² + C", "2x² + C", "x² ⁄ 2 + C", "2 + C"],
        "answer": 0,
        "explanation": "Using the power rule, ∫ 2x dx = x² + C. Always include the constant of integration.",
    },
    {
        "key": "math",
        "topic": "Applications of derivatives",
        "question": "A derivative describes which of the following?",
        "options": ["The total area under a curve", "The instantaneous rate of change", "The average of a dataset", "The product of two functions"],
        "answer": 1,
        "explanation": "The derivative measures how a quantity changes at a particular instant.",
    },
    {
        "key": "math",
        "topic": "Sequences and series",
        "question": "An infinite geometric series converges only when the common ratio r satisfies:",
        "options": ["r > 1", "r = 1", "|r| < 1", "r < -1"],
        "answer": 2,
        "explanation": "The series converges when the absolute value of the common ratio is less than one.",
    },
    {
        "key": "math",
        "topic": "Linear algebra",
        "question": "What does an eigenvector of a matrix satisfy?",
        "options": ["Av = λv for some scalar λ", "Av = 0 for every v", "Aᵀ = −A", "det(A) = 1"],
        "answer": 0,
        "explanation": "An eigenvector is only scaled by the matrix, so Av = λv for its eigenvalue λ.",
    },
    {
        "key": "math",
        "topic": "Definite integrals",
        "question": "The definite integral of a positive function between a and b gives:",
        "options": ["The slope at a", "The area under the curve from a to b", "The average of a and b", "The derivative of the function"],
        "answer": 1,
        "explanation": "Definite integration accumulates area beneath the curve between the two limits.",
    },
    {
        "key": "data",
        "topic": "Trees",
        "question": "Which traversal visits a binary tree's root between its left and right subtrees?",
        "options": ["Pre-order", "In-order", "Post-order", "Breadth-first"],
        "answer": 1,
        "explanation": "In-order visits left, root, then right — and yields sorted values in a binary search tree.",
    },
    {
        "key": "data",
        "topic": "Hashing",
        "question": "What is the average time complexity of a lookup in a well-designed hash table?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"],
        "answer": 0,
        "explanation": "With a good hash function and low load factor, lookups take constant time on average.",
    },
    {
        "key": "data",
        "topic": "Stacks and queues",
        "question": "Which data structure follows First-In-First-Out (FIFO)?",
        "options": ["Stack", "Queue", "Binary search tree", "Heap"],
        "answer": 1,
        "explanation": "A queue removes items in the same order they were added.",
    },
    {
        "key": "data",
        "topic": "Dynamic programming",
        "question": "Dynamic programming primarily improves performance by:",
        "options": ["Using less memory always", "Storing overlapping subproblem results", "Sorting the input", "Randomising recursion"],
        "answer": 1,
        "explanation": "Memoisation or tabulation avoids repeating overlapping subproblems, reducing exponential work.",
    },
    {
        "key": "data",
        "topic": "Graphs",
        "question": "Which algorithm finds shortest paths in a graph with non-negative edge weights?",
        "options": ["Dijkstra's algorithm", "Bubble sort", "Pre-order traversal", "Binary search"],
        "answer": 0,
        "explanation": "Dijkstra's algorithm greedily settles the nearest unvisited node.",
    },
    {
        "key": "physics",
        "topic": "Newton's laws",
        "question": "Newton's second law is best expressed as:",
        "options": ["F = mv", "F = ma", "E = mc²", "p = mv"],
        "answer": 1,
        "explanation": "Force equals mass times acceleration; net force determines acceleration.",
    },
    {
        "key": "physics",
        "topic": "Electromagnetism",
        "question": "Faraday's law relates induced EMF to:",
        "options": ["The rate of change of magnetic flux", "The mass of the conductor", "The colour of the coil", "The resistance only"],
        "answer": 0,
        "explanation": "A changing magnetic flux through a loop induces an electromotive force.",
    },
    {
        "key": "physics",
        "topic": "Optics",
        "question": "Which phenomenon explains why white light separates into colours through a prism?",
        "options": ["Reflection", "Dispersion", "Diffraction", "Polarisation"],
        "answer": 1,
        "explanation": "Different wavelengths bend by different amounts in glass — this is dispersion.",
    },
    {
        "key": "physics",
        "topic": "Work and energy",
        "question": "Work is calculated as:",
        "options": ["Force × displacement in the force direction", "Mass × velocity", "Force × time", "Mass × acceleration"],
        "answer": 0,
        "explanation": "Only the component of force along the displacement contributes to mechanical work.",
    },
    {
        "key": "english",
        "topic": "Academic writing",
        "question": "Which sentence states a debatable, focused argument?",
        "options": ["University libraries are old.", "Libraries should offer late-night study spaces because demand peaks after 10 p.m.", "Many students use libraries.", "This essay is about libraries."],
        "answer": 1,
        "explanation": "A strong thesis makes a claim that can be supported and debated, not just a fact.",
    },
    {
        "key": "english",
        "topic": "Research citations",
        "question": "In APA style, what appears first in a reference-list entry?",
        "options": ["The publisher", "The author's surname", "The page number", "The journal name"],
        "answer": 1,
        "explanation": "APA references are alphabetised by the first author's surname, followed by initials.",
    },
    {
        "key": "english",
        "topic": "Presentation skills",
        "question": "The most effective way to open a presentation is to:",
        "options": ["Read your slides aloud", "Tell a relevant story or pose a question", "List every source", "Apologise for being nervous"],
        "answer": 1,
        "explanation": "A story or question creates a reason to listen and makes your message relevant.",
    },
    {
        "key": "english",
        "topic": "Argumentation",
        "question": "A counterargument is most useful when you:",
        "options": ["Ignore it", "Acknowledge and respond to it", "End the essay with it", "Replace your thesis with it"],
        "answer": 1,
        "explanation": "Addressing a genuine objection demonstrates critical thinking and strengthens your position.",
    },
    {
        "key": "generic",
        "topic": "Active recall",
        "question": "Which revision method is most likely to improve long-term retention?",
        "options": ["Rereading notes", "Highlighting the textbook", "Spaced active recall", "Listening to lectures once"],
        "answer": 2,
        "explanation": "Retrieving answers over spaced intervals builds durable memory far more effectively than rereading.",
    },
    {
        "key": "generic",
        "topic": "Time management",
        "question": "An effective first step in planning a study week is to:",
        "options": ["Study every subject equally", "List deadlines and rank them by urgency and value", "Wait for motivation", "Only study your easiest subject"],
        "answer": 1,
        "explanation": "Prioritising by both urgency and importance makes your limited hours count.",
    },
    {
        "key": "generic",
        "topic": "Wellbeing",
        "question": "A healthy way to handle an overwhelming study list is to:",
        "options": ["Skip sleeping", "Break tasks into small blocks with short movement breaks", "Study all night before each deadline", "Avoid planning"],
        "answer": 1,
        "explanation": "Small, specific blocks plus real breaks make progress visible and protect focus.",
    },
]

DIFFICULTY_COUNTS = {"Quick recall": 3, "Standard": 5, "Deep practice": 8}


def subject_key(subject_name: str) -> str:
    name = (subject_name or "").lower()
    if "math" in name:
        return "math"
    if any(word in name for word in ("data", "algorithm", "comput")):
        return "data"
    if "phys" in name:
        return "physics"
    if any(word in name for word in ("english", "communicat", "literature")):
        return "english"
    return "generic"


def generate_quiz(subject_name: str, difficulty: str = "Standard", count: int | None = None) -> list[dict]:
    """Draw a mixed quiz, weighted toward the chosen subject."""
    count = max(1, min(10, count or DIFFICULTY_COUNTS.get(difficulty, 5)))
    key = subject_key(subject_name)
    own = [question for question in QUIZ_BANK if question["key"] == key]
    generic = [question for question in QUIZ_BANK if question["key"] == "generic"]
    others = [question for question in QUIZ_BANK if question["key"] not in (key, "generic")]

    pool = random.sample(own, len(own)) + random.sample(generic, len(generic)) + random.sample(others, len(others))
    selected = pool[:count]
    quiz = []
    for index, question in enumerate(selected):
        quiz.append({**question, "id": f"{key}-{index}-{random.randint(1000, 9999)}"})
    return quiz


def score_quiz(questions: list[dict], answers: list[int]) -> dict:
    score = 0
    review = []
    for index, question in enumerate(questions):
        selected = answers[index] if index < len(answers) else -1
        correct = selected == question["answer"]
        if correct:
            score += 1
        review.append(
            {
                "question": question["question"],
                "selected": selected,
                "correct_index": question["answer"],
                "selected_text": question["options"][selected] if 0 <= selected < len(question["options"]) else "No answer",
                "correct_text": question["options"][question["answer"]],
                "explanation": question["explanation"],
                "topic": question["topic"],
                "correct": correct,
            }
        )
    total = len(questions)
    percent = round((score / total) * 100) if total else 0
    if percent >= 80:
        message = "Strong recall — that knowledge is settling in."
    elif percent >= 60:
        message = "A solid base, with a little room to grow."
    else:
        message = "Every attempt is useful. Let's turn this into progress."
    return {"score": score, "total": total, "percent": percent, "message": message, "review": review}


def feedback_for(percent: int) -> str:
    if percent >= 80:
        return "Try the next difficulty or revisit this set tomorrow to make the learning durable."
    if percent >= 60:
        return "Review the explanations for the questions you missed, then try again in 24 hours."
    return "Read each explanation carefully, revisit one syllabus topic, and retake a shorter quiz."
