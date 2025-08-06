from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from core.database import get_db
from models.database import (
    Project, CrawlSession, Page, SEOIssue, Competitor, 
    Keyword, ContentBrief, PageLink
)
from schemas.schemas import (
    ProjectCreate, ProjectResponse, ProjectUpdate, 
    ProjectStats, DashboardResponse, CrawlSessionResponse,
    CompetitorCreate, CompetitorResponse, KeywordCreate,
    ContentBriefResponse, ProjectAnalytics
)
from services.ai_analyzer import AIAnalyzer
from services.competitor_analyzer import CompetitorAnalyzer
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new SEO project with enhanced setup"""
    # Check if domain already exists
    existing_project = db.query(Project).filter(Project.domain == project.domain).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Project with this domain already exists")
    
    # Create project with enhanced fields
    db_project = Project(
        name=project.name,
        domain=project.domain,
        description=project.description,
        default_crawl_config=project.default_crawl_config or {
            "max_urls": 100,
            "max_depth": 3,
            "delay": 1.0,
            "render_javascript": True,
            "mobile_analysis": True,
            "screenshot_enabled": False
        },
        notification_settings=project.notification_settings or {
            "email_notifications": True,
            "webhook_url": None,
            "notify_on_completion": True,
            "notify_on_critical_issues": True
        }
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Schedule initial domain analysis
    background_tasks.add_task(analyze_domain_setup, db_project.id, project.domain)
    
    logger.info(f"Created new project: {project.name} ({project.domain})")
    return db_project

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or domain"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """Get all projects with enhanced filtering and sorting"""
    query = db.query(Project).filter(Project.is_active == True)
    
    # Apply search filter
    if search:
        search_filter = or_(
            Project.name.ilike(f"%{search}%"),
            Project.domain.ilike(f"%{search}%"),
            Project.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Apply sorting
    sort_column = getattr(Project, sort_by, Project.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    projects = query.offset(skip).limit(limit).all()
    
    # Enhance with quick stats
    for project in projects:
        project.quick_stats = get_project_quick_stats(db, project.id)
    
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project with detailed information"""
    project = db.query(Project).options(
        joinedload(Project.crawl_sessions),
        joinedload(Project.competitors),
        joinedload(Project.keywords)
    ).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Add enhanced statistics
    project.detailed_stats = get_project_detailed_stats(db, project_id)
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, 
    project_update: ProjectUpdate, 
    db: Session = Depends(get_db)
):
    """Update a project with enhanced validation"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate domain change
    if hasattr(project_update, 'domain') and project_update.domain != project.domain:
        existing = db.query(Project).filter(
            Project.domain == project_update.domain,
            Project.id != project_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Domain already exists in another project")
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    logger.info(f"Updated project: {project.name}")
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project (soft delete with cleanup)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Cancel any running crawls
    running_crawls = db.query(CrawlSession).filter(
        CrawlSession.project_id == project_id,
        CrawlSession.status.in_(["pending", "running"])
    ).all()
    
    for crawl in running_crawls:
        crawl.status = "cancelled"
    
    project.is_active = False
    project.updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Deleted project: {project.name}")
    return {"message": "Project deleted successfully"}

@router.get("/{project_id}/dashboard", response_model=DashboardResponse)
async def get_project_dashboard(project_id: str, db: Session = Depends(get_db)):
    """Get comprehensive project dashboard data"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get latest completed crawl session
    latest_session = db.query(CrawlSession).filter(
        CrawlSession.project_id == project_id,
        CrawlSession.status == "completed"
    ).order_by(desc(CrawlSession.completed_at)).first()
    
    if not latest_session:
        # No completed crawls yet
        stats = ProjectStats(
            total_pages=0,
            pages_with_issues=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            avg_load_time=0.0,
            last_crawl=None,
            total_internal_links=0,
            total_external_links=0,
            duplicate_content_pages=0,
            pages_missing_meta_desc=0,
            pages_missing_title=0
        )
        recent_crawls = []
        top_issues = []
        performance_trends = []
    else:
        stats = calculate_comprehensive_stats(db, latest_session.id)
        
        # Get recent crawl sessions
        recent_crawls = db.query(CrawlSession).filter(
            CrawlSession.project_id == project_id
        ).order_by(desc(CrawlSession.started_at)).limit(5).all()
        
        # Get top issues by impact
        top_issues = get_top_issues(db, latest_session.id)
        
        # Get performance trends
        performance_trends = get_performance_trends(db, project_id)
    
    # Get AI insights
    ai_insights = await get_ai_insights(db, project_id, latest_session.id if latest_session else None)
    
    return DashboardResponse(
        project=project,
        stats=stats,
        recent_crawls=recent_crawls,
        top_issues=top_issues,
        performance_trends=performance_trends,
        ai_insights=ai_insights
    )

