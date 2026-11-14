from typing import Annotated
from fastapi import Path

Id = Annotated[int, Path(gt=0)]
