from pydantic import Field
from app.schemas.profile_update import ProfileUpdate


class AccountUpdate(ProfileUpdate):
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
