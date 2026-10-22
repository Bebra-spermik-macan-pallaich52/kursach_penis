"""Пароль должен сохраняться точно; непригодный для БД/Word текст отклоняется."""
import json
import pytest
from tests.test_accounts import student_data

BASE = "/api/v1"


@pytest.mark.parametrize("password", ["  ExactPass2026!  ", "\tExactPass2026!\t"])
def test_password_keeps_spaces(client, headers, password):
    data = student_data()
    data["password"] = password
    assert client.post(BASE + "/users", headers=headers["teacher"], json=data).status_code == 201
    assert client.post(BASE + "/auth/token", data={
        "username": data["username"], "password": password}).status_code == 200
    assert client.post(BASE + "/auth/token", data={
        "username": data["username"], "password": password.strip()}).status_code == 401


def test_password_change_keeps_exact_old_and_new_values(client, headers):
    url = BASE + "/users/me/password"
    assert client.put(url, headers=headers["student"], json={
        "oldPassword": " TestPass2026! ", "newPassword": "NewPass2026!"}).status_code == 400
    password = " NewExactPass2026! "
    assert client.put(url, headers=headers["student"], json={
        "oldPassword": "TestPass2026!", "newPassword": password}).status_code == 200
    assert client.get(BASE + "/users/me", headers=headers["student"]).status_code == 401
    assert client.post(BASE + "/auth/token", data={
        "username": "student", "password": password}).status_code == 200


def test_admin_password_reset_keeps_spaces(client, headers, accounts):
    password = " ResetExactPass2026! "
    assert client.patch(BASE + f'/users/{accounts["student"].id}',
        headers=headers["admin"], json={"password": password}).status_code == 200
    assert client.post(BASE + "/auth/token", data={
        "username": "student", "password": password}).status_code == 200
    assert client.get(BASE + "/users/me", headers=headers["student"]).status_code == 401


@pytest.mark.parametrize("character", ["\x00", "\x01", "\ud800"],
                         ids=["nul", "xml-control", "unpaired-surrogate"])
def test_invalid_text_is_validation_error(client, headers, accounts, olympiad, character):
    data = {"title": "Название" + character + "проверка",
            "teacherId": accounts["teacher"].id,
            "startDate": olympiad.start_date.isoformat(),
            "endDate": olympiad.end_date.isoformat()}
    response = client.post(BASE + "/olympiads", headers={
        **headers["admin"], "Content-Type": "application/json"},
        content=json.dumps(data, ensure_ascii=True))
    assert response.status_code == 422
    assert client.get(BASE + f"/olympiads/{olympiad.id}").status_code == 200


@pytest.mark.parametrize("part", ["title", "filename", "template"])
def test_invalid_document_text_is_validation_error(client, headers, olympiad, part):
    url = BASE + f"/olympiads/{olympiad.id}"
    if part == "template":
        response = client.post(url + "/templates", headers=headers["teacher"],
            data={"kind": "award", "title": "Бланк", "text": "Текст\x01документа"})
    elif part == "filename":
        # Готовый multipart: httpx в files= сам заменяет NUL на буквальную строку %00.
        body = (b'--edge\r\nContent-Disposition: form-data; name="kind"\r\n\r\naward\r\n'
                b'--edge\r\nContent-Disposition: form-data; name="title"\r\n\r\nBlank\r\n'
                b'--edge\r\nContent-Disposition: form-data; name="file"; filename="x\x00.txt"\r\n'
                b'Content-Type: text/plain\r\n\r\nDocument\r\n--edge--\r\n')
        response = client.post(url + "/attachments",
            headers={**headers["teacher"], "Content-Type": "multipart/form-data; boundary=edge"},
            content=body)
    else:
        response = client.post(url + "/attachments", headers=headers["teacher"],
            data={"kind": "award", "title": "Бланк\x00"},
            files={"file": ("x.txt", b"Document")})
    assert response.status_code == 422
    assert client.get(url + "/attachments").json() == []
