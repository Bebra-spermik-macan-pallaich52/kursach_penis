from app.errors import log_error
from app.database import fetch_one
from dataclasses import asdict
from psycopg import sql
from app.database import execute
from app.names import read_full_name


async def insert_user(db, user):
    try:
        user.full_name = read_full_name(user.full_name)
        row = await fetch_one(
            db,
            """
                INSERT INTO users (username, password_hash, full_name, email, role, birth_date,
                    institution, education_level, course, specialty, is_active, token_version, created_by)
                VALUES (%(username)s, %(password_hash)s, %(full_name)s, %(email)s, %(role)s,
                    %(birth_date)s, %(institution)s, %(education_level)s, %(course)s, %(specialty)s,
                    %(is_active)s, %(token_version)s, %(created_by)s) RETURNING id
            """,
            asdict(user),
        )
        user.id = row["id"]
        return user
    except Exception as error:
        log_error(error, "insert_user")
        raise


async def insert_olympiad(db, item):
    try:
        row = await fetch_one(
            db,
            """
                INSERT INTO olympiads (title, description, teacher_id, start_date, end_date, protocol_status)
                VALUES (%(title)s, %(description)s, %(teacher_id)s, %(start_date)s, %(end_date)s,
                    %(protocol_status)s) RETURNING id
            """,
            asdict(item),
        )
        item.id = row["id"]
        return item
    except Exception as error:
        log_error(error, "insert_olympiad")
        raise


async def insert_participation(db, item):
    try:
        row = await fetch_one(
            db,
            """
                INSERT INTO participations (olympiad_id, student_id, score, result)
                VALUES (%(olympiad_id)s, %(student_id)s, %(score)s, %(result)s) RETURNING id
            """,
            asdict(item),
        )
        item.id = row["id"]
        return item
    except Exception as error:
        log_error(error, "insert_participation")
        raise


async def insert_attachment(db, item):
    try:
        row = await fetch_one(
            db,
            """
                INSERT INTO attachments (olympiad_id, kind, title, original_name, stored_name)
                VALUES (%(olympiad_id)s, %(kind)s, %(title)s, %(original_name)s, %(stored_name)s)
                RETURNING id
            """,
            asdict(item),
        )
        item.id = row["id"]
        return item
    except Exception as error:
        log_error(error, "insert_attachment")
        raise


async def update_fields(db, table, record_id, values):
    try:
        fields = {
            "users": {
                "full_name",
                "email",
                "birth_date",
                "institution",
                "education_level",
                "course",
                "specialty",
                "password_hash",
                "is_active",
            },
            "olympiads": {
                "title",
                "description",
                "teacher_id",
                "start_date",
                "end_date",
                "protocol_status",
            },
            "participations": {"score", "result"},
            "attachments": {"kind", "title", "original_name", "stored_name"},
        }
        if table not in fields or set(values) - fields[table]:
            raise ValueError("Неизвестные поля таблицы")
        if table == "users" and "full_name" in values:
            values["full_name"] = read_full_name(values["full_name"])
        if values:
            columns = sql.SQL(", ").join(
                (sql.SQL("{} = %s").format(sql.Identifier(name)) for name in values)
            )
            query = sql.SQL("UPDATE {} SET {} WHERE id = %s").format(sql.Identifier(table), columns)
            await execute(db, query, [*values.values(), record_id])
    except Exception as error:
        log_error(error, "update_fields")
        raise
