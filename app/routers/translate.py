from fastapi import APIRouter
from app.schemas.language import (
    TranslateTextRequest,
    TranslateTextResponse,
    LanguageSupportResponse,
)
from app.services.translation import (
    translate_text,
    get_supported_languages,
    BhashiniUnavailableError,
)

router = APIRouter(prefix="", tags=["translation"])

@router.get("/languages/supported", response_model=LanguageSupportResponse)
def list_supported_languages():
    langs = get_supported_languages()
    return LanguageSupportResponse(languages=langs)

@router.post("/translate/text", response_model=TranslateTextResponse)
async def translate_text_endpoint(payload: TranslateTextRequest):
    try:
        translated = await translate_text(
            text=payload.text,
            source_lang=payload.source_lang,
            target_lang=payload.target_lang
        )
        return TranslateTextResponse(
            translated_text=translated,
            source_lang=payload.source_lang,
            target_lang=payload.target_lang,
            translation_unavailable=False
        )
    except BhashiniUnavailableError as err:
        # Fallback gracefully
        return TranslateTextResponse(
            translated_text=payload.text,
            source_lang=payload.source_lang,
            target_lang=payload.target_lang,
            translation_unavailable=True
        )
