from decimal import Decimal
from typing import Literal
from pydantic import Field
from app.schemas.api_model import ApiModel


class ResultUpdate(ApiModel):
    score: Decimal = Field(ge=0, le=999999.99, max_digits=8, decimal_places=2)
    result: Literal["winner", "prize", "participant"]
