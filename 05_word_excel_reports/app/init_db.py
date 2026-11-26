from app.names import read_full_name
from app.errors import log_error
from app.database import fetch_one
from app.runtime import run
import asyncio
from datetime import date
import argparse
import os
from uuid import uuid4
from app.documents import make_docx
from app.config import STORAGE
from app.database import connect
from app.records import insert_user, insert_olympiad, insert_participation, insert_attachment
from app.migrate import migrate
from app.models.user import User
from app.models.olympiad import Olympiad
from app.models.participation import Participation
from app.models.attachment import Attachment
from app.security import hash_password


async def add_user(db, username, password, role, full_name, **extra):
    try:
        user = User(
            username=username,
            password_hash=await asyncio.to_thread(hash_password, password),
            role=role,
            full_name=read_full_name(full_name),
            email=username + "@example.org",
            **extra,
        )
        await insert_user(db, user)
        return user
    except Exception as error:
        log_error(error, "add_user")
        raise


async def seed_demo(db):
    try:
        if await fetch_one(db, "SELECT 1 FROM users LIMIT 1"):
            print("База непустая: демонстрационные данные не добавлены и не изменены")
            return
        admin = await add_user(db, "admin", "Admin2026!", "admin", "Администратор учебной системы")
        teachers = []
        for i in range(1, 51):
            teachers.append(
                await add_user(
                    db,
                    f"teacher{i}",
                    "Teacher2026!",
                    "teacher",
                    f"Преподаватель Тестовый Номер {i}",
                    created_by=admin.id,
                )
            )
        surnames = [
            "Иванов",
            "Петров",
            "Сидоров",
            "Смирнов",
            "Кузнецов",
            "Попов",
            "Васильев",
            "Соколов",
            "Михайлов",
            "Новиков",
        ]
        students = []
        for i in range(1, 61):
            students.append(
                await add_user(
                    db,
                    f"student{i}",
                    "Student2026!",
                    "student",
                    f"{surnames[(i - 1) % 10]} Алексей Учебный {i}",
                    birth_date=date(2006 + i % 3, 1 + i % 12, 1 + i % 25),
                    institution="Екатеринбургский монтажный колледж (учебные данные)",
                    education_level="Среднее профессиональное",
                    course=1 + i % 4,
                    specialty="09.02.07 Информационные системы и программирование",
                    created_by=teachers[(i - 1) % 50].id,
                )
            )
        subjects = [
            "Программирование на Python",
            "Веб-разработка",
            "Базы данных",
            "Компьютерные сети",
            "Информационная безопасность",
        ]
        await asyncio.to_thread(STORAGE.mkdir, parents=True, exist_ok=True)
        created_files = []
        try:
            for i in range(50):
                event_date = date.today() if i == 0 else date(2024 + i % 3, 3 + i % 6, 1 + i % 25)
                olympiad = Olympiad(
                    title=f"{subjects[i % 5]} — учебная олимпиада {i + 1}",
                    description="Вымышленное мероприятие для демонстрации и тестирования.",
                    teacher_id=teachers[i].id,
                    start_date=event_date,
                    end_date=event_date,
                    protocol_status=["draft", "published", "prepared"][i % 3],
                )
                await insert_olympiad(db, olympiad)
                for k in range(3):
                    await insert_participation(
                        db,
                        Participation(
                            olympiad_id=olympiad.id,
                            student_id=students[(i * 3 + k) % 60].id,
                            score=95 - k * 15,
                            result=["winner", "prize", "participant"][k],
                        ),
                    )
                for kind, title in [
                    ("regulation", "Положение"),
                    ("task", "Задание"),
                    ("certificate", "Сертификат"),
                    ("award", "Грамота"),
                ]:
                    if kind == "regulation":
                        text = "Цель: развитие профессиональных навыков. К участию допускаются студенты. Результат определяет преподаватель по критериям."
                    elif kind == "task":
                        text = "Разработать программу обработки списка участников и подсчёта баллов. Максимум — 100 баллов."
                    else:
                        text = "Награждается: __________________. Результат: __________. Дата и подпись: __________."
                    content = await asyncio.to_thread(make_docx, title, olympiad.title, text)
                    name = uuid4().hex + ".docx"
                    path = STORAGE / name
                    await asyncio.to_thread(path.write_bytes, content)
                    created_files.append(path)
                    await insert_attachment(
                        db,
                        Attachment(
                            olympiad_id=olympiad.id,
                            kind=kind,
                            title=title,
                            original_name=kind + ".docx",
                            stored_name=name,
                        ),
                    )
            await db.commit()
        except Exception:
            await db.rollback()
            for path in created_files:
                await asyncio.to_thread(path.unlink, missing_ok=True)
            raise
        print("Создано: 111 пользователей, 50 олимпиад, 150 заявок, 200 документов")
        print(
            "Учебные аккаунты: admin, teacher1..teacher50, student1..student60. Пароли — в README"
        )
    except Exception as error:
        log_error(error, "seed_demo")
        raise


async def main():
    try:
        parser = argparse.ArgumentParser(description="Создание таблиц и учебных данных")
        parser.add_argument(
            "--demo", action="store_true", help="Заполнить только пустую БД учебными данными"
        )
        args = parser.parse_args()
        await migrate()
        async with await connect() as db:
            if args.demo:
                await seed_demo(db)
            elif not await fetch_one(db, "SELECT 1 FROM users LIMIT 1"):
                username = os.getenv("ADMIN_USERNAME", "admin")
                password = os.getenv("ADMIN_PASSWORD", "")
                if len(password) < 8:
                    raise RuntimeError("Укажите ADMIN_PASSWORD длиной от 8 символов в .env")
                await add_user(db, username, password, "admin", "Администратор системы")
                await db.commit()
                print("Таблицы и учётная запись администратора созданы")
            else:
                print("Таблицы уже существуют; пользовательские данные сохранены")
    except Exception as error:
        log_error(error, "main")
        raise


if __name__ == "__main__":
    run(main())
