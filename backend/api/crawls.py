from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import logging
from core.database import get_db
from models.database import (
    Project, CrawlSession, Page, SEOIssue, PageLink, CrawlQueue
)
from schemas.schemas import (
    CrawlSessionCreate, CrawlSessionResponse, PageResponse, 
    PageDetailResponse, SEOIssueResponse, CrawlConfigCreate,
    CrawlProgressResponse, CrawlAnalyticsResponse
)
from services.unified_crawler import UnifiedWebCrawler, CrawlConfig
from services.ai_analyzer import AIAnalyzer
from services.report_generator import ReportGenerator
from celery.result import AsyncResult
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket connection manager for real-time updates
class CrawlConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_progress_update(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Failed to send WebSocket update: {e}")
                self.disconnect(session_id)

manager = CrawlConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time crawl progress updates"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive and listen for client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(session_id)

@router.post("/{project_id}/start")
async def start_crawl(
    project_id: str,
    crawl_config: CrawlConfigCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a new unified crawl for a project"""
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
    
    # Merge project defaults with provided config
    default_config = project.default_crawl_config or {}
    final_config = {**default_config, **crawl_config.dict(exclude_unset=True)}
    
    # Create new crawl session with enhanced fields
    session = CrawlSession(
        project_id=project.id,
        status="pending",
        max_urls=final_config.get("max_urls", 100),
        max_depth=final_config.get("max_depth", 3),
        delay=final_config.get("delay", 1.0),
        render_javascript=final_config.get("render_javascript", True),
        mobile_analysis=final_config.get("mobile_analysis", True),
        screenshot_enabled=final_config.get("screenshot_enabled", False),
        exclude_patterns=final_config.get("exclude_patterns", []),
        user_agent=final_config.get("user_agent", "SEO-Analyzer-Bot/1.0")
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Start unified crawl task
    background_tasks.add_task(
        start_unified_crawl,
        str(session.id),
        project.domain,
        final_config,
        db
    )
    
    logger.info(f"Started crawl session {session.id} for project {project.name}")
    
    return {
        "session_id": str(session.id),
        "status": "started",
        "config": final_config,
        "websocket_url": f"/api/crawls/ws/{session.id}"
    }

@router.get("/{session_id}", response_model=CrawlSessionResponse)
async def get_crawl_session(session_id: str, db: Session = Depends(get_db)):
    """Get comprehensive crawl session details"""
    session = db.query(CrawlSession).options(
        joinedload(CrawlSession.project),
        joinedload(CrawlSession.pages)
    ).filter(CrawlSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    # Add real-time statistics
    session.current_stats = get_session_current_stats(db, session_id)
    
    return session

@router.get("/{session_id}/status")
async def get_crawl_status(session_id: str, db: Session = Depends(get_db)):
    """Get detailed crawl status and real-time progress"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    # Get queue status
    queue_stats = db.query(
        CrawlQueue.status,
        func.count(CrawlQueue.id)
    ).filter(
        CrawlQueue.crawl_session_id == session_id
    ).group_by(CrawlQueue.status).all()
    
    queue_summary = {status: count for status, count in queue_stats}
    
    # Calculate progress
    total_discovered = session.crawled_urls + queue_summary.get("pending", 0)
    progress_percentage = (session.crawled_urls / max(total_discovered, 1)) * 100
    
    # Estimate completion time
    estimated_completion = None
    if session.status == "running" and session.crawled_urls > 0:
        elapsed_time = (datetime.utcnow() - session.started_at).total_seconds()
        avg_time_per_page = elapsed_time / session.crawled_urls
        remaining_pages = queue_summary.get("pending", 0)
        estimated_seconds = remaining_pages * avg_time_per_page
        estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_seconds)
    
    return {
        "session_id": session_id,
        "status": session.status,
        "progress": {
            "crawled_urls": session.crawled_urls,
            "failed_urls": session.failed_urls,
            "queue_size": queue_summary.get("pending", 0),
            "total_discovered": total_discovered,
            "percentage": round(progress_percentage, 2)
        },
        "performance": {
            "avg_load_time": session.avg_load_time,
            "total_data_processed": session.total_data_processed,
            "pages_per_minute": calculate_crawl_rate(session)
        },
        "issues_summary": {
            "total_issues": session.total_issues,
            "critical_issues": session.critical_issues,
            "high_issues": session.high_issues,
            "medium_issues": session.medium_issues,
            "low_issues": session.low_issues
        },
        "timing": {
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "estimated_completion": estimated_completion,
            "elapsed_time": (datetime.utcnow() - session.started_at).total_seconds() if session.started_at else 0
        },
        "error_message": session.error_message
    }

@router.get("/{session_id}/pages", response_model=List[PageResponse])
async def get_session_pages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    status_code: Optional[int] = None,
    has_issues: Optional[bool] = None,
    min_load_time: Optional[float] = None,
    max_load_time: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """Get pages from a crawl session with advanced filtering"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    query = db.query(Page).filter(Page.crawl_session_id == session_id)
    
    # Apply filters
    if status_code:
        query = query.filter(Page.status_code == status_code)
    
    if has_issues is not None:
        if has_issues:
            query = query.join(SEOIssue)
        else:
            query = query.outerjoin(SEOIssue).filter(SEOIssue.id.is_(None))
    
    if min_load_time:
        query = query.filter(Page.load_time >= min_load_time)
    
    if max_load_time:
        query = query.filter(Page.load_time <= max_load_time)
    
    if search:
        search_filter = or_(
            Page.url.ilike(f"%{search}%"),
            Page.title.ilike(f"%{search}%"),
            Page.meta_description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Apply sorting
    sort_column = getattr(Page, sort_by, Page.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    pages = query.offset(skip).limit(limit).all()
    
    # Enhance with issue counts
    for page in pages:
        page.issue_count = db.query(func.count(SEOIssue.id)).filter(
            SEOIssue.page_id == page.id
        ).scalar()
    
    return pages

@router.get("/pages/{page_id}", response_model=PageDetailResponse)
async def get_page_details(page_id: str, db: Session = Depends(get_db)):
    """Get comprehensive page information including all analysis data"""
    page = db.query(Page).options(
        joinedload(Page.issues),
        joinedload(Page.links_from),
        joinedload(Page.links_to)
    ).filter(Page.id == page_id).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Get AI recommendations for this page
    ai_recommendations = await get_page_ai_recommendations(db, page_id)
    
    # Enhanced page response with all analysis data
    return PageDetailResponse(
        id=str(page.id),
        url=page.url,
        status_code=page.status_code,
        title=page.title,
        meta_description=page.meta_description,
        h1=page.h1,
        word_count=page.word_count,
        character_count=page.character_count,
        paragraph_count=page.paragraph_count,
        readability_score=page.readability_score,
        load_time=page.load_time,
        page_size=page.page_size,
        depth=page.depth,
        internal_links_count=page.internal_links_count,
        external_links_count=page.external_links_count,
        total_images=page.total_images,
        images_missing_alt=page.images_missing_alt,
        canonical_url=page.canonical_url,
        robots_meta=page.robots_meta,
        lang_attribute=page.lang_attribute,
        content_hash=page.content_hash,
        keyword_density=page.keyword_density,
        entities=page.entities,
        headings_structure=page.headings_structure,
        schema_markup=page.schema_markup,
        social_tags=page.social_tags,
        mobile_analysis=page.mobile_analysis,
        performance_metrics=page.performance_metrics,
        screenshot_path=page.screenshot_path,
        created_at=page.created_at,
        seo_issues=page.issues,
        internal_links=page.links_from,
        external_links_to_page=page.links_to,
        ai_recommendations=ai_recommendations
    )

@router.get("/{session_id}/issues")
async def get_session_issues(
    session_id: str,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    issue_type: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    min_impact_score: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "impact_score",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """Get SEO issues from a crawl session with advanced filtering"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    query = db.query(SEOIssue).join(Page).filter(Page.crawl_session_id == session_id)
    
    # Apply filters
    if severity:
        query = query.filter(SEOIssue.severity == severity)
    if category:
        query = query.filter(SEOIssue.category == category)
    if issue_type:
        query = query.filter(SEOIssue.issue_type == issue_type)
    if is_resolved is not None:
        query = query.filter(SEOIssue.is_resolved == is_resolved)
    if min_impact_score:
        query = query.filter(SEOIssue.impact_score >= min_impact_score)
    
    # Apply sorting
    sort_column = getattr(SEOIssue, sort_by, SEOIssue.impact_score)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    issues = query.offset(skip).limit(limit).all()
    
    return issues

@router.get("/{session_id}/analytics", response_model=CrawlAnalyticsResponse)
async def get_crawl_analytics(session_id: str, db: Session = Depends(get_db)):
    """Get comprehensive crawl analytics and insights"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Analytics only available for completed crawls")
    
    analytics = {
        "session_overview": {
            "session_id": session_id,
            "project_id": session.project_id,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "duration_minutes": (session.completed_at - session.started_at).total_seconds() / 60,
            "total_pages": session.crawled_urls,
            "failed_pages": session.failed_urls,
            "success_rate": (session.crawled_urls / (session.crawled_urls + session.failed_urls)) * 100 if (session.crawled_urls + session.failed_urls) > 0 else 0
        }
    }
    
    # Content analysis
    analytics["content_analysis"] = analyze_content_distribution(db, session_id)
    
    # Technical analysis
    analytics["technical_analysis"] = analyze_technical_issues(db, session_id)
    
    # Performance analysis
    analytics["performance_analysis"] = analyze_performance_metrics(db, session_id)
    
    # Site structure analysis
    analytics["site_structure"] = analyze_site_structure(db, session_id)
    
    # Issue distribution
    analytics["issue_distribution"] = analyze_issue_distribution(db, session_id)
    
    # AI insights
    analytics["ai_insights"] = await generate_crawl_ai_insights(db, session_id)
    
    return analytics

@router.get("/{session_id}/summary")
async def get_crawl_summary(session_id: str, db: Session = Depends(get_db)):
    """Get enhanced crawl session summary"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    # Status code distribution
    status_counts = db.query(
        Page.status_code,
        func.count(Page.id)
    ).filter(Page.crawl_session_id == session_id).group_by(Page.status_code).all()
    
    # Issue distribution by severity and category
    issue_severity_counts = db.query(
        SEOIssue.severity,
        func.count(SEOIssue.id)
    ).join(Page).filter(Page.crawl_session_id == session_id).group_by(SEOIssue.severity).all()
    
    issue_category_counts = db.query(
        SEOIssue.category,
        func.count(SEOIssue.id)
    ).join(Page).filter(Page.crawl_session_id == session_id).group_by(SEOIssue.category).all()
    
    # Performance metrics
    performance = db.query(
        func.avg(Page.load_time),
        func.min(Page.load_time),
        func.max(Page.load_time),
        func.avg(Page.word_count),
        func.avg(Page.page_size)
    ).filter(Page.crawl_session_id == session_id).first()
    
    # Content metrics
    content_metrics = db.query(
        func.count(Page.id).filter(Page.title.is_(None) | (Page.title == "")),
        func.count(Page.id).filter(Page.meta_description.is_(None) | (Page.meta_description == "")),
        func.count(Page.id).filter(Page.h1.is_(None) | (Page.h1 == "")),
        func.sum(Page.total_images),
        func.sum(Page.images_missing_alt)
    ).filter(Page.crawl_session_id == session_id).first()
    
    # Depth distribution
    depth_distribution = db.query(
        Page.depth,
        func.count(Page.id)
    ).filter(Page.crawl_session_id == session_id).group_by(Page.depth).all()
    
    return {
        "session": {
            "id": session.id,
            "status": session.status,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "crawled_urls": session.crawled_urls,
            "failed_urls": session.failed_urls,
            "total_issues": session.total_issues
        },
        "status_codes": dict(status_counts),
        "issues": {
            "by_severity": dict(issue_severity_counts),
            "by_category": dict(issue_category_counts)
        },
        "performance": {
            "avg_load_time": float(performance[0]) if performance[0] else 0,
            "min_load_time": float(performance[1]) if performance[1] else 0,
            "max_load_time": float(performance[2]) if performance[2] else 0,
            "avg_word_count": float(performance[3]) if performance[3] else 0,
            "avg_page_size": float(performance[4]) if performance[4] else 0
        },
        "content": {
            "pages_missing_title": content_metrics[0] or 0,
            "pages_missing_meta_desc": content_metrics[1] or 0,
            "pages_missing_h1": content_metrics[2] or 0,
            "total_images": content_metrics[3] or 0,
            "images_missing_alt": content_metrics[4] or 0
        },
        "site_structure": {
            "depth_distribution": dict(depth_distribution),
            "max_depth": max([depth for depth, _ in depth_distribution]) if depth_distribution else 0
        }
    }

@router.post("/{session_id}/stop")
async def stop_crawl(session_id: str, db: Session = Depends(get_db)):
    """Stop a running crawl session"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    if session.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Crawl is not running")
    
    # Update session status
    session.status = "cancelled"
    session.completed_at = datetime.utcnow()
    session.error_message = "Crawl stopped by user"
    
    # Update queue items
    db.query(CrawlQueue).filter(
        CrawlQueue.crawl_session_id == session_id,
        CrawlQueue.status == "pending"
    ).update({"status": "cancelled"})
    
    db.commit()
    
    # Send WebSocket update
    await manager.send_progress_update(session_id, {
        "type": "crawl_stopped",
        "status": "cancelled",
        "message": "Crawl stopped by user"
    })
    
    logger.info(f"Crawl session {session_id} stopped by user")
    
    return {"message": "Crawl stopped successfully"}

@router.post("/{session_id}/export")
async def export_crawl_data(
    session_id: str,
    background_tasks: BackgroundTasks,
    format: str = "json",  # json, csv, xlsx, pdf
    include_issues: bool = True,
    include_pages: bool = True,
    db: Session = Depends(get_db)
):
    """Export crawl data in various formats"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    if format not in ["json", "csv", "xlsx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    # Schedule export task
    background_tasks.add_task(
        generate_crawl_export,
        session_id,
        format,
        include_issues,
        include_pages
    )
    
    return {
        "message": "Export started",
        "format": format,
        "estimated_time": "2-5 minutes"
    }

@router.delete("/{session_id}")
async def delete_crawl_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a crawl session and all associated data"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Crawl session not found")
    
    if session.status in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="Cannot delete running crawl session")
    
    # Delete session (cascade will handle related data)
    db.delete(session)
    db.commit()
    
    logger.info(f"Deleted crawl session {session_id}")
    
    return {"message": "Crawl session deleted successfully"}

