from app.schemas.api_model import ApiModel


class AttachmentRead(ApiModel):
    id: int
    olympiad_id: int
    kind: str
    title: str
    original_name: str
