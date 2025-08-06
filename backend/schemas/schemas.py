from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re

# Enums
class SeverityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class StatusEnum(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

class CategoryEnum(str, Enum):
    technical = "technical"
    content = "content"
    performance = "performance"
    accessibility = "accessibility"
    mobile = "mobile"
    security = "security"

class IssueTypeEnum(str, Enum):
    # Technical issues
    missing_title = "missing_title"
    duplicate_title = "duplicate_title"
    missing_meta_description = "missing_meta_description"
    duplicate_meta_description = "duplicate_meta_description"
    missing_h1 = "missing_h1"
    multiple_h1 = "multiple_h1"
    broken_internal_link = "broken_internal_link"
    broken_external_link = "broken_external_link"
    missing_alt_text = "missing_alt_text"
    large_image = "large_image"
    slow_loading = "slow_loading"
    large_page_size = "large_page_size"
    missing_canonical = "missing_canonical"
    duplicate_content = "duplicate_content"
    thin_content = "thin_content"
    missing_schema = "missing_schema"
    invalid_schema = "invalid_schema"
    missing_robots_meta = "missing_robots_meta"
    blocked_by_robots = "blocked_by_robots"
    redirect_chain = "redirect_chain"
    orphaned_page = "orphaned_page"
    deep_page = "deep_page"
    
    # Content issues
    keyword_stuffing = "keyword_stuffing"
    low_keyword_density = "low_keyword_density"
    poor_readability = "poor_readability"
    short_content = "short_content"
    long_content = "long_content"
    missing_headings = "missing_headings"
    poor_heading_structure = "poor_heading_structure"
    
    # Performance issues
    large_dom = "large_dom"
    too_many_requests = "too_many_requests"
    unoptimized_images = "unoptimized_images"
    render_blocking_resources = "render_blocking_resources"
    
    # Mobile issues
    viewport_not_set = "viewport_not_set"
    text_too_small = "text_too_small"
    clickable_elements_too_close = "clickable_elements_too_close"
    content_wider_than_screen = "content_wider_than_screen"

class ExportFormatEnum(str, Enum):
    json = "json"
    csv = "csv"
    xlsx = "xlsx"
    pdf = "pdf"

# Base schemas
class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None

# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('domain')
    def validate_domain(cls, v):
        # Remove protocol if present
        domain = re.sub(r'^https?://', '', v.lower())
        # Remove trailing slash
        domain = domain.rstrip('/')
        # Basic domain validation
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,})$', domain):
            raise ValueError('Invalid domain format')
        return domain

class NotificationSettings(BaseModel):
    email_notifications: bool = True
    webhook_url: Optional[str] = None
    notify_on_completion: bool = True
    notify_on_critical_issues: bool = True
    notify_on_errors: bool = True
    slack_webhook: Optional[str] = None
    discord_webhook: Optional[str] = None

class ProjectCreate(ProjectBase):
    default_crawl_config: Optional[Dict[str, Any]] = None
    notification_settings: Optional[NotificationSettings] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    default_crawl_config: Optional[Dict[str, Any]] = None
    notification_settings: Optional[NotificationSettings] = None
    is_active: Optional[bool] = None

class ProjectStats(BaseModel):
    total_pages: int = 0
    pages_with_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    avg_load_time: float = 0.0
    last_crawl: Optional[datetime] = None
    total_internal_links: int = 0
    total_external_links: int = 0
    duplicate_content_pages: int = 0
    pages_missing_meta_desc: int = 0
    pages_missing_title: int = 0
    orphaned_pages: int = 0
    deep_pages: int = 0
    slow_pages: int = 0
    large_pages: int = 0

class ProjectResponse(ProjectBase, TimestampMixin):
    id: str
    is_active: bool = True
    default_crawl_config: Optional[Dict[str, Any]] = None
    notification_settings: Optional[NotificationSettings] = None
    quick_stats: Optional[Dict[str, Any]] = None
    detailed_stats: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Crawl configuration schemas
class CrawlConfig(BaseModel):
    max_urls: int = Field(default=100, ge=1, le=10000)
    max_depth: int = Field(default=3, ge=1, le=10)
    delay: float = Field(default=1.0, ge=0.1, le=10.0)
    timeout: int = Field(default=30, ge=5, le=120)
    max_concurrent: int = Field(default=10, ge=1, le=50)
    render_javascript: bool = True
    respect_robots: bool = True
    follow_redirects: bool = True
    screenshot_enabled: bool = False
    mobile_analysis: bool = True
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)
    user_agent: str = "SEO-Analyzer-Bot/1.0"
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    analyze_images: bool = True
    analyze_links: bool = True
    analyze_performance: bool = True
    analyze_accessibility: bool = False
    analyze_security: bool = False

class CrawlConfigCreate(CrawlConfig):
    pass

class CrawlSessionCreate(BaseModel):
    config: Optional[CrawlConfig] = None

