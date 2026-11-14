from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Participation:
    olympiad_id: int
    student_id: int
    id: int | None = None
    score: Decimal | None = None
    result: str | None = None
