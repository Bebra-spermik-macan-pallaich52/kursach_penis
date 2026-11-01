from datetime import datetime, timedelta, timezone
import jwt
import pytest
from app.config import JWT_SECRET
from app.models.user import User
from app.security import hash_password, verify_password

BASE = '/api/v1'


def student_data(username='new_student'):
    return {'username': username, 'password': 'StudentPass2026!', 'role': 'student',
            'fullName': 'Иванов Иван Иванович', 'email': username + '@example.org',
            'birthDate': '2006-05-15', 'institution': 'Колледж',
            'educationLevel': 'СПО', 'course': 3, 'specialty': '09.02.07'}


def test_password_hashes():
    value = hash_password('TestPass2026!')
    assert value != hash_password('TestPass2026!')
    assert verify_password('TestPass2026!', value)
    assert not verify_password('bad', value)
    assert not verify_password('bad', 'invalid')
    assert not verify_password('bad', 'other$salt$value')


def test_login_profile_logout(client, accounts):
    response = client.post(BASE + '/auth/token', data={'username': 'student', 'password': 'TestPass2026!'})
    assert response.status_code == 200
    header = {'Authorization': 'Bearer ' + response.json()['access_token']}
    profile = client.get(BASE + '/users/me', headers=header)
    assert profile.status_code == 200
    assert profile.json()['fullName'] == accounts['student'].full_name
    assert 'passwordHash' not in profile.json()
    assert client.delete(BASE + '/auth/session', headers=header).status_code == 200
    assert client.get(BASE + '/users/me', headers=header).status_code == 401


@pytest.mark.parametrize('username,password', [('student','wrong'),('missing','TestPass2026!')])
def test_bad_login(client, accounts, username, password):
    assert client.post(BASE + '/auth/token', data={'username':username,'password':password}).status_code == 401


def test_inactive_login(client, db, accounts):
    accounts['student'].is_active = False
    db.commit()
    assert client.post(BASE + '/auth/token', data={'username':'student','password':'TestPass2026!'}).status_code == 401


@pytest.mark.parametrize('token', ['bad.token.value', '', 'undefined'])
def test_invalid_token(client, token):
    assert client.get(BASE + '/users/me', headers={'Authorization': 'Bearer ' + token}).status_code == 401


@pytest.mark.parametrize('subject,expired', [('123456789', False), ('oops',False), ('1',True)])
def test_missing_user_and_expired_token(client, subject, expired):
    now = datetime.now(timezone.utc)
    token = jwt.encode({'sub':subject,'ver':0,'iat':now-timedelta(hours=2),
        'exp':now-timedelta(hours=1) if expired else now+timedelta(hours=1)},JWT_SECRET,algorithm='HS256')
    assert client.get(BASE + '/users/me', headers={'Authorization':'Bearer '+token}).status_code == 401


def test_profile_and_password(client, headers):
    student = headers['student']
    response = client.patch(BASE+'/users/me',json={'fullName':'Новое Тестовое Имя','email':'NEW@example.org'},headers=student)
    assert response.status_code == 200
    assert response.json()['email'] == 'new@example.org'
    assert client.patch(BASE+'/users/me',json={'role':'admin'},headers=student).status_code == 422
    assert client.patch(BASE+'/users/me',json={'birthDate':'2999-01-01'},headers=student).status_code == 422
    assert client.patch(BASE+'/users/me',json={'fullName':None},headers=student).status_code == 422
    assert client.put(BASE+'/users/me/password',json={'oldPassword':'wrong','newPassword':'NewPass2026!'},headers=student).status_code == 400
    assert client.put(BASE+'/users/me/password',json={'oldPassword':'TestPass2026!','newPassword':'NewPass2026!'},headers=student).status_code == 200
    assert client.get(BASE+'/users/me',headers=student).status_code == 401
    assert client.post(BASE+'/auth/token',data={'username':'student','password':'NewPass2026!'}).status_code == 200


@pytest.mark.parametrize('actor,status', [('admin',201),('teacher',201),('student',403)])
def test_create_student(client, headers, actor, status):
    response=client.post(BASE+'/users',json=student_data(),headers=headers[actor])
    assert response.status_code==status
    if status==201:
        assert response.json()['course']==3
        assert 'password' not in response.json()


def test_create_teacher_and_duplicate(client, headers):
    data={'username':'new_teacher','password':'TeacherPass2026!', 'fullName':'Преподаватель Тестовый Новый', 'email':'new_teacher@example.org','role':'teacher'}
    assert client.post(BASE+'/users',json=data,headers=headers['teacher']).status_code==403
    assert client.post(BASE+'/users',json=data,headers=headers['admin']).status_code==201
    assert client.post(BASE+'/users',json=data,headers=headers['admin']).status_code==409


@pytest.mark.parametrize('changes', [{'course':0},{'course':7},{'email':'not-mail'},{'password':'123'},
    {'birthDate':'2999-01-01'},{'institution':''},{'role':'admin'},{'birthDate':None},{'username':'bad name'}])
def test_user_validation(client, headers, changes):
    data=student_data(); data.update(changes)
    assert client.post(BASE+'/users',json=data,headers=headers['teacher']).status_code==422


def test_admin_accounts(client, accounts, headers):
    assert client.get(BASE+'/users',headers=headers['admin']).status_code==200
    assert client.get(BASE+'/users',headers=headers['teacher']).status_code==403
    student_id=accounts['student'].id
    response=client.patch(BASE+f'/users/{student_id}',json={'password':'AnotherPass2026!','isActive':False},headers=headers['admin'])
    assert response.status_code==200
    assert not response.json()['isActive']
    assert client.get(BASE+'/users/me',headers=headers['student']).status_code==401
    assert client.patch(BASE+f'/users/{accounts["admin"].id}',json={'isActive':False},headers=headers['admin']).status_code==409
    assert client.patch(BASE+'/users/9999999',json={'fullName':'Тестовое Имя Фамилия'},headers=headers['admin']).status_code==404
    assert client.patch(BASE+f'/users/{student_id}',json={'isActive':None},headers=headers['admin']).status_code==422


def test_duplicate_profile_email(client, accounts, headers):
    assert client.patch(BASE+'/users/me',json={'email':accounts['admin'].email},headers=headers['student']).status_code==409
