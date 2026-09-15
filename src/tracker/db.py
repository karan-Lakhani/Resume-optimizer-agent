from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.tracker.models import Base

engine = create_engine("sqlite:///./data/career_agent.db")

SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)