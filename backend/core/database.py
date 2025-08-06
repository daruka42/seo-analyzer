from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database configuration - Updated to match docker-compose.yml
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://seouser:seopassword123@postgres:5432/seo_analyzer"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()