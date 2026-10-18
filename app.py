"""StudyPlanner AI — student study planner.

This is the single Streamlit entry point. The app opens directly on the
student dashboard; all navigation is student-facing.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="StudyPlanner AI — Student Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "StudyPlanner AI · A calmer way to plan your study.",
    },
)

import database  # noqa: E402
import planner  # noqa: E402

database.init_db()

from views import (  # noqa: E402
    components,
    dashboard,
    history,
    performance,
    profile as profile_view,
    quiz as quiz_view,
    settings as settings_view,
    subjects as subjects_view,
    syllabus as syllabus_view,
    timetable as timetable_view,
)

BASE_DIR = Path(__file__).resolve().parent
CSS_PATH = BASE_DIR / "assets" / "styles.css"
if CSS_PATH.exists():
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

PAGES = {
    "Dashboard": ("LayoutDashboard", dashboard),
    "Student Profile": ("UserRound", profile_view),
    "Subjects": ("BookOpen", subjects_view),
    "Syllabus Tracker": ("ListChecks", syllabus_view),
    "AI Timetable": ("CalendarDays", timetable_view),
    "Performance Analysis": ("ChartLine", performance),
    "Revision & Quiz": ("BrainCircuit", quiz_view),
    "Study History": ("History", history),
    "Settings & Help": ("Settings", settings_view),
}

NAV_GROUPS = [
    ("Workspace", ["Dashboard", "Student Profile", "Subjects", "Syllabus Tracker", "AI Timetable"]),
    ("Learn & review", ["Performance Analysis", "Revision & Quiz", "Study History"]),
    ("Account", ["Settings & Help"]),
]

NAV_ICONS = {
    "Dashboard": '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
    "Student Profile": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "Subjects": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
    "Syllabus Tracker": '<path d="m3 6 2 2 3-3M3 14l2 2 3-3M3 22l2-2 3 3"/><path d="M13 6h8M13 14h8M13 22h8"/>',
    "AI Timetable": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "Performance Analysis": '<path d="M3 3v18h18"/><path d="m7 14 4-4 3 3 5-6"/>',
    "Revision & Quiz": '<path d="M9.5 2a2.5 2.5 0 0 0-2.5 2.5v.2A2.5 2.5 0 0 0 4.5 7v1A2.5 2.5 0 0 0 3 10.5v3A2.5 2.5 0 0 0 5.5 16H6v2.5A2.5 2.5 0 0 0 8.5 21h1a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2Z"/><path d="M14.5 2A2.5 2.5 0 0 1 17 4.5v.2A2.5 2.5 0 0 1 19.5 7v1A2.5 2.5 0 0 1 21 10.5v3A2.5 2.5 0 0 1 18.5 16H18v2.5a2.5 2.5 0 0 1-2.5 2.5h-1a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/>',
    "Study History": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5M12 7v5l4 2"/>',
    "Settings & Help": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/>',
}


def brand_markup() -> str:
    return (
        '<div class="sb-brand">'
        '<div class="sb-logo">'
        '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"><path d="M22 10 12 5 2 10l10 5 10-5Z"/>'
        '<path d="M6 12v5c0 1 2.5 3 6 3s6-2 6-3v-5"/><path d="M22 10v6"/></svg>'
        "</div>"
        '<div class="sb-wordmark"><div><strong>StudyPlanner</strong><span>AI</span></div>'
        '<small>LEARN WITH INTENT</small></div></div>'
    )


def sidebar_render() -> None:
    profile = database.get_profile()
    hours = planner.weekly_hours()
    goal = float(profile.get("weekly_goal", 20) or 20)
    percent = min(100, round((hours / goal) * 100)) if goal else 0
    initial = "".join(part[0].upper() for part in (profile.get("name") or "Student").split()[:2])

    with st.sidebar:
        st.markdown(brand_markup(), unsafe_allow_html=True)
        st.markdown(
            '<div class="sb-profile">'
            f'<span class="sb-avatar">{initial}</span>'
            '<div><strong>' + components.safe(profile.get("name") or "Student") + "</strong>"
            "<small>" + components.safe(profile.get("course") or "Your study profile") + " · "
            + components.safe(profile.get("year") or "") + "</small></div>"
            "</div>",
            unsafe_allow_html=True,
        )

        for group, pages in NAV_GROUPS:
            st.markdown(f'<p class="sb-group">{group}</p>', unsafe_allow_html=True)
            for page in pages:
                icon_paths = NAV_ICONS.get(page, NAV_ICONS["Dashboard"])
                label = (
                    f'<span class="sb-nav-label"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" '
                    f'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
                    f"{icon_paths}</svg>{page}</span>"
                )
                if st.button(
                    page,
                    key=f"nav_{page}",
                    use_container_width=True,
                    type="primary" if st.session_state.get("page") == page else "secondary",
                    help=None,
                ):
                    st.session_state.page = page
                    st.rerun()
                # CSS targets each button's visible label; the accessible label remains the page name.

        st.markdown(
            '<div class="sb-focus">'
            '<div class="sb-focus-top"><div>'
            '<p>◆ WEEKLY FOCUS</p>'
            f'<strong>{hours:.1f}<span> / {int(goal)} hrs</span></strong>'
            f'<small>{percent}% of your weekly goal</small></div>'
            f'<div class="sb-ring"><svg width="52" height="52" viewBox="0 0 52 52">'
            '<circle cx="26" cy="26" r="21" fill="none" stroke="rgba(255,255,255,.13)" stroke-width="4"/>'
            f'<circle cx="26" cy="26" r="21" fill="none" stroke="#7dd3fc" stroke-width="4" stroke-linecap="round" '
            f'stroke-dasharray="131.95" stroke-dashoffset="{131.95 - (percent / 100) * 131.95:.1f}" transform="rotate(-90 26 26)"/>'
            "</svg></div></div>"
            '<div class="sb-focus-bar"><span style="width:' + str(percent) + '%"></span></div>'
            '<p class="sb-focus-note">Small steps, repeated, become strong results.</p>'
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sb-footer"><span>●</span> Your study space is ready</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    if "page" not in st.session_state or st.session_state.page not in PAGES:
        st.session_state.page = "Dashboard"
    sidebar_render()
    _, module = PAGES[st.session_state.page]
    module.render()


main()
