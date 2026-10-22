import re
from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from pydantic.alias_generators import to_camel

Password = Annotated[str, StringConstraints(strip_whitespace=False)]


def has_invalid_text(value):
    # Эти символы нельзя сохранять в PostgreSQL или записывать в XML документов Word.
    return re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]", value) is not None


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True,
                              from_attributes=True, str_strip_whitespace=True,
                              extra="forbid")

    @field_validator("*")
    @classmethod
    def check_text(cls, value):
        if isinstance(value, str) and has_invalid_text(value):
            raise ValueError("Текст содержит недопустимые управляющие символы")
        return value
