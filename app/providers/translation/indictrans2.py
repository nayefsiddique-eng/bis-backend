"""
AI4Bharat IndicTrans2 translation provider.

Model: ai4bharat/indictrans2-en-indic-dist-200M  (English → Indian languages)
       ai4bharat/indictrans2-indic-en-dist-200M  (Indian languages → English)

Both models are distilled (~200M params each) and can run on CPU.
They are loaded ONCE at application startup and reused for all requests.

Language codes: IndicTrans2 uses FLORES-200 script codes internally.
The LANGUAGE_MAP below maps standard ISO 639-1 codes to the correct FLORES codes.

Reference: https://github.com/AI4Bharat/IndicTrans2
"""

from __future__ import annotations

import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base interface (inline to avoid circular imports with base.py)
# ---------------------------------------------------------------------------

class BaseTranslationProvider(ABC):
    @abstractmethod
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        pass

# ---------------------------------------------------------------------------
# Centralized language code mapping: ISO 639-1 → IndicTrans2 FLORES-200 codes
# ---------------------------------------------------------------------------
# fmt: off
LANGUAGE_MAP: dict[str, str] = {
    "en":  "eng_Latn",   # English
    "hi":  "hin_Deva",   # Hindi
    "te":  "tel_Telu",   # Telugu
    "ta":  "tam_Taml",   # Tamil
    "kn":  "kan_Knda",   # Kannada
    "ml":  "mal_Mlym",   # Malayalam
    "mr":  "mar_Deva",   # Marathi
    "bn":  "ben_Beng",   # Bengali
    "gu":  "guj_Gujr",   # Gujarati
    "pa":  "pan_Guru",   # Punjabi (Gurmukhi)
    "ur":  "urd_Arab",   # Urdu
    "or":  "ory_Orya",   # Odia
    "as":  "asm_Beng",   # Assamese
    "ne":  "npi_Deva",   # Nepali
    "si":  "sin_Sinh",   # Sinhala
    "sa":  "san_Deva",   # Sanskrit
    "kok": "kok_Deva",   # Konkani
    "mai": "mai_Deva",   # Maithili
    "doi": "doi_Deva",   # Dogri
    "bho": "bho_Deva",   # Bhojpuri
    "mni": "mni_Mtei",   # Manipuri (Meitei)
    "sat": "sat_Olck",   # Santali
    "sd":  "snd_Arab",   # Sindhi
    "ks":  "kas_Arab",   # Kashmiri
    "gom": "gom_Deva",   # Goan Konkani
}
# fmt: on

# Reverse map: FLORES code → ISO 639-1 (for display purposes)
FLORES_TO_ISO: dict[str, str] = {v: k for k, v in LANGUAGE_MAP.items()}

# Languages that require the En→Indic model (target is Indian)
_INDIC_LANGS = set(LANGUAGE_MAP.keys()) - {"en"}


def _resolve_flores(lang: str) -> str:
    """Convert ISO 639-1 code to FLORES-200 code. Raises ValueError for unknown codes."""
    if lang in LANGUAGE_MAP:
        return LANGUAGE_MAP[lang]
    if lang in FLORES_TO_ISO:
        return lang  # already a flores code
    raise ValueError(
        f"Unknown language code: '{lang}'. "
        f"Supported codes: {sorted(LANGUAGE_MAP.keys())}"
    )


# ---------------------------------------------------------------------------
# Singleton thread-pool executor for CPU-bound inference
# ---------------------------------------------------------------------------
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="indictrans2")


# ---------------------------------------------------------------------------
# IndicTrans2Provider
# ---------------------------------------------------------------------------

