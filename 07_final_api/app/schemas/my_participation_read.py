from app.schemas.participation_read import ParticipationRead


class MyParticipationRead(ParticipationRead):
    title: str
    protocol_status: str
