from pydantic import BaseModel
from typing import Optional, Dict, Any

class OCRProcessRequest(BaseModel):
    document_id: str
    page_number: Optional[int] = None

class OCRProcessResponse(BaseModel):
    document_id: str
    page_number: int
    extracted_text: str
    confidence: float
    provider_used: str
