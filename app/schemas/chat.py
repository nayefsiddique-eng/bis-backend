from pydantic import BaseModel, Field
from typing import List, Optional

class SourceCitation(BaseModel):
    document: str = Field(..., description='Document name or title')
    standard_number: str = Field(..., description='BIS Standard identifier (e.g. IS 1234:2025)')
    page: int = Field(..., description='Page number')
    section: str = Field(..., description='Section or clause number')

class ChatInput(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    scan_id: Optional[str] = None
    lang: str = 'en'
    top_k: int = 5

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    confidence: float
    detected_intent: Optional[str] = 'general_qa'
    scan_context: Optional[dict] = None
