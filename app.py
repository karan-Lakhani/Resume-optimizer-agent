from pathlib import Path

import streamlit as st

from src.job_application.profile_service import get_current_profile, save_parsed_profile
from src.tracker.db import init_db

UPLOADS_DIR = Path("data/uploads")


def as_href(url: str) -> str:
    """Resume text often omits the scheme (e.g. "linkedin.com/in/x") — add one so links are clickable."""
    return url if url.startswith(("http://", "https://")) else f"https://{url}"

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

    uploaded_file = st.file_uploader("Upload your master resume (PDF)", type="pdf")

    if uploaded_file is not None:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = UPLOADS_DIR / uploaded_file.name
        pdf_path.write_bytes(uploaded_file.getvalue())

        with st.spinner("Parsing resume..."):
            try:
                profile = save_parsed_profile(str(pdf_path))
                st.success("Resume parsed and saved.")
            except Exception as e:
                st.error(f"Failed to parse resume: {e}")
                profile = None
    else:
        profile = get_current_profile()

    if profile and profile.parsed_json:
        data = profile.parsed_json
        personal = data.get("personal_information", {})

        st.subheader(personal.get("full_name", "—"))
        st.caption(
            " | ".join(
                filter(None, [personal.get("email"), personal.get("phone"), personal.get("location")])
            )
        )

        links = data.get("links", [])
        if links:
            st.markdown(
                " · ".join(
                    f"[{link.get('label')}]({as_href(link['url'])})"
                    for link in links
                    if link.get("url")
                )
            )

        if data.get("summary"):
            st.write(data["summary"])

        st.markdown("#### Experience")
        for exp in data.get("experience", []):
            st.markdown(f"**{exp.get('job_title')}** — {exp.get('company')}")
            st.caption(f"{exp.get('start_date')} – {exp.get('end_date') or 'Present'}")
            for bullet in exp.get("responsibilities", []):
                st.markdown(f"- {bullet}")

        st.markdown("#### Education")
        for edu in data.get("education", []):
            st.markdown(f"**{edu.get('institution')}** — {edu.get('degree')} in {edu.get('field_of_study')}")

        st.markdown("#### Projects")
        for proj in data.get("projects", []):
            title = proj.get("name", "")
            if proj.get("link"):
                title = f"[{title}]({as_href(proj['link'])})"
            st.markdown(f"**{title}**")
            if proj.get("technologies"):
                st.caption(", ".join(proj["technologies"]))
            for line in proj.get("description", []):
                st.markdown(f"- {line}")

        st.markdown("#### Skills")
        st.write(", ".join(skill.get("name", "") for skill in data.get("skills", [])))

        certifications = data.get("certifications", [])
        if certifications:
            st.markdown("#### Certifications")
            for cert in certifications:
                line = cert.get("name", "")
                if cert.get("issuer"):
                    line += f" — {cert['issuer']}"
                if cert.get("date_earned"):
                    line += f" ({cert['date_earned']})"
                st.markdown(f"- {line}")

        additional_sections = data.get("additional_sections", [])
        if additional_sections:
            for section_title in dict.fromkeys(s.get("section_title", "Additional") for s in additional_sections):
                st.markdown(f"#### {section_title}")
                for entry in additional_sections:
                    if entry.get("section_title") != section_title:
                        continue
                    heading = " — ".join(filter(None, [entry.get("title"), entry.get("organization")]))
                    if heading:
                        st.markdown(f"**{heading}**")
                    if entry.get("dates"):
                        st.caption(entry["dates"])
                    for bullet in entry.get("bullets", []):
                        st.markdown(f"- {bullet}")
    elif uploaded_file is None:
        st.info("No profile yet — upload your resume above to get started.")

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