import pytest
import json
from unittest.mock import patch, MagicMock

def test_generate_token_route(client, mock_crypto_manager, mock_web3_manager, mock_token_client, mock_ipfs):
    # Register user
    reg = client.post('/api/auth/register', json={
        'name': 'Generate Token User',
        'email': 'generate@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    # Upload doc to get a document_id
    import io
    upload_res = client.post('/api/documents/upload', headers={
        'Authorization': f'Bearer {token}'
    }, data={
        'file': (io.BytesIO(b"dummy"), 'test.pdf', 'application/pdf'),
        'title': 'My Doc',
        'doc_type': 'national_id'
    }, content_type='multipart/form-data')
    doc_id = json.loads(upload_res.data)['document']['id']
    
    # Generate token
    user_id = json.loads(reg.data)['user']['user_id']
    res = client.post('/api/blockchain/token/generate', headers={
        'Authorization': f'Bearer {token}'
    }, json={
        'user_id': user_id,
        'government_id_number': '123456789'
    })
    
    assert res.status_code == 201
    res_data = json.loads(res.data)
    assert res_data['success'] is True
    assert 'token_hash' in res_data

def test_verify_token_route(client, mock_crypto_manager, mock_web3_manager, mock_token_client):
    # Register company
    reg = client.post('/api/company/auth/register', json={
        'company_name': 'Verifier Route Corp',
        'email': 'verify_route@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    res = client.post('/api/blockchain/token/verify', headers={
        'Authorization': f'Bearer {token}'
    }, json={
        'token': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
    })
    
    assert res.status_code == 200
    res_data = json.loads(res.data)
    assert res_data['valid'] is True
    assert res_data['user_address'] == '0xABC'

def test_verify_token_missing_token(client, mock_crypto_manager):
    # Register company
    reg = client.post('/api/company/auth/register', json={
        'company_name': 'Verifier Fail Corp',
        'email': 'verify_fail@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    res = client.post('/api/blockchain/token/verify', headers={
        'Authorization': f'Bearer {token}'
    }, json={})
    
    assert res.status_code == 400

def test_verify_token_rpc_failure(client, mock_crypto_manager, mock_web3_manager, mock_token_client):
    mock_token_client.verify_token_hash.side_effect = Exception("Web3 exception")
    reg = client.post('/api/company/auth/register', json={
        'company_name': 'RPC Fail Corp',
        'email': 'rpc_fail@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    # Mock an RPC failure returning 500 equivalent via the manager
    
    res = client.post('/api/blockchain/token/verify', headers={
        'Authorization': f'Bearer {token}'
    }, json={
        'token': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
    })
    
    # Standard Flask 500
    assert res.status_code == 500
