# Учёт олимпиад — простая версия

Учебный REST-сервис на FastAPI, SQLAlchemy и PostgreSQL. Запуск без Docker.
Код находится в нескольких файлах: маршруты — `app/main.py`, таблицы —
`app/models.py`, проверка входных данных — `app/schemas.py`, авторизация —
`app/auth.py`, работа с базой — `app/database.py`, отчёты — `app/reports.py`.

Это простая версия в ветке `simple-student`. Отдельного клиента и презентации нет.
В [docs](docs/) лежат только материалы сдачи: пояснительная записка, описание API,
установка, план, тест-кейсы и отчёт о тестировании. Тесты находятся в `tests/`.
Учебное заполнение: по 50 пользователей, олимпиад, заявок и документов.
Более подробная версия проекта сохранена в
[ветке main](https://github.com/Bebra-spermik-macan-pallaich52/kursach_penis/tree/main).

## Запуск

Нужны Python 3.11 или новее и установленный PostgreSQL 15 или новее.
PostgreSQL должен быть запущен как обычная служба.

1. Создать виртуальное окружение и установить зависимости:

   ```bash
   python -m venv .venv
   ```

   Linux/macOS: `source .venv/bin/activate`.
   Windows PowerShell: `.venv\Scripts\Activate.ps1`.

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Создать роль и базу из `database.sql`. Например, в Linux:

   ```bash
   sudo -u postgres psql -v ON_ERROR_STOP=1 -f database.sql
   ```

   В Windows открыть SQL Shell (psql) под администратором PostgreSQL
   и выполнить `\i 'C:/путь/к/проекту/database.sql'`.
   Если роль `olympiad` уже есть от основной версии, выполнить только
   строки создания баз `olympiads_simple` и `olympiads_simple_test`.

3. Скопировать `.env.example` в `.env`. Указать свой адрес базы, порт и пароль.
   Выполнить команду и вставить результат в `JWT_SECRET`:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. Создать таблицы с учебными данными и запустить сервер:

   ```bash
   python init_db.py
   python -m uvicorn app.main:app --reload
   ```

Первый запуск создаёт по 50 записей на сущность, включая настоящие DOCX-файлы.
Повторный запуск `init_db.py` не меняет данные непустой базы. Скрипт не создаёт
сам сервер PostgreSQL, роль или базу: они должны существовать до его запуска.
Не подключайте эту версию к базе полной курсовой: используйте `olympiads_simple`.

Swagger: <http://127.0.0.1:8000/api/v1/docs> и
<http://127.0.0.1:8000/api/v2/docs>. ReDoc доступен по тем же адресам с `/redoc`.
Для загрузки оформления документации нужен интернет; сами методы работают локально.

## Аккаунты

| Логин | Пароль | Роль |
| --- | --- | --- |
| admin | Admin2026! | Администратор |
| teacher1, teacher2 | Teacher2026! | Преподаватель |
| student1…student47 | Student2026! | Студент |

Это демонстрационные пароли для локальной учебной базы. Перед использованием
на общем сервере сменить их через `PATCH /users/{user_id}` от администратора.
Пароли хранятся в виде хешей, JWT действует 60 минут.

В Swagger нажать **Authorize**, ввести логин и пароль. Можно также получить
токен через `POST /api/v1/auth/token` с полями формы `username` и `password`,
а затем передавать заголовок `Authorization: Bearer <токен>`.

## Что можно делать

Все пути ниже начинаются с `/api/v1` или `/api/v2`. JSON-поля записываются
через подчёркивание: `teacher_id`, `start_date`, `full_name` и т. д.

| Кто | Основные методы |
| --- | --- |
| Гость | `GET /olympiads?year=2026`, `GET /olympiads/{id}`, опубликованный `GET /olympiads/{id}/protocol`, список и скачивание документов |
| Студент | `GET/PATCH /users/me`, `POST /olympiads/{id}/participations`, `GET /users/me/participations`, `DELETE /participations/{id}` |
| Преподаватель | `POST /users` для студентов, заявки и результаты своих олимпиад, подготовка/отзыв протокола, загрузка документов, скачивание отчётов |
| Администратор | Список, создание и изменение пользователей; `POST/PUT/PATCH/DELETE /olympiads`; публикация протоколов; годовой отчёт |

Для создания пользователя нужны `username`, `password`, `full_name`, `email`,
`role` (`student` или `teacher`). Для студента также обязательны `birth_date`,
`institution`, `education_level`, `course` и `specialty`.

Пример создания олимпиады от администратора:

```json
{
  "title": "Олимпиада по программированию",
  "description": "Учебная олимпиада",
  "teacher_id": 2,
  "start_date": "2026-12-01",
  "end_date": "2026-12-01"
}
```

Для v1 `GET /olympiads` возвращает список. Для v2 метод
`GET /olympiads?page=1&page_size=10&year=2026` возвращает объект
`items`, `total`, `page`, `page_size`. Дополнительно есть поиск `search` по названию.
Остальные методы у версий одинаковые.

## Проверка рабочего сценария

1. Войти как `student1` и записаться на текущую олимпиаду через
   `POST /olympiads/{id}/participations`. Повторная запись вернёт 409.
2. Войти как `teacher1`, получить заявки через
   `GET /olympiads/{id}/participations`. Взять номер новой заявки `student1` и выполнить
   `PUT /participations/{id}/result` с телом
   `{"score": 90, "result": "winner"}`.
   Другие результаты: `prize`, `participant`.
3. Выполнить `PATCH /olympiads/{id}/protocol` с `{"status":"prepared"}`.
   Для этого олимпиада должна закончиться, а результаты всех участников — быть заполнены.
   Учебная текущая олимпиада имеет дату сегодняшнего дня, поэтому сценарий доступен сразу.
4. Войти как `admin`, выполнить тот же PATCH с `{"status":"published"}`.
   До публикации гостям недоступен протокол, студенту скрыты баллы.
5. Скачать `GET /olympiads/{id}/reports/protocol?format=docx` от преподавателя
   или администратора; для Excel передать `format=xlsx`.
   Администратору также доступен `GET /reports/annual?year=2026&format=xlsx`.
   Указать год нужной олимпиады.

Разрешены переходы `draft → prepared → published` и `prepared → draft`.
Публикует только администратор. Чужие олимпиады преподаватель не редактирует.
После подготовки протокола заявки и баллы заблокированы до отзыва в `draft`;
опубликованный протокол отзывать нельзя. Служебный список статусов:
`GET /protocols`, просмотр до публикации: `GET /olympiads/{id}/protocol-draft`.

Документы загружаются через `POST /olympiads/{id}/attachments` (форма: `kind`,
`title`, `file`). Типы: `regulation` — положение, `task` — задание,
`certificate` — сертификат, `award` — грамота. Можно прикрепить несколько файлов.
Поддерживаются PDF, DOCX, XLSX, PNG, JPG, UTF-8 TXT до 5 МБ. Файлы сохраняются
в `storage`, метаданные — в базе. Служебный список всех файлов:
`GET /olympiads/{id}/attachments/manage`, общедоступный список:
`GET /olympiads/{id}/attachments`, скачивание: `GET /attachments/{id}`.
Задания текущего и будущих лет скрыты. Удаление: `DELETE /attachments/{id}`;
для замены передать ту же форму в `PUT /attachments/{id}` — номер документа сохранится.

Пустую олимпиаду можно удалить администратору, пока она в `draft`. Перед удалением
олимпиады с данными нужно удалить её заявки и документы.

## Проверка

В `.env` указать `TEST_DATABASE_URL` отдельной базы с окончанием `_test`.
Рабочую базу для испытаний не использовать. Таблицы в тестовой базе создаются
автоматически, записи каждого теста откатываются, файлы сохраняются во временные папки.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Команда проверяет API и не завершится успешно при покрытии `app` ниже 80%.
Отдельно прогоняются обе версии и проверяется первоначальное заполнение базы.
Подробности: [план](docs/TEST_PLAN.md), [сценарии](docs/TEST_CASES.md),
[фактический отчёт](docs/TEST_REPORT.md).
