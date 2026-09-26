import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, headers={"X-API-Key": "demo-key-123"})

def test_api_health():
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.json()['status'] == 'ok'

def test_api_ready():
    res = client.get('/api/ready')
    assert res.status_code == 200
    assert res.json()['status'] == 'ready'

def test_api_chat():
    res = client.post('/api/chat', json={'query': 'What are the safety norms for electrical toys?', 'top_k': 3})
    assert res.status_code == 200
    data = res.json()
    assert 'answer' in data
    assert 'sources' in data
    assert 'confidence' in data

def test_api_flashcards():
    res = client.post('/api/flashcards/generate', json={'count': 3})
    assert res.status_code == 200
    data = res.json()
    assert data['total'] > 0

    res_list = client.get('/api/flashcards')
    assert res_list.status_code == 200

def test_api_ocr():
    res = client.post('/api/ocr/process', json={'document_id': 'doc_test_1', 'page_number': 1})
    assert res.status_code == 200
    assert 'extracted_text' in res.json()

def test_api_translation():
    res = client.post('/api/translation/translate', json={'text': 'IS 9873 Clause 4.1 compliant', 'source_lang': 'en', 'target_lang': 'hi'})
    assert res.status_code == 200
    assert 'translated_text' in res.json()
