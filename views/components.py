"""Reusable HTML presentation helpers for the Streamlit interface."""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import planner

# Inline line icons keep the interface lightweight and consistent without image requests.
ICON_PATHS = {
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "flame": '<path d="M12 22c4 0 7-3 7-7 0-3-2-5-3-7-1-2-1-4-1-5-3 1-5 4-5 7 0 1 0 2 1 3-1 0-2-1-2-3-2 2-4 4-4 7 0 3 3 5 7 5Z"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 14 4-4 3 3 5-6"/>',
    "sparkles": '<path d="m12 3 1.9 4.6L18.5 9.5l-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9L12 3Z"/><path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
    "brain": '<path d="M9.5 2a2.5 2.5 0 0 0-2.5 2.5v.2A2.5 2.5 0 0 0 4.5 7v1A2.5 2.5 0 0 0 3 10.5v3A2.5 2.5 0 0 0 5.5 16H6v2.5A2.5 2.5 0 0 0 8.5 21h1a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2Z"/><path d="M14.5 2A2.5 2.5 0 0 1 17 4.5v.2A2.5 2.5 0 0 1 19.5 7v1A2.5 2.5 0 0 1 21 10.5v3A2.5 2.5 0 0 1 18.5 16H18v2.5a2.5 2.5 0 0 1-2.5 2.5h-1a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/>',
    "clock3": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5h4"/>',
    "lightbulb": '<path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12c1 1 1 2 1 3h6c0-1 0-2 1-3a7 7 0 0 0-4-12Z"/>',
    "list": '<path d="m3 6 2 2 3-3M3 14l2 2 3-3M3 22l2-2 3 3"/><path d="M13 6h8M13 14h8M13 22h8"/>',
    "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 21 2c0 4-1 9-3 12-2 2-4 3-7 3Z"/><path d="M2 22c4-8 8-12 15-16"/>',
}

TONES = {
    "blue": ("rgba(59, 130, 246, 0.16)", "#93C5FD"),
    "amber": ("rgba(245, 158, 11, 0.15)", "#FCD34D"),
    "violet": ("rgba(139, 92, 246, 0.16)", "#C4B5FD"),
    "green": ("rgba(16, 185, 129, 0.15)", "#6EE7B7"),
    "rose": ("rgba(244, 63, 94, 0.15)", "#FDA4AF"),
    "cyan": ("rgba(6, 182, 212, 0.15)", "#67E8F9"),
    "slate": ("rgba(148, 163, 184, 0.13)", "#CBD5E1"),
}


def safe(value: Any) -> str:
    return escape(str(value if value is not None else ""))


