from core.celery import celery_app

# Export celery_app so it can be imported as tasks.celery_app
__all__ = ['celery_app']