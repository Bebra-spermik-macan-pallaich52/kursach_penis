# Установка и запуск в Windows

Выполните команды из [README проекта](../../README.md) в Windows PowerShell.

Нужны Python 3.12, PostgreSQL и работающая служба БД. По умолчанию используются порт 5432, базы olympiads_stage07 и olympiads_stage07_test. SQL-скрипт создаёт базы, app.migrate — таблицы, app.init_db --demo — учебные данные.

При последующих запусках откройте PowerShell в папке проекта и выполните:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Документация API: http://127.0.0.1:8000/api/v1/docs. Остановка — Ctrl+C.
