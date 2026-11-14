from dataclasses import dataclass
from datetime import date


@dataclass
class User:
    username: str
    password_hash: str
    full_name: str
    email: str
    role: str
    id: int | None = None
    birth_date: date | None = None
    institution: str = ""
    education_level: str = ""
    course: int | None = None
    specialty: str = ""
    is_active: bool = True
    token_version: int = 0
    created_by: int | None = None
