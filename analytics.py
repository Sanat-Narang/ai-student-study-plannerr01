"""Plotly charts for StudyPlanner AI.

Charts use the same dark navy palette as the Streamlit interface: transparent
plot surfaces, slate gridlines, white primary labels, and light gray ticks.
"""

from __future__ import annotations

import plotly.graph_objects as go

import database
import planner

BLUE = "#3B82F6"
NAVY = "#F8FAFC"
MUTED = "#CBD5E1"
SUBTLE = "#94A3B8"
GRID = "#2B3A50"
PALETTE = ["#3B82F6", "#A78BFA", "#22D3EE", "#FBBF24", "#34D399", "#F472B6"]

FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"


def _clean_layout(height: int = 260, show_legend: bool = False) -> dict:
    return {
        "height": height,
        "margin": {"l": 12, "r": 12, "t": 18, "b": 22},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": FONT, "color": "#CBD5E1", "size": 11},
        "showlegend": show_legend,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "x": 0,
            "font": {"size": 10, "color": MUTED},
        },
        "hoverlabel": {
            "bgcolor": "#1B2940",
            "font": {"color": "#F8FAFC", "family": FONT, "size": 11},
            "bordercolor": "#334155",
        },
    }


def study_activity_figure(activity: list[dict] | None = None, days: int = 7) -> go.Figure:
    activity = activity if activity is not None else planner.daily_activity(days)
    labels = [point["label"] for point in activity]
    hours = [point["hours"] for point in activity]
    dates = [point["date"] for point in activity]
    figure = go.Figure(
        go.Scatter(
            x=labels,
            y=hours,
            mode="lines+markers",
            line={"color": BLUE, "width": 2.5, "shape": "spline", "smoothing": 1.1},
            marker={"size": 6, "color": "#0B1220", "line": {"color": BLUE, "width": 2}},
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.16)",
            customdata=dates,
            hovertemplate="%{customdata}<br><b>%{y}h</b> studied<extra></extra>",
            name="Study hours",
        )
    )
    layout = _clean_layout(height=245)
    layout.update(
        {
            "xaxis": {
                "showgrid": False,
                "zeroline": False,
                "tickfont": {"size": 10, "color": MUTED},
                "fixedrange": True,
            },
            "yaxis": {
                "showgrid": True,
                "gridcolor": GRID,
                "gridwidth": 1,
                "zeroline": False,
                "ticksuffix": "h",
                "tickfont": {"size": 9, "color": SUBTLE},
                "fixedrange": True,
                "rangemode": "tozero",
            },
        }
    )
    figure.update_layout(**layout)
    return figure


def subject_mastery_figure(subjects: list[dict] | None = None) -> go.Figure:
    subjects = subjects if subjects is not None else database.list_subjects()
    subjects = list(reversed(subjects))
    figure = go.Figure(
        go.Bar(
            x=[subject.get("progress", 0) for subject in subjects],
            y=[subject["code"] or subject["name"] for subject in subjects],
            orientation="h",
            marker={
                "color": [subject.get("color", BLUE) for subject in subjects],
                "cornerradius": 6,
            },
            text=[f"{subject.get('progress', 0)}%" for subject in subjects],
            textposition="outside",
            textfont={"size": 10, "color": "#F8FAFC"},
            hovertemplate="<b>%{y}</b><br>%{x}% complete<extra></extra>",
            cliponaxis=False,
        )
    )
    layout = _clean_layout(height=max(190, len(subjects) * 42))
    layout.update(
        {
            "xaxis": {
                "range": [0, 112],
                "showgrid": True,
                "gridcolor": GRID,
                "zeroline": False,
                "ticksuffix": "%",
                "tickfont": {"size": 9, "color": SUBTLE},
                "fixedrange": True,
            },
            "yaxis": {
                "showgrid": False,
                "tickfont": {"size": 10, "color": "#CBD5E1"},
                "fixedrange": True,
            },
        }
    )
    figure.update_layout(**layout)
    return figure


