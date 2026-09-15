from fastapi import APIRouter
from app.schemas.compliance import QueryInput, QueryResponse
from app.services.intent_classifier import classify_intent

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def handle_query(input_data: QueryInput):
    intent = classify_intent(input_data.query)

    intent_messages = {
        "general_qa": "General BIS standards query identified.",
        "compliance_check": "Product compliance evaluation query identified.",
        "certification_process": "Certification roadmap & process query identified.",
        "hybrid": "Multi-topic query requiring compliance and process evaluation identified."
    }

    return QueryResponse(
        intent=intent.value,
        message=intent_messages.get(intent.value, "Query classified successfully."),
        data={
            "original_query": input_data.query,
            "detected_intent": intent.value
        }
    )
