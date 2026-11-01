from datetime import date
from app.schemas.api_model import ApiModel


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
