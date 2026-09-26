from fastapi import APIRouter, HTTPException, Depends
from app.schemas.chat import ChatInput, ChatResponse
from app.services.rag_service import get_rag_service, RAGService

router = APIRouter(tags=['Chat and RAG'])

@router.post('/chat', response_model=ChatResponse)
async def chat_endpoint(input_data: ChatInput, rag_service: RAGService = Depends(get_rag_service)):
    return await rag_service.execute_rag_pipeline(
        query=input_data.query,
        top_k=input_data.top_k,
        document_ids=input_data.document_ids,
        scan_id=input_data.scan_id
    )

@router.post('/rag/query', response_model=ChatResponse)
async def rag_query_endpoint(input_data: ChatInput, rag_service: RAGService = Depends(get_rag_service)):
    return await rag_service.execute_rag_pipeline(
        query=input_data.query,
        top_k=input_data.top_k,
        document_ids=input_data.document_ids,
        scan_id=input_data.scan_id
    )
