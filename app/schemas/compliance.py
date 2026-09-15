from datetime import date
from typing import Literal
from pydantic import BaseModel
from app.schemas.product import ProductInput

class SourceCitation(BaseModel):
    document_id: str
    clause: str | None = None
    title: str
    url: str | None = None

class ComplianceRequirement(BaseModel):
    requirement: str
    test_or_document: Literal["test", "document", "marking"]
    mandatory: bool
    source: SourceCitation

class QCOResult(BaseModel):
    qco_id: str
    standard_id: str
    applies: bool
    reasoning: str
    effective_date: date
    exemption_status: Literal["none", "msme", "import", "grandfathered"]
    source: SourceCitation

class ComplianceCheckResponse(BaseModel):
    product: ProductInput
    qco_result: QCOResult
    requirements: list[ComplianceRequirement]
    recommended_labs: list[str]
    unverified_claims: list[str] = []
    roadmap_available: bool = True

class QueryInput(BaseModel):
    query: str

class QueryResponse(BaseModel):
    intent: str
    message: str
    data: dict | None = None

class RoadmapRequest(BaseModel):
    qco_result: QCOResult

class RoadmapStep(BaseModel):
    step_number: int
    title: str
    description: str

class RoadmapResponse(BaseModel):
    qco_id: str
    steps: list[RoadmapStep]
