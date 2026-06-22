import json
import io

def test_document_upload(client, mock_crypto_manager, mock_ipfs, mock_token_client):
    # Register and login first
    reg = client.post('/api/auth/register', json={
        'name': 'Doc User',
        'email': 'doc@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    data = {
        'file': (io.BytesIO(b"dummy file content"), 'test.pdf', 'application/pdf'),
        'title': 'My Document',
        'doc_type': 'national_id'
    }
    
    res = client.post('/api/documents/upload', headers={
        'Authorization': f'Bearer {token}'
    }, data=data, content_type='multipart/form-data')
    
    assert res.status_code == 200
    res_data = json.loads(res.data)
    assert 'document' in res_data
    assert 'id' in res_data['document']

def test_get_documents(client, mock_crypto_manager, mock_ipfs):
    reg = client.post('/api/auth/register', json={
        'name': 'Doc User 2',
        'email': 'doc2@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    res = client.get('/api/users/documents', headers={
        'Authorization': f'Bearer {token}'
    })
    assert res.status_code == 200
    res_data = json.loads(res.data)
    assert 'documents' in res_data
    assert isinstance(res_data['documents'], list)

def test_document_upload_unsupported_file(client, mock_crypto_manager, mock_ipfs, mock_token_client):
    reg = client.post('/api/auth/register', json={
        'name': 'Doc User Err',
        'email': 'doc_err@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    # Missing file
    res = client.post('/api/documents/upload', headers={
        'Authorization': f'Bearer {token}'
    }, data={
        'title': 'My Doc',
        'doc_type': 'national_id'
    }, content_type='multipart/form-data')
    assert res.status_code == 400

def test_get_document_by_id_and_download(client, mock_crypto_manager, mock_ipfs, mock_token_client):
    reg = client.post('/api/auth/register', json={
        'name': 'Doc User Get',
        'email': 'doc_get@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    upload_res = client.post('/api/documents/upload', headers={
        'Authorization': f'Bearer {token}'
    }, data={
        'file': (io.BytesIO(b"dummy file"), 'test.pdf', 'application/pdf'),
        'title': 'My Document to Get',
        'doc_type': 'national_id'
    }, content_type='multipart/form-data')
    doc_id = json.loads(upload_res.data)['document']['id']
    
    # Get metadata
    res = client.get(f'/api/documents/{doc_id}', headers={
        'Authorization': f'Bearer {token}'
    })
    assert res.status_code == 200
    
    # Download
    res_dl = client.get(f'/api/documents/{doc_id}/download', headers={
        'Authorization': f'Bearer {token}'
    })
    assert res_dl.status_code == 200, f"Status code is {res_dl.status_code}, data is {res_dl.data}"
    assert res_dl.data == b"dummy file"

def test_get_document_not_found(client, mock_crypto_manager):
    reg = client.post('/api/auth/register', json={
        'name': 'Doc User 404',
        'email': 'doc_404@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    res = client.get('/api/documents/fake_doc_id', headers={
        'Authorization': f'Bearer {token}'
    })
    assert res.status_code == 404

def test_document_forbidden(client, mock_crypto_manager, mock_ipfs, mock_token_client):
    reg1 = client.post('/api/auth/register', json={
        'name': 'Doc User A',
        'email': 'doc_a@example.com',
        'password': 'Password123!'
    })
    token_a = json.loads(reg1.data)['access_token']
    
    reg2 = client.post('/api/auth/register', json={
        'name': 'Doc User B',
        'email': 'doc_b@example.com',
        'password': 'Password123!'
    })
    token_b = json.loads(reg2.data)['access_token']
    
    upload_res = client.post('/api/documents/upload', headers={
        'Authorization': f'Bearer {token_a}'
    }, data={
        'file': (io.BytesIO(b"dummy file"), 'test.pdf', 'application/pdf'),
        'title': 'User A Doc',
        'doc_type': 'national_id'
    }, content_type='multipart/form-data')
    doc_id = json.loads(upload_res.data)['document']['id']
    
    # User B tries to read User A's doc
    res = client.get(f'/api/documents/{doc_id}', headers={
        'Authorization': f'Bearer {token_b}'
    })
    # Should be 403 or 404, we enforce 403 according to standard if ownership checks fail
    # or 404 to not leak existence. Let's assume 404 or 403.
    assert res.status_code in [403, 404]
