def test_login_valid_username(client, login_as):
    response = login_as('admin')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/inventory')

def test_login_valid_email(client):
    response = client.post('/login', data={'username': 'manager@test.local', 'password': 'CorrectPass!23'})
    assert response.status_code == 302

def test_login_wrong_password(client):
    response = client.post('/login', data={'username': 'admin', 'password': 'wrong'})
    assert response.status_code == 401
    assert b'Invalid username/email or password' in response.data

def test_login_unknown_user(client):
    response = client.post('/login', data={'username': 'nobody', 'password': 'whatever'})
    assert response.status_code == 401

def test_login_inactive_account(client):
    response = client.post('/login', data={'username': 'inactive', 'password': 'CorrectPass!23'})
    assert response.status_code == 401

def test_login_requires_both_fields(client):
    response = client.post('/login', data={'username': '', 'password': ''})
    assert response.status_code == 400

def test_password_not_returned(client, login_as):
    login_as('admin')
    response = client.get('/inventory')
    assert b'CorrectPass!23' not in response.data

def test_logout_clears_session(client, login_as):
    login_as('admin')
    response = client.post('/logout')
    assert response.status_code == 302 and response.headers['Location'].endswith('/login')
    assert client.get('/inventory').status_code == 302

def test_logout_get_not_allowed(client, login_as):
    login_as('admin')
    assert client.get('/logout').status_code == 405
