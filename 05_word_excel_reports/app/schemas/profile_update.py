from datetime import date
from pydantic import EmailStr, Field, model_validator
from app.schemas.api_model import ApiModel


class ProfileUpdate(ApiModel):
    full_name: str | None = Field(default=None, min_length=5, max_length=150)
    email: EmailStr | None = None
    birth_date: date | None = None
    institution: str | None = Field(default=None, min_length=1, max_length=200)
    education_level: str | None = Field(default=None, min_length=1, max_length=100)
    course: int | None = Field(default=None, ge=1, le=6, strict=True)
    specialty: str | None = Field(default=None, min_length=1, max_length=150)

    @model_validator(mode="after")
    def check_values(self):
        if not self.model_fields_set:
            raise ValueError("Укажите хотя бы одно поле")
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError("Переданное поле не может быть null")
        if self.birth_date and not date(1900, 1, 1) <= self.birth_date < date.today():
            raise ValueError("Укажите дату рождения между 1900 годом и сегодняшним днём")
        return self
