from pydantic import BaseModel


class ErrorRead(BaseModel):
    detail: str | list[dict]
