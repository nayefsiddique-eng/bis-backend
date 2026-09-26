from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.schemas.ocr import OCRProcessRequest, OCRProcessResponse
from app.services.ocr_service import get_ocr_service, OCRService

router = APIRouter(prefix="/ocr", tags=['OCR'])

@router.post('/process', response_model=OCRProcessResponse)
async def process_ocr(request: OCRProcessRequest, ocr_service: OCRService = Depends(get_ocr_service)):
    return await ocr_service.process_image_page(document_id=request.document_id, page_number=request.page_number or 1)