def icon(name: str, size: int = 16, stroke: float = 1.9) -> str:
    paths = ICON_PATHS.get(name, ICON_PATHS["sparkles"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{paths}</svg>'
    )


def icon_tile(name: str, tone: str = "blue", size: int = 32) -> str:
    background, foreground = TONES.get(tone, TONES["blue"])
    return (
        f'<span class="icon-tile" style="width:{size}px;height:{size}px;'
        f'background:{background};color:{foreground}">{icon(name, size=round(size * 0.48))}</span>'
    )


def badge(text: str, tone: str = "slate") -> str:
    colors = {
        "blue": ("rgba(59, 130, 246, 0.18)", "#93C5FD"),
        "green": ("rgba(16, 185, 129, 0.16)", "#6EE7B7"),
        "amber": ("rgba(245, 158, 11, 0.16)", "#FCD34D"),
        "rose": ("rgba(244, 63, 94, 0.16)", "#FDA4AF"),
        "violet": ("rgba(139, 92, 246, 0.17)", "#C4B5FD"),
        "slate": ("rgba(148, 163, 184, 0.13)", "#CBD5E1"),
    }
    background, foreground = colors.get(tone, colors["slate"])
    return f'<span class="badge" style="background:{background};color:{foreground}">{safe(text)}</span>'


def page_header(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    eyebrow_html = (
        f'<p class="page-eyebrow"><span class="eyebrow-dot"></span>{safe(eyebrow)}</p>' if eyebrow else ""
    )
    st_html(
        f'<div class="page-header">{eyebrow_html}'
        f'<h1 class="page-title">{safe(title)}</h1>'
        f'<p class="page-subtitle">{safe(subtitle)}</p></div>'
    )


def st_html(markup: str) -> None:
    import streamlit as st

    st.markdown(markup, unsafe_allow_html=True)


def metric_grid(items: list[dict]) -> None:
    cards = []
    for item in items:
        background, foreground = TONES.get(item.get("tone", "blue"), TONES["blue"])
        suffix = (
            f'<span class="metric-suffix">{safe(item["suffix"])}</span>' if item.get("suffix") else ""
        )
        hint = f'<p class="metric-hint">{safe(item["hint"])}</p>' if item.get("hint") else ""
        cards.append(
            '<div class="metric-card">'
            '<div class="metric-top">'
            f'<p class="metric-label">{safe(item["label"])}</p>'
            f'<span class="icon-tile" style="background:{background};color:{foreground}">'
            f'{icon(item.get("icon", "chart"), 16)}</span>'
            "</div>"
            f'<div class="metric-value-row"><span class="metric-value">{safe(item["value"])}</span>{suffix}</div>'
            f"{hint}</div>"
        )
    st_html(f'<div class="metric-grid">{"".join(cards)}</div>')


def section_head(title: str, subtitle: str = "", icon_name: str = "sparkles", badge_html: str = "") -> None:
    subtitle_html = f'<p class="section-subtitle">{safe(subtitle)}</p>' if subtitle else ""
    st_html(
        '<div class="section-head">'
        f'<div class="section-head-main">{icon_tile(icon_name, "blue", 30)}'
        f'<div><h2 class="section-title">{safe(title)}</h2>{subtitle_html}</div></div>'
        f'<div>{badge_html}</div>'
        "</div>"
    )


def card_title(title: str, subtitle: str = "", icon_name: str = "sparkles", badge_html: str = "") -> None:
    section_head(title, subtitle, icon_name, badge_html)


def progress_html(percent: int | float, color: str = "#3B82F6", height: int = 6) -> str:
    value = max(0, min(100, int(percent or 0)))
    return (
        f'<div class="progress-track" style="height:{height}px">'
        f'<div class="progress-fill" style="width:{value}%;background:{safe(color)}"></div></div>'
    )


def ring_html(percent: int | float, size: int = 62, color: str = "#60A5FA", track: str = "rgba(203,213,225,.18)", label: str = "") -> str:
    value = max(0, min(100, int(percent or 0)))
    radius = (size - 7) / 2
    circumference = 2 * 3.14159 * radius
    offset = circumference - (value / 100) * circumference
    caption = f'<span class="ring-label">{safe(label)}</span>' if label else ""
    return (
        f'<div class="ring" style="width:{size}px;height:{size}px">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
        f'<circle cx="{size / 2}" cy="{size / 2}" r="{radius}" fill="none" stroke="{track}" stroke-width="5"/>'
        f'<circle cx="{size / 2}" cy="{size / 2}" r="{radius}" fill="none" stroke="{color}" stroke-width="5" '
        f'stroke-linecap="round" stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}" '
        f'transform="rotate(-90 {size / 2} {size / 2})"/></svg>{caption}</div>'
    )


def subject_progress_rows(subjects: list[dict], limit: int | None = None) -> str:
    rows = []
    for subject in subjects[: limit or len(subjects)]:
        rows.append(
            '<div class="subject-progress-row">'
            '<div class="subject-progress-top">'
            '<span class="subject-mini" style="background:' + safe(subject["color"]) + '">'
            + safe((subject["code"] or "SUB").split(" ")[0][:3])
            + "</span>"
            '<span class="subject-progress-name">' + safe(subject["name"]) + "</span>"
            '<span class="subject-progress-meta">' + str(subject.get("topic_completed", 0)) + "/" + str(subject.get("topic_total", 0)) + " topics</span>"
            '<span class="subject-progress-percent">' + str(subject.get("progress", 0)) + "%</span>"
            "</div>"
            + progress_html(subject.get("progress", 0), subject["color"], 5)
            + "</div>"
        )
    return "".join(rows) or '<p class="muted-copy">Add a subject to see your progress here.</p>'


def focus_card(profile: dict, hours: float, percent: int) -> None:
    goal = profile.get("weekly_goal", 20) or 20
    st_html(
        '<div class="focus-card">'
        '<div class="focus-card-top"><div>'
        '<p class="focus-eyebrow">◆ Weekly focus</p>'
        f'<p class="focus-percent">{percent}%</p>'
        f'<p class="focus-caption">of your {int(goal)}-hour goal</p></div>'
        + ring_html(percent, 66, "#7dd3fc", "rgba(255,255,255,.14)", "AI plan")
        + "</div>"
        '<div class="focus-stats">'
        f'<div class="focus-stat"><span>Studied</span><strong>{hours:.1f} hrs</strong></div>'
        f'<div class="focus-stat"><span>Remaining</span><strong>{max(0, round(goal - hours, 1))} hrs</strong></div>'
        "</div>"
        '<div class="focus-bar"><span style="width:' + str(min(100, int(percent))) + '%"></span></div>'
        '<div class="focus-note">A balanced plan beats a perfect one. Your timetable is ready to adapt.</div>'
        "</div>"
    )


def exam_outlook(exams: list[dict], limit: int = 3) -> str:
    if not exams:
        return (
            '<div class="empty-inline">'
            '<p class="empty-inline-title">No assessments scheduled</p>'
            '<p class="muted-copy">Add your next quiz or exam so your plan can make room for it.</p>'
            "</div>"
        )
    items = []
    for exam in exams[:limit]:
        color = exam.get("subject_color") or "#2563eb"
        items.append(
            '<div class="exam-item">'
            f'<div class="exam-date" style="background:rgba(59,130,246,.13);color:#F8FAFC;border:1px solid {safe(color)}55">'
            f'<span>{safe(planner.format_date(exam["exam_date"], False).split(" ")[0])}</span>'
            f'<strong>{safe(planner.format_date(exam["exam_date"], False).split(" ")[-1])}</strong></div>'
            '<div class="exam-body">'
            f'<p class="exam-title">{safe(exam["title"])}</p>'
            f'<p class="exam-meta">{safe(exam.get("subject_name", ""))} · {safe(exam["start_time"])}</p>'
            f'<div class="exam-readiness">{progress_html(exam.get("readiness", 0), color, 3)}'
            f'<span>{int(exam.get("readiness", 0))}% ready</span></div>'
            f'</div><div class="exam-when">{safe(planner.countdown_label(exam["exam_date"]))}</div>'
            "</div>"
        )
    return '<div class="exam-list">' + "".join(items) + "</div>"


def empty_state(title: str, text: str, icon_name: str = "calendar", hint: str = "") -> None:
    hint_html = f'<p class="empty-hint">{safe(hint)}</p>' if hint else ""
    st_html(
        '<div class="empty-state">'
        f'<div class="empty-icon">{icon(icon_name, 22)}</div>'
        f'<h3>{safe(title)}</h3><p>{safe(text)}</p>{hint_html}</div>'
    )


def insight_card(title: str, text: str, icon_name: str = "sparkles") -> None:
    st_html(
        '<div class="insight-card">'
        f'<div class="insight-icon">{icon(icon_name, 16)}</div>'
        f'<div><p class="insight-eyebrow">One useful insight</p>'
        f'<h3>{safe(title)}</h3><p>{safe(text)}</p></div></div>'
    )


def weekly_focus_banner(blocks: int, minutes: int, completed: int) -> None:
    st_html(
        '<div class="planning-banner">'
        '<div class="planning-copy"><div class="planning-icon">' + icon("sparkles", 18) + "</div>"
        '<div><p class="planning-eyebrow">Your planning assistant</p>'
        '<h2>A balanced week, without the guesswork.</h2>'
        '<p>New study blocks prioritise the assessments closest to you, rotate your unfinished topics, and respect your study preferences.</p>'
        "</div></div>"
        '<div class="planning-stats">'
        f'<div><strong>{blocks}</strong><span>Blocks</span></div>'
        f'<div><strong>{planner.hours_label(minutes)}</strong><span>Planned</span></div>'
        f'<div><strong>{completed}</strong><span>Complete</span></div>'
        "</div></div>"
    )


def avatar_html(name: str, size: int = 54) -> str:
    initials = "".join(part[0].upper() for part in (name or "Student").split()[:2]) or "S"
    return (
        f'<span class="profile-avatar" style="width:{size}px;height:{size}px;font-size:{round(size * 0.32)}px">'
        f"{safe(initials)}</span>"
    )


def status_badge(status: str) -> str:
    mapping = {
        "completed": ("Completed", "green"),
        "in-progress": ("In progress", "amber"),
        "not-started": ("Not started", "slate"),
    }
    label, tone = mapping.get(status, ("Not started", "slate"))
    return badge(label, tone)


def member_since() -> str:
    return datetime.now().strftime("%b %Y")
