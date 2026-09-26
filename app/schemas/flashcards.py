from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FlashcardCreateInput(BaseModel):
    document_id: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    topic: Optional[str] = None
    count: int = 5

class FlashcardItem(BaseModel):
    id: str
    question: str
    answer: str
    source_document: str
    standard_number: str
    page_number: int
    section: str
    difficulty: str
    topic: str
    created_at: str

class FlashcardListResponse(BaseModel):
    total: int
    flashcards: List[FlashcardItem]
