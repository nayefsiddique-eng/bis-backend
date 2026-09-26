import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app, headers={'X-API-Key': settings.API_KEY})

def test_live_scan_invalid_format():
    files = {'file': ('test.txt', b'Plain text content', 'text/plain')}
    res = client.post('/api/documents/scan', files=files)
    assert res.status_code == 400
    assert res.json()['error_code'] == 'INVALID_IMAGE_FORMAT'

def test_live_scan_empty_image():
    files = {'file': ('empty.jpg', b'', 'image/jpeg')}
    res = client.post('/api/documents/scan', files=files)
    assert res.status_code == 400
    assert res.json()['error_code'] == 'EMPTY_OR_CORRUPT_IMAGE'

def test_live_scan_success_and_retrieval():
    fake_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00' + b'Technical BIS Standard Specification Clause 4.1' * 20
    files = {'file': ('camera_page.jpg', fake_jpeg, 'image/jpeg')}

    res_upload = client.post('/api/documents/scan', files=files)
    assert res_upload.status_code == 200
    data_upload = res_upload.json()
    assert 'scan_id' in data_upload
    assert data_upload['status'] == 'COMPLETED'
    assert 'extracted_text' in data_upload
    scan_id = data_upload['scan_id']

    res_get = client.get('/api/documents/scan/' + scan_id)
    assert res_get.status_code == 200
    assert res_get.json()['scan_id'] == scan_id

    chat_payload = {
        'query': 'Compare the operating parameters in this photographed document with verified BIS standards.',
        'scan_id': scan_id,
        'top_k': 3
    }
    res_chat = client.post('/api/chat', json=chat_payload)
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert 'answer' in chat_data
    assert len(chat_data['sources']) > 0
    assert chat_data['sources'][0]['document'] == 'User Captured Document'

    res_del = client.delete('/api/documents/scan/' + scan_id)
    assert res_del.status_code == 200
