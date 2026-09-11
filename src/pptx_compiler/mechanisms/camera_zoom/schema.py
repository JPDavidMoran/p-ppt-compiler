from pydantic import BaseModel, ConfigDict, Field


class CameraZoomParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: str = Field(description="Id del objeto a encuadrar")
    scale: float = Field(default=2.0, gt=0, description="Mayor acerca la cámara")
