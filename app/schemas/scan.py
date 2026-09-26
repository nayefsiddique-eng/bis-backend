from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ScanProcessResponse(BaseModel):
    scan_id: str
    status: str
    extracted_text: str
    confidence: float
    provider_used: str
    created_at: str
    image_info: Optional[Dict[str, Any]] = None

class ScanStatusResponse(BaseModel):
    scan_id: str
    status: str
    extracted_text: str
    confidence: float
    created_at: str
