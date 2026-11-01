from typing import Literal
from app.schemas.api_model import ApiModel


class StatusRead(ApiModel):
    status: Literal["draft", "prepared", "published"]
