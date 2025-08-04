from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# SQLAlchemy Engine
engine = create_engine(settings.DATABASE_URL)

# DB session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
