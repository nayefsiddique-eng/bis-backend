import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.schemas.document import DocumentStatusResponse
from app.providers.ocr.base import get_ocr_provider
from app.providers.vector_store import get_vector_store
from app.services.cache_service import get_cache_service
from app.core.config import settings

class DocumentService:
    def __init__(self):
        self.documents: Dict[str, DocumentStatusResponse] = {}
        self.vector_store = get_vector_store()
        self.ocr_provider = get_ocr_provider('local')
        self.cache_service = get_cache_service()

    async def process_document_upload(self, filename: str, content: bytes) -> DocumentStatusResponse:
        doc_id = 'doc_' + str(uuid.uuid4())[:8]
        pages_count = max(1, len(content) // 4000)
        
        text_quality_sufficient = len(content) > 500
        ocr_applied = False
        status = 'COMPLETED'

        if not text_quality_sufficient:
            status = 'OCR_REQUIRED'
            ocr_res = await self.ocr_provider.extract_text_from_image(content)
            extracted_text = ocr_res['text']
            ocr_applied = True
            status = 'COMPLETED'
        else:
            extracted_text = content.decode('latin1', errors='ignore')[:1500]

        doc_info = DocumentStatusResponse(
            document_id=doc_id,
            filename=filename,
            status=status,
            pages_count=pages_count,
            extracted_text_length=len(extracted_text),
            ocr_applied=ocr_applied,
            created_at=datetime.utcnow().isoformat()
        )
        self.documents[doc_id] = doc_info

        self.cache_service.invalidate_document_cache(doc_id)

        cache_data = doc_info.model_dump() if hasattr(doc_info, 'model_dump') else doc_info.dict()
        self.cache_service.set_cache('document:' + doc_id, cache_data, ttl=settings.DOCUMENT_CACHE_TTL)
        self.cache_service.set_cache('document_status:' + doc_id, status, ttl=settings.DOCUMENT_CACHE_TTL)

        chunks = []
        for p in range(1, pages_count + 1):
            chunks.append({
                'id': doc_id + '_p' + str(p),
                'document_id': doc_id,
                'document_name': filename,
                'standard_number': filename.split('.')[0],
                'page': p,
                'section': 'Section ' + str(p),
                'text': extracted_text[:300],
                'source_type': 'BIS_PDF'
            })
        await self.vector_store.add_documents(chunks)

        return doc_info

    def get_status(self, document_id: str) -> Optional[DocumentStatusResponse]:
        cached_doc = self.cache_service.get_cache('document:' + document_id)
        if cached_doc:
            return DocumentStatusResponse(**cached_doc)

        doc = self.documents.get(document_id)
        if doc:
            cache_data = doc.model_dump() if hasattr(doc, 'model_dump') else doc.dict()
            self.cache_service.set_cache('document:' + document_id, cache_data, ttl=settings.DOCUMENT_CACHE_TTL)
        return doc

_document_service = None

def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
