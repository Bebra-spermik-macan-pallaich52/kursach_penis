from datetime import date
from pydantic import Field, model_validator
from app.schemas.api_model import ApiModel


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
