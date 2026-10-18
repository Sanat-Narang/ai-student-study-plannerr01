# StudyPlanner AI

A student-facing AI study planner built with **Python, Streamlit, SQLite, and Plotly**. The application opens directly on the student dashboard and includes a complete planning, progress, revision, and reflection workflow.

Everything a student needs is in the application itself. Installation instructions belong only in this README and never appear inside the website.

## Features

- **Student dashboard first** — no landing page, promotional splash, or setup screen.
- **Student profile** — personal details, learning style, weekly goal, target assessment, and timezone.
- **Subjects** — add, edit, and delete courses with colour, lecturer, credits, target grade, and an assigned assessment.
- **Syllabus tracker** — break subjects into units and topics, track status and confidence, and filter by what needs attention.
- **AI timetable** — generate a balanced seven-day plan from assessment proximity, syllabus progress, available study days, preferred start time, and session length. Export the week as an `.ics` calendar file.
- **Performance analysis** — Plotly charts for study rhythm, subject mastery, exam readiness, and quiz accuracy, with plain-language insights.
- **Revision & quiz** — active-recall quizzes with several depths, immediate explanations, stored attempts, and a full answer review.
- **Study history** — searchable and filterable session log, CSV export, 14-day consistency view, and complete study-mix breakdown.
- **Settings & help** — study rhythm preferences, reminders, student-facing FAQs, JSON data export, and workspace reset.
- **Useful empty states** — each page explains the next useful step and offers a working action when data is missing.
- **Professional student UI** — a consistent dark navy dashboard on every page, a deeper navy sidebar, slate navy cards, lighter navy inputs, electric-blue accents, high-contrast labels, responsive layouts, and no developer documentation in the interface.

The sample workspace is loaded on the very first launch so a new student can see how the planner works. The workspace can be cleared or restored at any time from **Settings & Help**.

## Project structure

```
.
├── app.py                    # Streamlit entry point and navigation shell
├── database.py               # SQLite schema, seed data, and persistence helpers
├── planner.py                # Study plan generation and progress calculations
├── analytics.py              # Plotly figures
├── quiz.py                   # Revision question bank and scoring
├── requirements.txt
├── render.yaml               # Render deployment blueprint
├── .streamlit/
│   └── config.toml           # Application theme
├── assets/
│   ├── styles.css            # Student-facing visual theme
│   └── logo.svg
├── data/                     # SQLite database is created here at runtime
├── views/
│   ├── __init__.py
│   ├── components.py         # Shared cards, icons, headings, and progress display
│   ├── forms.py              # Streamlit dialogs for adding and editing data
│   ├── dashboard.py
│   ├── profile.py
│   ├── subjects.py
│   ├── syllabus.py
│   ├── timetable.py
│   ├── performance.py
│   ├── quiz.py
│   ├── history.py
│   └── settings.py
└── README.md
```

## Local setup

Requirements: Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The application opens at `http://localhost:8501`.

The SQLite database is created automatically at `data/studyplanner.db`. To store it elsewhere, set the `STUDYPLANNER_DB` environment variable to a writable file path.

## Deploy on Render

This repository includes `render.yaml`, so it can be deployed as a Render Blueprint:

1. Push the project to GitHub.
2. In Render, choose **New → Blueprint** and connect the repository.
3. Render reads `render.yaml`, installs dependencies, and starts Streamlit with `$PORT`.
4. Optionally change `STUDYPLANNER_DB` or the service plan in the Render dashboard.

Manual web-service settings:

- **Runtime:** Python
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- **Environment variable:** `PYTHON_VERSION=3.11.9`
- **Database path:** `STUDYPLANNER_DB=/var/data/studyplanner.db` with a persistent disk mounted at `/var/data`

Use a persistent disk if study data must survive a redeploy or a sleeping free instance. Without a disk, SQLite data can be reset by the hosting environment.

## Data and privacy

- All study data is stored locally in SQLite.
- The app does not call an external AI service. Plan generation is a deterministic, explainable algorithm based on deadlines, syllabus progress, and the student's preferences.
- Quiz scoring is local.
- Students can export study data as JSON or study history as CSV at any time.
- The workspace can be reset or loaded with sample content from **Settings & Help**.

## Notes

- There is no Next.js, React, TypeScript, JavaScript framework, or Node.js dependency in this project.
- No developer landing page, installation command, or setup guide appears anywhere in the application UI.
- The app's first screen is the student dashboard.
