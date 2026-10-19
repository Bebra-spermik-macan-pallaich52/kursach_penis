"""Проверка полного сценария через настоящий HTTP-сервер на учебной базе.

Создаёт одну олимпиаду и одного вымышленного студента. Их данные сохраняются
как пример опубликованного протокола. Запуск: python -m scripts.smoke.
"""
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4
import json
import requests

URL = "http://127.0.0.1:8000/api/v1"
ROOT = Path(__file__).resolve().parents[1]


def main():
    def login(username, password):
        response = requests.post(URL + "/auth/token", data={"username": username, "password": password}, timeout=10)
        response.raise_for_status()
        return {"Authorization": "Bearer " + response.json()["access_token"]}

    admin = login("admin", "Admin2026!")
    teacher = login("teacher1", "Teacher2026!")
    response = requests.get(URL + "/users/me", headers=teacher, timeout=10)
    response.raise_for_status()
    teacher_id = response.json()["id"]
    username = "smoke_" + uuid4().hex[:8]
    student_data = {"username": username, "password": "SmokeStudent2026!", "role": "student",
        "fullName": "Учебный Студент Для Проверки", "email": username + "@example.org",
        "birthDate": "2006-05-10", "institution": "Учебный колледж", "educationLevel": "СПО",
        "course": 3, "specialty": "09.02.07"}
    response = requests.post(URL + "/users", json=student_data, headers=teacher, timeout=10)
    response.raise_for_status()
    student = login(username, "SmokeStudent2026!")
    response = requests.post(URL + "/olympiads", json={"title": "Проверка полного сценария FastAPI",
        "teacherId": teacher_id, "startDate": date.today().isoformat(), "endDate": date.today().isoformat()}, headers=admin, timeout=10)
    response.raise_for_status()
    oid = response.json()["id"]
    response = requests.post(URL + f"/olympiads/{oid}/participations", headers=student, timeout=10)
    response.raise_for_status()
    pid = response.json()["id"]
    response = requests.put(URL + f"/participations/{pid}/result", json={"score": 95.5, "result": "winner"}, headers=teacher, timeout=10)
    response.raise_for_status()
    assert requests.get(URL + f"/olympiads/{oid}/protocol", timeout=10).status_code == 404
    for status, header in [("prepared", teacher), ("published", admin)]:
        response = requests.patch(URL + f"/olympiads/{oid}/protocol", json={"status": status}, headers=header, timeout=10)
        response.raise_for_status()
    public = requests.get(URL + f"/olympiads/{oid}/protocol", timeout=10)
    public.raise_for_status()
    assert public.json()["participants"][0]["score"] == 95.5
    target = ROOT / "docs" / "examples"
    target.mkdir(parents=True, exist_ok=True)
    for format in ("docx", "xlsx"):
        response = requests.get(URL + f"/olympiads/{oid}/reports/protocol", params={"format": format}, headers=teacher, timeout=10)
        response.raise_for_status()
        (target / f"protocol.{format}").write_bytes(response.content)
        response = requests.get(URL + "/reports/annual", params={"format": format, "year": date.today().year}, headers=admin, timeout=10)
        response.raise_for_status()
        (target / f"annual.{format}").write_bytes(response.content)
    result = {"checkedAtUtc": datetime.now(timezone.utc).isoformat(), "result": "passed",
              "olympiadId": oid, "checks": ["login", "create_student", "create_olympiad", "enroll",
              "save_result", "private_before_publish", "prepare", "publish", "public_after_publish",
              "protocol_docx", "protocol_xlsx", "annual_docx", "annual_xlsx"]}
    (ROOT / "docs" / "evidence" / "smoke.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

