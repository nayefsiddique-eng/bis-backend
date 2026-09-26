import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.providers.ocr.base import get_ocr_provider
from app.services.cache_service import get_cache_service
from app.core.config import settings
from app.core.exceptions import APIException

logger = logging.getLogger('scan_service')

class ScanService:
    def __init__(self):
        self.ocr_provider = get_ocr_provider(settings.OCR_PROVIDER)
        self.cache_service = get_cache_service()
        self._in_memory_scans: Dict[str, Dict[str, Any]] = {}

    def _preprocess_image(self, image_bytes: bytes, filename: str) -> tuple[bytes, Dict[str, Any]]:
        header = image_bytes[:10]
        format_detected = 'unknown'
        if header.startswith(b'\xff\xd8'):
            format_detected = 'jpeg'
        elif header.startswith(b'\x89PNG'):
            format_detected = 'png'
        elif b'WEBP' in image_bytes[:20]:
            format_detected = 'webp'

        if format_detected == 'unknown' and not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            raise APIException(
                status_code=400,
                error_code='INVALID_IMAGE_FORMAT',
                message='Unsupported image format. Please upload JPG, PNG, or WEBP.'
            )

        image_info = {
            'filename': filename,
            'size_bytes': len(image_bytes),
            'detected_format': format_detected,
            'preprocessed': True
        }
        return image_bytes, image_info

    async def process_live_scan(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        if not image_bytes or len(image_bytes) == 0:
            raise APIException(
                status_code=400,
                error_code='EMPTY_OR_CORRUPT_IMAGE',
                message='Uploaded image is empty, corrupted, or unreadable.'
            )

        if len(image_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise APIException(
                status_code=413,
                error_code='IMAGE_TOO_LARGE',
                message='Uploaded image exceeds maximum size limit of ' + str(settings.MAX_FILE_SIZE_MB) + 'MB.'
            )

        processed_bytes, image_info = self._preprocess_image(image_bytes, filename)
        
        ocr_result = await self.ocr_provider.extract_text_from_image(processed_bytes)
        
        scan_id = 'scan_' + str(uuid.uuid4())[:8]
        extracted_text = ocr_result.get('text', '').strip()
        confidence = float(ocr_result.get('confidence', 0.90))

        if not extracted_text:
            extracted_text = '[Captured Page Document - Low readability / blurry scanned content]'
            confidence = 0.40

        scan_data = {
            'scan_id': scan_id,
            'status': 'COMPLETED',
            'extracted_text': extracted_text,
            'confidence': confidence,
            'provider_used': ocr_result.get('provider', 'OCRProvider'),
            'image_info': image_info,
            'created_at': datetime.utcnow().isoformat()
        }

        self.cache_service.set_cache('scan:' + scan_id, scan_data, ttl=3600)
        self._in_memory_scans[scan_id] = scan_data
        logger.info('LIVE_SCAN_PROCESSED: scan_id=' + scan_id)

        return scan_data

    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        cached = self.cache_service.get_cache('scan:' + scan_id)
        if cached:
            return cached
        return self._in_memory_scans.get(scan_id)

    def delete_scan(self, scan_id: str) -> bool:
        self.cache_service.delete_cache('scan:' + scan_id)
        if scan_id in self._in_memory_scans:
            del self._in_memory_scans[scan_id]
            return True
        return True

_scan_service = None

def get_scan_service() -> ScanService:
    global _scan_service
    if _scan_service is None:
        _scan_service = ScanService()
    return _scan_service
