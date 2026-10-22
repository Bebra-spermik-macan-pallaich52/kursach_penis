-- Один раз выполнить от имени администратора PostgreSQL.
-- Используются обычная служба PostgreSQL и отдельная учебная база.
CREATE ROLE olympiad LOGIN PASSWORD 'olympiad_local';
CREATE DATABASE olympiads_simple OWNER olympiad;
CREATE DATABASE olympiads_simple_test OWNER olympiad;