@router.get("/{project_id}/analytics", response_model=ProjectAnalytics)
async def get_project_analytics(
    project_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get detailed project analytics and trends"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get crawl sessions in date range
    sessions = db.query(CrawlSession).filter(
        CrawlSession.project_id == project_id,
        CrawlSession.completed_at >= start_date,
        CrawlSession.status == "completed"
    ).order_by(CrawlSession.completed_at).all()
    
    if not sessions:
        raise HTTPException(status_code=404, detail="No completed crawls found in date range")
    
    analytics = {
        "project_id": project_id,
        "date_range": {"start": start_date, "end": end_date},
        "crawl_history": [],
        "issue_trends": {},
        "performance_trends": {},
        "content_analysis": {},
        "technical_health": {}
    }
    
    # Analyze each session
    for session in sessions:
        session_analytics = analyze_crawl_session(db, session)
        analytics["crawl_history"].append(session_analytics)
    
    # Calculate trends
    analytics["issue_trends"] = calculate_issue_trends(analytics["crawl_history"])
    analytics["performance_trends"] = calculate_performance_trends(analytics["crawl_history"])
    analytics["content_analysis"] = calculate_content_trends(analytics["crawl_history"])
    analytics["technical_health"] = calculate_technical_health_trends(analytics["crawl_history"])
    
    return analytics

@router.post("/{project_id}/competitors", response_model=CompetitorResponse)
async def add_competitor(
    project_id: str,
    competitor: CompetitorCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Add a competitor for analysis"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if competitor already exists
    existing = db.query(Competitor).filter(
        Competitor.project_id == project_id,
        Competitor.domain == competitor.domain
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Competitor already exists")
    
    db_competitor = Competitor(
        project_id=project_id,
        domain=competitor.domain,
        name=competitor.name
    )
    
    db.add(db_competitor)
    db.commit()
    db.refresh(db_competitor)
    
    # Schedule competitor analysis
    background_tasks.add_task(analyze_competitor, db_competitor.id)
    
    return db_competitor

@router.get("/{project_id}/competitors", response_model=List[CompetitorResponse])
async def get_competitors(project_id: str, db: Session = Depends(get_db)):
    """Get all competitors for a project"""
    competitors = db.query(Competitor).filter(
        Competitor.project_id == project_id,
        Competitor.is_active == True
    ).all()
    return competitors

@router.post("/{project_id}/keywords", response_model=KeywordCreate)
async def add_keyword(
    project_id: str,
    keyword: KeywordCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Add a keyword for tracking"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_keyword = Keyword(
        project_id=project_id,
        keyword=keyword.keyword,
        target_position=keyword.target_position
    )
    
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    
    # Schedule keyword analysis
    background_tasks.add_task(analyze_keyword_ranking, db_keyword.id)
    
    return db_keyword

@router.get("/{project_id}/content-briefs", response_model=List[ContentBriefResponse])
async def get_content_briefs(project_id: str, db: Session = Depends(get_db)):
    """Get AI-generated content briefs"""
    briefs = db.query(ContentBrief).filter(
        ContentBrief.project_id == project_id
    ).order_by(desc(ContentBrief.created_at)).all()
    return briefs

@router.post("/{project_id}/content-briefs")
async def generate_content_brief(
    project_id: str,
    target_keyword: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate AI-powered content brief"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Schedule content brief generation
    background_tasks.add_task(generate_ai_content_brief, project_id, target_keyword)
    
    return {"message": "Content brief generation started", "keyword": target_keyword}

@router.get("/{project_id}/site-architecture")
async def get_site_architecture(project_id: str, db: Session = Depends(get_db)):
    """Analyze site architecture and internal linking"""
    latest_session = db.query(CrawlSession).filter(
        CrawlSession.project_id == project_id,
        CrawlSession.status == "completed"
    ).order_by(desc(CrawlSession.completed_at)).first()
    
    if not latest_session:
        raise HTTPException(status_code=404, detail="No completed crawls found")
    
    # Get internal linking data
    links = db.query(PageLink).join(Page).filter(
        Page.crawl_session_id == latest_session.id,
        PageLink.is_internal == True
    ).all()
    
    # Calculate architecture metrics
    architecture_analysis = {
        "total_internal_links": len(links),
        "pages_by_depth": {},
        "orphaned_pages": [],
        "pages_with_most_internal_links": [],
        "link_distribution": {},
        "navigation_analysis": {}
    }
    
    # Analyze depth distribution
    pages = db.query(Page).filter(Page.crawl_session_id == latest_session.id).all()
    for page in pages:
        depth = page.depth
        if depth not in architecture_analysis["pages_by_depth"]:
            architecture_analysis["pages_by_depth"][depth] = 0
        architecture_analysis["pages_by_depth"][depth] += 1
    
    # Find orphaned pages (pages with no internal links pointing to them)
    linked_urls = {link.target_url for link in links}
    for page in pages:
        if page.url not in linked_urls and page.depth > 0:
            architecture_analysis["orphaned_pages"].append({
                "url": page.url,
                "title": page.title,
                "depth": page.depth
            })
    
    return architecture_analysis

# Helper functions

def get_project_quick_stats(db: Session, project_id: str) -> Dict:
    """Get quick statistics for project list view"""
    latest_session = db.query(CrawlSession).filter(
        CrawlSession.project_id == project_id,
        CrawlSession.status == "completed"
    ).order_by(desc(CrawlSession.completed_at)).first()
    
    if not latest_session:
        return {"pages": 0, "issues": 0, "last_crawl": None}
    
    pages_count = db.query(func.count(Page.id)).filter(
        Page.crawl_session_id == latest_session.id
    ).scalar()
    
    issues_count = db.query(func.count(SEOIssue.id)).join(Page).filter(
        Page.crawl_session_id == latest_session.id
    ).scalar()
    
    return {
        "pages": pages_count,
        "issues": issues_count,
        "last_crawl": latest_session.completed_at
    }

def calculate_comprehensive_stats(db: Session, session_id: str) -> ProjectStats:
    """Calculate comprehensive project statistics"""
    # Basic counts
    total_pages = db.query(func.count(Page.id)).filter(
        Page.crawl_session_id == session_id
    ).scalar()
    
    # Issue counts by severity
    issue_counts = db.query(
        SEOIssue.severity,
        func.count(SEOIssue.id)
    ).join(Page).filter(
        Page.crawl_session_id == session_id
    ).group_by(SEOIssue.severity).all()
    
    severity_counts = {severity: count for severity, count in issue_counts}
    
    # Pages with issues
    pages_with_issues = db.query(func.count(func.distinct(Page.id))).join(
        SEOIssue
    ).filter(Page.crawl_session_id == session_id).scalar() or 0
    
    # Performance metrics
    avg_load_time = db.query(func.avg(Page.load_time)).filter(
        Page.crawl_session_id == session_id
    ).scalar() or 0.0
    
    # Link counts
    total_internal_links = db.query(func.sum(Page.internal_links_count)).filter(
        Page.crawl_session_id == session_id
    ).scalar() or 0
    
    total_external_links = db.query(func.sum(Page.external_links_count)).filter(
        Page.crawl_session_id == session_id
    ).scalar() or 0
    
    # Content issues
    pages_missing_meta_desc = db.query(func.count(Page.id)).filter(
        Page.crawl_session_id == session_id,
        or_(Page.meta_description.is_(None), Page.meta_description == "")
    ).scalar() or 0
    
    pages_missing_title = db.query(func.count(Page.id)).filter(
        Page.crawl_session_id == session_id,
        or_(Page.title.is_(None), Page.title == "")
    ).scalar() or 0
    
    # Duplicate content (same content hash)
    duplicate_content_pages = db.query(func.count(Page.id)).filter(
        Page.crawl_session_id == session_id,
        Page.content_hash.in_(
            db.query(Page.content_hash).filter(
                Page.crawl_session_id == session_id
            ).group_by(Page.content_hash).having(func.count(Page.id) > 1)
        )
    ).scalar() or 0
    
    return ProjectStats(
        total_pages=total_pages,
        pages_with_issues=pages_with_issues,
        critical_issues=severity_counts.get('critical', 0),
        high_issues=severity_counts.get('high', 0),
        medium_issues=severity_counts.get('medium', 0),
        low_issues=severity_counts.get('low', 0),
        avg_load_time=float(avg_load_time),
        total_internal_links=total_internal_links,
        total_external_links=total_external_links,
        duplicate_content_pages=duplicate_content_pages,
        pages_missing_meta_desc=pages_missing_meta_desc,
        pages_missing_title=pages_missing_title,
        last_crawl=None  # Will be set by caller
    )

def get_top_issues(db: Session, session_id: str, limit: int = 10) -> List[Dict]:
    """Get top issues by impact score"""
    top_issues = db.query(
        SEOIssue.issue_type,
        SEOIssue.description,
        SEOIssue.severity,
        func.count(SEOIssue.id).label('count'),
        func.avg(SEOIssue.impact_score).label('avg_impact')
    ).join(Page).filter(
        Page.crawl_session_id == session_id
    ).group_by(
        SEOIssue.issue_type, SEOIssue.description, SEOIssue.severity
    ).order_by(
        desc('avg_impact'), desc('count')
    ).limit(limit).all()
    
    return [
        {
            'type': issue.issue_type,
            'description': issue.description,
            'severity': issue.severity,
            'count': issue.count,
            'avg_impact': float(issue.avg_impact)
        }
        for issue in top_issues
    ]

async def get_ai_insights(db: Session, project_id: str, session_id: Optional[str]) -> Dict:
    """Generate AI-powered insights for the project"""
    if not session_id:
        return {"message": "No crawl data available for AI analysis"}
    
    try:
        ai_analyzer = AIAnalyzer()
        insights = await ai_analyzer.generate_project_insights(db, project_id, session_id)
        return insights
    except Exception as e:
        logger.error(f"Failed to generate AI insights: {e}")
        return {"error": "AI insights temporarily unavailable"}

# Background task functions

async def analyze_domain_setup(project_id: str, domain: str):
    """Analyze domain setup and configuration"""
    # Implementation for domain analysis
    pass

async def analyze_competitor(competitor_id: str):
    """Analyze competitor domain"""
    # Implementation for competitor analysis
    pass

async def analyze_keyword_ranking(keyword_id: str):
    """Analyze keyword ranking"""
    # Implementation for keyword ranking analysis
    pass

async def generate_ai_content_brief(project_id: str, target_keyword: str):
    """Generate AI-powered content brief"""
    # Implementation for content brief generation
    pass