def quiz_accuracy_figure(attempts: list[dict] | None = None) -> go.Figure:
    attempts = attempts if attempts is not None else database.list_attempts()
    score = sum(int(attempt["score"]) for attempt in attempts)
    total = sum(int(attempt["total"]) for attempt in attempts)
    correct = score
    missed = max(0, total - score)
    values = [correct, missed] if total else [1]
    labels = ["Correct answers", "Needs another look"] if total else ["No attempts yet"]
    colors = [BLUE, "#27364D"] if total else ["#27364D"]
    figure = go.Figure(
        go.Pie(
            values=values,
            labels=labels,
            hole=0.72,
            marker={"colors": colors, "line": {"color": "#111C2E", "width": 2}},
            textinfo="none",
            hovertemplate="%{label}: %{value}<extra></extra>",
            sort=False,
        )
    )
    layout = _clean_layout(height=160, show_legend=False)
    layout.update({"margin": {"l": 4, "r": 4, "t": 4, "b": 4}})
    figure.update_layout(**layout)
    if total:
        figure.add_annotation(
            text=f"<b>{round((score / total) * 100)}%</b><br><span style='font-size:9px;color:{MUTED}'>accuracy</span>",
            showarrow=False,
            font={"size": 19, "color": NAVY, "family": FONT},
        )
    return figure


def mastery_radar_figure(subjects: list[dict] | None = None) -> go.Figure:
    subjects = subjects if subjects is not None else database.list_subjects()
    labels = [subject["code"] or subject["name"] for subject in subjects]
    values = [subject.get("progress", 0) for subject in subjects]
    if labels:
        labels.append(labels[0])
        values.append(values[0])
    figure = go.Figure(
        go.Scatterpolar(
            r=values,
            theta=labels,
            fill="toself",
            fillcolor="rgba(59,130,246,0.22)",
            line={"color": BLUE, "width": 2},
            marker={"size": 4, "color": "#93C5FD"},
            hovertemplate="<b>%{theta}</b><br>%{r}% mastery<extra></extra>",
        )
    )
    layout = _clean_layout(height=270)
    layout.update(
        {
            "polar": {
                "bgcolor": "rgba(0,0,0,0)",
                "radialaxis": {
                    "visible": True,
                    "range": [0, 100],
                    "showticklabels": False,
                    "gridcolor": GRID,
                    "linecolor": GRID,
                },
                "angularaxis": {
                    "gridcolor": GRID,
                    "linecolor": GRID,
                    "tickfont": {"size": 9, "color": "#CBD5E1"},
                },
            },
            "margin": {"l": 28, "r": 28, "t": 16, "b": 16},
        }
    )
    figure.update_layout(**layout)
    return figure


def exam_readiness_figure(exams: list[dict] | None = None) -> go.Figure:
    exams = exams if exams is not None else database.list_exams()
    figure = go.Figure(
        go.Bar(
            x=[exam["title"] for exam in exams],
            y=[int(exam.get("readiness", 0)) for exam in exams],
            marker={
                "color": [exam.get("subject_color") or BLUE for exam in exams],
                "cornerradius": 6,
            },
            text=[f"{int(exam.get('readiness', 0))}%" for exam in exams],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y}% ready<extra></extra>",
            cliponaxis=False,
        )
    )
    layout = _clean_layout(height=220)
    layout.update(
        {
            "xaxis": {
                "showgrid": False,
                "tickfont": {"size": 9, "color": MUTED},
                "tickangle": -12,
            },
            "yaxis": {
                "range": [0, 112],
                "showgrid": True,
                "gridcolor": GRID,
                "ticksuffix": "%",
                "tickfont": {"size": 9, "color": SUBTLE},
                "zeroline": False,
            },
        }
    )
    figure.update_layout(**layout)
    return figure


def weekly_balance_figure(subjects_with_minutes: list[dict] | None = None) -> go.Figure:
    subjects_with_minutes = subjects_with_minutes if subjects_with_minutes is not None else planner.subject_study_minutes()
    subjects_with_minutes = [subject for subject in subjects_with_minutes if subject.get("minutes")]
    figure = go.Figure(
        go.Pie(
            labels=[subject["name"] for subject in subjects_with_minutes],
            values=[subject["minutes"] for subject in subjects_with_minutes],
            hole=0.62,
            marker={"colors": [subject["color"] for subject in subjects_with_minutes]},
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} minutes<extra></extra>",
            sort=False,
        )
    )
    layout = _clean_layout(height=240, show_legend=True)
    layout.update({"margin": {"l": 8, "r": 8, "t": 8, "b": 8}})
    figure.update_layout(**layout)
    return figure
