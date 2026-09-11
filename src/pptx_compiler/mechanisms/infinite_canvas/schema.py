from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from pptx_compiler.dsl.schema import StyleSpec


class RectSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    w: float = Field(gt=0)
    h: float = Field(gt=0)


class CanvasObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: Literal["text", "shape", "image"] = "shape"
    at: RectSpec
    content: str = ""
    source: str | None = None
    style: StyleSpec = Field(default_factory=StyleSpec)


class TourStop(BaseModel):
    model_config = ConfigDict(extra="forbid")

    at: str = Field(description="Id del objeto a encuadrar en esta parada")
    scale: float = Field(default=1.5, gt=0)


class InfiniteCanvasParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objects: list[CanvasObject] = Field(default_factory=list)
    tour: list[TourStop] = Field(min_length=1)
