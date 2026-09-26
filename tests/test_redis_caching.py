import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.cache_service import get_cache_service

client = TestClient(app, headers={'X-API-Key': 'demo-key-123'})
cache = get_cache_service()

def test_redis_cache_service():
    cache.set_cache('test_key', {'data': 'bis_test'}, ttl=60)
    res = cache.get_cache('test_key')
    assert res is not None
    assert res.get('data') == 'bis_test'
    cache.delete_cache('test_key')

def test_rag_cache_hit_behavior():
    query_payload = {'query': 'What are electrical safety norms for BIS certification?', 'top_k': 3}
    
    # 1st Request: CACHE MISS
    res1 = client.post('/api/chat', json=query_payload)
    assert res1.status_code == 200
    data1 = res1.json()

    # 2nd Request: CACHE HIT
    res2 = client.post('/api/chat', json=query_payload)
    assert res2.status_code == 200
    data2 = res2.json()

    assert data1['answer'] == data2['answer']

def test_document_metadata_caching():
    doc_id = 'doc_redis_test'
    cache.set_cache('document:' + doc_id, {'document_id': doc_id, 'status': 'COMPLETED'}, ttl=60)
    cached_doc = cache.get_cache('document:' + doc_id)
    assert cached_doc['status'] == 'COMPLETED'
    cache.invalidate_document_cache(doc_id)
    assert cache.get_cache('document:' + doc_id) is None
