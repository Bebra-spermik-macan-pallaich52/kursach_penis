-- Первичная настройка обычной локальной PostgreSQL.
-- Выполнять один раз от администратора postgres, подключившись к базе postgres:
-- psql -h localhost -U postgres -d postgres -v ON_ERROR_STOP=1 -f scripts/setup_database.sql
-- Пароль учебный: при его замене исправьте также обе строки подключения в .env.
CREATE ROLE olympiad LOGIN PASSWORD 'olympiad_local';
CREATE DATABASE olympiads OWNER olympiad;
CREATE DATABASE olympiads_test OWNER olympiad;
