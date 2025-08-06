from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from core.database import Base
import uuid


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Enhanced project settings
    default_crawl_config = Column(JSONB, nullable=True)  # Store default crawl configuration
    notification_settings = Column(JSONB, nullable=True)  # Email/webhook notifications
    
    # Project statistics (updated by triggers/background tasks)
    total_pages_crawled = Column(Integer, default=0)
    last_crawl_date = Column(DateTime(timezone=True), nullable=True)
    avg_page_load_time = Column(Float, nullable=True)
    total_issues_found = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    crawl_sessions = relationship("CrawlSession", back_populates="project", cascade="all, delete-orphan")
    competitors = relationship("Competitor", back_populates="project", cascade="all, delete-orphan")
    keywords = relationship("Keyword", back_populates="project", cascade="all, delete-orphan")


class CrawlSession(Base):
    __tablename__ = "crawl_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Enhanced configuration
    max_urls = Column(Integer, default=100)
    max_depth = Column(Integer, default=3)
    delay = Column(Float, default=1.0)
    render_javascript = Column(Boolean, default=True)
    mobile_analysis = Column(Boolean, default=True)
    screenshot_enabled = Column(Boolean, default=False)
    exclude_patterns = Column(ARRAY(String), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Progress tracking
    crawled_urls = Column(Integer, default=0)
    total_urls = Column(Integer, nullable=True)
    failed_urls = Column(Integer, default=0)
    queue_size = Column(Integer, default=0)
    
    # Performance metrics
    avg_load_time = Column(Float, nullable=True)
    total_data_processed = Column(Integer, default=0)  # bytes
    
    # Summary statistics (computed after crawl)
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Relationships
    project = relationship("Project", back_populates="crawl_sessions")
    pages = relationship("Page", back_populates="crawl_session", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    crawl_session_id = Column(String, ForeignKey("crawl_sessions.id"), nullable=False)
    
    # Basic page info
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    h1 = Column(Text, nullable=True)
    status_code = Column(Integer, nullable=True)
    load_time = Column(Float, nullable=True)
    depth = Column(Integer, default=0)
    
    # Content analysis
    word_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    paragraph_count = Column(Integer, nullable=True)
    readability_score = Column(Float, nullable=True)
    content_hash = Column(String(64), nullable=True)  # For duplicate detection
    
    # Link analysis
    internal_links_count = Column(Integer, default=0)
    external_links_count = Column(Integer, default=0)
    
    # Image analysis
    total_images = Column(Integer, default=0)
    images_missing_alt = Column(Integer, default=0)
    
    # Performance data
    page_size = Column(Integer, nullable=True)  # bytes
    performance_metrics = Column(JSONB, nullable=True)  # JS performance data
    
    # Enhanced analysis data
    keyword_density = Column(JSONB, nullable=True)  # Top keywords and density
    entities = Column(JSONB, nullable=True)  # Named entities from NLP
    headings_structure = Column(JSONB, nullable=True)  # H1-H6 structure
    schema_markup = Column(JSONB, nullable=True)  # Structured data
    social_tags = Column(JSONB, nullable=True)  # OG, Twitter cards
    mobile_analysis = Column(JSONB, nullable=True)  # Mobile-specific data
    
    # Technical SEO
    canonical_url = Column(Text, nullable=True)
    robots_meta = Column(String(255), nullable=True)
    lang_attribute = Column(String(10), nullable=True)
    
    # File paths
    screenshot_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    crawl_session = relationship("CrawlSession", back_populates="pages")
    issues = relationship("SEOIssue", back_populates="page", cascade="all, delete-orphan")
    links_from = relationship("PageLink", foreign_keys="PageLink.source_page_id", back_populates="source_page")
    links_to = relationship("PageLink", foreign_keys="PageLink.target_page_id", back_populates="target_page")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_page_url_hash', func.md5(url)),
        Index('idx_page_content_hash', 'content_hash'),
        Index('idx_page_status_code', 'status_code'),
        Index('idx_page_crawl_session', 'crawl_session_id'),
    )


class SEOIssue(Base):
    __tablename__ = "seo_issues"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String, ForeignKey("pages.id"), nullable=False)
    
    # Issue classification
    issue_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    category = Column(String(50), nullable=True)  # technical, content, performance, accessibility, social
    
    # Issue details
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    impact_score = Column(Integer, default=0)  # 0-100 scale
    
    # AI-generated suggestions
    ai_suggestion = Column(Text, nullable=True)
    priority_score = Column(Float, nullable=True)  # AI-calculated priority
    effort_estimate = Column(String(20), nullable=True)  # easy, medium, hard
    
    # Issue context
    element_selector = Column(String(500), nullable=True)  # CSS selector for specific element
    current_value = Column(Text, nullable=True)  # Current problematic value
    suggested_value = Column(Text, nullable=True)  # AI-suggested improvement
    
    # Tracking
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    first_detected = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    page = relationship("Page", back_populates="issues")
    
    # Indexes
    __table_args__ = (
        Index('idx_issue_severity', 'severity'),
        Index('idx_issue_category', 'category'),
        Index('idx_issue_type', 'issue_type'),
        Index('idx_issue_resolved', 'is_resolved'),
    )


