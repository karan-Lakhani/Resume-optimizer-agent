import streamlit as st
from src.tracker.db import init_db

st.set_page_config(
    page_title="AI Career Agent",
    page_icon="💼",
    layout="wide",
)

init_db()

PAGES = [
    "🏠 Dashboard",
    "👤 My Profile",
    "🔎 Job Search",
    "🎯 Recommended Jobs",
    "📄 Resume Versions",
    "✉️ Application Materials",
    "📊 Application Tracker",
    "📈 Job Market Insights",
    "⚙️ Settings",
]

st.sidebar.title("AI Career Agent")
choice = st.sidebar.radio("", PAGES)

if choice == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    st.info("Welcome to your AI Career Agent. Use the sidebar to navigate.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jobs Found", 0)
    col2.metric("Applications", 0)
    col3.metric("Interviews", 0)
    col4.metric("Offers", 0)

elif choice == "👤 My Profile":
    st.title("👤 My Profile")
    st.warning("Coming in Milestone 2 — Resume Parsing.")

elif choice == "🔎 Job Search":
    st.title("🔎 Job Search")
    st.warning("Coming in Milestone 3 — Job Discovery.")

elif choice == "🎯 Recommended Jobs":
    st.title("🎯 Recommended Jobs")
    st.warning("Coming in Milestone 4 — Matching.")

elif choice == "📄 Resume Versions":
    st.title("📄 Resume Versions")
    st.warning("Coming in Milestone 5 — Application Generation.")

elif choice == "✉️ Application Materials":
    st.title("✉️ Application Materials")
    st.warning("Coming in Milestone 5 — Application Generation.")

elif choice == "📊 Application Tracker":
    st.title("📊 Application Tracker")
    st.warning("Coming in Milestone 6 — Tracker.")

elif choice == "📈 Job Market Insights":
    st.title("📈 Job Market Insights")
    st.warning("Coming in Milestone 8 — Intelligence.")

elif choice == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.warning("Coming soon.")