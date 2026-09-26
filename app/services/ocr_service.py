from typing import Dict, Any
from app.providers.ocr.base import get_ocr_provider
from app.schemas.ocr import OCRProcessResponse

class OCRService:
    def __init__(self):
        self.provider = get_ocr_provider('local')

    async def process_image_page(self, document_id: str, page_number: int = 1, image_bytes: bytes = b'') -> OCRProcessResponse:
        res = await self.provider.extract_text_from_image(image_bytes)
        return OCRProcessResponse(
            document_id=document_id,
            page_number=page_number,
            extracted_text=res['text'],
            confidence=res['confidence'],
            provider_used=res['provider']
        )

_ocr_service = None

def get_ocr_service() -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