class IndicTrans2Provider(BaseTranslationProvider):
    """
    AI4Bharat IndicTrans2 local model provider.

    Model loading is LAZY:
      - Instantiation is lightweight and does NOT load models or tokenizers into RAM.
      - Models are loaded into RAM only upon receiving the first actual translation request.
      - Loading is thread-safe using a threading lock.
      - After loading once, the model is reused for subsequent requests.

    Supports CUDA GPU if available, falling back to CPU automatically.
    """

    EN_INDIC_MODEL = "ai4bharat/indictrans2-en-indic-dist-200M"
    INDIC_EN_MODEL = "ai4bharat/indictrans2-indic-en-dist-200M"

    def __init__(self, device: str = "auto", batch_size: int = 1):
        self._device_setting = device
        self._device = self._resolve_device(device)
        self._batch_size = batch_size
        self._en_indic_tokenizer = None
        self._en_indic_model = None
        self._indic_en_tokenizer = None
        self._indic_en_model = None
        self._loaded = False
        self._load_error: Optional[str] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Model loading (Lazy & Thread-safe)
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_device(device: str) -> str:
        """Resolve 'auto' to 'cuda' or 'cpu' depending on availability."""
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return device  # 'cuda' or 'cpu' as explicitly set

    def load_models(self) -> None:
        """
        Lazy-load both IndicTrans2 models synchronously under a thread lock.
        Triggers automatically on first translation request.
        """
        if self._loaded:
            return

        with self._lock:
            if self._loaded:
                return

            try:
                logger.info(
                    "Lazy-loading IndicTrans2 models into RAM on device=%s...",
                    self._device,
                )
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

                logger.info("Loading En→Indic model & tokenizer: %s", self.EN_INDIC_MODEL)
                self._en_indic_tokenizer = AutoTokenizer.from_pretrained(
                    self.EN_INDIC_MODEL, trust_remote_code=True
                )
                self._en_indic_model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.EN_INDIC_MODEL, trust_remote_code=True
                ).to(self._device)
                self._en_indic_model.eval()

                logger.info("Loading Indic→En model & tokenizer: %s", self.INDIC_EN_MODEL)
                self._indic_en_tokenizer = AutoTokenizer.from_pretrained(
                    self.INDIC_EN_MODEL, trust_remote_code=True
                )
                self._indic_en_model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.INDIC_EN_MODEL, trust_remote_code=True
                ).to(self._device)
                self._indic_en_model.eval()

                self._loaded = True
                self._load_error = None
                logger.info("IndicTrans2 models loaded successfully into memory on %s", self._device)

            except Exception as exc:
                self._loaded = False
                self._load_error = str(exc)
                logger.error("Failed to lazy-load IndicTrans2 models: %s", exc)
                raise

    # ------------------------------------------------------------------
    # Inference helpers (sync, run inside executor)
    # ------------------------------------------------------------------

    def _run_translation(self, text: str, src_flores: str, tgt_flores: str) -> str:
        """Synchronous inference — runs inside ThreadPoolExecutor."""
        import torch

        # Select correct model direction
        if src_flores == "eng_Latn":
            tokenizer = self._en_indic_tokenizer
            model = self._en_indic_model
        else:
            tokenizer = self._indic_en_tokenizer
            model = self._indic_en_model

        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        ).to(self._device)

        # Inject source/target language tokens required by IndicTrans2
        forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_flores)

        with torch.no_grad():
            generated = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                num_beams=5,
                max_new_tokens=512,
            )

        return tokenizer.batch_decode(generated, skip_special_tokens=True)[0]

    # ------------------------------------------------------------------
    # Public async translate method
    # ------------------------------------------------------------------

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        src_flores = _resolve_flores(source_lang)
        tgt_flores = _resolve_flores(target_lang)

        if src_flores == tgt_flores:
            return text

        # Trigger lazy model load on first translation request if not loaded yet
        if not self._loaded:
            if self._load_error:
                raise RuntimeError(
                    f"IndicTrans2 models previously failed to load: {self._load_error}"
                )
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(_executor, self.load_models)

        loop = asyncio.get_running_loop()
        fn = partial(self._run_translation, text, src_flores, tgt_flores)
        result: str = await loop.run_in_executor(_executor, fn)
        return result

    # ------------------------------------------------------------------
    # Status / Health helpers
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def device(self) -> str:
        return self._device

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    @property
    def status(self) -> str:
        if self._loaded:
            return "model_loaded"
        if self._load_error:
            return "model_load_failed"
        return "model_not_loaded"


# ---------------------------------------------------------------------------
# Global singleton — one instance shared across all requests
# ---------------------------------------------------------------------------

_indictrans2_singleton: Optional[IndicTrans2Provider] = None


def initialize_indictrans2() -> IndicTrans2Provider:
    """
    Create the lightweight IndicTrans2 provider object.
    Does NOT load the heavy model/tokenizer into memory.
    Model loading happens lazily when the first translation request is processed.
    """
    global _indictrans2_singleton
    if _indictrans2_singleton is not None:
        return _indictrans2_singleton

    provider = IndicTrans2Provider(
        device=settings.INDICTRANS2_DEVICE,
        batch_size=settings.INDICTRANS2_BATCH_SIZE,
    )

    _indictrans2_singleton = provider
    logger.info("IndicTrans2 provider initialized (Lazy mode: model NOT loaded on startup).")
    return _indictrans2_singleton


def _get_indictrans2_singleton() -> Optional[IndicTrans2Provider]:
    """Return the existing singleton (or initialize lightweight object if None)."""
    global _indictrans2_singleton
    if _indictrans2_singleton is None:
        _indictrans2_singleton = initialize_indictrans2()
    return _indictrans2_singleton
