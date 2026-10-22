from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="forbid")


class UserCreate(ApiModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=5, max_length=150)
    email: EmailStr
    role: Literal["student", "teacher"]
    birth_date: date | None = None
    institution: str = Field(default="", max_length=200)
    education_level: str = Field(default="", max_length=100)
    course: int | None = Field(default=None, ge=1, le=6)
    specialty: str = Field(default="", max_length=150)

    @model_validator(mode="after")
    def check_student(self):
        if self.birth_date and self.birth_date >= date.today():
            raise ValueError("Дата рождения должна быть в прошлом")
        if self.role == "student" and not all([self.birth_date, self.institution,
                self.education_level, self.course, self.specialty]):
            raise ValueError("Для студента нужны все учебные данные и дата рождения")
        return self


class UserRead(ApiModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    birth_date: date | None
    institution: str
    education_level: str
    course: int | None
    specialty: str
    is_active: bool


class ProfileUpdate(ApiModel):
    full_name: str | None = Field(default=None, min_length=5, max_length=150)
    email: EmailStr | None = None
    birth_date: date | None = None
    institution: str | None = Field(default=None, min_length=1, max_length=200)
    education_level: str | None = Field(default=None, min_length=1, max_length=100)
    course: int | None = Field(default=None, ge=1, le=6)
    specialty: str | None = Field(default=None, min_length=1, max_length=150)

    @model_validator(mode="after")
    def check_values(self):
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError("Переданное поле не может быть null")
        if self.birth_date and self.birth_date >= date.today():
            raise ValueError("Дата рождения должна быть в прошлом")
        return self


class AccountUpdate(ProfileUpdate):
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class OlympiadCreate(ApiModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    teacher_id: int = Field(gt=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("Окончание не может быть раньше начала")
        return self


class OlympiadUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    teacher_id: int | None = Field(default=None, gt=0)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def reject_null(self):
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Переданное поле не может быть null")
        return self


class OlympiadRead(ApiModel):
    id: int
    title: str
    description: str
    teacher_id: int
    start_date: date
    end_date: date
    protocol_status: str


class OlympiadPage(ApiModel):
    items: list[OlympiadRead]
    total: int
    page: int
    page_size: int


class ResultUpdate(ApiModel):
    score: Decimal = Field(ge=0, le=999999.99, max_digits=8, decimal_places=2)
    result: Literal["winner", "prize", "participant"]


class ProtocolUpdate(ApiModel):
    status: Literal["draft", "prepared", "published"]


class AttachmentRead(ApiModel):
    id: int
    olympiad_id: int
    kind: str
    title: str
    original_name: str
