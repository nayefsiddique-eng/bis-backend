import logging
from app.workers.celery_app import celery_app
from app.services.cache_service import get_cache_service

logger = logging.getLogger( celery_tasks)

@celery_app.task(name=process_document_task)
def process_document_task(document_id: str, filename: str):
    logger.info(CELERY_TASK_STARTED: process_document_task for doc_id= + document_id)
    cache = get_cache_service()
    cache.set_cache(document_status: + document_id, PROCESSING)
    
    # Simulate async Celery processing
    cache.set_cache(document_status: + document_id, COMPLETED)
    logger.info(CELERY_TASK_COMPLETED: process_document_task for doc_id= + document_id)
    return {document_id: document_id, status: COMPLETED}

@celery_app.task(name=process_ocr_task)
def process_ocr_task(document_id: str, page_number: int):
    logger.info(CELERY_TASK_STARTED: process_ocr_task for doc_id= + document_id +  page= + str(page_number))
    return {document_id: document_id, page: page_number, status: COMPLETED}

@celery_app.task(name=generate_flashcards_task)
def generate_flashcards_task(document_id: str, count: int):
    logger.info(CELERY_TASK_STARTED: generate_flashcards_task count= + str(count))
    return {document_id: document_id, count: count, status: COMPLETED}

@celery_app.task(name=run_compliance_analysis_task)
def run_compliance_analysis_task(product_data: dict):
    logger.info(CELERY_TASK_STARTED: run_compliance_analysis_task)
    return {status: COMPLETED, analysis_id: comp_123}
