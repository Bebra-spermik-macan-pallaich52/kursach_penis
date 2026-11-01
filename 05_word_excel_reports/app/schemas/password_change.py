from pydantic import Field
from app.schemas.api_model import ApiModel, Password


class PasswordChange(ApiModel):
    old_password: Password
    new_password: Password = Field(min_length=8, max_length=128)