class PageLink(Base):
    """Track internal links between pages for site architecture analysis"""
    __tablename__ = "page_links"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_page_id = Column(String, ForeignKey("pages.id"), nullable=False)
    target_page_id = Column(String, ForeignKey("pages.id"), nullable=True)  # Null if external
    
    # Link details
    target_url = Column(Text, nullable=False)  # Full URL
    anchor_text = Column(Text, nullable=True)
    link_title = Column(Text, nullable=True)
    rel_attributes = Column(ARRAY(String), nullable=True)  # nofollow, sponsored, etc.
    is_internal = Column(Boolean, default=True)
    
    # Link context
    link_position = Column(String(50), nullable=True)  # header, footer, content, sidebar
    is_navigation = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    source_page = relationship("Page", foreign_keys=[source_page_id], back_populates="links_from")
    target_page = relationship("Page", foreign_keys=[target_page_id], back_populates="links_to")


class Competitor(Base):
    """Track competitor websites for comparison analysis"""
    __tablename__ = "competitors"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    domain = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Competitor metrics (updated via API integrations)
    domain_authority = Column(Float, nullable=True)
    backlink_count = Column(Integer, nullable=True)
    organic_keywords = Column(Integer, nullable=True)
    monthly_traffic = Column(Integer, nullable=True)
    
    # Last analysis data
    last_analyzed = Column(DateTime(timezone=True), nullable=True)
    analysis_data = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="competitors")


class Keyword(Base):
    """Track keywords for SERP analysis and ranking monitoring"""
    __tablename__ = "keywords"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    keyword = Column(String(255), nullable=False)
    search_volume = Column(Integer, nullable=True)
    difficulty = Column(Float, nullable=True)  # 0-100 scale
    cpc = Column(Float, nullable=True)  # Cost per click
    
    # Current ranking data
    current_position = Column(Integer, nullable=True)
    current_url = Column(Text, nullable=True)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    
    # SERP features
    serp_features = Column(JSONB, nullable=True)  # Featured snippets, PAA, etc.
    
    # Tracking settings
    is_active = Column(Boolean, default=True)
    target_position = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="keywords")
    ranking_history = relationship("KeywordRanking", back_populates="keyword", cascade="all, delete-orphan")


class KeywordRanking(Base):
    """Historical ranking data for keywords"""
    __tablename__ = "keyword_rankings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    keyword_id = Column(String, ForeignKey("keywords.id"), nullable=False)
    
    position = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    meta_description = Column(Text, nullable=True)
    
    # SERP context
    serp_features = Column(JSONB, nullable=True)
    competitors_in_top10 = Column(JSONB, nullable=True)
    
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    keyword = relationship("Keyword", back_populates="ranking_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_ranking_keyword_date', 'keyword_id', 'checked_at'),
        Index('idx_ranking_position', 'position'),
    )


class ContentBrief(Base):
    """AI-generated content briefs for optimization"""
    __tablename__ = "content_briefs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    # Target info
    target_keyword = Column(String(255), nullable=False)
    target_url = Column(Text, nullable=True)  # If optimizing existing page
    
    # Brief content
    title = Column(String(255), nullable=False)
    recommended_word_count = Column(Integer, nullable=True)
    target_readability_score = Column(Float, nullable=True)
    
    # Content structure
    recommended_headings = Column(JSONB, nullable=True)  # H2, H3 structure
    key_topics = Column(JSONB, nullable=True)  # Topics to cover
    entities_to_mention = Column(JSONB, nullable=True)  # People, places, things
    questions_to_answer = Column(JSONB, nullable=True)  # PAA questions
    
    # Competitor analysis
    top_competitor_analysis = Column(JSONB, nullable=True)
    content_gaps = Column(JSONB, nullable=True)
    
    # Implementation tracking
    status = Column(String(50), default="draft")  # draft, in_progress, completed
    assigned_to = Column(String(255), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CrawlQueue(Base):
    """Queue for managing crawl tasks"""
    __tablename__ = "crawl_queue"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    crawl_session_id = Column(String, ForeignKey("crawl_sessions.id"), nullable=False)
    
    url = Column(Text, nullable=False)
    depth = Column(Integer, default=0)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    attempts = Column(Integer, default=0)
    last_attempt = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_queue_status_priority', 'status', 'priority'),
        Index('idx_queue_session', 'crawl_session_id'),
    )