# Enhanced crawl session schemas
class CrawlProgressResponse(BaseModel):
    session_id: str
    status: StatusEnum
    progress: Dict[str, Any]
    performance: Dict[str, Any]
    issues_summary: Dict[str, int]
    timing: Dict[str, Any]
    error_message: Optional[str] = None

class CrawlSessionResponse(BaseModel):
    id: str
    project_id: str
    status: StatusEnum
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    crawled_urls: int = 0
    failed_urls: int = 0
    queue_size: int = 0
    max_urls: int = 100
    max_depth: int = 3
    delay: float = 1.0
    render_javascript: bool = True
    mobile_analysis: bool = True
    screenshot_enabled: bool = False
    exclude_patterns: List[str] = Field(default_factory=list)
    user_agent: str = "SEO-Analyzer-Bot/1.0"
    avg_load_time: float = 0.0
    total_data_processed: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    error_message: Optional[str] = None
    current_stats: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Page schemas
class PageLink(BaseModel):
    url: str
    anchor_text: Optional[str] = None
    title: Optional[str] = None
    rel_attributes: List[str] = Field(default_factory=list)
    is_internal: bool = True
    is_navigation: bool = False
    position: Optional[int] = None

class MobileAnalysis(BaseModel):
    viewport_configured: bool = False
    mobile_friendly: bool = False
    text_size_ok: bool = True
    tap_targets_ok: bool = True
    content_fits_viewport: bool = True
    mobile_speed_score: Optional[int] = None

class PerformanceMetrics(BaseModel):
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None
    first_input_delay: Optional[float] = None
    time_to_interactive: Optional[float] = None
    total_blocking_time: Optional[float] = None
    speed_index: Optional[float] = None

class SocialTags(BaseModel):
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_url: Optional[str] = None
    og_type: Optional[str] = None
    twitter_card: Optional[str] = None
    twitter_title: Optional[str] = None
    twitter_description: Optional[str] = None
    twitter_image: Optional[str] = None

class PageResponse(BaseModel):
    id: str
    url: str
    status_code: Optional[int] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    paragraph_count: Optional[int] = None
    readability_score: Optional[float] = None
    load_time: Optional[float] = None
    page_size: Optional[int] = None
    depth: int = 0
    internal_links_count: int = 0
    external_links_count: int = 0
    total_images: int = 0
    images_missing_alt: int = 0
    canonical_url: Optional[str] = None
    robots_meta: Optional[str] = None
    lang_attribute: Optional[str] = None
    content_hash: Optional[str] = None
    screenshot_path: Optional[str] = None
    created_at: datetime
    issue_count: Optional[int] = None
    
    class Config:
        from_attributes = True

# SEO Issue schemas
class SEOIssueBase(BaseModel):
    issue_type: str
    severity: SeverityEnum
    category: CategoryEnum = CategoryEnum.technical
    description: str
    recommendation: Optional[str] = None
    impact_score: int = Field(default=0, ge=0, le=100)
    priority_score: Optional[int] = Field(None, ge=0, le=100)
    effort_estimate: Optional[str] = None  # "low", "medium", "high"
    element_selector: Optional[str] = None
    current_value: Optional[str] = None
    suggested_value: Optional[str] = None
    ai_suggestion: Optional[str] = None

class SEOIssueCreate(SEOIssueBase):
    page_id: str

class SEOIssueUpdate(BaseModel):
    is_resolved: Optional[bool] = None
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None

class SEOIssueResponse(SEOIssueBase, TimestampMixin):
    id: str
    page_id: str
    is_resolved: bool = False
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    
    class Config:
        from_attributes = True

