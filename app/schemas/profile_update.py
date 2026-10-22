from datetime import date
from pydantic import EmailStr, Field, model_validator
from app.schemas.api_model import ApiModel


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
