# Этап 4. Аутентификация и роли

Срок по плану: **23.11.2026**. Полностью самостоятельный проект: достаточно скопировать только эту папку. У него собственные код, зависимости, миграции, настройки, база и хранилище; файлы из корня и соседних проектов не используются.

Добавлены JWT, роли student/teacher/admin, изменение своего профиля, управление аккаунтами, собственные заявки, баллы и результаты, ответственность преподавателя, подготовка, отзыв и публикация протоколов. Публичны только опубликованные результаты. Есть загрузка, замена, скачивание и удаление документов. Генерация документов и отчётов появится на этапе 5. Две версии API: v1 и v2; в v2 список содержит пагинацию и поиск.

## Установка

Нужны Python **3.12**, установленный и запущенный PostgreSQL и его клиент psql. Docker не используется. Проверено на PostgreSQL 17; запуск Windows и PostgreSQL 18 в этой среде не проверялся. Python 3.14 для закреплённых зависимостей не подходит.

Откройте терминал именно в этой папке, например из корня клона (если скопировали только эту папку, сразу откройте её):

```text
cd 04_auth_roles
```

Базы этого этапа: `olympiads_stage04` и `olympiads_stage04_test`. У других этапов другие имена. Роль `olympiad` общая; если она уже существует, SQL не меняет её пароль. В этом случае укажите её действующий пароль в обеих строках подключения в `.env`.

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

Swagger: `http://127.0.0.1:8000/api/v1/docs` и `/api/v2/docs`; ReDoc: `/api/v1/redoc` и `/api/v2/redoc`; проверка БД: `/health`. Документация использует локальные файлы, Интернет для её открытия не нужен.

Учебные аккаунты:

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | admin | Admin2026! |
| Преподаватель | teacher1…teacher50 | Teacher2026! |
| Студент | student1…student60 | Student2026! |

Нажмите Authorize в Swagger и введите логин/пароль. В ручных запросах токен выдаёт `POST /api/v1/auth/token` (форма username/password), затем передавайте `Authorization: Bearer <токен>`. Преподаватель меняет только свои олимпиады. Публикация разрешена администратору после подготовки. Гость видит результаты только после публикации.

## Если запуск не получился

Если установщик сообщает об отсутствии psycopg-binary, проверьте версию именно `.venv`: должна быть 3.12. Установка Python 3.12 рядом с 3.14 не меняет старое окружение. Создайте новое окружение командой `py -3.12 -m venv .venv` в папке этапа, где `.venv` ещё нет.

Ошибка соединения с БД означает, что нужно проверить службу PostgreSQL, порт, учётную запись и обе строки `.env`. Если порт HTTP 8000 занят, добавьте к Uvicorn `--port 8001` и открывайте документацию на этом порту. Для scripts.smoke в этапе 7 используйте порт 8000.

Фактические проверки этой папки и ограничения перечислены в [CHECKS.md](CHECKS.md).