# Enhanced background task function
async def start_unified_crawl(session_id: str, domain: str, config: dict, db: Session):
    """Start unified crawl with real-time progress updates"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        return
    
    try:
        # Update session status
        session.status = "running"
        session.started_at = datetime.utcnow()
        db.commit()
        
        # Send initial WebSocket update
        await manager.send_progress_update(session_id, {
            "type": "crawl_started",
            "status": "running",
            "message": "Crawl started successfully"
        })
        
        # Create crawler configuration
        crawl_config = CrawlConfig(
            max_urls=config.get("max_urls", 100),
            max_depth=config.get("max_depth", 3),
            delay=config.get("delay", 1.0),
            user_agent=config.get("user_agent", "SEO-Analyzer-Bot/1.0"),
            respect_robots=config.get("respect_robots", True),
            render_javascript=config.get("render_javascript", True),
            timeout=config.get("timeout", 30),
            exclude_patterns=config.get("exclude_patterns", []),
            follow_redirects=config.get("follow_redirects", True),
            max_concurrent=config.get("max_concurrent", 10),
            screenshot_enabled=config.get("screenshot_enabled", False),
            mobile_analysis=config.get("mobile_analysis", True)
        )
        
        # Progress callback for real-time updates
        async def progress_callback(progress_data):
            # Update session in database
            session.crawled_urls = progress_data["pages_crawled"]
            session.failed_urls = progress_data["failed"]
            session.queue_size = progress_data["queue_size"]
            
            if progress_data["pages_crawled"] > 0:
                session.avg_load_time = calculate_average_load_time(db, session_id)
            
            db.commit()
            
            # Send WebSocket update
            await manager.send_progress_update(session_id, {
                "type": "progress_update",
                "data": progress_data
            })
        
        # Start crawling with unified crawler
        async with UnifiedWebCrawler(crawl_config) as crawler:
            start_url = f"https://{domain}" if not domain.startswith("http") else domain
            crawled_pages = await crawler.crawl_website(start_url, progress_callback)
            
            # Save crawled pages to database
            await save_crawled_pages(db, session_id, crawled_pages)
            
            # Update session statistics
            await update_session_statistics(db, session_id)
            
            # Mark session as completed
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            db.commit()
            
            # Send completion update
            await manager.send_progress_update(session_id, {
                "type": "crawl_completed",
                "status": "completed",
                "total_pages": len(crawled_pages),
                "message": "Crawl completed successfully"
            })
            
            logger.info(f"Crawl session {session_id} completed successfully with {len(crawled_pages)} pages")
    
    except Exception as e:
        # Handle errors
        session.status = "failed"
        session.completed_at = datetime.utcnow()
        session.error_message = str(e)
        db.commit()
        
        # Send error update
        await manager.send_progress_update(session_id, {
            "type": "crawl_failed",
            "status": "failed",
            "error": str(e)
        })
        
        logger.error(f"Crawl session {session_id} failed: {e}")

# Helper functions

def get_session_current_stats(db: Session, session_id: str) -> Dict:
    """Get current session statistics"""
    stats = db.query(
        func.count(Page.id).label("total_pages"),
        func.count(SEOIssue.id).label("total_issues"),
        func.avg(Page.load_time).label("avg_load_time")
    ).outerjoin(SEOIssue).filter(Page.crawl_session_id == session_id).first()
    
    return {
        "total_pages": stats.total_pages or 0,
        "total_issues": stats.total_issues or 0,
        "avg_load_time": float(stats.avg_load_time or 0)
    }

def calculate_crawl_rate(session: CrawlSession) -> float:
    """Calculate pages per minute crawl rate"""
    if not session.started_at or session.crawled_urls == 0:
        return 0.0
    
    elapsed_minutes = (datetime.utcnow() - session.started_at).total_seconds() / 60
    return session.crawled_urls / elapsed_minutes if elapsed_minutes > 0 else 0.0

async def save_crawled_pages(db: Session, session_id: str, crawled_pages: List[Dict]):
    """Save crawled pages and their analysis data to database"""
    for page_data in crawled_pages:
        # Create page record
        page = Page(
            crawl_session_id=session_id,
            url=page_data["url"],
            title=page_data.get("title"),
            meta_description=page_data.get("meta_description"),
            h1=page_data.get("h1"),
            status_code=page_data.get("status_code"),
            load_time=page_data.get("load_time"),
            depth=page_data.get("depth", 0),
            word_count=page_data.get("word_count"),
            character_count=page_data.get("character_count"),
            paragraph_count=page_data.get("paragraph_count"),
            readability_score=page_data.get("readability_score"),
            content_hash=page_data.get("content_hash"),
            internal_links_count=len(page_data.get("internal_links", [])),
            external_links_count=len(page_data.get("external_links", [])),
            total_images=page_data.get("total_images", 0),
            images_missing_alt=page_data.get("images_missing_alt", 0),
            page_size=page_data.get("page_size"),
            canonical_url=page_data.get("canonical_url"),
            robots_meta=page_data.get("robots_meta"),
            lang_attribute=page_data.get("lang_attribute"),
            keyword_density=page_data.get("keyword_density"),
            entities=page_data.get("entities"),
            headings_structure=page_data.get("headings_structure"),
            schema_markup=page_data.get("schema_markup"),
            social_tags=page_data.get("social_tags"),
            mobile_analysis=page_data.get("mobile_analysis"),
            performance_metrics=page_data.get("performance_metrics"),
            screenshot_path=page_data.get("screenshot_path")
        )
        
        db.add(page)
        db.flush()  # Get page ID
        
        # Save SEO issues
        for issue in page_data.get("seo_issues", []):
            seo_issue = SEOIssue(
                page_id=page.id,
                issue_type=issue["type"],
                severity=issue["severity"],
                category=issue["category"],
                description=issue["description"],
                recommendation=issue.get("recommendation"),
                impact_score=issue.get("impact_score", 1),
                element=issue.get("element"),
                context=issue.get("context")
            )
            db.add(seo_issue)
        
        # Save page links
        for link in page_data.get("internal_links", []):
            page_link = PageLink(
                from_page_id=page.id,
                to_url=link["url"],
                anchor_text=link.get("anchor_text"),
                link_type="internal",
                is_nofollow=link.get("is_nofollow", False)
            )
            db.add(page_link)
        
        for link in page_data.get("external_links", []):
            page_link = PageLink(
                from_page_id=page.id,
                to_url=link["url"],
                anchor_text=link.get("anchor_text"),
                link_type="external",
                is_nofollow=link.get("is_nofollow", False)
            )
            db.add(page_link)
    
    db.commit()

async def update_session_statistics(db: Session, session_id: str):
    """Update session-level statistics after crawl completion"""
    session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
    if not session:
        return
    
    # Calculate issue counts by severity
    issue_counts = db.query(
        SEOIssue.severity,
        func.count(SEOIssue.id)
    ).join(Page).filter(
        Page.crawl_session_id == session_id
    ).group_by(SEOIssue.severity).all()
    
    severity_counts = dict(issue_counts)
    
    # Update session statistics
    session.total_issues = sum(severity_counts.values())
    session.critical_issues = severity_counts.get("critical", 0)
    session.high_issues = severity_counts.get("high", 0)
    session.medium_issues = severity_counts.get("medium", 0)
    session.low_issues = severity_counts.get("low", 0)
    
    # Calculate average load time
    avg_load_time = db.query(func.avg(Page.load_time)).filter(
        Page.crawl_session_id == session_id
    ).scalar()
    session.avg_load_time = float(avg_load_time) if avg_load_time else 0.0
    
    # Calculate total data processed
    total_size = db.query(func.sum(Page.page_size)).filter(
        Page.crawl_session_id == session_id
    ).scalar()
    session.total_data_processed = int(total_size) if total_size else 0
    
    db.commit()

def calculate_average_load_time(db: Session, session_id: str) -> float:
    """Calculate current average load time for session"""
    avg_time = db.query(func.avg(Page.load_time)).filter(
        Page.crawl_session_id == session_id
    ).scalar()
    return float(avg_time) if avg_time else 0.0

def analyze_content_distribution(db: Session, session_id: str) -> Dict:
    """Analyze content distribution across crawled pages"""
    # Title length distribution
    title_stats = db.query(
        func.avg(func.length(Page.title)),
        func.min(func.length(Page.title)),
        func.max(func.length(Page.title))
    ).filter(Page.crawl_session_id == session_id).first()
    
    # Meta description length distribution
    meta_stats = db.query(
        func.avg(func.length(Page.meta_description)),
        func.min(func.length(Page.meta_description)),
        func.max(func.length(Page.meta_description))
    ).filter(Page.crawl_session_id == session_id).first()
    
    # Word count distribution
    word_stats = db.query(
        func.avg(Page.word_count),
        func.min(Page.word_count),
        func.max(Page.word_count)
    ).filter(Page.crawl_session_id == session_id).first()
    
    return {
        "title_lengths": {
            "average": float(title_stats[0]) if title_stats[0] else 0,
            "min": int(title_stats[1]) if title_stats[1] else 0,
            "max": int(title_stats[2]) if title_stats[2] else 0
        },
        "meta_description_lengths": {
            "average": float(meta_stats[0]) if meta_stats[0] else 0,
            "min": int(meta_stats[1]) if meta_stats[1] else 0,
            "max": int(meta_stats[2]) if meta_stats[2] else 0
        },
        "word_counts": {
            "average": float(word_stats[0]) if word_stats[0] else 0,
            "min": int(word_stats[1]) if word_stats[1] else 0,
            "max": int(word_stats[2]) if word_stats[2] else 0
        }
    }

def analyze_technical_issues(db: Session, session_id: str) -> Dict:
    """Analyze technical SEO issues"""
    # Status code distribution
    status_codes = db.query(
        Page.status_code,
        func.count(Page.id)
    ).filter(Page.crawl_session_id == session_id).group_by(Page.status_code).all()
    
    # Common technical issues
    technical_issues = db.query(
        SEOIssue.issue_type,
        func.count(SEOIssue.id)
    ).join(Page).filter(
        Page.crawl_session_id == session_id,
        SEOIssue.category == "technical"
    ).group_by(SEOIssue.issue_type).all()
    
    return {
        "status_codes": dict(status_codes),
        "common_issues": dict(technical_issues),
        "error_rate": len([code for code, _ in status_codes if code >= 400]) / len(status_codes) if status_codes else 0
    }

def analyze_performance_metrics(db: Session, session_id: str) -> Dict:
    """Analyze performance metrics"""
    # Load time distribution
    load_time_stats = db.query(
        func.avg(Page.load_time),
        func.min(Page.load_time),
        func.max(Page.load_time),
        func.percentile_cont(0.5).within_group(Page.load_time),
        func.percentile_cont(0.95).within_group(Page.load_time)
    ).filter(Page.crawl_session_id == session_id).first()
    
    # Page size distribution
    size_stats = db.query(
        func.avg(Page.page_size),
        func.min(Page.page_size),
        func.max(Page.page_size)
    ).filter(Page.crawl_session_id == session_id).first()
    
    # Slow pages (>3 seconds)
    slow_pages_count = db.query(func.count(Page.id)).filter(
        Page.crawl_session_id == session_id,
        Page.load_time > 3.0
    ).scalar()
    
    total_pages = db.query(func.count(Page.id)).filter(
        Page.crawl_session_id == session_id
    ).scalar()
    
    return {
        "load_times": {
            "average": float(load_time_stats[0]) if load_time_stats[0] else 0,
            "min": float(load_time_stats[1]) if load_time_stats[1] else 0,
            "max": float(load_time_stats[2]) if load_time_stats[2] else 0,
            "median": float(load_time_stats[3]) if load_time_stats[3] else 0,
            "p95": float(load_time_stats[4]) if load_time_stats[4] else 0
        },
        "page_sizes": {
            "average": float(size_stats[0]) if size_stats[0] else 0,
            "min": int(size_stats[1]) if size_stats[1] else 0,
            "max": int(size_stats[2]) if size_stats[2] else 0
        },
        "performance_issues": {
            "slow_pages": slow_pages_count,
            "slow_pages_percentage": (slow_pages_count / total_pages * 100) if total_pages > 0 else 0
        }
    }

def analyze_site_structure(db: Session, session_id: str) -> Dict:
    """Analyze site structure and internal linking"""
    # Depth distribution
    depth_distribution = db.query(
        Page.depth,
        func.count(Page.id)
    ).filter(Page.crawl_session_id == session_id).group_by(Page.depth).all()
    
    # Internal linking analysis
    internal_links_stats = db.query(
        func.avg(Page.internal_links_count),
        func.min(Page.internal_links_count),
        func.max(Page.internal_links_count)
    ).filter(Page.crawl_session_id == session_id).first()
    
    # Pages with no internal links
    orphaned_pages = db.query(func.count(Page.id)).filter(
        Page.crawl_session_id == session_id,
        Page.internal_links_count == 0
    ).scalar()
    
    return {
        "depth_distribution": dict(depth_distribution),
        "max_depth": max([depth for depth, _ in depth_distribution]) if depth_distribution else 0,
        "internal_linking": {
            "average_links_per_page": float(internal_links_stats[0]) if internal_links_stats[0] else 0,
            "min_links": int(internal_links_stats[1]) if internal_links_stats[1] else 0,
            "max_links": int(internal_links_stats[2]) if internal_links_stats[2] else 0,
            "orphaned_pages": orphaned_pages
        }
    }

def analyze_issue_distribution(db: Session, session_id: str) -> Dict:
    """Analyze SEO issue distribution"""
    # Issues by category
    category_distribution = db.query(
        SEOIssue.category,
        func.count(SEOIssue.id)
    ).join(Page).filter(
        Page.crawl_session_id == session_id
    ).group_by(SEOIssue.category).all()
    
    # Issues by severity
    severity_distribution = db.query(
        SEOIssue.severity,
        func.count(SEOIssue.id)
    ).join(Page).filter(
        Page.crawl_session_id == session_id
    ).group_by(SEOIssue.severity).all()
    
    # Most common issues
    common_issues = db.query(
        SEOIssue.issue_type,
        func.count(SEOIssue.id)
    ).join(Page).filter(
        Page.crawl_session_id == session_id
    ).group_by(SEOIssue.issue_type).order_by(
        func.count(SEOIssue.id).desc()
    ).limit(10).all()
    
    return {
        "by_category": dict(category_distribution),
        "by_severity": dict(severity_distribution),
        "most_common": dict(common_issues)
    }

async def generate_crawl_ai_insights(db: Session, session_id: str) -> Dict:
    """Generate AI-powered insights for the crawl"""
    try:
        # Get session data
        session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
        if not session:
            return {}
        
        # Get top issues
        top_issues = db.query(SEOIssue).join(Page).filter(
            Page.crawl_session_id == session_id
        ).order_by(SEOIssue.impact_score.desc()).limit(10).all()
        
        # Get performance data
        performance_data = db.query(
            func.avg(Page.load_time),
            func.count(Page.id).filter(Page.load_time > 3.0),
            func.avg(Page.word_count)
        ).filter(Page.crawl_session_id == session_id).first()
        
        # Initialize AI analyzer
        ai_analyzer = AIAnalyzer()
        
        # Generate insights
        insights = await ai_analyzer.generate_crawl_insights({
            "session_id": session_id,
            "total_pages": session.crawled_urls,
            "total_issues": session.total_issues,
            "top_issues": [
                {
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "category": issue.category,
                    "impact_score": issue.impact_score
                } for issue in top_issues
            ],
            "performance": {
                "avg_load_time": float(performance_data[0]) if performance_data[0] else 0,
                "slow_pages": performance_data[1] or 0,
                "avg_word_count": float(performance_data[2]) if performance_data[2] else 0
            }
        })
        
        return insights
    
    except Exception as e:
        logger.error(f"Failed to generate AI insights: {e}")
        return {"error": "Failed to generate AI insights"}

async def get_page_ai_recommendations(db: Session, page_id: str) -> List[Dict]:
    """Get AI recommendations for a specific page"""
    try:
        page = db.query(Page).options(joinedload(Page.issues)).filter(Page.id == page_id).first()
        if not page:
            return []
        
        ai_analyzer = AIAnalyzer()
        
        page_data = {
            "url": page.url,
            "title": page.title,
            "meta_description": page.meta_description,
            "h1": page.h1,
            "word_count": page.word_count,
            "load_time": page.load_time,
            "issues": [
                {
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description
                } for issue in page.issues
            ]
        }
        
        recommendations = await ai_analyzer.generate_page_recommendations(page_data)
        return recommendations
    
    except Exception as e:
        logger.error(f"Failed to generate page recommendations: {e}")
        return []

async def generate_crawl_export(session_id: str, format: str, include_issues: bool, include_pages: bool):
    """Generate crawl data export in specified format"""
    try:
        # This would integrate with the report generator
        report_generator = ReportGenerator()
        
        export_config = {
            "session_id": session_id,
            "format": format,
            "include_issues": include_issues,
            "include_pages": include_pages
        }
        
        # Generate export file
        file_path = await report_generator.generate_crawl_export(export_config)
        
        # Store file path in session or send notification
        logger.info(f"Export generated for session {session_id}: {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate export for session {session_id}: {e}")