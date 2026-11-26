import asyncio
import inspect
import threading
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from psycopg import OperationalError
from app.database import connect, fetch_one, get_db
from app.runtime import run
from app.main import app
from app.names import make_full_name
from app.models.user import User
from tests.test_accounts import student_data


def test_async_database_can_execute_queries_together(db):
    """Два запроса одновременно находятся в активном состоянии PostgreSQL."""
    async def check():
        name = 'parallel_' + uuid4().hex
        async with await connect(application_name=name) as first:
            async with await connect(application_name=name) as second:
                async with await connect() as control:
                    tasks = [asyncio.create_task(fetch_one(connection, 'SELECT pg_sleep(%s)', (0.5,)))
                             for connection in (first, second)]
                    seen = False
                    for attempt in range(100):
                        row = await fetch_one(control, """
                            SELECT count(*) AS total FROM pg_stat_activity
                            WHERE application_name = %s AND state = 'active' AND query LIKE %s
                            """, (name, '%pg_sleep%'))
                        if row['total'] == 2:
                            seen = True
                            break
                        await control.commit()
                        await asyncio.sleep(0.01)
                    await asyncio.gather(*tasks)
                    assert seen, 'Два запроса должны выполняться в PostgreSQL одновременно'
    assert inspect.iscoroutinefunction(connect)
    assert inspect.isasyncgenfunction(get_db)
    run(check())


def test_password_check_does_not_block_another_login(client, accounts, monkeypatch):
    """Две проверки пароля выполняются в фоновых потоках одновременно."""
    import app.api.auth as auth
    original = auth.verify_password
    barrier = threading.Barrier(2)

    def check_password(password, stored):
        barrier.wait(timeout=5)
        return original(password, stored)

    monkeypatch.setattr(auth, 'verify_password', check_password)

    async def check():
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as api:
            responses = await asyncio.gather(*[
                api.post('/api/v1/auth/token', data={'username': 'student', 'password': 'TestPass2026!'})
                for _ in range(2)
            ])
            assert [response.status_code for response in responses] == [200, 200]
    run(check())


def test_all_routes_use_async_functions():
    """HTTP-маршруты обеих версий объявлены асинхронными."""
    for application in [route.app for route in app.routes if hasattr(route, 'app') and hasattr(route.app, 'routes')]:
        for route in application.routes:
            if hasattr(route, 'endpoint'):
                assert inspect.iscoroutinefunction(route.endpoint), route.path


def test_name_is_created_outside_the_model():
    """ФИО собирает отдельная функция, отсутствующая в классе пользователя."""
    assert make_full_name('Пеннер', 'Андрей', 'Владимирович') == 'Пеннер Андрей Владимирович'
    assert make_full_name('  Иванов ', ' Иван ') == 'Иванов Иван'
    assert 'make_full_name' not in User.__dict__


@pytest.mark.parametrize('version', ['v1', 'v2'])
def test_create_user_from_name_parts(client, headers, version):
    """API принимает фамилию, имя и отчество отдельными полями."""
    data = student_data('name_parts_' + version)
    data.pop('fullName')
    data.update({'lastName': 'Пеннер', 'firstName': 'Андрей', 'middleName': 'Владимирович'})
    response = client.post('/api/' + version + '/users', json=data, headers=headers['teacher'])
    assert response.status_code == 201
    assert response.json()['fullName'] == 'Пеннер Андрей Владимирович'


@pytest.mark.parametrize('changes', [
    {'lastName': 'Иванов'},
    {'firstName': 'Иван'},
    {'lastName': ' ', 'firstName': 'Иван'},
    {'lastName': 'Иванов', 'firstName': 'Иван', 'fullName': 'Другое Имя'},
])
def test_invalid_name_parts(client, headers, changes):
    """Неполные и противоречивые части ФИО дают 422."""
    data = student_data()
    data.pop('fullName')
    data.update(changes)
    response = client.post('/api/v1/users', json=data, headers=headers['teacher'])
    assert response.status_code == 422
    assert set(response.json()) == {'detail'}


def test_update_profile_from_name_parts(client, headers):
    """При изменении профиля части имени превращаются в строку ФИО."""
    response = client.patch('/api/v1/users/me', json={'lastName': 'Иванов', 'firstName': 'Иван'}, headers=headers['student'])
    assert response.status_code == 200
    assert response.json()['fullName'] == 'Иванов Иван'


def test_database_failure_uses_common_error_format(client, monkeypatch):
    """Недоступная БД возвращает общий формат 503 без реквизитов подключения."""
    import app.database as database

    async def unavailable(*args, **kwargs):
        raise OperationalError('private database password')

    monkeypatch.setattr(database, 'connect', unavailable)
    response = client.get('/api/v1/olympiads')
    assert response.status_code == 503
    assert response.json() == {'detail': 'База данных временно недоступна'}
    assert 'private' not in response.text


def test_unexpected_failure_does_not_disclose_details(client, accounts, monkeypatch):
    """Неожиданная ошибка даёт 500 без внутренних сведений."""
    import app.api.auth as auth

    def failed(*args):
        raise RuntimeError('private credentials')

    monkeypatch.setattr(auth, 'verify_password', failed)
    with TestClient(app, raise_server_exceptions=False) as api:
        response = api.post('/api/v1/auth/token', data={'username': 'student', 'password': 'TestPass2026!'})
    assert response.status_code == 500
    assert response.json() == {'detail': 'Не удалось выполнить операцию'}
    assert 'private' not in response.text
