from dataclasses import asdict
from psycopg import sql
from app.database import execute


def insert_user(db, user):
    row = execute(db, """
        INSERT INTO users (username, password_hash, full_name, email, role, birth_date,
            institution, education_level, course, specialty, is_active, token_version, created_by)
        VALUES (%(username)s, %(password_hash)s, %(full_name)s, %(email)s, %(role)s,
            %(birth_date)s, %(institution)s, %(education_level)s, %(course)s, %(specialty)s,
            %(is_active)s, %(token_version)s, %(created_by)s) RETURNING id
        """, asdict(user)).fetchone()
    user.id = row["id"]
    return user


def insert_olympiad(db, item):
    row = execute(db, """
        INSERT INTO olympiads (title, description, teacher_id, start_date, end_date, protocol_status)
        VALUES (%(title)s, %(description)s, %(teacher_id)s, %(start_date)s, %(end_date)s,
            %(protocol_status)s) RETURNING id
        """, asdict(item)).fetchone()
    item.id = row["id"]
    return item


def insert_participation(db, item):
    row = execute(db, """
        INSERT INTO participations (olympiad_id, student_id, score, result)
        VALUES (%(olympiad_id)s, %(student_id)s, %(score)s, %(result)s) RETURNING id
        """, asdict(item)).fetchone()
    item.id = row["id"]
    return item


def insert_attachment(db, item):
    row = execute(db, """
        INSERT INTO attachments (olympiad_id, kind, title, original_name, stored_name)
        VALUES (%(olympiad_id)s, %(kind)s, %(title)s, %(original_name)s, %(stored_name)s)
        RETURNING id
        """, asdict(item)).fetchone()
    item.id = row["id"]
    return item


def update_fields(db, table, record_id, values):
    fields = {
        "users": {"full_name", "email", "birth_date", "institution", "education_level",
                  "course", "specialty", "password_hash", "is_active"},
        "olympiads": {"title", "description", "teacher_id", "start_date", "end_date", "protocol_status"},
        "participations": {"score", "result"},
        "attachments": {"kind", "title", "original_name", "stored_name"},
    }
    if table not in fields or set(values) - fields[table]:
        raise ValueError("Неизвестные поля таблицы")
    if values:
        columns = sql.SQL(", ").join(sql.SQL("{} = %s").format(sql.Identifier(name)) for name in values)
        query = sql.SQL("UPDATE {} SET {} WHERE id = %s").format(sql.Identifier(table), columns)
        execute(db, query, [*values.values(), record_id])
