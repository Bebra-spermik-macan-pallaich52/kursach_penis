# Справочник REST API

Базовый путь: `/api/v1`. Для второй версии — `/api/v2`. JSON-поля имеют camelCase.

JWT получается формой POST /auth/token. Остальные тела запросов — JSON, кроме файлов и шаблонов (multipart/form-data).

В таблице «вход» означает Bearer JWT. Конкретные роли и принадлежность проверяются внутри маршрута.

| Метод | Путь | Назначение | Авторизация |
|---|---|---|---|
| POST | `/auth/token` | Получить JWT-токен | гость |
| GET | `/users/me` | Посмотреть свой профиль | вход |
| PATCH | `/users/me` | Изменить свой профиль | вход |
| PUT | `/users/me/password` | Сменить пароль и отозвать старые токены | вход |
| DELETE | `/auth/session` | Завершить все свои сеансы | вход |
| GET | `/users` | Список учетных записей (администратор) | вход |
| POST | `/users` | Создать студента или преподавателя | вход |
| PATCH | `/users/{user_id}` | Редактировать учетную запись | вход |
| GET | `/olympiads` | Все олимпиады, фильтр по году | гость |
| POST | `/olympiads` | Создать олимпиаду | вход |
| GET | `/olympiads/{olympiad_id}` | Карточка олимпиады | гость |
| PATCH | `/olympiads/{olympiad_id}` | Изменить поля карточки | вход |
| PUT | `/olympiads/{olympiad_id}` | Заменить данные карточки | вход |
| DELETE | `/olympiads/{olympiad_id}` | Удалить пустую олимпиаду | вход |
| POST | `/olympiads/{olympiad_id}/participations` | Записаться на олимпиаду | вход |
| GET | `/olympiads/{olympiad_id}/participations` | Заявки для ответственного преподавателя | вход |
| GET | `/users/me/participations` | Свои заявки и опубликованные результаты | вход |
| PUT | `/participations/{participation_id}/result` | Записать баллы и результат | вход |
| DELETE | `/participations/{participation_id}` | Удалить заявку до подготовки протокола | вход |
| GET | `/protocols` | Состояния протоколов (служебный список) | вход |
| GET | `/olympiads/{olympiad_id}/protocol` | Опубликованный протокол (общедоступный) | гость |
| PATCH | `/olympiads/{olympiad_id}/protocol` | Подготовить, отозвать или опубликовать протокол | вход |
| GET | `/olympiads/{olympiad_id}/protocol-draft` | Просмотреть служебный протокол | вход |
| GET | `/olympiads/{olympiad_id}/reports/protocol` | Скачать протокол Word или Excel | вход |
| GET | `/reports/annual` | Годовой отчёт по опубликованным результатам | вход |
| GET | `/olympiads/{olympiad_id}/attachments` | Положение и бланки; задания прошлых лет | гость |
| POST | `/olympiads/{olympiad_id}/attachments` | Прикрепить файл | вход |
| GET | `/attachments/{attachment_id}` | Скачать общедоступный документ | гость |
| PUT | `/attachments/{attachment_id}` | Заменить файл или название | вход |
| DELETE | `/attachments/{attachment_id}` | Удалить документ | вход |
| GET | `/olympiads/{olympiad_id}/attachments/manage` | Все файлы ответственного преподавателя | вход |
| POST | `/olympiads/{olympiad_id}/templates` | Создать положение или бланк Word из текста | вход |

## Список и версии

v1: GET /olympiads?year=2025 возвращает массив объектов.
v2: GET /olympiads?year=2025&search=Python&page=1&pageSize=10 возвращает:

```json
{"items": [], "total": 0, "page": 1, "pageSize": 10}
```

Пустой результат — 200 и пустой массив/список items. page ≥ 1, pageSize 1…100.
Поиск без учёта регистра, символы % и _ считаются обычными символами.
Год — 2000…2100. Сортировка по startDate, затем id обеспечивает стабильность.
v2 сохраняет пути CRUD, авторизацию и предметные ограничения v1.

## Вход и профиль

```python
import requests
base_url = "http://127.0.0.1:8000/api/v1"
response = requests.post(base_url + "/auth/token",
    data={"username": "admin", "password": "Admin2026!"}, timeout=10)
response.raise_for_status()
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(base_url + "/users/me", headers=headers, timeout=10)
print(response.status_code)
print(response.json())
```

Тело смены пароля: {"oldPassword":"Admin2026!","newPassword":"NewAdmin2026!"}.
После PUT /users/me/password старый токен перестаёт действовать.
DELETE /auth/session отзывает все текущие токены пользователя.

## Создание студента

POST /users: преподаватель или администратор. Преподавателя создаёт только администратор.

