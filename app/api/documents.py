from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.schemas.document import DocumentStatusResponse
from app.schemas.scan import ScanProcessResponse, ScanStatusResponse
from app.services.document_service import get_document_service, DocumentService
from app.services.scan_service import get_scan_service, ScanService

router = APIRouter(prefix='/documents', tags=['Documents and Live Scans'])

@router.post('/upload', response_model=DocumentStatusResponse)
async def upload_document(file: UploadFile = File(...), doc_service: DocumentService = Depends(get_document_service)):
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail='Empty file uploaded.')
    return await doc_service.process_document_upload(file.filename, content)

@router.post('/scan', response_model=ScanProcessResponse)
async def scan_live_document(file: UploadFile = File(...), scan_service: ScanService = Depends(get_scan_service)):
    content = await file.read()
    return await scan_service.process_live_scan(content, file.filename)

@router.get('/scan/{scan_id}', response_model=ScanProcessResponse)
async def get_scan_status(scan_id: str, scan_service: ScanService = Depends(get_scan_service)):
    scan = scan_service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail='Temporary document scan not found or expired.')
    return scan

@router.delete('/scan/{scan_id}')
async def delete_scan(scan_id: str, scan_service: ScanService = Depends(get_scan_service)):
    success = scan_service.delete_scan(scan_id)
    return {'status': 'deleted', 'scan_id': scan_id}

@router.get('/{document_id}', response_model=DocumentStatusResponse)
async def get_document_status(document_id: str, doc_service: DocumentService = Depends(get_document_service)):
    doc = doc_service.get_status(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found.')
    return doc
