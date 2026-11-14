from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import connect


with connect() as db:
    tables = {row['tablename'] for row in db.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")}
    assert {'users', 'olympiads', 'participations', 'attachments', 'schema_migrations'} <= tables
    for name in ('users', 'olympiads', 'participations', 'attachments'):
        print(name, db.execute('SELECT count(*) AS total FROM ' + name).fetchone()['total'])
    rows = db.execute("""
        SELECT conrelid::regclass::text AS source, confrelid::regclass::text AS target
        FROM pg_constraint WHERE contype = 'f'
        """).fetchall()
    links = {(row['source'], row['target']) for row in rows}
    assert {('olympiads', 'users'), ('participations', 'users'),
            ('participations', 'olympiads'), ('attachments', 'olympiads')} <= links
    assert db.execute("SELECT 1 FROM pg_constraint WHERE conname = 'unique_enrollment'").fetchone()
    versions = {row['version'] for row in db.execute('SELECT version FROM schema_migrations')}
    assert {'001_initial', '002_validation'} <= versions
print('Таблицы, связи и миграции проверены')
