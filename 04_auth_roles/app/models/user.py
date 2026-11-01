from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
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
