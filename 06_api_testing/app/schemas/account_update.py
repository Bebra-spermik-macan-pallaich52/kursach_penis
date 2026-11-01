from pydantic import Field
from app.schemas.profile_update import ProfileUpdate
from app.schemas.api_model import Password


class AccountUpdate(ProfileUpdate):
    is_active: bool | None = None
    password: Password | None = Field(default=None, min_length=8, max_length=128)
