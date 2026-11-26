import json
import pytest
from tests.test_accounts import student_data
from tests.test_olympiads import payload


@pytest.mark.parametrize('value', [0, -1])
@pytest.mark.parametrize('path', ['/olympiads/{id}', '/olympiads/{id}/protocol', '/attachments/{id}'])
def test_positive_identifiers(client, value, path):
    """Нулевые и отрицательные идентификаторы отклоняются."""
    assert client.get('/api/v1' + path.format(id=value)).status_code == 422


@pytest.mark.parametrize('changes', [
    {'fullName': '     '}, {'birthDate': '1800-01-01'}, {'course': True},
    {'course': 1.5}, {'password': '        '}, {'email': 'x' * 255 + '@example.org'},
])
def test_student_data_limits(client, headers, changes):
    """Поля студента проверяются по типам, длинам и допустимым значениям."""
    data = student_data()
    data.update(changes)
    assert client.post('/api/v1/users', json=data, headers=headers['teacher']).status_code == 422


@pytest.mark.parametrize('changes', [
    {'title': '   '}, {'teacherId': True}, {'teacherId': "1; DROP TABLE users"},
    {'startDate': '1999-01-01'}, {'endDate': '2101-01-01'},
])
def test_olympiad_data_limits(client, headers, accounts, changes):
    """Название, год и идентификатор преподавателя проверяются."""
    data = payload(accounts['teacher'].id)
    data.update(changes)
    assert client.post('/api/v1/olympiads', json=data, headers=headers['admin']).status_code == 422


@pytest.mark.parametrize('search', ['\x00', 'x' * 101])
def test_search_validation(client, search):
    """Некорректный поисковый текст даёт 422."""
    response = client.get('/api/v2/olympiads', params={'search': search})
    assert response.status_code == 422


def test_search_treats_sql_as_text(client, olympiad):
    """SQL-подобный запрос поиска остаётся обычным текстом."""
    response = client.get('/api/v2/olympiads', params={'search': "' OR 1=1 --"})
    assert response.status_code == 200
    assert response.json()['total'] == 0
    assert len(client.get('/api/v1/olympiads').json()) == 1


def test_empty_updates_and_whitespace_template(client, headers, olympiad):
    """Пустое изменение и шаблон из пробелов отклоняются."""
    assert client.patch('/api/v1/users/me', json={}, headers=headers['student']).status_code == 422
    assert client.patch('/api/v1/olympiads/' + str(olympiad.id), json={}, headers=headers['admin']).status_code == 422
    response = client.post('/api/v1/olympiads/' + str(olympiad.id) + '/templates',
                           data={'kind': 'award', 'title': 'Грамота', 'text': '   '}, headers=headers['teacher'])
    assert response.status_code == 422


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-Infinity'])
def test_nonfinite_scores(client, headers, olympiad, value):
    """NaN и бесконечность не принимаются в качестве баллов."""
    response = client.post('/api/v1/olympiads/' + str(olympiad.id) + '/participations', headers=headers['student'])
    url = '/api/v1/participations/' + str(response.json()['id']) + '/result'
    response = client.put(url, content='{"score":' + value + ',"result":"winner"}',
                          headers={**headers['teacher'], 'Content-Type': 'application/json'})
    assert response.status_code == 422
    json.loads(response.content, parse_constant=lambda value: pytest.fail('Некорректный JSON: ' + value))
