import json

def test_user_registration(client, mock_crypto_manager):
    response = client.post('/api/auth/register', json={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'Password123!',
        'phone': '+1234567890',
        'dob': '1990-01-01'
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert data['user']['email'] == 'test@example.com'

def test_user_login(client, mock_crypto_manager):
    # Register first
    client.post('/api/auth/register', json={
        'name': 'Test User 2',
        'email': 'test2@example.com',
        'password': 'Password123!'
    })
    
    # Then login
    response = client.post('/api/auth/login', json={
        'email': 'test2@example.com',
        'password': 'Password123!'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    
def test_invalid_login(client, mock_crypto_manager):
    # Register first
    client.post('/api/auth/register', json={
        'name': 'Test User 3',
        'email': 'test3@example.com',
        'password': 'Password123!'
    })
    
    response = client.post('/api/auth/login', json={
        'email': 'test3@example.com',
        'password': 'WrongPassword123!'
    })
    assert response.status_code == 401

def test_duplicate_registration(client, mock_crypto_manager):
    payload = {
        'name': 'Duplicate User',
        'email': 'dup@example.com',
        'password': 'Password123!'
    }
    res1 = client.post('/api/auth/register', json=payload)
    assert res1.status_code == 201
    
    res2 = client.post('/api/auth/register', json=payload)
    assert res2.status_code == 409

def test_missing_jwt(client):
    res = client.get('/api/users/profile')
    assert res.status_code == 401

def test_invalid_jwt(client):
    res = client.get('/api/users/profile', headers={
        'Authorization': 'Bearer fake.invalid.token'
    })
    assert res.status_code == 401

def test_company_registration_duplicate(client, mock_crypto_manager):
    payload = {
        'company_name': 'Dup Corp',
        'email': 'dup_corp@example.com',
        'password': 'Password123!'
    }
    res1 = client.post('/api/company/auth/register', json=payload)
    assert res1.status_code == 201
    
    res2 = client.post('/api/company/auth/register', json=payload)
    assert res2.status_code == 409
