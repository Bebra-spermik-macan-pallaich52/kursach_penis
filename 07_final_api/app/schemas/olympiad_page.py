from app.schemas.api_model import ApiModel
from app.schemas.olympiad_read import OlympiadRead


class OlympiadPage(ApiModel):
    items: list[OlympiadRead]
    total: int
    page: int
    page_size: int
