from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RevealParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cover: str = Field(description="Objeto que tapa")
    target: str = Field(description="Objeto que queda al descubierto")
    direction: Literal["up", "down", "left", "right"] = "up"
