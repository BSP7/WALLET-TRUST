import pytest
import json
import io
from unittest.mock import patch, MagicMock

def test_complete_integration_workflow(client, mock_crypto_manager, mock_ipfs, mock_web3_manager, mock_token_client):
    """
    Test the complete MVP workflow:
    User Registration -> Upload -> Encrypt -> IPFS -> Token Gen -> Company Registration -> Token Verify -> Validation Logged
    """
    # 1. User Registration
    user_payload = {
        'name': 'Integration User',
        'email': 'integration_user@example.com',
        'password': 'StrongPassword123!',
        'phone': '+1987654321',
        'dob': '1985-05-15'
    }
    reg_res = client.post('/api/auth/register', json=user_payload)
    assert reg_res.status_code == 201
    user_token = json.loads(reg_res.data)['access_token']

    # 2. Document Upload & IPFS Storage & Encryption
    upload_res = client.post('/api/documents/upload', headers={
        'Authorization': f'Bearer {user_token}'
    }, data={
        'file': (io.BytesIO(b"Integration Document Content"), 'integration.pdf', 'application/pdf'),
        'title': 'My Integration Doc',
        'doc_type': 'passport'
    }, content_type='multipart/form-data')
    print("UPLOAD RES:", upload_res.data)
    assert upload_res.status_code == 200
    upload_data = json.loads(upload_res.data)
    doc_id = upload_data['document']['id']
    
    # 3. Generate Blockchain Token
    user_id = json.loads(reg_res.data)['user']['user_id']
    gen_res = client.post('/api/blockchain/token/generate', headers={
        'Authorization': f'Bearer {user_token}'
    }, json={
        'user_id': user_id,
        'government_id_number': '123456789'
    })
    print("GEN RES:", gen_res.data)
    assert gen_res.status_code == 201
    gen_data = json.loads(gen_res.data)
    blockchain_token = gen_data['token_hash']
    
    # 4. Company Registration
    comp_payload = {
        'company_name': 'Integration Verifiers Inc.',
        'email': 'verifiers@integration.com',
        'password': 'SecureCompanyPass123!'
    }
    comp_reg_res = client.post('/api/company/auth/register', json=comp_payload)
    assert comp_reg_res.status_code == 201
    comp_token = json.loads(comp_reg_res.data)['access_token']
    
    # 5. Company Verifies Token
    verify_res = client.post('/api/blockchain/token/verify', headers={
        'Authorization': f'Bearer {comp_token}'
    }, json={
        'token': blockchain_token
    })
    assert verify_res.status_code == 200
    verify_data = json.loads(verify_res.data)
    assert verify_data['valid'] is True
    
    # 6. Retrieve Validation History
    history_res = client.get('/api/company/validations', headers={
        'Authorization': f'Bearer {comp_token}'
    })
    assert history_res.status_code == 200
    history_data = json.loads(history_res.data)
    
    validations = history_data['validations']
    assert len(validations) > 0
    assert validations[0]['token'] == blockchain_token
    assert validations[0]['is_valid'] is True
