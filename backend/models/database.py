from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    crawl_sessions = relationship("CrawlSession", back_populates="project")


class CrawlSession(Base):
    __tablename__ = "crawl_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Configuration
    max_urls = Column(Integer, default=100)
    max_depth = Column(Integer, default=3)
    delay = Column(Float, default=1.0)
    render_javascript = Column(Boolean, default=True)
    
    # Progress
    crawled_urls = Column(Integer, default=0)
    total_urls = Column(Integer, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="crawl_sessions")
    pages = relationship("Page", back_populates="crawl_session")


class Page(Base):
    __tablename__ = "pages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    crawl_session_id = Column(String, ForeignKey("crawl_sessions.id"), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=True)
    load_time = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    crawl_session = relationship("CrawlSession", back_populates="pages")
    issues = relationship("SEOIssue", back_populates="page")


class SEOIssue(Base):
    __tablename__ = "seo_issues"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String, ForeignKey("pages.id"), nullable=False)
    issue_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    category = Column(String(50), nullable=True)  # technical, content, performance, etc.
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    impact_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    page = relationship("Page", back_populates="issues")