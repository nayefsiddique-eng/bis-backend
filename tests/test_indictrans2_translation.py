"""
Tests for AI4Bharat IndicTrans2 translation provider.

All model inference is mocked — no real model download or GPU required.
Tests cover:
  - Provider language code mapping (FLORES codes)
  - Singleton initialization logic
  - TranslationService routing (indictrans2 / bhashini / auto / fallback)
  - BIS technical term protection & restoration
  - HTTP endpoint integration
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.translation.base import (
    TranslationService,
    FallbackProvider,
    reset_translation_service,
)
from app.providers.translation.indictrans2 import (
    LANGUAGE_MAP,
    FLORES_TO_ISO,
    _resolve_flores,
    IndicTrans2Provider,
)
from app.services.translation import BhashiniUnavailableError


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def run_async(coro):
    return asyncio.run(coro)


def _make_loaded_provider(device: str = "cpu") -> IndicTrans2Provider:
    """Build a mock IndicTrans2Provider that reports as loaded."""
    provider = IndicTrans2Provider.__new__(IndicTrans2Provider)
    provider._loaded = True
    provider._load_error = None
    provider._device = device
    provider._batch_size = 1
    return provider


# ---------------------------------------------------------------------------
# Language code mapping tests
# ---------------------------------------------------------------------------

class TestLanguageMap:

    def test_all_required_languages_present(self):
        required = ["en", "hi", "te", "ta", "kn", "ml", "mr", "bn", "gu", "pa", "ur"]
        for lang in required:
            assert lang in LANGUAGE_MAP, f"Missing language: {lang}"

    def test_flores_codes_are_correct_format(self):
        for iso, flores in LANGUAGE_MAP.items():
            parts = flores.split("_")
            assert len(parts) == 2, f"Bad FLORES code for {iso}: {flores}"

    def test_english_maps_to_eng_Latn(self):
        assert LANGUAGE_MAP["en"] == "eng_Latn"

    def test_hindi_maps_to_hin_Deva(self):
        assert LANGUAGE_MAP["hi"] == "hin_Deva"

    def test_telugu_maps_to_tel_Telu(self):
        assert LANGUAGE_MAP["te"] == "tel_Telu"

    def test_resolve_flores_known_code(self):
        assert _resolve_flores("hi") == "hin_Deva"
        assert _resolve_flores("en") == "eng_Latn"

    def test_resolve_flores_already_flores(self):
        # Flores codes passed directly should also be accepted
        assert _resolve_flores("hin_Deva") == "hin_Deva"

    def test_resolve_flores_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown language code"):
            _resolve_flores("xx")

    def test_reverse_map_consistent(self):
        for iso, flores in LANGUAGE_MAP.items():
            assert FLORES_TO_ISO[flores] == iso


# ---------------------------------------------------------------------------
# IndicTrans2Provider unit tests
# ---------------------------------------------------------------------------

class TestIndicTrans2Provider:

    def test_device_auto_resolves_to_cpu_when_no_cuda(self):
        with patch("app.providers.translation.indictrans2.IndicTrans2Provider._resolve_device",
                   return_value="cpu"):
            provider = IndicTrans2Provider(device="auto")
            assert provider.device == "cpu"

    def test_provider_initialization_does_not_load_model(self):
        provider = IndicTrans2Provider(device="cpu")
        assert provider.is_loaded is False
        assert provider.status == "model_not_loaded"
        assert provider._en_indic_model is None
        assert provider._indic_en_model is None

    def test_lazy_loading_triggers_on_translate(self):
        async def _test():
            provider = IndicTrans2Provider(device="cpu")
            with patch.object(provider, "load_models") as mock_load, \
                 patch.object(provider, "_run_translation", return_value="नमस्ते"):
                
                # Mock load_models so it marks as loaded
                def _fake_load():
                    provider._loaded = True
                mock_load.side_effect = _fake_load

                result = await provider.translate("hello", "en", "hi")
                assert result == "नमस्ते"
                mock_load.assert_called_once()

        run_async(_test())

    def test_translate_raises_load_error_message(self):
        async def _test():
            provider = IndicTrans2Provider.__new__(IndicTrans2Provider)
            provider._loaded = False
            provider._load_error = "ImportError: No module named torch"
            provider._device = "cpu"

            with pytest.raises(RuntimeError, match="previously failed to load"):
                await provider.translate("hello", "en", "hi")

        run_async(_test())

    def test_translate_same_lang_returns_input(self):
        async def _test():
            provider = _make_loaded_provider()
            # Patch _run_translation to ensure it's never called
            provider._run_translation = MagicMock()

            result = await provider.translate("hello", "en", "en")
            assert result == "hello"
            provider._run_translation.assert_not_called()

        run_async(_test())

    def test_translate_calls_run_translation(self):
        async def _test():
            provider = _make_loaded_provider()

            with patch.object(
                provider,
                "_run_translation",
                return_value="नमस्ते",
            ) as mock_run:
                result = await provider.translate("hello", "en", "hi")

            assert result == "नमस्ते"
            mock_run.assert_called_once_with("hello", "eng_Latn", "hin_Deva")

        run_async(_test())

    def test_is_loaded_property(self):
        provider = _make_loaded_provider()
        assert provider.is_loaded is True
        assert provider.status == "model_loaded"

    def test_device_property(self):
        provider = _make_loaded_provider(device="cuda")
        assert provider.device == "cuda"



# ---------------------------------------------------------------------------
# TranslationService routing tests
# ---------------------------------------------------------------------------

class TestTranslationServiceRouting:

    def setup_method(self):
        reset_translation_service()

    def _make_service(self) -> TranslationService:
        it2 = _make_loaded_provider()
        it2.translate = AsyncMock(return_value="indictrans2 output")

        bhashini = MagicMock()
        bhashini.translate = AsyncMock(return_value="bhashini output")

        return TranslationService(
            indictrans2_provider=it2,
            bhashini_provider=bhashini,
        )

    def test_explicit_indictrans2(self):
        async def _test():
            svc = self._make_service()
            result = await svc.translate("Hello", "en", "hi", provider="indictrans2")
            assert result["provider_used"] == "indictrans2"
            assert result["translated_text"] == "indictrans2 output"

        run_async(_test())

    def test_explicit_bhashini(self):
        async def _test():
            svc = self._make_service()
            result = await svc.translate("Hello", "en", "hi", provider="bhashini")
            assert result["provider_used"] == "bhashini"
            assert result["translated_text"] == "bhashini output"

        run_async(_test())

    def test_same_lang_skips_translation(self):
        async def _test():
            svc = self._make_service()
            result = await svc.translate("Hello", "en", "en", provider="indictrans2")
            assert result["provider_used"] == "none"
            assert result["translated_text"] == "Hello"
            svc._indictrans2.translate.assert_not_called()

        run_async(_test())

    def test_empty_text_skips_translation(self):
        async def _test():
            svc = self._make_service()
            result = await svc.translate("   ", "en", "hi", provider="indictrans2")
            assert result["provider_used"] == "none"
            svc._indictrans2.translate.assert_not_called()

        run_async(_test())

    def test_auto_prefers_bhashini_when_configured(self):
        async def _test():
            svc = self._make_service()

            with patch("app.providers.translation.base.settings") as mock_cfg:
                mock_cfg.BHASHINI_USER_ID = "uid"
                mock_cfg.BHASHINI_API_KEY = "key"

                result = await svc.translate("Hello", "en", "hi", provider="auto")
                assert result["provider_used"] == "bhashini"
                svc._indictrans2.translate.assert_not_called()

        run_async(_test())

    def test_auto_uses_indictrans2_when_bhashini_unconfigured(self):
        async def _test():
            svc = self._make_service()

            with patch("app.providers.translation.base.settings") as mock_cfg:
                mock_cfg.BHASHINI_USER_ID = ""
                mock_cfg.BHASHINI_API_KEY = ""

                result = await svc.translate("Hello", "en", "hi", provider="auto")
                assert result["provider_used"] == "indictrans2"

        run_async(_test())

    def test_auto_falls_to_passthrough_when_all_fail(self):
        async def _test():
            svc = self._make_service()
            svc._indictrans2.translate = AsyncMock(side_effect=Exception("model error"))
            svc._bhashini.translate = AsyncMock(side_effect=Exception("bhashini error"))

            with patch("app.providers.translation.base.settings") as mock_cfg:
                mock_cfg.BHASHINI_USER_ID = ""
                mock_cfg.BHASHINI_API_KEY = ""

                result = await svc.translate("Hello", "en", "hi", provider="auto")
                assert result["provider_used"] == "fallback_passthrough"
                assert result["translated_text"] == "Hello"

        run_async(_test())

    def test_indictrans2_not_loaded_falls_to_passthrough(self):
        async def _test():
            it2 = IndicTrans2Provider.__new__(IndicTrans2Provider)
            it2.translate = AsyncMock(side_effect=RuntimeError("load failed"))

            svc = TranslationService(indictrans2_provider=it2)
            result = await svc.translate("Hello", "en", "hi", provider="indictrans2")
            assert result["provider_used"] == "fallback_passthrough"

        run_async(_test())


# ---------------------------------------------------------------------------
# BIS technical term protection tests
# ---------------------------------------------------------------------------

class TestTechnicalTermProtection:

    def test_is_standard_numbers_preserved(self):
        svc = TranslationService(indictrans2_provider=None)
        text = "Product must comply with IS 302-1 and IS 1234:2025 standards."
        protected, placeholders = svc._protect_technical_terms(text)
        restored = svc._restore_technical_terms(protected, placeholders)
        assert "IS 302-1" in restored
        assert "IS 1234:2025" in restored

    def test_clause_and_section_preserved(self):
        svc = TranslationService(indictrans2_provider=None)
        text = "See Clause 4.2 and Section 5.3 for more."
        protected, placeholders = svc._protect_technical_terms(text)
        restored = svc._restore_technical_terms(protected, placeholders)
        assert "Clause 4.2" in restored
        assert "Section 5.3" in restored

    def test_measurements_preserved(self):
        svc = TranslationService(indictrans2_provider=None)
        text = "Minimum thickness 5mm, max weight 10kg."
        protected, placeholders = svc._protect_technical_terms(text)
        restored = svc._restore_technical_terms(protected, placeholders)
        assert "5mm" in restored
        assert "10kg" in restored

    def test_bis_identifiers_survive_translation(self):
        async def _test():
            it2 = _make_loaded_provider()

            async def _mock_translate(text, src, tgt):
                # Simulate model translating plain words but leaving placeholders intact
                return text.replace("comply with", "ka paalan karein")

            it2.translate = AsyncMock(side_effect=_mock_translate)
            svc = TranslationService(indictrans2_provider=it2)

            result = await svc.translate(
                "Product must comply with IS 302-1 standards.",
                "en", "hi", provider="indictrans2"
            )
            assert "IS 302-1" in result["translated_text"]
            assert result["provider_used"] == "indictrans2"

        run_async(_test())


# ---------------------------------------------------------------------------
# HTTP endpoint integration test
# ---------------------------------------------------------------------------

class TestTranslationEndpoint:

    def setup_method(self):
        reset_translation_service()

    def test_endpoint_indictrans2_provider(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.config import settings as real_settings

        client = TestClient(app)
        auth = {"X-API-Key": real_settings.API_KEY}

        with patch(
            "app.providers.translation.base.TranslationService.translate",
            new_callable=AsyncMock,
        ) as mock_translate:
            mock_translate.return_value = {
                "translated_text": "नमस्ते",
                "provider_used": "indictrans2",
                "source_lang": "en",
                "target_lang": "hi",
            }
            response = client.post(
                "/api/translation/translate",
                json={"text": "Hello", "source_lang": "en", "target_lang": "hi",
                      "provider": "indictrans2"},
                headers=auth,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["provider_used"] == "indictrans2"
        assert data["translated_text"] == "नमस्ते"

    def test_endpoint_same_lang_no_op(self):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.config import settings as real_settings

        client = TestClient(app)
        auth = {"X-API-Key": real_settings.API_KEY}

        response = client.post(
            "/api/translation/translate",
            json={"text": "Hello", "source_lang": "en", "target_lang": "en",
                  "provider": "indictrans2"},
            headers=auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["translated_text"] == "Hello"
        assert data["provider_used"] == "none"
