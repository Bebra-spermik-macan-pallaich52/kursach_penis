# Словарь данных PostgreSQL

Состав и типы столбцов получены из фактической PostgreSQL БД через SQLAlchemy Inspector.

PK — первичный ключ; FK — внешний ключ; UQ — уникальность. Проверки ролей и большинства входных полей выполняются схемами Pydantic и обработчиками API; ограничения БД перечислены отдельно.

## users

| Ключ | Поле | Тип PostgreSQL | NULL | Назначение |
|---|---|---|---|---|
| PK | id | INTEGER | нет | Идентификатор аккаунта |
| UQ | username | VARCHAR(50) | нет | Уникальный логин, 3–50 символов |
| — | password_hash | VARCHAR(256) | нет | PBKDF2-хеш; исходный пароль не хранится |
| — | full_name | VARCHAR(150) | нет | Фамилия, имя, отчество |
| — | birth_date | DATE | да | Дата рождения; для студента обязательна |
| UQ | email | VARCHAR(254) | нет | Уникальная электронная почта |
| — | institution | VARCHAR(200) | нет | Учебное заведение |
| — | education_level | VARCHAR(100) | нет | Уровень образования |
| — | course | INTEGER | да | Курс обучения, 1–6 |
| — | specialty | VARCHAR(150) | нет | Код и название специальности |
| — | role | VARCHAR(20) | нет | admin / teacher / student |
| — | is_active | BOOLEAN | нет | Признак действующего аккаунта |
| — | token_version | INTEGER | нет | Версия токенов для отзыва сеансов |
| FK → users.id | created_by | INTEGER | да | Кто создал аккаунт; допускается NULL для начального администратора |

## olympiads

| Ключ | Поле | Тип PostgreSQL | NULL | Назначение |
|---|---|---|---|---|
| PK | id | INTEGER | нет | Идентификатор мероприятия |
| — | title | VARCHAR(200) | нет | Название |
| — | description | TEXT | нет | Описание |
| FK → users.id | teacher_id | INTEGER | нет | Ответственный действующий преподаватель |
| — | start_date | DATE | нет | Дата начала и источник года для фильтра |
| — | end_date | DATE | нет | Дата окончания, не раньше начала |
| — | protocol_status | VARCHAR(20) | нет | draft / prepared / published |

## participations

| Ключ | Поле | Тип PostgreSQL | NULL | Назначение |
|---|---|---|---|---|
| PK | id | INTEGER | нет | Идентификатор заявки |
| FK → olympiads.id | olympiad_id | INTEGER | нет | Ссылка на мероприятие |
| FK → users.id | student_id | INTEGER | нет | Ссылка на студента |
| — | score | NUMERIC(8, 2) | да | Баллы 0…999999.99, два десятичных знака; NULL до ввода |
| — | result | VARCHAR(20) | да | winner / prize / participant; NULL до ввода |

## attachments

| Ключ | Поле | Тип PostgreSQL | NULL | Назначение |
|---|---|---|---|---|
| PK | id | INTEGER | нет | Идентификатор документа |
| FK → olympiads.id | olympiad_id | INTEGER | нет | Владелец документа — мероприятие |
| — | kind | VARCHAR(20) | нет | regulation / task / certificate / award |
| — | title | VARCHAR(150) | нет | Отображаемое название |
| — | original_name | VARCHAR(200) | нет | Исходное безопасное имя для скачивания |
| — | stored_name | VARCHAR(100) | нет | Случайное имя физического файла, не выдаётся API |

## Связи и ограничения

users → olympiads: один преподаватель отвечает за много мероприятий. users → participations: один студент имеет много заявок. olympiads → participations и olympiads → attachments: связи один-ко-многим. users.created_by ссылается на users.id.

В БД действуют уникальности username, email и пары (olympiad_id, student_id), CHECK end_date ≥ start_date, CHECK score ≥ 0, NOT NULL и внешние ключи. Значения ролей, категории результата, верхняя граница баллов, активность ответственного, обязательность учебных полей и переходы статусов проверяются приложением. Ошибки целостности откатываются и возвращают 409.

Удаление олимпиад с зависимостями блокируется. Файловое содержимое хранится вне БД: attachments содержит только метаданные. Схема соответствует третьей нормальной форме в принятом объёме: данные студента не дублируются в каждой заявке; название мероприятия не дублируется в результатах; справочные роли и типы имеют небольшой фиксированный набор и не вынесены в отдельные таблицы.