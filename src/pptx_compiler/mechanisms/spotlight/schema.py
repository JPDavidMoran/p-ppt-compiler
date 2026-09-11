from pydantic import BaseModel, ConfigDict, Field


class SpotlightParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: str = Field(description="Id del objeto a destacar")
    dim: float = Field(default=0.25, ge=0.0, le=1.0, description="Opacidad del resto")
    keep: list[str] = Field(default_factory=list, description="Objetos que no se atenúan")
