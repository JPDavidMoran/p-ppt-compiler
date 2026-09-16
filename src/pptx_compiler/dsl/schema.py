"""Schemas del DSL. Fuente única de verdad de la estructura del documento.

`extra="forbid"` en todos los modelos: un campo mal escrito falla rápido
en vez de ignorarse en silencio.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RectSpec(Strict):
    x: float
    y: float
    w: float = Field(gt=0)
    h: float = Field(gt=0)


class CameraSpec(Strict):
    x: float
    y: float
    w: float = Field(gt=0)
    h: float = Field(gt=0)


class StyleSpec(Strict):
    font_size: float = Field(default=18.0, gt=0, alias="fontSize")
    color: str = "202020"
    fill: str | None = None
    line: str | None = None
    bold: bool = False
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    rotation: float = Field(default=0.0, ge=-360.0, le=360.0)
    sector_start: float = Field(default=0.0, ge=0.0, le=360.0, alias="sectorStart")
    sector_end: float = Field(default=90.0, ge=0.0, le=360.0, alias="sectorEnd")
    align: Literal["left", "center", "right"] = "left"
    shape: Literal["rect", "ellipse", "roundRect", "pie", "blockArc"] = "rect"

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


    @model_validator(mode="after")
    def _sector_bien_orientado(self) -> "StyleSpec":
        """Un sector que acaba antes de empezar no dibuja nada visible."""
        if self.sector_end <= self.sector_start:
            raise ValueError(
                f"sectorEnd ({self.sector_end}) debe ser mayor que "
                f"sectorStart ({self.sector_start})"
            )
        return self


class ObjectSpec(Strict):
    id: str = Field(min_length=1)
    type: Literal["text", "shape", "image"]
    at: RectSpec
    content: str = ""
    source: str | None = None
    style: StyleSpec = Field(default_factory=StyleSpec)

    @model_validator(mode="after")
    def _image_needs_source(self) -> "ObjectSpec":
        """Una imagen sin origen es un error de escritura, no de render."""
        if self.type == "image" and not self.source:
            raise ValueError(
                f"el objeto {self.id!r} es de tipo image y necesita un campo "
                '"source" con la ruta del archivo'
            )
        return self


class SceneSpec(Strict):
    id: str = Field(min_length=1)
    camera: CameraSpec | None = None
    objects: list[ObjectSpec] = Field(default_factory=list)


class SceneRef(Strict):
    """Una entrada de escena en la secuencia.

    `emit: false` carga el estado sin dibujar la slide: deja la escena
    disponible como punto de partida de un mecanismo sin mostrar antes
    lo que ese mecanismo va a ir revelando.
    """

    scene: str
    emit: bool = True


class MechanismCall(Strict):
    model_config = ConfigDict(extra="allow")

    mechanism: str


class WorldSpec(Strict):
    w: float = Field(default=100.0, gt=0)
    h: float = Field(default=56.25, gt=0)


class PresentationSpec(Strict):
    title: str = "Untitled"
    aspect_ratio: Literal["16:9"] = Field(default="16:9", alias="aspectRatio")
    transition_ms: int = Field(default=2000, gt=0, alias="transitionMs")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Document(Strict):
    presentation: PresentationSpec = Field(default_factory=PresentationSpec)
    world: WorldSpec = Field(default_factory=WorldSpec)
    scenes: list[SceneSpec] = Field(default_factory=list)
    sequence: list[SceneRef | MechanismCall] = Field(min_length=1)