```json
{
  "username": "new_student", "password": "StudentPass2026!", "role": "student",
  "fullName": "Иванов Иван Иванович", "birthDate": "2006-05-15",
  "email": "new_student@example.org", "institution": "Учебный колледж",
  "educationLevel": "Среднее профессиональное", "course": 3,
  "specialty": "09.02.07 Информационные системы и программирование"
}
```

Логин: 3…50 символов A–Z/a–z/0–9/подчёркивание; пароль: 8…128 символов;
ФИО: 5…150; курс: 1…6; дата рождения строго раньше текущей.
Для student все учебные поля обязательны. email и username уникальны.
Лишние поля отклоняются. Успех — 201, дубликат — 409, валидация — 422.
Ответ не включает хеш, пароль и tokenVersion.
PATCH /users/me разрешает только личные поля. PATCH /users/{id} — администратор;
дополнительно доступны password и isActive. Публичного POST /register нет.

## Карточка олимпиады

POST /olympiads (201), PUT /olympiads/{id} (200) и PATCH (200) — администратор.
teacherId берётся из существующего активного преподавателя, а не из студента.

```json
{"title":"Олимпиада по Python", "description":"Учебное мероприятие",
 "teacherId":2, "startDate":"2026-12-10", "endDate":"2026-12-10"}
```

PUT требует все обязательные поля, PATCH — только изменяемые. Окончание не раньше начала.
После подготовки или публикации изменения запрещены (409).
DELETE возвращает 204 без JSON-тела; удаляется только draft без заявок и файлов.

## Участие и результаты

POST /olympiads/{id}/participations — студент, без тела, ответ 201:

```json
{"id":1,"olympiadId":1,"studentId":52,"fullName":"Иванов Иван Иванович",
 "score":null,"result":null}
```

GET /users/me/participations — собственные заявки. До публикации score/result=null.
GET /olympiads/{id}/participations — ответственный преподаватель или администратор.
PUT /participations/{id}/result:

```json
{"score":95.5,"result":"winner"}
```

Результаты: winner/prize/participant; баллы неотрицательны, максимум 999999.99,
не больше двух знаков после точки. Студент результат не изменяет.
DELETE /participations/{id}: свой студент, ответственный преподаватель или администратор,
только draft, ответ 204. Чужая заявка — 403, отсутствующая — 404.

## Протоколы

GET /protocols — служебный список. Преподаватель получает только свои мероприятия.
GET .../protocol-draft — служебный протокол. GET .../protocol — публичный published.
PATCH .../protocol принимает {"status":"prepared"}, {"status":"draft"}
или {"status":"published"}. Допустимые переходы: draft→prepared,
prepared→draft, prepared→published. Публикация — только администратор.
Статус возвращается как {"status":"prepared"}.
Запрос published→draft возвращает 409. Гостевой протокол до публикации — 404.

## Документы

POST /olympiads/{id}/attachments — multipart: kind, title, file.
kind: regulation/task/certificate/award. Размер до 5 МБ.
Загрузка — 201; PUT /attachments/{id} заменяет файл и метаданные — 200.

```python
with open("regulation.pdf", "rb") as file:
    response = requests.post(base_url + "/olympiads/1/attachments",
        data={"kind":"regulation", "title":"Положение"},
        files={"file":file}, headers=headers, timeout=10)
    print(response.status_code, response.json())
```

POST .../templates — multipart kind/title/text: создание Word из текста, 201.
GET .../attachments — общедоступный список. GET .../attachments/manage — все файлы
ответственного. GET /attachments/{id} скачивает доступный файл как attachment.
DELETE /attachments/{id} — ответственный или администратор, 204.
Бланков award/certificate может быть сколько угодно на одно мероприятие.

## Экспорт

GET /olympiads/{id}/reports/protocol?format=docx или xlsx — ответственный/администратор.
GET /reports/annual?year=2026&format=xlsx — только администратор; поддерживается docx.
Ответ бинарный, 200, с Content-Disposition. Пустой годовой отчёт допустим.

```python
response = requests.get(base_url + "/reports/annual",
    params={"year":2026,"format":"xlsx"}, headers=headers, timeout=10)
response.raise_for_status()
with open("annual.xlsx", "wb") as file:
    file.write(response.content)
```

## Ошибки и спецификация

401 — отсутствующий, просроченный или отозванный токен; 403 — недостаточно прав;
404 — нет записи либо закрыт публичный результат; 409 — дубликат или неверный статус;
413 — файл больше лимита; 422 — неверный формат данных. Для обычных ошибок тело
{"detail":"Описание"}; для валидации detail — массив с loc/msg/type.
Не следует вызывать response.json() у успешного DELETE 204 и бинарного экспорта.

Полные схемы, ограничения, обязательные поля и типы тел приведены в
openapi-v1.json и openapi-v2.json; эти файлы экспортированы из работающего приложения.
