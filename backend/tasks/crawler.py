from celery import current_task
from .celery_app import celery_app  # Import from tasks module
from services.crawler import AsyncWebCrawler, CrawlConfig
from models.database import CrawlSession, Page, SEOIssue
from core.database import SessionLocal
from sqlalchemy.orm import Session
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def crawl_website_task(self, session_id: str, start_url: str, config: Dict[str, Any]):
    """
    Celery task to crawl a website and save results to database
    """
    db = SessionLocal()
    try:
        # Update session status
        session = db.query(CrawlSession).filter(CrawlSession.id == session_id).first()
        if not session:
            raise Exception(f"Session {session_id} not found")
        
        session.status = "running"
        db.commit()
        
        # Create crawler config
        crawl_config = CrawlConfig(
            max_urls=config.get('max_urls', 100),
            max_depth=config.get('max_depth', 3),
            delay=config.get('delay', 1.0),
            render_javascript=config.get('render_javascript', True),
            respect_robots=config.get('respect_robots', True),
            follow_redirects=config.get('follow_redirects', True),
            exclude_patterns=config.get('exclude_patterns', [])
        )
        
        # Progress callback
        async def progress_callback(pages_crawled: int, stats: Dict):
            # Update session progress
            session.crawled_urls = pages_crawled
            session.total_urls = stats.get('total_processed', 0)
            db.commit()
            
            # Update Celery task state
            current_task.update_state(
                state='PROGRESS',
                meta={
                    'current': pages_crawled,
                    'total': crawl_config.max_urls,
                    'status': f'Crawled {pages_crawled} pages'
                }
            )
        
        # Run the crawler
        async def run_crawler():
            async with AsyncWebCrawler(crawl_config) as crawler:
                return await crawler.crawl_website(start_url, progress_callback)
        
        # Execute crawler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(run_crawler())
        loop.close()
        
        # Save results to database
        saved_pages = save_crawl_results(db, session_id, results)
        
        # Update session as completed
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        session.crawled_urls = len(saved_pages)
        db.commit()
        
        logger.info(f"Crawl task completed for session {session_id}: {len(saved_pages)} pages")
        
        return {
            'status': 'completed',
            'pages_crawled': len(saved_pages),
            'session_id': session_id
        }
        
    except Exception as e:
        logger.error(f"Crawl task failed for session {session_id}: {str(e)}")
        
        # Update session as failed
        if 'session' in locals():
            session.status = "failed"
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            db.commit()
        
        raise e
    finally:
        db.close()

def save_crawl_results(db: Session, session_id: str, results: list) -> list:
    """Save crawl results to database"""
    saved_pages = []
    
    for page_data in results:
        try:
            # Create page record
            page = Page(
                session_id=session_id,
                url=page_data['url'],
                status_code=page_data.get('status_code'),
                title=page_data.get('title'),
                meta_description=page_data.get('meta_description'),
                h1=page_data.get('h1'),
                word_count=page_data.get('word_count'),
                load_time=page_data.get('load_time'),
                content_hash=page_data.get('content_analysis', {}).get('content_hash'),
                technical_issues=page_data.get('technical_issues', []),
                content_analysis=page_data.get('content_analysis', {}),
                headers=page_data.get('headers', {}),
                depth=page_data.get('depth', 0)
            )
            
            db.add(page)
            db.commit()
            db.refresh(page)
            
            # Create SEO issue records
            for issue in page_data.get('technical_issues', []):
                seo_issue = SEOIssue(
                    page_id=page.id,
                    issue_type=issue.get('type'),
                    severity=issue.get('severity'),
                    category=issue.get('category'),
                    description=issue.get('description'),
                    recommendation=issue.get('recommendation'),
                    impact_score=issue.get('impact_score', 0)
                )
                db.add(seo_issue)
            
            saved_pages.append(page)
            
        except Exception as e:
            logger.error(f"Failed to save page {page_data.get('url')}: {str(e)}")
            db.rollback()
    
    db.commit()
    return saved_pages
