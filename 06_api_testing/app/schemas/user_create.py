from app.errors import log_error
from datetime import date
from typing import Literal
from pydantic import EmailStr, Field, model_validator
from app.schemas.api_model import ApiModel, Password
from app.names import read_full_name


class UserCreate(ApiModel):
    username: str = Field(min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: Password = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, min_length=5, max_length=150)
    last_name: str | None = Field(default=None, min_length=1, max_length=70, exclude=True)
    first_name: str | None = Field(default=None, min_length=1, max_length=70, exclude=True)
    middle_name: str | None = Field(default=None, max_length=70, exclude=True)
    email: EmailStr
    role: Literal["student", "teacher"]
    birth_date: date | None = None
    institution: str = Field(default="", max_length=200)
    education_level: str = Field(default="", max_length=100)
    course: int | None = Field(default=None, ge=1, le=6, strict=True)
    specialty: str = Field(default="", max_length=150)

    @model_validator(mode="after")
    def check_student(self):
        try:
            self.full_name = read_full_name(
                self.full_name, self.last_name, self.first_name, self.middle_name
            )
            if self.birth_date and (not date(1900, 1, 1) <= self.birth_date < date.today()):
                raise ValueError("Укажите дату рождения между 1900 годом и сегодняшним днём")
            if self.role == "student" and (
                not all(
                    [
                        self.birth_date,
                        self.institution,
                        self.education_level,
                        self.course,
                        self.specialty,
                    ]
                )
            ):
                raise ValueError("Для студента нужны все учебные данные и дата рождения")
            return self
        except Exception as error:
            log_error(error, "check_student")
            raise
