import json

def test_company_registration(client, mock_crypto_manager):
    response = client.post('/api/company/auth/register', json={
        'company_name': 'Test Corp',
        'email': 'corp@example.com',
        'password': 'Password123!'
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'access_token' in data

def test_company_login(client, mock_crypto_manager):
    client.post('/api/company/auth/register', json={
        'company_name': 'Test Corp 2',
        'email': 'corp2@example.com',
        'password': 'Password123!'
    })
    
    response = client.post('/api/company/auth/login', json={
        'email': 'corp2@example.com',
        'password': 'Password123!'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data

def test_company_validations_history(client, mock_crypto_manager):
    reg = client.post('/api/company/auth/register', json={
        'company_name': 'Test Corp 3',
        'email': 'corp3@example.com',
        'password': 'Password123!'
    })
    token = json.loads(reg.data)['access_token']
    
    # Fetch validations
    res = client.get('/api/company/validations', headers={
        'Authorization': f'Bearer {token}'
    })
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'validations' in data
    assert isinstance(data['validations'], list)
