"""Создать таблицы и три учебных аккаунта: python init_db.py."""
from datetime import date
from app.database import Base, engine, SessionLocal
from app.models import Olympiad, Participation, User
from app.auth import hash_password


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.query(User).first():
            print("В базе уже есть пользователи. Данные не изменены.")
            return
        admin = User(username="admin", password_hash=hash_password("Admin2026!"),
                     full_name="Администратор системы", email="admin@example.org", role="admin")
        teacher = User(username="teacher1", password_hash=hash_password("Teacher2026!"),
                       full_name="Иванов Иван Иванович", email="teacher1@example.org", role="teacher")
        student = User(username="student1", password_hash=hash_password("Student2026!"),
                       full_name="Петров Пётр Петрович", email="student1@example.org", role="student",
                       birth_date=date(2007, 5, 14), institution="Учебный колледж",
                       education_level="Среднее профессиональное", course=2,
                       specialty="Информационные системы и программирование")
        db.add_all([admin, teacher, student])
        db.flush()
        today = date.today()
        current = Olympiad(title="Олимпиада по Python", description="Учебное мероприятие",
                           teacher_id=teacher.id, start_date=today, end_date=today)
        previous = Olympiad(title="Олимпиада прошлого года", teacher_id=teacher.id,
                            start_date=date(today.year - 1, 5, 10),
                            end_date=date(today.year - 1, 5, 10), protocol_status="published")
        db.add_all([current, previous])
        db.flush()
        db.add(Participation(olympiad_id=previous.id, student_id=student.id,
                             score=90, result="winner"))
        db.commit()
        print("Созданы таблицы, admin, teacher1, student1 и две олимпиады.")
        print("Учебные пароли приведены в README.md.")


if __name__ == "__main__":
    main()
