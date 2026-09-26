from pydantic import BaseModel
from typing import Optional

class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str  # UPLOADED, PROCESSING, OCR_REQUIRED, INDEXING, COMPLETED, FAILED
    pages_count: int
    extracted_text_length: int
    ocr_applied: bool
    created_at: str
