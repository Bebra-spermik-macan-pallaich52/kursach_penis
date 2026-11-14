from datetime import datetime, timedelta, timezone
import jwt
import pytest
from app.config import JWT_SECRET
from app.create_token import create_token
from app.refresh_token import refresh_token


@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_refresh_rotates_token(client, accounts, version):
    base = '/api/' + version
    response = client.post(base + '/auth/token', data={'username': 'student', 'password': 'TestPass2026!'})
    token = response.json()['access_token']
    old = {'Authorization': 'Bearer ' + token}
    response = client.post(base + '/auth/refresh', headers=old)
    assert response.status_code == 200
    new_token = response.json()['access_token']
    assert new_token != token
    new = {'Authorization': 'Bearer ' + new_token}
    assert client.get(base + '/users/me', headers=new).status_code == 200
    assert client.get(base + '/users/me', headers=old).status_code == 401
    assert client.post(base + '/auth/refresh', headers=old).status_code == 401
    claims = jwt.decode(new_token, JWT_SECRET, algorithms=['HS256'])
    assert claims['ver'] == 1 and claims['jti']
    response = client.post(base + '/auth/refresh', headers=new)
    assert response.status_code == 200
    assert client.get(base + '/users/me', headers=new).status_code == 401


@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_refresh_rejects_invalid_and_expired_tokens(client, accounts, version):
    url = '/api/' + version + '/auth/refresh'
    assert client.post(url).status_code == 401
    assert client.post(url, headers={'Authorization': 'Bearer invalid'}).status_code == 401
    now = datetime.now(timezone.utc)
    token = jwt.encode({'sub': str(accounts['student'].id), 'ver': 0,
                       'iat': now - timedelta(hours=2), 'exp': now - timedelta(hours=1)},
                      JWT_SECRET, algorithm='HS256')
    assert client.post(url, headers={'Authorization': 'Bearer ' + token}).status_code == 401


def test_refresh_after_account_block(client, accounts, headers):
    response = client.patch('/api/v1/users/' + str(accounts['student'].id),
                            json={'isActive': False}, headers=headers['admin'])
    assert response.status_code == 200
    assert client.post('/api/v1/auth/refresh', headers=headers['student']).status_code == 401


def test_token_functions_and_unique_values(accounts):
    assert create_token.__module__ == 'app.create_token'
    assert refresh_token.__module__ == 'app.refresh_token'
    assert create_token(accounts['student']) != create_token(accounts['student'])
