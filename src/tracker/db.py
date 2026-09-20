from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import get_settings
from src.tracker.models import Base

engine = create_engine(get_settings().database_url)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)