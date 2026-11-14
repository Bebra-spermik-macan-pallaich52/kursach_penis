from dataclasses import dataclass
from datetime import date


@dataclass
class Olympiad:
    title: str
    teacher_id: int
    start_date: date
    end_date: date
    id: int | None = None
    description: str = ""
    protocol_status: str = "draft"
