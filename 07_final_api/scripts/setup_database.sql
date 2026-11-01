DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'olympiad') THEN
        CREATE ROLE olympiad LOGIN PASSWORD 'olympiad_local';
    END IF;
END
$$;
SELECT 'CREATE DATABASE olympiads_stage07 OWNER olympiad' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'olympiads_stage07')\gexec
SELECT 'CREATE DATABASE olympiads_stage07_test OWNER olympiad' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'olympiads_stage07_test')\gexec
