# 3. Схемы Pydantic

## Установка в Windows

Установите Python **3.12** и PostgreSQL **18**. Служба PostgreSQL должна работать на порту **5432**. Откройте PowerShell в папке `03_pydantic_schemas` и выполняйте команды по одной:

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

При запросе psql введите пароль пользователя `postgres`, заданный при установке PostgreSQL. Для PostgreSQL 17 замените `18` в пути на `17`. Скрипт создаёт базы `olympiads_stage03` и `olympiads_stage03_test` автоматически.

Если роль `olympiad` уже существует с другим паролем, после `configure.py` укажите этот пароль в обеих строках подключения файла `.env`, затем продолжите команды. При другом порте добавьте `-p НОМЕР_ПОРТА` к psql и исправьте порт в `.env` перед подключением Python к БД.

## Запуск

Команда выбирает цикл событий Windows, совместимый с асинхронным psycopg.

```powershell
.\.venv\Scripts\python.exe -m app.run
```

Откройте `http://127.0.0.1:8000/docs`. Вход не требуется.

Остановка сервера: **Ctrl+C**. При следующих запусках повторяйте только команду запуска. Если порт занят, добавьте `--port 8001` и открывайте адрес на порту 8001.
