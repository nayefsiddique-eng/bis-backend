"""
Bhashini NMT translation provider.

API approval is pending. This provider is preserved for future activation.
When credentials are configured, it will be used automatically in 'auto' mode
or explicitly via TRANSLATION_PROVIDER=bhashini.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from app.services.translation import translate_text, BhashiniUnavailableError

__all__ = ["BhashiniProvider", "BhashiniUnavailableError"]


class BaseTranslationProvider(ABC):
    """Inline copy to avoid circular imports with base.py."""
    @abstractmethod
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        pass


class BhashiniProvider(BaseTranslationProvider):
    """
    Wraps the existing Bhashini NMT service (app/services/translation.py).
    API approval pending — implementation is complete, credentials are not yet active.
    """

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return await translate_text(text, source_lang, target_lang)
