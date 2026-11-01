from app.schemas.api_model import ApiModel


class ParticipationRead(ApiModel):
    id: int
    olympiad_id: int
    student_id: int
    full_name: str
    score: float | None
    result: str | None
