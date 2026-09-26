from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.providers.translation.base import get_translation_service, TranslationService

router = APIRouter(prefix="/translation", tags=['Translation'])

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = 'auto'
    target_lang: str = 'en'
    provider: str = 'auto'

@router.post('/translate')
async def translate_endpoint(req: TranslationRequest, trans_service: TranslationService = Depends(get_translation_service)):
    return await trans_service.translate(
        text=req.text,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
        provider=req.provider
    )

