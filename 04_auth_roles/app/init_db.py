from datetime import date
import argparse
from app.database import connect
from app.records import insert_user, insert_olympiad, insert_participation
from app.migrate import migrate
from app.models.user import User
from app.models.olympiad import Olympiad
from app.models.participation import Participation
from app.security import hash_password


def seed_demo(db):
    if db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        print("База непустая: данные сохранены")
        return
    teacher_password = hash_password("Teacher2026!")
    student_password = hash_password("Student2026!")
    admin = User(username="admin", password_hash=hash_password("Admin2026!"),
                 role="admin", full_name="Администратор системы", email="admin@example.org")
    insert_user(db, admin)
    teachers = []
    students = []
    for number in range(1, 51):
        teacher = User(username=f"teacher{number}", password_hash=teacher_password,
                       role="teacher", full_name=f"Преподаватель Тестовый {number}",
                       email=f"teacher{number}@example.org")
        insert_user(db, teacher)
        teachers.append(teacher)
    for number in range(1, 61):
        student = User(username=f"student{number}", password_hash=student_password,
                       role="student", full_name=f"Иванов Алексей Учебный {number}",
                       email=f"student{number}@example.org", birth_date=date(2007, 1, 1),
                       institution="Учебный колледж", education_level="СПО", course=3,
                       specialty="09.02.07 Информационные системы и программирование")
        insert_user(db, student)
        students.append(student)
    for number in range(50):
        item = Olympiad(title=f"Учебная олимпиада по программированию {number + 1}",
                        teacher_id=teachers[number].id, start_date=date(2026, 1, 10),
                        end_date=date(2026, 1, 10))
        insert_olympiad(db, item)
        for offset in range(3):
            student = students[(number * 3 + offset) % 60]
            insert_participation(db, Participation(olympiad_id=item.id, student_id=student.id))
    db.commit()
    print("Создано: 111 пользователей, 50 олимпиад, 150 заявок")


def main():
    parser = argparse.ArgumentParser(description="Создание таблиц и учебных данных")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    migrate()
    if args.demo:
        with connect() as db:
            seed_demo(db)


if __name__ == "__main__":
    main()
