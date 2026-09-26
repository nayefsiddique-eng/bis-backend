"""
Translation provider abstraction layer.

Architecture:
    TranslationService.translate()
        ↓
    Provider selected by 'provider' argument
        ↓
    IndicTrans2Provider (local model, active)
    BhashiniProvider   (API pending approval, preserved)
    FallbackProvider   (passthrough, last resort)

No other part of the backend should import providers directly —
always use get_translation_service() and call .translate().
"""

from __future__ import annotations

import re
import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base interface — all providers must implement this
# ---------------------------------------------------------------------------

class BaseTranslationProvider(ABC):
    @abstractmethod
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        pass


# ---------------------------------------------------------------------------
# Passthrough fallback — used when all real providers fail
# ---------------------------------------------------------------------------

class FallbackProvider(BaseTranslationProvider):
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return text


# ---------------------------------------------------------------------------
# TranslationService — singleton orchestrator
# ---------------------------------------------------------------------------

class TranslationService:
    """
    Orchestrates translation across providers.

    Provider routing:
      "indictrans2" → AI4Bharat IndicTrans2 local model (active)
      "bhashini"    → Bhashini NMT API (preserved, API approval pending)
      "auto"        → Bhashini (if configured) → IndicTrans2 → passthrough
      "fallback"    → passthrough (no translation)
    """

    # BIS technical identifiers that must survive translation unchanged.
    # They are replaced with placeholders before translation and restored after.
    _TECH_PATTERNS = [
        r"IS\s*\d+(?:[-:]\d+)?(?::\d{4})?",    # IS 302-1, IS 1234:2025
        r"Clause\s*\d+(?:\.\d+)*",               # Clause 4.2.1
        r"Section\s*\d+(?:\.\d+)*",              # Section 5.3
        r"BIS\b",                                 # BIS standalone
        r"ISI\s+mark",                            # ISI mark
        r"\d+(?:\.\d+)?\s*(?:kg|mm|cm|m|V|A|Hz|MPa|N|kN|kV|kW|W|l|L|ml|ML)",
    ]

    def __init__(
        self,
        indictrans2_provider: Optional[object] = None,
        bhashini_provider: Optional[object] = None,
    ):
        # IndicTrans2 — injected from startup singleton (already loaded)
        self._indictrans2 = indictrans2_provider
        # Bhashini — lazy import to avoid circular deps
        if bhashini_provider is not None:
            self._bhashini = bhashini_provider
        else:
            from app.providers.translation.bhashini import BhashiniProvider
            self._bhashini = BhashiniProvider()
        self._fallback = FallbackProvider()

    # ------------------------------------------------------------------
    # Provider availability checks
    # ------------------------------------------------------------------

    def _bhashini_configured(self) -> bool:
        return bool(settings.BHASHINI_USER_ID and settings.BHASHINI_API_KEY)

    def _indictrans2_ready(self) -> bool:
        return self._indictrans2 is not None

    # ------------------------------------------------------------------
    # Technical term protection
    # ------------------------------------------------------------------

    def _protect_technical_terms(self, text: str) -> tuple[str, dict]:
        placeholders: dict = {}
        counter = 0
        protected = text
        for pat in self._TECH_PATTERNS:
            for m in re.findall(pat, protected, flags=re.IGNORECASE):
                ph = "__TECH_TERM_" + str(counter) + "__"
                placeholders[ph] = m
                protected = protected.replace(m, ph, 1)
                counter += 1
        return protected, placeholders

    def _restore_technical_terms(self, text: str, placeholders: dict) -> str:
        restored = text
        for ph, orig in placeholders.items():
            restored = restored.replace(ph, orig)
        return restored

    # ------------------------------------------------------------------
    # Main translate method
    # ------------------------------------------------------------------

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        provider: str = "auto",
    ) -> dict:
        """
        Translate text and return a structured result dict.

        Args:
            text: Text to translate.
            source_lang: ISO 639-1 source language code (e.g. 'en', 'hi', 'te').
            target_lang: ISO 639-1 target language code.
            provider: 'indictrans2' | 'bhashini' | 'auto' | 'fallback'

        Returns:
            {
                "translated_text": str,
                "provider_used": str,
                "source_lang": str,
                "target_lang": str,
            }
        """
        # Skip translation when not needed
        if source_lang == target_lang or not text.strip():
            return {
                "translated_text": text,
                "provider_used": "none",
                "source_lang": source_lang,
                "target_lang": target_lang,
            }

        protected_text, placeholders = self._protect_technical_terms(text)
        translated_text = ""
        provider_used = ""

        # ---- Explicit: IndicTrans2 ----------------------------------------
        if provider == "indictrans2":
            if self._indictrans2_ready():
                try:
                    translated_text = await self._indictrans2.translate(
                        protected_text, source_lang, target_lang
                    )
                    provider_used = "indictrans2"
                except Exception as exc:
                    logger.warning("IndicTrans2 failed: %s — using passthrough", exc)
            else:
                logger.warning(
                    "IndicTrans2 requested but model not loaded — using passthrough"
                )

        # ---- Explicit: Bhashini -------------------------------------------
        elif provider == "bhashini":
            try:
                from app.services.translation import BhashiniUnavailableError
                translated_text = await self._bhashini.translate(
                    protected_text, source_lang, target_lang
                )
                provider_used = "bhashini"
            except Exception as exc:
                logger.warning("Bhashini failed: %s — using passthrough", exc)

        # ---- Auto: Bhashini → IndicTrans2 → passthrough ------------------
        elif provider == "auto":
            if self._bhashini_configured():
                try:
                    from app.services.translation import BhashiniUnavailableError
                    translated_text = await self._bhashini.translate(
                        protected_text, source_lang, target_lang
                    )
                    provider_used = "bhashini"
                except Exception:
                    logger.info("Bhashini unavailable in auto mode, trying IndicTrans2")

            if not translated_text and self._indictrans2_ready():
                try:
                    translated_text = await self._indictrans2.translate(
                        protected_text, source_lang, target_lang
                    )
                    provider_used = "indictrans2"
                except Exception as exc:
                    logger.info("IndicTrans2 failed in auto mode: %s", exc)

        # ---- Passthrough / unknown ----------------------------------------
        if not translated_text:
            translated_text = await self._fallback.translate(
                text, source_lang, target_lang
            )
            provider_used = "fallback_passthrough"
        else:
            translated_text = self._restore_technical_terms(translated_text, placeholders)

        return {
            "translated_text": translated_text,
            "provider_used": provider_used,
            "source_lang": source_lang,
            "target_lang": target_lang,
        }


# ---------------------------------------------------------------------------
# Singleton management
# ---------------------------------------------------------------------------

_translation_service_instance: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """
    Returns the singleton TranslationService.
    On first call, the IndicTrans2 provider is retrieved from the
    global singleton set during application startup.
    """
    global _translation_service_instance
    if _translation_service_instance is None:
        # Get the already-loaded IndicTrans2 singleton (set by lifespan startup)
        from app.providers.translation.indictrans2 import _get_indictrans2_singleton
        it2 = _get_indictrans2_singleton()
        _translation_service_instance = TranslationService(indictrans2_provider=it2)
    return _translation_service_instance


def reset_translation_service() -> None:
    """Reset singleton — used in tests."""
    global _translation_service_instance
    _translation_service_instance = None
