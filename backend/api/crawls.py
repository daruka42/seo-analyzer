from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from models.database import Project, CrawlSession, Page, SEOIssue
from schemas.schemas import (
    CrawlSessionCreate, CrawlSessionResponse, PageResponse, 
    PageDetailResponse, SEOIssueResponse
)
from tasks.crawler import crawl_website_task
from celery.result import AsyncResult
import uuid

router = APIRouter()

@router.post("/{project_id}/start")
async def start_crawl(
    project_id: str,
    crawl_config: CrawlSessionCreate,
    db: Session = Depends(get_db)
):
    """Start a new crawl for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if there's already a running crawl
    running_session = db.query(CrawlSession).filter(
        CrawlSession.project_id == project_id,
        CrawlSession.status.in_(["pending", "running"])
    ).first()
    
    if running_session:
        raise HTTPException(status_code=400, detail="A crawl is already running for this project")
    
    # Create new crawl session
    session = CrawlSession(
        project_id=project.id,
        status="pending",
        config=crawl_config.config.dict()
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Start background task
    task = crawl_website_task.delay(
        str(session.id),
        project.domain,
        crawl_config.config.dict()
    )
    
    return {
        "session_id": str(session.id),
        "task_id": task.id,
        "status": "started"
    }

@router.get("/{session_id}", response_model=CrawlSessionResponse)
async def get_crawl_session(session_id: str, db: Session = Depends(get_db)):
    """Get crawl session details"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    return session

@router.get("/{session_id}/status")
async def get_crawl_status(session_id: str, db: Session = Depends(get_db)):
    """Get crawl status and progress"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    # If session has a task_id, check Celery task status
    # For now, we'll just return the database status
    return {
        "session_id": session_id,
        "status": session.status,
        "progress": {
            "crawled_urls": session.crawled_urls,
            "total_urls": session.total_urls,
            "percentage": (session.crawled_urls / max(session.total_urls, 1)) * 100 if session.total_urls else 0
        },
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "error_message": session.error_message
    }

@router.get("/{session_id}/pages", response_model=List[PageResponse])
async def get_session_pages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get pages from a crawl session"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    pages = db.query(Page).filter(
        Page.session_id == session_id
    ).offset(skip).limit(limit).all()
    
    return pages

@router.get("/pages/{page_id}", response_model=PageDetailResponse)
async def get_page_details(page_id: str, db: Session = Depends(get_db)):
    """Get detailed page information including issues"""
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get SEO issues for this page
    seo_issues = db.query(SEOIssue).filter(SEOIssue.page_id == page_id).all()
    
    return PageDetailResponse(
        id=str(page.id),
        url=page.url,
        status_code=page.status_code,
        title=page.title,
        meta_description=page.meta_description,
        h1=page.h1,
        word_count=page.word_count,
        load_time=page.load_time,
        depth=page.depth,
        created_at=page.created_at,
        technical_issues=page.technical_issues or [],
        content_analysis=page.content_analysis or {},
        seo_issues=seo_issues
    )

@router.get("/{session_id}/issues")
async def get_session_issues(
    session_id: str,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get SEO issues from a crawl session"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    query = db.query(SEOIssue).join(Page).filter(Page.session_id == session_id)
    
    if severity:
        query = query.filter(SEOIssue.severity == severity)
    if category:
        query = query.filter(SEOIssue.category == category)
    
    issues = query.offset(skip).limit(limit).all()
    
    return issues

@router.get("/{session_id}/summary")
async def get_crawl_summary(session_id: str, db: Session = Depends(get_db)):
    """Get crawl session summary"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    # Count pages by status code
    status_counts = db.query(
        Page.status_code,
        func.count(Page.id)
    ).filter(Page.session_id == session_id).group_by(Page.status_code).all()
    
    # Count issues by severity
    issue_counts = db.query(
        SEOIssue.severity,
        func.count(SEOIssue.id)
    ).join(Page).filter(Page.session_id == session_id).group_by(SEOIssue.severity).all()
    
    # Performance metrics
    performance = db.query(
        func.avg(Page.load_time),
        func.avg(Page.word_count)
    ).filter(Page.session_id == session_id).first()
    
    return {
        "session": session,
        "status_codes": dict(status_counts),
        "issues_by_severity": dict(issue_counts),
        "avg_load_time": float(performance[0]) if performance[0] else 0,
        "avg_word_count": float(performance[1]) if performance[1] else 0
    }

@router.delete("/{session_id}")
async def delete_crawl_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a crawl session and all associated data"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    # Delete all associated pages and issues (cascade should handle this)
    db.delete(session)
    db.commit()
    
    return {"message": "Crawl session deleted successfully"}
