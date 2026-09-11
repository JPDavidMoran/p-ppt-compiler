from pydantic import BaseModel, ConfigDict, Field


class FocusTransitionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: list[str] = Field(min_length=1, description="Objetos a enfocar en orden")
    scale: float = Field(default=2.0, gt=0)
