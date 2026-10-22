# Руководство по REST API

Первый этап персонального ТЗ «Пеннер (1).pdf»: REST-сервис FastAPI до 15.12.2026.
Django, пользовательские HTML-формы и их UI-тесты относятся ко второму этапу до
01.05.2027. Адрес после обычного запуска: `http://127.0.0.1:8000`.

## Версии и авторизация

Префикс каждого метода: `/api/v1` или `/api/v2`. Для каждой версии доступны
`/docs`, `/redoc`, `/openapi.json`. Swagger и ReDoc загружают оформление с CDN,
поэтому для этих страниц нужен интернет. Для запросов к локальному API он не нужен.

`POST /auth/token` принимает форму `username`, `password` и возвращает
`{"access_token":"<JWT>","token_type":"bearer"}`. В остальных защищённых запросах
передавать `Authorization: Bearer <JWT>`. Срок JWT — 60 минут. Блокировка или
смена пароля администратором отзывают старые токены. Саморегистрации нет.

Гость не передаёт токен. Студента создаёт преподаватель/администратор,
преподавателя — администратор. Профиль не позволяет изменить роль или активность.
Преподаватель управляет только олимпиадами, в которых он указан ответственным.
Администратор управляет всеми олимпиадами, но не записывает себя как студента.

Все JSON-поля имеют `snake_case`. Даты: `YYYY-MM-DD`. Неизвестные поля и явно
переданные `null` в частичном обновлении отклоняются. В ответах профиля никогда
нет хеша пароля или версии токена. Гостевой протокол содержит только ФИО и результаты.

## Методы

Параметры `{...}` в пути — положительные идентификаторы существующих записей.
В таблице указан путь без префикса версии. Подробные поля запросов перечислены ниже.

| Метод | Путь | Назначение | Доступ |
| --- | --- | --- | --- |
| GET | `/olympiads` | Все олимпиады, фильтр по году | Все |
| POST | `/olympiads` | Создать олимпиаду | Администратор |
| POST | `/auth/token` | Получить JWT-токен | Гость |
| GET | `/users/me` | Посмотреть свой профиль | Вошедший пользователь |
| PATCH | `/users/me` | Изменить свой профиль | Свой профиль |
| GET | `/users` | Список учетных записей (администратор) | Администратор |
| POST | `/users` | Создать студента или преподавателя | Преподаватель: студенты; администратор: студенты и преподаватели |
| PATCH | `/users/{user_id}` | Редактировать учетную запись | Администратор |
| GET | `/olympiads/{olympiad_id}` | Карточка олимпиады | Все |
| PATCH | `/olympiads/{olympiad_id}` | Изменить поля карточки | Администратор, только draft |
| PUT | `/olympiads/{olympiad_id}` | Заменить данные карточки | Администратор, только draft |
| DELETE | `/olympiads/{olympiad_id}` | Удалить пустую олимпиаду | Администратор, пустая олимпиада в draft |
| POST | `/olympiads/{olympiad_id}/participations` | Записаться на олимпиаду | Студент |
| GET | `/olympiads/{olympiad_id}/participations` | Заявки для ответственного преподавателя | Ответственный преподаватель / администратор |
| GET | `/users/me/participations` | Свои заявки и опубликованные результаты | Собственные заявки |
| PUT | `/participations/{participation_id}/result` | Записать баллы и результат | Ответственный преподаватель / администратор, только draft |
| DELETE | `/participations/{participation_id}` | Удалить заявку до подготовки протокола | Свой студент / ответственный преподаватель / администратор, только draft |
| GET | `/protocols` | Состояния протоколов (служебный список) | Преподаватель: свои; администратор: все |
| GET | `/olympiads/{olympiad_id}/protocol` | Опубликованный протокол (общедоступный) | Все, только published |
| PATCH | `/olympiads/{olympiad_id}/protocol` | Подготовить, отозвать или опубликовать протокол | Ответственный преподаватель / администратор; публикация только администратором |
| GET | `/olympiads/{olympiad_id}/protocol-draft` | Просмотреть служебный протокол | Ответственный преподаватель / администратор |
| GET | `/olympiads/{olympiad_id}/reports/protocol` | Скачать протокол Word или Excel | Ответственный преподаватель / администратор |
| GET | `/reports/annual` | Годовой отчёт по опубликованным результатам | Администратор |
| GET | `/olympiads/{olympiad_id}/attachments` | Положение и бланки; задания прошлых лет | Все; задания только прошлых лет |
| POST | `/olympiads/{olympiad_id}/attachments` | Прикрепить файл | Ответственный преподаватель / администратор |
| GET | `/attachments/{attachment_id}` | Скачать общедоступный документ | Все; задания только прошлых лет |
| PUT | `/attachments/{attachment_id}` | Заменить файл или название | Ответственный преподаватель / администратор |
| DELETE | `/attachments/{attachment_id}` | Удалить документ | Ответственный преподаватель / администратор |
| GET | `/olympiads/{olympiad_id}/attachments/manage` | Все файлы ответственного преподавателя | Ответственный преподаватель / администратор |

