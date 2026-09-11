from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RegroupParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    targets: list[str] = Field(min_length=1, description="Objetos a reorganizar")
    layout: Literal["row", "column", "grid"] = "row"
    area: dict | None = Field(default=None, description="Zona destino; por defecto, el encuadre")
    gap: float = Field(default=3.0, ge=0.0, description="Separación entre objetos")
