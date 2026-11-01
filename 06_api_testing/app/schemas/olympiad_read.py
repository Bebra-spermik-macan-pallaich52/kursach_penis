from datetime import date
from app.schemas.api_model import ApiModel


class OlympiadRead(ApiModel):
    id: int
    title: str
    description: str
    teacher_id: int
    start_date: date
    end_date: date
    protocol_status: str
