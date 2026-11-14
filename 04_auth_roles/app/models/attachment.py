from dataclasses import dataclass


@dataclass
class Attachment:
    olympiad_id: int
    id: int | None = None
    kind: str = ""
    title: str = ""
    original_name: str = ""
    stored_name: str = ""