## Списки, заявки и состояния

В v1 `GET /olympiads?year=2026` возвращает массив. В v2 добавлены параметры
`page` (от 1), `page_size` (1–100, по умолчанию 10), `search` (до 100 символов)
и тот же `year` (2000–2100). Ответ v2:
`{"items":[],"total":0,"page":1,"page_size":10}`. Год — год начала олимпиады.
Все остальные методы и проверки доступа общие для версий.

При записи на олимпиаду тело не требуется. Можно подать заявки на несколько
мероприятий; на каждое — одну. Нужны `draft` и дата окончания не раньше сегодняшней.
Ответ заявки: `id`, `olympiad_id`, `student_id`, `full_name`, `score`, `result`.
В собственном списке добавляются `title`, `protocol_status`. До публикации `score`
и `result` у студента равны `null`. Преподаватель видит баллы до публикации.

Баллы: 0–999999.99, до двух знаков после точки. Результат задаёт преподаватель:
`winner`, `prize`, `participant`. Автоматическое назначение мест не предусмотрено ТЗ.

Статусы: `draft` → `prepared` → `published`, разрешён отзыв `prepared` → `draft`.
Перед подготовкой нужна хотя бы одна заявка, заполненные баллы и результаты,
наступившая дата окончания. Изменять результаты и состав участников можно только
в `draft`. Публикация — право администратора. Публичный протокол имеет поля
`olympiad_id`, `title`, `status`, `participants` (массив заявок с ФИО и результатами).
Неопубликованный протокол возвращает гостю 404. Повторный/запрещённый переход — 409.

## Документы и отчёты

Для загрузки и замены документа передать multipart-форму `kind`, `title`, `file`.
`kind`: `regulation`, `task`, `certificate`, `award`. `title`: 1–150 символов.
PDF, DOCX, XLSX, PNG, JPG/JPEG, UTF-8 TXT: до 5 МБ; проверяется соответствие
содержимого расширению. Положение или бланк создаётся преподавателем в редакторе
и прикрепляется готовым файлом. К одной олимпиаде можно добавить несколько грамот.
PUT заменяет файл и название, сохраняя ID. Старый файл удаляется после сохранения.
Задания текущего и будущих лет отсутствуют в публичном списке и недоступны по ID.

`GET /olympiads/{id}/reports/protocol?format=docx` — протокол Word;
`format=xlsx` — Excel. Протокол содержит №, ФИО, баллы, результат и статус.
`GET /reports/annual?year=2026&format=xlsx` — годовой отчёт; поддерживается и DOCX.
В годовой отчёт попадают опубликованные результаты, по одной строке на участие:
олимпиада, дата начала, ФИО, баллы, результат. Пустой год даёт читаемую пустую таблицу.
Экспорт возвращает двоичные данные и `Content-Disposition: attachment`, а не JSON.

## Коды ответов

| Код | Значение |
| --- | --- |
| 200 | Чтение, обновление, вход, скачивание |
| 201 | Созданы пользователь, олимпиада, заявка или вложение |
| 204 | Удалено; тело ответа пустое |
| 401 | Неверные учётные данные, отсутствующий/истёкший/отозванный JWT |
| 403 | Неподходящая роль или чужая олимпиада/заявка |
| 404 | Нет записи/файла; протокол ещё скрыт; задание текущего года |
| 409 | Дубликат, неверный статус, завершённый приём заявок, зависимые записи |
| 413 | Файл больше 5 МБ |
| 422 | Неверные поля, даты, формат отчёта или содержимое файла |

Ошибка предметной проверки: `{"detail":"Сообщение"}`. Ошибка валидации FastAPI:
`{"detail":[{"loc":["body","title"],"msg":"...","type":"..."}]}`.

