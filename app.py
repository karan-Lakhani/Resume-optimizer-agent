from pathlib import Path

import streamlit as st

from src.job_application.profile_service import get_current_profile, save_parsed_profile
from src.job_search.search_service import generate_search_params, run_search, save_job
from src.common.schemas import ResumeProfile
from src.tracker.db import SessionLocal, init_db
from config.settings import get_settings

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

    settings = get_settings()
    if not settings.jsearch_api_key:
        st.error("No `JSEARCH_API_KEY` found in `.env`. Add your OpenWebNinja API key and restart the app.")
    else:
        # --- Auto-fill search params from profile ---
        profile_data = get_current_profile()
        default_params = {"query": "", "location": "", "remote_only": False, "date_posted": "month"}

        if profile_data:
            try:
                profile_obj = ResumeProfile.model_validate(profile_data.parsed_json)
                default_params = generate_search_params(profile_obj)
            except Exception:
                pass  # no profile yet or malformed — fall through to empty defaults

        # Persist search params in session state so the form is sticky.
        # Only initialise once — user's edits are preserved across reruns.
        # "Refresh from profile" button below resets them to current profile.
        if "job_search_query" not in st.session_state:
            st.session_state.job_search_query = default_params["query"]
        if "job_search_location" not in st.session_state:
            st.session_state.job_search_location = default_params["location"]
        if "job_search_remote" not in st.session_state:
            st.session_state.job_search_remote = default_params["remote_only"]
        if "job_search_date" not in st.session_state:
            st.session_state.job_search_date = default_params["date_posted"]

        if profile_data and st.button("↻ Refresh suggestions from profile", type="secondary"):
            st.session_state.job_search_query = default_params["query"]
            st.session_state.job_search_location = default_params["location"]
            st.session_state.job_search_remote = default_params["remote_only"]
            st.session_state.job_search_date = default_params["date_posted"]
            st.rerun()

        # --- Search form ---
        with st.form("job_search_form"):
            col1, col2 = st.columns([3, 2])
            with col1:
                query = st.text_input(
                    "Keywords / Job Title",
                    value=st.session_state.job_search_query,
                    placeholder="e.g. Python Developer, Machine Learning",
                )
            with col2:
                location = st.text_input(
                    "Location",
                    value=st.session_state.job_search_location,
                    placeholder="e.g. New York, Remote",
                )

            col3, col4 = st.columns([1, 2])
            with col3:
                remote_only = st.checkbox("Remote only", value=st.session_state.job_search_remote)
            with col4:
                date_posted = st.selectbox(
                    "Posted within",
                    options=["month", "week", "3days", "today", "all"],
                    index=["month", "week", "3days", "today", "all"].index(
                        st.session_state.job_search_date
                    ),
                )

            submitted = st.form_submit_button("🔍 Search", use_container_width=True)

        if submitted:
            st.session_state.job_search_query = query
            st.session_state.job_search_location = location
            st.session_state.job_search_remote = remote_only
            st.session_state.job_search_date = date_posted

            if not query.strip():
                st.warning("Enter at least a keyword or job title to search.")
            else:
                with st.spinner("Searching jobs…"):
                    try:
                        session = SessionLocal()
                        try:
                            results = run_search(
                                api_key=settings.jsearch_api_key,
                                query=query,
                                location=location,
                                remote_only=remote_only,
                                date_posted=date_posted,
                                session=session,
                            )
                        finally:
                            session.close()
                        st.session_state.job_results = results
                    except Exception as e:
                        st.error(f"Search failed: {e}")
                        st.session_state.job_results = []

        # --- Results ---
        results = st.session_state.get("job_results")
        if results is not None:
            if not results:
                st.info("No jobs found — try broader keywords or a different location.")
            else:
                st.markdown(f"**{len(results)} jobs found**")
                for job in results:
                    with st.container(border=True):
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.markdown(f"### {job['title']}")
                            st.markdown(
                                f"**{job['company']}** &nbsp;·&nbsp; {job['location'] or 'Location not specified'}"
                            )

                            badges = []
                            if job.get("employment_type"):
                                badges.append(job["employment_type"].replace("_", " ").title())
                            if job.get("is_remote"):
                                badges.append("Remote")
                            if job.get("salary_min") or job.get("salary_max"):
                                lo = f"${job['salary_min']:,.0f}" if job.get("salary_min") else ""
                                hi = f"${job['salary_max']:,.0f}" if job.get("salary_max") else ""
                                salary = " – ".join(filter(None, [lo, hi]))
                                badges.append(salary)
                            if badges:
                                st.caption(" · ".join(badges))

                        with c2:
                            if job.get("application_url"):
                                st.link_button("Apply ↗", job["application_url"], use_container_width=True)
                            db_id = job.get("db_id")
                            if db_id:
                                saved_key = f"saved_{db_id}"
                                if st.session_state.get(saved_key):
                                    st.button("✓ Saved", key=f"save_{db_id}", disabled=True, use_container_width=True)
                                else:
                                    if st.button("Save", key=f"save_{db_id}", use_container_width=True):
                                        session = SessionLocal()
                                        try:
                                            save_job(db_id, session)
                                        finally:
                                            session.close()
                                        st.session_state[saved_key] = True
                                        st.toast("Job saved!", icon="✅")
                                        st.rerun()

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