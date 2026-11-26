from app.errors import log_error
from datetime import date
from pydantic import Field, model_validator
from app.schemas.api_model import ApiModel


class OlympiadCreate(ApiModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=5000)
    teacher_id: int = Field(gt=0, strict=True)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self):
        try:
            if not 2000 <= self.start_date.year <= 2100 or not 2000 <= self.end_date.year <= 2100:
                raise ValueError("Год проведения должен быть от 2000 до 2100")
            if self.end_date < self.start_date:
                raise ValueError("Окончание не может быть раньше начала")
            return self
        except Exception as error:
            log_error(error, "check_dates")
            raise
