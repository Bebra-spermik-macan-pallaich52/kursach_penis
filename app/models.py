from sqlalchemy import (Boolean, CheckConstraint, Column, Date, ForeignKey,
                        Integer, Numeric, String, Text, UniqueConstraint)
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(150), nullable=False)
    birth_date = Column(Date)
    email = Column(String(254), unique=True, nullable=False)
    institution = Column(String(200), nullable=False, default="")
    education_level = Column(String(100), nullable=False, default="")
    course = Column(Integer)
    specialty = Column(String(150), nullable=False, default="")
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    token_version = Column(Integer, nullable=False, default=0)
    created_by = Column(Integer, ForeignKey("users.id"))


class Olympiad(Base):
    __tablename__ = "olympiads"
    __table_args__ = (CheckConstraint("end_date >= start_date", name="dates_order"),)
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False, default="")
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    protocol_status = Column(String(20), nullable=False, default="draft")


class Participation(Base):
    __tablename__ = "participations"
    __table_args__ = (
        UniqueConstraint("olympiad_id", "student_id", name="unique_enrollment"),
        CheckConstraint("score >= 0", name="nonnegative_score"),
    )
    id = Column(Integer, primary_key=True)
    olympiad_id = Column(Integer, ForeignKey("olympiads.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Numeric(8, 2))
    result = Column(String(20))


class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True)
    olympiad_id = Column(Integer, ForeignKey("olympiads.id"), nullable=False)
    kind = Column(String(20), nullable=False)
    title = Column(String(150), nullable=False)
    original_name = Column(String(200), nullable=False)
    stored_name = Column(String(100), nullable=False)
