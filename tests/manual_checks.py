from src.common.schemas import EducationEntry

edu = EducationEntry(
    institution="Christ University",
    degree="Bachelor of Science in Data Science",
    start_date="Aug 2022",
    end_date="Jun 2025",
    is_present=False,
    coursework=[
        "Python Programming",
        "Exploratory Data Analysis",
        "Data Visualization",
        "Database Management Systems (SQL and NoSQL)",
        "Machine Learning",
        "Deep Learning",
        "Image Processing",
        "Artificial Intelligence",
    ],
)
print(edu)