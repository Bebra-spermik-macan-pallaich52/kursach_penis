from pydantic import Field
from app.schemas.api_model import ApiModel


class PasswordChange(ApiModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
