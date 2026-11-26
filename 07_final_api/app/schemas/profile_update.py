from app.errors import log_error
from datetime import date
from pydantic import EmailStr, Field, model_validator
from app.schemas.api_model import ApiModel
from app.names import read_full_name


class ProfileUpdate(ApiModel):
    full_name: str | None = Field(default=None, min_length=5, max_length=150)
    last_name: str | None = Field(default=None, min_length=1, max_length=70, exclude=True)
    first_name: str | None = Field(default=None, min_length=1, max_length=70, exclude=True)
    middle_name: str | None = Field(default=None, max_length=70, exclude=True)
    email: EmailStr | None = None
    birth_date: date | None = None
    institution: str | None = Field(default=None, min_length=1, max_length=200)
    education_level: str | None = Field(default=None, min_length=1, max_length=100)
    course: int | None = Field(default=None, ge=1, le=6, strict=True)
    specialty: str | None = Field(default=None, min_length=1, max_length=150)

    @model_validator(mode="after")
    def check_values(self):
        try:
            if not self.model_fields_set:
                raise ValueError("Укажите хотя бы одно поле")
            name_fields = {"full_name", "last_name", "first_name", "middle_name"}
            if self.model_fields_set & name_fields:
                self.full_name = read_full_name(
                    self.full_name, self.last_name, self.first_name, self.middle_name
                )
            for field in self.model_fields_set:
                if field == "middle_name":
                    continue
                if getattr(self, field) is None:
                    raise ValueError("Переданное поле не может быть null")
            if self.birth_date and (not date(1900, 1, 1) <= self.birth_date < date.today()):
                raise ValueError("Укажите дату рождения между 1900 годом и сегодняшним днём")
            return self
        except Exception as error:
            log_error(error, "check_values")
            raise
