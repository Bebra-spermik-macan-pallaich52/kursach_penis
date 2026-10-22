# Установка и запуск

Первый этап, ветка `simple-student`. Используются обычная служба PostgreSQL и
виртуальное окружение Python. Docker, Django и отдельный клиент не нужны.

## 1. Подготовка

Установить Python 3.11+ и PostgreSQL 15+ (проверено на Python 3.12.14,
PostgreSQL 17.11). При установке PostgreSQL запомнить пароль администратора.
Служба PostgreSQL должна работать; обычный порт — 5432, порт приложения — 8000.
Скачать эту ветку репозитория и открыть терминал в корне проекта:

```bash
git clone --branch simple-student https://github.com/Bebra-spermik-macan-pallaich52/kursach_penis.git
cd kursach_penis
python -m venv .venv
```

Активировать окружение: Linux/macOS — `source .venv/bin/activate`,
Windows PowerShell — `.venv\Scripts\Activate.ps1`.

```bash
python -m pip install -r requirements.txt
```

## 2. Базы данных

`database.sql` выполняется один раз от имени администратора PostgreSQL.
Он создаёт роль `olympiad`, рабочую базу `olympiads_simple` и отдельную
`olympiads_simple_test`. Учебный пароль роли — `olympiad_local`.

Linux с установленной службой:

```bash
sudo -u postgres psql -v ON_ERROR_STOP=1 -f database.sql
```

Windows: открыть SQL Shell (psql), войти как `postgres` и выполнить:

```sql
\i 'C:/путь/к/kursach_penis/database.sql'
```

macOS: войти в psql под своей административной ролью и выполнить `\i` с полным
путём к файлу. Если роль уже есть от полной версии, пропустить её создание,
выполнить только отсутствующие команды `CREATE DATABASE`. Существующие базы
не удалять. Для этой ветки не использовать рабочую базу полной версии.

## 3. Настройки

Скопировать `.env.example` в `.env` и указать свой порт и пароль PostgreSQL.
Пример для локальной учебной установки:

```dotenv
DATABASE_URL=postgresql+psycopg://olympiad:olympiad_local@localhost:5432/olympiads_simple
TEST_DATABASE_URL=postgresql+psycopg://olympiad:olympiad_local@localhost:5432/olympiads_simple_test
JWT_SECRET=<случайная строка длиной от 32 символов>
```

Сгенерировать секрет и вручную вставить результат вместо заполнителя:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`.env` не включается в Git. Для непустого хранилища можно задать `STORAGE_DIR`;
по умолчанию файлы лежат в `storage/` корня проекта.

## 4. Инициализация и запуск

```bash
python init_db.py
python -m uvicorn app.main:app --reload
```

В пустой базе появятся по 50 записей в `users`, `olympiads`, `participations`,
`attachments` и 50 файлов DOCX. Аккаунты: `admin` / `Admin2026!`,
`teacher1` и `teacher2` / `Teacher2026!`, `student1`…`student47` / `Student2026!`.
Это вымышленные учебные данные. Преподаватели имеют разные ответственные олимпиады.
Первая олимпиада проводится сегодня; остальные относятся к прошлому году.

При повторном запуске непустая база не меняется. Если раньше запускалась старая
минимальная версия с тремя аккаунтами, она не дополняется автоматически: для
проверки нового заполнения создать отдельную пустую базу, указать её в `.env`
и выполнить `init_db.py`. Нужные старые данные не удалять.

Открыть <http://127.0.0.1:8000/> и
<http://127.0.0.1:8000/api/v1/docs>. Нажать **Authorize** для входа по роли.
Первая заявка от `student1` в первую олимпиаду доступна; уже имеющаяся учебная
заявка в этом мероприятии принадлежит другому студенту. Снимок рабочего запуска
на рисунке 1 сделан при проверке на портах 5433/8001, поскольку обычные порты
в проверочной среде заняты основной версией.

![Рисунок 1 — Swagger работающего сервера](illustrations/start.png)

Для v2 открыть `/api/v2/docs`, для ReDoc — `/api/v1/redoc` или `/api/v2/redoc`.
Оформление Swagger/ReDoc загружается через интернет; HTTP API работает локально.
Закрытие сервера: Ctrl+C. Повторный запуск не очищает БД и хранилище.
Проверка бизнес-сценария и методы по ролям описаны в [API.md](API.md).

## 5. Запуск тестов

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

`TEST_DATABASE_URL` обязателен; имя базы должно оканчиваться на `_test`.
Таблицы создаются автоматически, записи тестов откатываются, файлы временные.
Для подробного отчёта:

```bash
python -m pytest --cov-report=html:reports/coverage --junitxml=reports/junit.xml
```

Порог покрытия 80% задан в `pytest.ini`. Отчёты генерируются локально и не
добавляются в Git. Состав проверок: [TEST_PLAN.md](TEST_PLAN.md),
результаты последнего прогона: [TEST_REPORT.md](TEST_REPORT.md).

## 6. Типовые проблемы

| Сообщение / симптом | Действие |
| --- | --- |
| PostgreSQL connection refused | Запустить службу, проверить host/port в `.env` |
| Password authentication failed | Проверить роль и пароль, не использовать пароль администратора для роли olympiad |
| База не существует | Выполнить соответствующий CREATE DATABASE под администратором |
| Relation does not exist | Запустить `python init_db.py` с адресом нужной рабочей базы |
| Ошибка JWT_SECRET | Сгенерировать ключ, заменить заполнитель, перезапустить сервер |
| Не найден пакет | Активировать `.venv`, установить requirements |
| Порт 8000 занят | Остановить свой старый процесс или передать `--port 8001` и изменить адрес браузера |
| Пустая страница Swagger | Проверить доступ к CDN; доступность API проверить через `/api/v1/openapi.json` |
| Файл из базы не скачивается | Проверить наличие соответствующего файла в `storage`; БД и файлы переносятся вместе |
