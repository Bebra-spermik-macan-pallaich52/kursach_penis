# Этап 7. Итоговое API

Срок по плану: **14.12.2026**. Полностью самостоятельный проект: достаточно скопировать только эту папку. У него собственные код, зависимости, миграции, настройки, база и хранилище; файлы из корня и соседних проектов не используются.

Полная версия первого этапа FastAPI. Добавлены пояснительная записка, ER-диаграмма и словарь данных, диаграммы работы, документация методов, руководство и сценарий демонстрации, requests-клиент. Django относится ко второй части и здесь отсутствует.

## Установка

Нужны Python **3.12**, установленный и запущенный PostgreSQL и его клиент psql. Docker не используется. Проверено на PostgreSQL 17; запуск Windows и PostgreSQL 18 в этой среде не проверялся. Python 3.14 для закреплённых зависимостей не подходит.

Откройте терминал именно в этой папке, например из корня клона (если скопировали только эту папку, сразу откройте её):

```text
cd 07_final_api
```

Базы этого этапа: `olympiads_stage07` и `olympiads_stage07_test`. У других этапов другие имена. Роль `olympiad` общая; если она уже существует, SQL не меняет её пароль. В этом случае укажите её действующий пароль в обеих строках подключения в `.env`.

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

После заполнения: 111 пользователей (1 администратор, 50 преподавателей, 60 студентов), 50 олимпиад, 150 заявок, 200 документов. Данные вымышлены и предназначены для проверки. Повторное заполнение сохраняет имеющиеся записи и файлы.

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

## Отчёты

После входа преподавателем откройте `GET /olympiads/{id}/reports/protocol?format=docx` или `format=xlsx` для его олимпиады. Администратор получает годовой отчёт через `GET /reports/annual?year=2026&format=xlsx` (также доступен docx). Маршруты имеют префикс `/api/v1` или `/api/v2`. Внутри DOCX/XLSX находятся таблицы с результатами, файлы открываются в Word/Excel или LibreOffice.

## Автотесты

Сервер Uvicorn для тестов не нужен. Тестовая база уже создана SQL-скриптом. Запуск из папки этапа:

Windows:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=json:reports/coverage.json --junitxml=reports/junit.xml --cov-fail-under=80
```

Linux/macOS:

```bash
.venv/bin/python -m pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=json:reports/coverage.json --junitxml=reports/junit.xml --cov-fail-under=80
```

План и двумерная матрица: [TEST_PLAN.md](docs/testing/TEST_PLAN.md); сценарии: [TEST_CASES.md](docs/testing/TEST_CASES.md); фактические результаты: [TESTING.md](docs/testing/TESTING.md). Описания фикстур приведены в отчёте. Общий порог — 80%; доля выполненных строк app/api и app/services.py проверяется отдельно по coverage.json.

## Документация и демонстрация

- [Документы для сдачи](docs/README.md).
- [Пояснительная записка DOCX](docs/coursework/Пояснительная_записка.docx) и [PDF](docs/coursework/Пояснительная_записка.pdf).
- [Документация API](docs/api/API.md), [план защиты](docs/guides/DEFENSE.md), [требования](docs/coursework/REQUIREMENTS.md).
- [Демонстрация итогового API](DEMO.md).

При запущенном на порту 8000 сервере `python -m scripts.smoke` выполняет полный HTTP-сценарий и сохраняет четыре отчёта в reports/smoke. Сценарий добавляет учебного студента и олимпиаду в рабочую базу. Интерактивный клиент: `python -m client.main`.

Основная инструкция установки — этот README. Общего проекта в корне репозитория нет. Пояснительная записка и руководства этой папки актуализированы под этап 7.

## Если запуск не получился

Если установщик сообщает об отсутствии psycopg-binary, проверьте версию именно `.venv`: должна быть 3.12. Установка Python 3.12 рядом с 3.14 не меняет старое окружение. Создайте новое окружение командой `py -3.12 -m venv .venv` в папке этапа, где `.venv` ещё нет.

Ошибка соединения с БД означает, что нужно проверить службу PostgreSQL, порт, учётную запись и обе строки `.env`. Если порт HTTP 8000 занят, добавьте к Uvicorn `--port 8001` и открывайте документацию на этом порту. Для scripts.smoke в этапе 7 используйте порт 8000.

Фактические проверки этой папки и ограничения перечислены в [CHECKS.md](CHECKS.md).
