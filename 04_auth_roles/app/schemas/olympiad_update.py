from app.errors import log_error
from datetime import date
from pydantic import Field, model_validator
from app.schemas.api_model import ApiModel


class OlympiadUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    teacher_id: int | None = Field(default=None, gt=0, strict=True)
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def reject_null(self):
        try:
            if not self.model_fields_set:
                raise ValueError("Укажите хотя бы одно поле")
            for value in (self.start_date, self.end_date):
                if value and (not 2000 <= value.year <= 2100):
                    raise ValueError("Год проведения должен быть от 2000 до 2100")
            if any((getattr(self, field) is None for field in self.model_fields_set)):
                raise ValueError("Переданное поле не может быть null")
            return self
        except Exception as error:
            log_error(error, "reject_null")
            raise