## Примеры запросов

Войти можно из Swagger через **Authorize** либо командой:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token -d "username=teacher1&password=Teacher2026!"
```

Создание олимпиады (JSON, токен администратора):

```json
{"title":"Олимпиада Python","description":"Учебная","teacher_id":2,"start_date":"2026-12-01","end_date":"2026-12-01"}
```

Создание студента (JSON, токен преподавателя):

```json
{"username":"new_student","password":"StudentPass2026!","full_name":"Иванов Иван Иванович","email":"new_student@example.org","role":"student","birth_date":"2007-05-15","institution":"Колледж","education_level":"СПО","course":2,"specialty":"09.02.07"}
```

Заполнение результата: `PUT /participations/{id}/result`,
`{"score":95.5,"result":"winner"}`. Подготовка протокола:
`PATCH /olympiads/{id}/protocol`, `{"status":"prepared"}`.
Публикация — тем же методом от администратора с `{"status":"published"}`.

Запрос с заголовком авторизации:

```bash
curl http://127.0.0.1:8000/api/v1/users/me -H "Authorization: Bearer <JWT>"
```

## Схемы запросов и ответов

Схемы ниже получены из OpenAPI проверяемой версии. Для PATCH передавать только
изменяемые поля. PUT карточки принимает ту же полную схему, что и POST.

### AccountUpdate

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `full_name` | string / null | нет | — |
| `email` | email / null | нет | — |
| `birth_date` | date / null | нет | — |
| `institution` | string / null | нет | — |
| `education_level` | string / null | нет | — |
| `course` | integer / null | нет | — |
| `specialty` | string / null | нет | — |
| `is_active` | boolean / null | нет | — |
| `password` | string / null | нет | — |

### AttachmentRead

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `id` | integer | да | — |
| `olympiad_id` | integer | да | — |
| `kind` | string | да | — |
| `title` | string | да | — |
| `original_name` | string | да | — |

### OlympiadCreate

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `title` | string | да | minLength: 3; maxLength: 200 |
| `description` | string | нет | maxLength: 5000; default:  |
| `teacher_id` | integer | да | exclusiveMinimum: 0.0 |
| `start_date` | date | да | — |
| `end_date` | date | да | — |

### OlympiadRead

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `id` | integer | да | — |
| `title` | string | да | — |
| `description` | string | да | — |
| `teacher_id` | integer | да | — |
| `start_date` | date | да | — |
| `end_date` | date | да | — |
| `protocol_status` | string | да | — |

### OlympiadUpdate

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `title` | string / null | нет | — |
| `description` | string / null | нет | — |
| `teacher_id` | integer / null | нет | — |
| `start_date` | date / null | нет | — |
| `end_date` | date / null | нет | — |

### ProfileUpdate

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `full_name` | string / null | нет | — |
| `email` | email / null | нет | — |
| `birth_date` | date / null | нет | — |
| `institution` | string / null | нет | — |
| `education_level` | string / null | нет | — |
| `course` | integer / null | нет | — |
| `specialty` | string / null | нет | — |

### ProtocolUpdate

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `status` | string | да | enum: ['draft', 'prepared', 'published'] |

### ResultUpdate

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `score` | number / string | да | — |
| `result` | string | да | enum: ['winner', 'prize', 'participant'] |

### UserCreate

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `username` | string | да | minLength: 3; maxLength: 50; pattern: ^[a-zA-Z0-9_]+$ |
| `password` | string | да | minLength: 8; maxLength: 128 |
| `full_name` | string | да | minLength: 5; maxLength: 150 |
| `email` | email | да | — |
| `role` | string | да | enum: ['student', 'teacher'] |
| `birth_date` | date / null | нет | — |
| `institution` | string | нет | maxLength: 200; default:  |
| `education_level` | string | нет | maxLength: 100; default:  |
| `course` | integer / null | нет | — |
| `specialty` | string | нет | maxLength: 150; default:  |

### UserRead

| Поле | Тип | Обязательно | Ограничения |
| --- | --- | --- | --- |
| `id` | integer | да | — |
| `username` | string | да | — |
| `full_name` | string | да | — |
| `email` | string | да | — |
| `role` | string | да | — |
| `birth_date` | date / null | да | — |
| `institution` | string | да | — |
| `education_level` | string | да | — |
| `course` | integer / null | да | — |
| `specialty` | string | да | — |
| `is_active` | boolean | да | — |
