# SIH 2026 – AI-Powered Intelligent Assistant for Indian Standards (BIS) Backend

Production-ready backend API providing BIS document intelligence, compliance checking, OCR, multilingual translation (AI4Bharat IndicTrans2 & BHASHINI), flashcards, and live document scanning.

---

## Multilingual Translation Architecture (AI4Bharat IndicTrans2)

The backend features a unified `TranslationService` with clean provider abstraction:
- **IndicTrans2** (`ai4bharat/indictrans2-en-indic-dist-200M` & `ai4bharat/indictrans2-indic-en-dist-200M`): Active provider.
- **BHASHINI**: Preserved provider for future activation (API approval pending).

### Lazy Loading Strategy
To accommodate development environments with limited RAM (~2 GB), **IndicTrans2 model weights are NOT loaded during application startup**.

1. **FastAPI Lifespan Startup**: Instantiates only a lightweight `IndicTrans2Provider` handle. No PyTorch tensors or HuggingFace tokenizers are loaded into memory.
2. **First Translation Request**: Triggers thread-safe lazy loading of model weights and tokenizers in a background worker pool (`ThreadPoolExecutor`).
3. **Subsequent Requests**: Reuse the in-memory loaded models seamlessly.

---

## Deployment & Setup Guide

### 1. Requirements & Environment
- **Python**: 3.12+
- **PyTorch**: 2.5.1+ (CPU or CUDA)
- **Transformers**: 4.46.3+
- **RAM / Hardware Recommendation**:
  - Development / API Startup: Light (~200-300 MB RAM required)
  - Full In-Memory Inference: 4 GB+ RAM or NVIDIA CUDA GPU recommended when serving actual translation inference.

### 2. Hugging Face Authentication (If needed)
For restricted model access or custom environments:
```bash
huggingface-cli login
```

### 3. Environment Configuration (`.env`)
```env
TRANSLATION_PROVIDER=indictrans2
INDICTRANS2_DEVICE=auto   # 'auto' (CUDA if available, else CPU), 'cuda', or 'cpu'
INDICTRANS2_BATCH_SIZE=1
```

---

## Running the Backend

```bash
# Start backend API
uvicorn app.main:app --reload --port 8000
```

---

## API Testing & Verification

### 1. Check Readiness Status
```bash
curl -X GET "http://localhost:8000/api/ready" -H "X-API-Key: demo-key-123"
```
**Response Output**:
```json
{
  "status": "ready",
  "database": "connected",
  "vector_store": "connected",
  "redis": "fallback_in_memory",
  "translation_provider": "indictrans2",
  "indictrans2_status": "model_not_loaded",
  "indictrans2_model_loaded": false,
  "translation_device": "cpu",
  "bhashini_configured": false
}
```

### 2. Test Translation Endpoint (Triggers Lazy Load on 1st request)
```bash
curl -X POST "http://localhost:8000/api/translation/translate" \
  -H "X-API-Key: demo-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What are the requirements in IS 302-1 Clause 4.2?",
    "source_lang": "en",
    "target_lang": "hi",
    "provider": "indictrans2"
  }'
```

---

## Running Tests
```bash
# Run pytest suite (all 75 unit/integration tests use mocked inference and do not load 200M model)
python -m pytest tests/ -v
```
