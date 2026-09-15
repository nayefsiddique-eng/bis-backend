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
from app.services.translation import translate_text, BhashiniUnavailableError

router = APIRouter(prefix="/compliance", tags=["compliance"])

@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(product: ProductInput):
    target_lang = product.lang.lang_code
    translation_unavailable = False

    # 1. Translate incoming product category & description to English if needed
    product_en = product.model_copy()
    if target_lang != "en":
        try:
            product_en.category = await translate_text(product.category, source_lang=target_lang, target_lang="en")
            if product.sub_category:
                product_en.sub_category = await translate_text(product.sub_category, source_lang=target_lang, target_lang="en")
            product_en.description = await translate_text(product.description, source_lang=target_lang, target_lang="en")
        except BhashiniUnavailableError:
            translation_unavailable = True

    # 2. Run compliance engine and citation verifier in English
    qco_result = check_qco_applicability(product_en)
    requirements, recommended_labs = resolve_requirements(qco_result)

    response = ComplianceCheckResponse(
        product=product,  # keep original input product
        qco_result=qco_result,
        requirements=requirements,
        recommended_labs=recommended_labs,
        unverified_claims=[],
        roadmap_available=qco_result.applies,
        response_lang="en",
        translation_unavailable=translation_unavailable
    )

    verified_response = verify_response_citations(response)

    # 3. Translate human-readable fields back to target_lang if requested and translation is available
    if target_lang != "en" and not translation_unavailable:
        try:
            # Translate reasoning (human-readable string)
            verified_response.qco_result.reasoning = await translate_text(
                verified_response.qco_result.reasoning, source_lang="en", target_lang=target_lang
            )

            # Translate requirement names (keep structured source, document_id, clause, mandatory intact!)
            for req in verified_response.requirements:
                req.requirement = await translate_text(req.requirement, source_lang="en", target_lang=target_lang)

            verified_response.response_lang = target_lang
        except BhashiniUnavailableError:
            verified_response.translation_unavailable = True
            verified_response.response_lang = "en"

    return verified_response

@router.post("/roadmap", response_model=RoadmapResponse)
async def get_roadmap(request: RoadmapRequest):
    target_lang = request.lang.lang_code
    translation_unavailable = False

    steps = generate_roadmap(request.qco_result)

    if target_lang != "en":
        try:
            for step in steps:
                step.title = await translate_text(step.title, source_lang="en", target_lang=target_lang)
                step.description = await translate_text(step.description, source_lang="en", target_lang=target_lang)
        except BhashiniUnavailableError:
            translation_unavailable = True

    return RoadmapResponse(
        qco_id=request.qco_result.qco_id,
        steps=steps,
        response_lang=target_lang if not translation_unavailable else "en",
        translation_unavailable=translation_unavailable
    )
