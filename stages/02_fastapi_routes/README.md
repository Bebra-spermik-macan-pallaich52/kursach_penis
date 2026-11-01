# Этап 2. Маршруты FastAPI

Срок по плану: **09.11.2026**. Самостоятельная накопительная версия: соседние папки для запуска не нужны.

Добавлены HTTP-маршруты списка и создания пользователей, CRUD олимпиад, запись студента и просмотр участников. Год фильтруется параметром year. Тело запроса пока разбирается вручную; отдельных классов схем нет. Авторизация появится на этапе 4. Использовать только локально с учебными данными.

## Установка

Нужны Python **3.12**, установленный и запущенный PostgreSQL и его клиент psql. Docker не используется. Проверено на PostgreSQL 17; запуск Windows и PostgreSQL 18 в этой среде не проверялся. Python 3.14 для закреплённых зависимостей не подходит.

Откройте терминал именно в этой папке, например из корня клона:

```text
cd stages/02_fastapi_routes
```

Базы этого этапа: `olympiads_stage02` и `olympiads_stage02_test`. У других этапов другие имена. Роль `olympiad` общая; если она уже существует, SQL не меняет её пароль. В этом случае укажите её действующий пароль в обеих строках подключения в `.env`.

Windows PowerShell, команды по одной:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 -f scripts/setup_database.sql
.\.venv\Scripts\python.exe scripts/configure.py
.\.venv\Scripts\python.exe scripts/create_test_db.py
.\.venv\Scripts\python.exe -m app.migrate
.\.venv\Scripts\python.exe -m app.init_db --demo
```

Если установлена PostgreSQL 17, замените `18` в пути к psql на `17`. При запросе пароля psql введите пароль администратора postgres, заданный при установке PostgreSQL. Скрипт выполняется через psql, поскольку использует команду `\gexec`; вставлять его целиком в Query Tool pgAdmin нельзя. Создавать базы вручную не требуется. Если порт отличается от 5432, добавьте `-p ВАШ_ПОРТ` к psql и измените порт в `.env` перед выполнением Python-команд, подключающихся к БД.

Linux/macOS, при установленном Python 3.12 и доступной TCP-учётной записи postgres:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
psql -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 -f scripts/setup_database.sql
.venv/bin/python scripts/configure.py
.venv/bin/python scripts/create_test_db.py
.venv/bin/python -m app.migrate
.venv/bin/python -m app.init_db --demo
```

На Linux с peer-аутентификацией вместо команды psql можно выполнить `sudo -u postgres psql -d postgres -v ON_ERROR_STOP=1 < scripts/setup_database.sql`.

Скрипт configure.py создаёт `.env` со случайным ключом JWT и сохраняет существующий файл. Учебный пароль роли БД в `.env.example` — `olympiad_local`. Для своей установки замените его согласованно в PostgreSQL и `.env`. Файлы `.env`, `.venv` и storage с учебными вложениями в Git не загружаются.

## Миграция и данные

`python -m app.migrate` применяет файл `migrations/001_initial.sql` в транзакции и записывает его имя в schema_migrations. Повторный запуск не пересоздаёт таблицы. `python -m app.init_db --demo` сначала выполняет миграцию, затем заполняет только пустую базу. Удаление таблиц и автоматический откат миграции не предусмотрены.

После заполнения: 111 пользователей (1 администратор, 50 преподавателей, 60 студентов), 50 олимпиад, 150 заявок. Вложения пока не создаются; таблица attachments подготовлена для последующих этапов.

## Запуск

Windows:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Linux/macOS:

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`; ReDoc: `http://127.0.0.1:8000/redoc`; состояние БД: `http://127.0.0.1:8000/health`. Маршруты имеют префикс `/api/v1`.

В Swagger выполните `GET /api/v1/users` и найдите ID преподавателя. Для `POST /api/v1/olympiads` используйте его ID, пример тела:

```json
{"title":"Олимпиада Python","teacher_id":2,"start_date":"2026-11-09","end_date":"2026-11-09"}
```

Далее проверьте `GET /api/v1/olympiads?year=2026`, `PATCH /api/v1/olympiads/{id}` и `POST /api/v1/olympiads/{id}/participants/{student_id}`. ID студента берётся из списка пользователей. Дубликат заявки возвращает 409. Удаление олимпиады со связанными заявками запрещено; для проверки DELETE создайте отдельную пустую олимпиаду.

## Если запуск не получился

Если установщик сообщает об отсутствии psycopg-binary, проверьте версию именно `.venv`: должна быть 3.12. Установка Python 3.12 рядом с 3.14 не меняет старое окружение. Создайте новое окружение командой `py -3.12 -m venv .venv` в папке этапа, где `.venv` ещё нет.

Ошибка соединения с БД означает, что нужно проверить службу PostgreSQL, порт, учётную запись и обе строки `.env`. Если порт HTTP 8000 занят, добавьте к Uvicorn `--port 8001` и открывайте документацию на этом порту. Для scripts.smoke в этапе 7 используйте порт 8000.

Фактические проверки этой папки и ограничения перечислены в [CHECKS.md](CHECKS.md).
