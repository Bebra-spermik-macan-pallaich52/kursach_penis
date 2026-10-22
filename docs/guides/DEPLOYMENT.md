# Установка и обслуживание

## Что нужно установить

- Python 3.12 с модулем venv и pip.
- PostgreSQL 17 как обычную службу операционной системы.
- Клиентские команды psql, pg_dump, pg_restore из комплекта PostgreSQL.

Python-приложение работает в `.venv`, а база — отдельным процессом PostgreSQL.
Контейнеры и Docker для установки, запуска и тестирования не используются.
Основные команды выполняются из корня проекта.

## Windows

1. Установите Python 3.12, включив добавление в PATH.
2. Скачайте установщик с [официального сайта PostgreSQL](https://www.postgresql.org/download/windows/).
   Установите сервер и Command Line Tools; pgAdmin можно установить для удобства.
3. Во время установки задайте и запомните пароль администратора `postgres`.
   Оставьте порт 5432, если он свободен.
4. В приложении «Службы» убедитесь, что служба PostgreSQL запущена.
   Имя зависит от установщика, обычно `postgresql-x64-17`.
5. Добавьте `C:\Program Files\PostgreSQL\17\bin` в PATH или вызывайте psql полным путём.

Например, в PowerShell из корня проекта:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 -f scripts/setup_database.sql
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.venv\Scripts\python.exe scripts/configure.py
.venv\Scripts\python.exe scripts/create_test_db.py
.venv\Scripts\python.exe -m app.init_db --demo
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

При работе через pgAdmin подключитесь администратором к базе `postgres` и
выполните три команды из setup_database.sql **по одной** с включённым autocommit.
CREATE DATABASE нельзя выполнять внутри блока транзакции. Активация venv
в PowerShell необязательна: прямой вызов `.venv\Scripts\python.exe` работает
без изменения политики выполнения скриптов.

## Linux

Установите PostgreSQL из официального репозитория своего дистрибутива.
Например, для Debian/Ubuntu:

```bash
sudo apt update
sudo apt install postgresql postgresql-client python3-venv
sudo systemctl enable --now postgresql
sudo -u postgres psql -d postgres -v ON_ERROR_STOP=1 -f "$PWD/scripts/setup_database.sql"
```

Последнюю команду запускайте из каталога проекта, доступного системному
пользователю postgres. Если каталог закрыт правами, используйте ввод из файла:

```bash
sudo -u postgres psql -d postgres -v ON_ERROR_STOP=1 < scripts/setup_database.sql
```

Дистрибутив устанавливает собственную поддерживаемую версию PostgreSQL;
целевой вариант проекта — 17. Для другой версии отдельно проверьте тесты.
После создания роли и баз:

```bash
bash scripts/setup_environment.sh
.venv/bin/python -m uvicorn app.main:app --reload
```

Скрипт устанавливает зависимости, сохраняет имеющуюся .env, проверяет тестовую
базу и инициализирует учебную БД. Сам сервер PostgreSQL скрипт не устанавливает
и не запускает — это системная служба.

## macOS

Установите PostgreSQL 17 через Homebrew:

```bash
brew install postgresql@17
brew services start postgresql@17
export PATH="$(brew --prefix postgresql@17)/bin:$PATH"
psql -d postgres -v ON_ERROR_STOP=1 -f scripts/setup_database.sql
bash scripts/setup_environment.sh
.venv/bin/python -m uvicorn app.main:app --reload
```

Для доступа к командам после нового открытия терминала добавьте каталог `bin`
в PATH своего shell. При стандартной установке Homebrew локальная
административная роль совпадает с именем пользователя ОС, поэтому здесь не
указано `-U postgres`. Python 3.12 должен быть установлен отдельно; при наличии
нескольких версий создайте venv командой `python3.12 -m venv .venv`.

## Первичная настройка PostgreSQL

Скрипт [setup_database.sql](../../scripts/setup_database.sql) создаёт:

- роль `olympiad` с учебным паролем `olympiad_local`;
- рабочую базу `olympiads`;
- отдельную тестовую базу `olympiads_test`.

Он предназначен для **однократной настройки нового сервера** и останавливается
при ошибке благодаря `ON_ERROR_STOP`. При наличии роли или баз не удаляйте их:
проверьте существующие настройки и создайте только недостающие объекты.
Скрипт не выдаёт прикладной роли права суперпользователя или создания баз.

Команда `scripts/create_test_db.py` проверяет доступность уже созданной тестовой
БД. Она может создать отсутствующую БД, только если пользователь имеет право
CREATEDB; обычной роли из SQL-файла это право не требуется, поскольку тестовая
база заранее создаётся администратором.

Пароль роли, имя базы и порт должны совпадать с `.env`. Если меняете учебный
пароль в SQL, измените обе строки подключения в `.env`. Старые пользовательские
данные и пароли конфигурационные скрипты автоматически не переписывают.

## Настройки приложения

`python scripts/configure.py` создаёт .env из примера со случайным JWT_SECRET,
если файла ещё нет. При наличии .env настройки сохраняются.

| Переменная | Назначение |
|---|---|
| DATABASE_URL | `postgresql+psycopg://olympiad:olympiad_local@localhost:5432/olympiads` |
| TEST_DATABASE_URL | Аналогичное подключение к `olympiads_test`; суффикс `_test` обязателен |
| JWT_SECRET | Случайный ключ минимум 32 символа; configure.py создаёт 64 hex-символа |
| TOKEN_MINUTES | Срок действия токена, по умолчанию 60 минут |
| ADMIN_USERNAME / ADMIN_PASSWORD | Создание первого администратора без --demo |
| STORAGE_DIR | Необязательный путь к файлам вместо storage/ |
| BASE_URL | Базовый адрес requests-клиента |

Для специальных символов пароля в URL используйте URL-кодирование.
Обычно PostgreSQL принимает локальные подключения, а проверка пароля для TCP
использует scram-sha-256. Не включайте trust для сетевых подключений.
Для внешней СУБД задайте соответствующий адрес и требуемые параметры TLS в URL.
Ключи и пароли не публикуются в Git.

## Проверка запуска

1. Убедитесь в готовности сервера: `pg_isready -h localhost -p 5432`.
2. Проверьте вход в БД: `psql -h localhost -U olympiad -d olympiads -c "SELECT 1"`.
3. Выполните `python -m app.init_db --demo` для первого заполнения.
4. Запустите `python -m uvicorn app.main:app --reload`.
5. GET `/health`: ожидается `{"status":"ok","database":"postgresql"}`.
6. GET `/api/v1/olympiads`: список мероприятий; авторизация — POST `/api/v1/auth/token`.
7. `python -m pytest -q`: тесты в отдельной PostgreSQL БД.
8. `python -m scripts.smoke`: HTTP-сценарий с учебными аккаунтами из --demo.

Проверка порта сама по себе не подтверждает вход в БД. create_all создаёт
отсутствующие таблицы, но не мигрирует уже существующие. Изменение моделей
в будущем требует отдельной миграции, а не удаления пользовательской БД.

## Остановка и повторный старт

Ctrl+C останавливает Uvicorn. PostgreSQL продолжает работать как служба ОС.
Данные сохраняются в её каталоге данных. Для повторного запуска приложения
достаточно запущенной службы и команды Uvicorn из активированного venv.

При необходимости остановить PostgreSQL:

- Windows — приложение «Службы», служба установленной PostgreSQL.
- Linux с systemd — `sudo systemctl stop postgresql`; запуск — `sudo systemctl start postgresql`.
- macOS — `brew services stop postgresql@17`; запуск — `brew services start postgresql@17`.

Остановка общей службы затрагивает и другие базы этого сервера. Повторные
configure.py и init_db --demo не очищают существующие настройки и записи.

## Резервное копирование

Остановите Uvicorn на время согласованного копирования БД и файлов storage.
Команды psql/pg_dump/pg_restore должны быть доступны в PATH.
Для копии создайте папку `backup` вручную или командой `mkdir backup`.

```bash
pg_dump -h localhost -p 5432 -U olympiad -d olympiads -Fc -f backup/olympiads.dump
python -c "import shutil; shutil.make_archive('backup/storage', 'zip', '.', 'storage')"
```

Пароль вводится по запросу. Ключ `-f` записывает бинарный дамп непосредственно
в файл, поэтому команды подходят и для PowerShell. Используйте pg_dump той же
основной версии, что сервер, или более новой. В резервную копию входят и дамп,
и файлы одного состояния; .env хранится отдельно с ограниченным доступом.

Для восстановления администратор создаёт новую пустую базу:

```bash
psql -h localhost -U postgres -d postgres -c "CREATE DATABASE olympiads_restore OWNER olympiad"
pg_restore -h localhost -U olympiad -d olympiads_restore --no-owner --exit-on-error backup/olympiads.dump
```

На macOS используйте имя административной роли своей установки вместо postgres.
Распакуйте storage.zip во временный каталог, проверьте файлы и перенесите storage
в восстановленный проект. Укажите новую БД в .env, запустите сервер и проверьте
профиль, список мероприятий и скачивание документов. Текущую рабочую БД
автоматически не удаляйте и не заменяйте.

## Диагностика

- `psql` не найден: добавьте bin PostgreSQL в PATH или укажите полный путь.
- Connection refused: проверьте службу, порт и адрес; выполните pg_isready.
- Неверный пароль: проверьте роль в PostgreSQL и обе строки подключения в .env.
- Permission denied to create database: создайте тестовую БД от администратора
  по setup_database.sql; не выдавайте приложению права суперпользователя.
- Порт 5432 занят: используйте имеющуюся установку или выберите другой порт
  PostgreSQL и укажите его в обеих строках подключения.
- Ошибка JWT_SECRET: создайте .env через configure.py либо исправьте ключ в
  существующем файле; configure.py его не перезаписывает.
- Документ возвращает 404: проверьте соответствующие файлы storage и копию БД.
- Нет учебных аккаунтов после --demo: база уже была непустой; используйте
  существующие аккаунты либо другую отдельную учебную БД.

TLS, аудит, ограничение частоты входа и нагрузочная пригодность для большого
числа пользователей требуют отдельных решений при реальном размещении.


## Фактическая проверка установки

На снимке ниже — вывод реально выполненных команд подключения к обычной
PostgreSQL, повторного наполнения и подсчёта записей в отдельной проверочной
базе. Вывод показан браузером из сохранённого журнала команд; это не снимок
окна SQL Shell. Порты проверки 5433/8001, стандартные в инструкции 5432/8000.

![Подключение PostgreSQL и проверка данных](../testing/illustrations/setup.png)

![Работающий Swagger основной ветки](../testing/illustrations/start.png)
