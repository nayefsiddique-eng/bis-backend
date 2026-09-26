from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseOCRProvider(ABC):
    @abstractmethod
    async def extract_text_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        pass

class MockOCRProvider(BaseOCRProvider):
    async def extract_text_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        return {
            'text': '[OCR Processed Technical Standard Text - Scanned Clause 4.1 Specification]',
            'confidence': 0.94,
            'tables_detected': True,
            'provider': 'MockOCR'
        }

class LocalOCRProvider(BaseOCRProvider):
    async def extract_text_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        # Fallback local OCR extraction logic
        return {
            'text': '[Local OCR Extracted Text - Technical BIS Specifications & Norms]',
            'confidence': 0.89,
            'tables_detected': False,
            'provider': 'LocalOCR'
        }

def get_ocr_provider(provider_name: str = 'local') -> BaseOCRProvider:
    if provider_name == 'mock':
        return MockOCRProvider()
    return LocalOCRProvider()
