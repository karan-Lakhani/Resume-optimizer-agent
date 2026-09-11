from src.common.schemas import (
    ResumeProfile, PersonalInformation, SkillEntry, EvidenceLevel,
    ExperienceEntry, EducationEntry, ProjectEntry, Link, MiscEntry,
)

resume = ResumeProfile(
    personal_information=PersonalInformation(
        full_name="Karan Lakhani",
        email="karanlakhani2712@gmail.com",
        phone="+91 7425902961",
    ),
    links=[
        Link(label="LinkedIn", url="linkedin.com/in/karanlkhani"),
        Link(label="GitHub", url="github.com/karan-Lakhani"),
        Link(label="Portfolio", url="karan-lakhani.vercel.app"),
    ],
    education=[
        EducationEntry(
            institution="Christ University",
            degree="Bachelor of Science in Data Science",
            start_date="Aug 2022",
            end_date="Jun 2025",
            coursework=["Python Programming", "Machine Learning", "Deep Learning"],
        )
    ],
    experience=[
        ExperienceEntry(
            job_title="Data Analysis Intern",
            company="Future Algorithms Pvt. Ltd.",
            start_date="Feb 2025",
            end_date="May 2025",
            responsibilities=[
                "Designed and developed interactive Power BI dashboards to monitor real-time KPIs across multiple manufacturing plants.",
                "Built end-to-end SQL-based ETL pipelines to extract, transform, and load production data into Power BI.",
            ],
            technologies=["Power BI", "SQL"],
        )
    ],
    projects=[
        ProjectEntry(
            name="Human Emotion Detection",
            description=["Compared four image preprocessing techniques on the CK+48 dataset."],
            technologies=["Python", "CNN", "OpenCV"],
        )
    ],
    skills=[
        SkillEntry(name="Python", evidence_level=EvidenceLevel.STRONG),
        SkillEntry(name="SQL", evidence_level=EvidenceLevel.STRONG),
    ],
    additional_sections=[
        MiscEntry(
            section_title="Leadership",
            title="Department Representative & Event Head",
            organization="Data Science Department / University Tech Fest",
            bullets=[
                "Represented the Data Science department at multiple intercollegiate technical events.",
                "Led a university-wide strategy event with 100+ participants.",
            ],
        ),
        MiscEntry(
            section_title="Leadership",
            title="Class Representative & Team Member",
            organization="Semester V / Sports & Cultural Teams",
            bullets=[
                "Acted as liaison for 50+ students, coordinating communication with faculty.",
                "Active member of the Table Tennis Team and SWO Cultural & Literary Team.",
            ],
        ),
    ],
)

print(resume.personal_information.full_name)
print(f"Education entries: {len(resume.education)}")
print(f"Experience entries: {len(resume.experience)}")
print(f"Leadership entries: {len(resume.additional_sections)}")
print(resume.model_dump_json(indent=2))