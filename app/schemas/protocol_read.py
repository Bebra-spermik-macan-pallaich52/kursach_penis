from app.schemas.api_model import ApiModel
from app.schemas.participation_read import ParticipationRead


class ProtocolRead(ApiModel):
    olympiad_id: int
    title: str
    status: str
    participants: list[ParticipationRead]
