from fastapi import APIRouter, HTTPException, Depends
from app.schemas.flashcards import FlashcardCreateInput, FlashcardItem, FlashcardListResponse
from app.services.flashcard_service import get_flashcard_service, FlashcardService

router = APIRouter(prefix="/flashcards", tags=['Flashcards'])

@router.post('/generate', response_model=FlashcardListResponse)
async def generate_cards(input_data: FlashcardCreateInput, fc_service: FlashcardService = Depends(get_flashcard_service)):
    return await fc_service.generate_flashcards(document_id=input_data.document_id, count=input_data.count)

@router.get('', response_model=FlashcardListResponse)
async def list_cards(fc_service: FlashcardService = Depends(get_flashcard_service)):
    return fc_service.get_all()

@router.get('/{flashcard_id}', response_model=FlashcardItem)
async def get_card(flashcard_id: str, fc_service: FlashcardService = Depends(get_flashcard_service)):
    card = fc_service.get_by_id(flashcard_id)
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found.")
    return card

@router.delete('/{flashcard_id}')
async def delete_card(flashcard_id: str, fc_service: FlashcardService = Depends(get_flashcard_service)):
    success = fc_service.delete_by_id(flashcard_id)
    if not success:
        raise HTTPException(status_code=404, detail="Flashcard not found.")
    return {"status": "deleted", "flashcard_id": flashcard_id}

