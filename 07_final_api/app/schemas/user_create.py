from datetime import date
from typing import Literal
from pydantic import EmailStr, Field, model_validator
from app.schemas.api_model import ApiModel, Password


class UserCreate(ApiModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: Password = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=5, max_length=150)
    email: EmailStr
    role: Literal["student", "teacher"]
    birth_date: date | None = None
    institution: str = Field(default="", max_length=200)
    education_level: str = Field(default="", max_length=100)
    course: int | None = Field(default=None, ge=1, le=6, strict=True)
    specialty: str = Field(default="", max_length=150)

    @model_validator(mode="after")
    def check_student(self):
        if self.birth_date and not date(1900, 1, 1) <= self.birth_date < date.today():
            raise ValueError("Укажите дату рождения между 1900 годом и сегодняшним днём")
        if self.role == "student" and not all([self.birth_date, self.institution,
                self.education_level, self.course, self.specialty]):
            raise ValueError("Для студента нужны все учебные данные и дата рождения")
        return self
