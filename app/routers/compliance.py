from fastapi import APIRouter
from app.schemas.product import ProductInput
from app.schemas.compliance import (
    ComplianceCheckResponse,
    RoadmapRequest,
    RoadmapResponse,
)
from app.services.compliance_engine import check_qco_applicability, resolve_requirements
from app.services.citation_verifier import verify_response_citations
from app.services.roadmap import generate_roadmap

router = APIRouter(prefix="/compliance", tags=["compliance"])

@router.post("/check", response_model=ComplianceCheckResponse)
def check_compliance(product: ProductInput):
    # 1. Run compliance decision engine
    qco_result = check_qco_applicability(product)

    # 2. Resolve mandatory requirements and labs
    requirements, recommended_labs = resolve_requirements(qco_result)

    # 3. Construct initial response object
    response = ComplianceCheckResponse(
        product=product,
        qco_result=qco_result,
        requirements=requirements,
        recommended_labs=recommended_labs,
        unverified_claims=[],
        roadmap_available=qco_result.applies
    )

    # 4. Run citation verifier to populate unverified_claims
    verified_response = verify_response_citations(response)

    return verified_response

@router.post("/roadmap", response_model=RoadmapResponse)
def get_roadmap(request: RoadmapRequest):
    steps = generate_roadmap(request.qco_result)
    return RoadmapResponse(qco_id=request.qco_result.qco_id, steps=steps)