# Enhanced page detail schema
class PageDetailResponse(PageResponse):
    keyword_density: Optional[Dict[str, float]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    headings_structure: Optional[Dict[str, List[str]]] = None
    schema_markup: Optional[List[Dict[str, Any]]] = None
    social_tags: Optional[SocialTags] = None
    mobile_analysis: Optional[MobileAnalysis] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    seo_issues: List[SEOIssueResponse] = Field(default_factory=list)
    internal_links: List[PageLink] = Field(default_factory=list)
    external_links_to_page: List[PageLink] = Field(default_factory=list)
    ai_recommendations: Optional[Dict[str, Any]] = None

# Competitor schemas
class CompetitorBase(BaseModel):
    domain: str = Field(..., min_length=1, max_length=255)
    name: Optional[str] = None

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorResponse(CompetitorBase, TimestampMixin):
    id: str
    project_id: str
    is_active: bool = True
    last_analyzed: Optional[datetime] = None
    analysis_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Keyword schemas
class KeywordBase(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=255)
    target_position: Optional[int] = Field(None, ge=1, le=100)

class KeywordCreate(KeywordBase):
    pass

class KeywordResponse(KeywordBase, TimestampMixin):
    id: str
    project_id: str
    current_position: Optional[int] = None
    search_volume: Optional[int] = None
    competition: Optional[str] = None  # "low", "medium", "high"
    cpc: Optional[float] = None
    last_checked: Optional[datetime] = None
    ranking_history: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True

# Content brief schemas
class ContentBriefResponse(BaseModel):
    id: str
    project_id: str
    target_keyword: str
    title_suggestions: List[str] = Field(default_factory=list)
    outline: Dict[str, Any] = Field(default_factory=dict)
    competitor_analysis: Dict[str, Any] = Field(default_factory=dict)
    recommended_length: Optional[int] = None
    related_keywords: List[str] = Field(default_factory=list)
    questions_to_answer: List[str] = Field(default_factory=list)
    ai_insights: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Analytics schemas
class TrendData(BaseModel):
    date: datetime
    value: float
    change_percentage: Optional[float] = None

class ProjectAnalytics(BaseModel):
    project_id: str
    date_range: Dict[str, datetime]
    crawl_history: List[Dict[str, Any]]
    issue_trends: Dict[str, List[TrendData]]
    performance_trends: Dict[str, List[TrendData]]
    content_analysis: Dict[str, Any]
    technical_health: Dict[str, Any]

class CrawlAnalyticsResponse(BaseModel):
    session_overview: Dict[str, Any]
    content_analysis: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    performance_analysis: Dict[str, Any]
    site_structure: Dict[str, Any]
    issue_distribution: Dict[str, Any]
    ai_insights: Dict[str, Any]

# Dashboard schemas
class TopIssue(BaseModel):
    type: str
    description: str
    severity: SeverityEnum
    count: int
    avg_impact: float

class PerformanceTrend(BaseModel):
    date: datetime
    avg_load_time: float
    total_pages: int
    total_issues: int

class AIInsight(BaseModel):
    type: str  # "recommendation", "warning", "opportunity"
    title: str
    description: str
    priority: str  # "low", "medium", "high"
    estimated_impact: Optional[str] = None
    action_items: List[str] = Field(default_factory=list)

class DashboardResponse(BaseModel):
    project: ProjectResponse
    stats: ProjectStats
    recent_crawls: List[CrawlSessionResponse]
    top_issues: List[TopIssue] = Field(default_factory=list)
    performance_trends: List[PerformanceTrend] = Field(default_factory=list)
    ai_insights: List[AIInsight] = Field(default_factory=list)

# Export schemas
class ExportRequest(BaseModel):
    format: ExportFormatEnum
    include_issues: bool = True
    include_pages: bool = True
    include_analytics: bool = False
    date_range: Optional[Dict[str, datetime]] = None
    filters: Optional[Dict[str, Any]] = None

class ExportResponse(BaseModel):
    export_id: str
    status: str  # "pending", "processing", "completed", "failed"
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CrawlProgressMessage(WebSocketMessage):
    type: str = "crawl_progress"
    session_id: str
    pages_crawled: int
    pages_failed: int
    queue_size: int
    current_url: Optional[str] = None
    estimated_completion: Optional[datetime] = None

class CrawlCompletedMessage(WebSocketMessage):
    type: str = "crawl_completed"
    session_id: str
    total_pages: int
    total_issues: int
    duration_seconds: float

class CrawlErrorMessage(WebSocketMessage):
    type: str = "crawl_error"
    session_id: str
    error: str
    error_code: Optional[str] = None

# Report schemas
class ReportSection(BaseModel):
    title: str
    content: Dict[str, Any]
    charts: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[str]] = None

class ReportResponse(BaseModel):
    id: str
    project_id: str
    session_id: Optional[str] = None
    report_type: str  # "crawl", "project", "comparison"
    title: str
    sections: List[ReportSection]
    executive_summary: str
    key_findings: List[str]
    action_items: List[str]
    generated_at: datetime
    generated_by: Optional[str] = None
    
    class Config:
        from_attributes = True

# Bulk operation schemas
class BulkIssueUpdate(BaseModel):
    issue_ids: List[str]
    action: str  # "resolve", "assign", "change_priority"
    value: Optional[str] = None
    notes: Optional[str] = None

class BulkOperationResponse(BaseModel):
    operation_id: str
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    errors: List[str] = Field(default_factory=list)

# Search and filter schemas
class PageFilter(BaseModel):
    status_codes: Optional[List[int]] = None
    has_issues: Optional[bool] = None
    issue_severity: Optional[List[SeverityEnum]] = None
    min_load_time: Optional[float] = None
    max_load_time: Optional[float] = None
    min_word_count: Optional[int] = None
    max_word_count: Optional[int] = None
    depth_range: Optional[List[int]] = None
    url_pattern: Optional[str] = None
    title_pattern: Optional[str] = None

class IssueFilter(BaseModel):
    severities: Optional[List[SeverityEnum]] = None
    categories: Optional[List[CategoryEnum]] = None
    issue_types: Optional[List[str]] = None
    is_resolved: Optional[bool] = None
    min_impact_score: Optional[int] = None
    assigned_to: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class SearchResponse(BaseModel):
    total_results: int
    results: List[Dict[str, Any]]
    facets: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None

# API response wrappers
class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

# Health check schema
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: str
    redis: Optional[str] = None
    celery: Optional[str] = None
    services: Dict[str, str] = Field(default_factory=dict)