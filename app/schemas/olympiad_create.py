from datetime import date
from pydantic import Field, model_validator
from app.schemas.api_model import ApiModel


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
