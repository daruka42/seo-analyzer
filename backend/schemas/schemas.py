from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

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

# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

# Crawl configuration schemas
class CrawlConfig(BaseModel):
    max_urls: int = Field(default=100, ge=1, le=10000)
    max_depth: int = Field(default=3, ge=1, le=10)
    delay: float = Field(default=1.0, ge=0.1, le=10.0)
    render_javascript: bool = True
    respect_robots: bool = True
    follow_redirects: bool = True
    exclude_patterns: List[str] = []

class CrawlSessionCreate(BaseModel):
    config: CrawlConfig

class CrawlSessionResponse(BaseModel):
    id: str
    project_id: str
    status: StatusEnum
    started_at: datetime
    completed_at: Optional[datetime]
    total_urls: int
    crawled_urls: int
    config: Dict[str, Any]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

# Page schemas
class PageResponse(BaseModel):
    id: str
    url: str
    status_code: Optional[int]
    title: Optional[str]
    meta_description: Optional[str]
    h1: Optional[str]
    word_count: Optional[int]
    load_time: Optional[float]
    depth: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# SEO Issue schemas
class SEOIssueResponse(BaseModel):
    id: str
    issue_type: str
    severity: SeverityEnum
    category: Optional[str]
    description: str
    recommendation: Optional[str]
    impact_score: int
    
    class Config:
        from_attributes = True

class PageDetailResponse(PageResponse):
    technical_issues: List[Dict[str, Any]]
    content_analysis: Dict[str, Any]
    seo_issues: List[SEOIssueResponse]

# Dashboard schemas
class ProjectStats(BaseModel):
    total_pages: int
    pages_with_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    avg_load_time: float
    last_crawl: Optional[datetime]

class DashboardResponse(BaseModel):
    project: ProjectResponse
    stats: ProjectStats
    recent_crawls: List[CrawlSessionResponse]
