from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from models.database import Project, CrawlSession, Page, SEOIssue
from schemas.schemas import (
    ProjectCreate, ProjectResponse, ProjectUpdate, 
    ProjectStats, DashboardResponse, CrawlSessionResponse
)
from sqlalchemy import func, desc
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new SEO project"""
    # Check if domain already exists
    existing_project = db.query(Project).filter(Project.domain == project.domain).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Project with this domain already exists")
    
    db_project = Project(
        name=project.name,
        domain=project.domain,
        description=project.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all projects with pagination"""
    projects = db.query(Project).filter(Project.is_active == True).offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str, 
    project_update: ProjectUpdate, 
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project (soft delete)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.is_active = False
    project.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Project deleted successfully"}

@router.get("/{project_id}/dashboard", response_model=DashboardResponse)
async def get_project_dashboard(project_id: str, db: Session = Depends(get_db)):
    """Get project dashboard data"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get latest crawl session
    latest_session = db.query(CrawlSession).filter(
        CrawlSession.project_id == project_id
    ).order_by(desc(CrawlSession.started_at)).first()
    
    if not latest_session:
        # No crawls yet
        stats = ProjectStats(
            total_pages=0,
            pages_with_issues=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            avg_load_time=0.0,
            last_crawl=None
        )
        recent_crawls = []
    else:
        # Calculate stats from latest session
        pages = db.query(Page).filter(Page.session_id == latest_session.id).all()
        
        # Count issues by severity
        issue_counts = db.query(
            SEOIssue.severity,
            func.count(SEOIssue.id)
        ).join(Page).filter(
            Page.session_id == latest_session.id
        ).group_by(SEOIssue.severity).all()
        
        severity_counts = {severity: count for severity, count in issue_counts}
        
        # Calculate average load time
        avg_load_time = db.query(func.avg(Page.load_time)).filter(
            Page.session_id == latest_session.id
        ).scalar() or 0.0
        
        # Count pages with issues
        pages_with_issues = db.query(func.count(func.distinct(Page.id))).join(
            SEOIssue
        ).filter(Page.session_id == latest_session.id).scalar() or 0
        
        stats = ProjectStats(
            total_pages=len(pages),
            pages_with_issues=pages_with_issues,
            critical_issues=severity_counts.get('critical', 0),
            high_issues=severity_counts.get('high', 0),
            medium_issues=severity_counts.get('medium', 0),
            low_issues=severity_counts.get('low', 0),
            avg_load_time=float(avg_load_time),
            last_crawl=latest_session.completed_at
        )
        
        # Get recent crawl sessions
        recent_crawls = db.query(CrawlSession).filter(
            CrawlSession.project_id == project_id
        ).order_by(desc(CrawlSession.started_at)).limit(5).all()
    
    return DashboardResponse(
        project=project,
        stats=stats,
        recent_crawls=recent_crawls
    )

@router.get("/{project_id}/stats")
async def get_project_stats(project_id: str, db: Session = Depends(get_db)):
    """Get detailed project statistics"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get latest session
    latest_session = db.query(CrawlSession).filter(
        CrawlSession.project_id == project_id,
        CrawlSession.status == "completed"
    ).order_by(desc(CrawlSession.completed_at)).first()
    
    if not latest_session:
        return {"message": "No completed crawls found"}
    
    # Detailed statistics
    stats = {}
    
    # Issue distribution by category
    category_stats = db.query(
        SEOIssue.category,
        SEOIssue.severity,
        func.count(SEOIssue.id)
    ).join(Page).filter(
        Page.session_id == latest_session.id
    ).group_by(SEOIssue.category, SEOIssue.severity).all()
    
    stats['issues_by_category'] = {}
    for category, severity, count in category_stats:
        if category not in stats['issues_by_category']:
            stats['issues_by_category'][category] = {}
        stats['issues_by_category'][category][severity] = count
    
    # Top issues by impact score
    top_issues = db.query(
        SEOIssue.issue_type,
        SEOIssue.description,
        func.count(SEOIssue.id).label('count'),
        func.avg(SEOIssue.impact_score).label('avg_impact')
    ).join(Page).filter(
        Page.session_id == latest_session.id
    ).group_by(
        SEOIssue.issue_type, SEOIssue.description
    ).order_by(
        desc('avg_impact')
    ).limit(10).all()
    
    stats['top_issues'] = [
        {
            'type': issue.issue_type,
            'description': issue.description,
            'count': issue.count,
            'avg_impact': float(issue.avg_impact)
        }
        for issue in top_issues
    ]
    
    # Performance stats
    performance_stats = db.query(
        func.avg(Page.load_time).label('avg_load_time'),
        func.min(Page.load_time).label('min_load_time'),
        func.max(Page.load_time).label('max_load_time'),
        func.avg(Page.word_count).label('avg_word_count')
    ).filter(Page.session_id == latest_session.id).first()
    
    stats['performance'] = {
        'avg_load_time': float(performance_stats.avg_load_time or 0),
        'min_load_time': float(performance_stats.min_load_time or 0),
        'max_load_time': float(performance_stats.max_load_time or 0),
        'avg_word_count': float(performance_stats.avg_word_count or 0)
    }
    
    return stats
