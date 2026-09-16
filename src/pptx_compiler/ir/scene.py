"""Scene IR: el mundo persistente del que se derivan las slides.

Una escena es un estado del mundo. Un objeto con el mismo id en dos
escenas es el mismo objeto conceptual, y es lo que hace posible el Morph.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from pptx_compiler.errors import IdentityConflictError
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect

ObjectType = Literal["text", "shape", "image"]


@dataclass(frozen=True)
class ObjectStyle:
    font_size: float = 18.0
    color: str = "202020"
    fill: str | None = None
    line: str | None = None
    line_width: float | None = None
    animation: tuple[str, dict] | None = None
    veil: dict | None = None
    bold: bool = False
    opacity: float = 1.0
    rotation: float = 0.0
    sector_start: float = 0.0
    sector_end: float = 90.0
    align: Literal["left", "center", "right"] = "left"
    shape: Literal["rect", "ellipse", "roundRect", "pie", "blockArc", "star4", "star5", "star6", "star8"] = "rect"


@dataclass(frozen=True)
class SceneObject:
    id: str
    type: ObjectType
    at: Rect
    content: str = ""
    source: str | None = None
    style: ObjectStyle = field(default_factory=ObjectStyle)

    def moved_to(self, at: Rect) -> SceneObject:
        return replace(self, at=at)


@dataclass(frozen=True)
class Scene:
    id: str
    camera: Camera
    objects: list[SceneObject] = field(default_factory=list)

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for obj in self.objects:
            if obj.id in seen:
                raise IdentityConflictError(obj.id, self.id)
            seen.add(obj.id)

    @property
    def object_ids(self) -> set[str]:
        return {obj.id for obj in self.objects}

    def get(self, object_id: str) -> SceneObject | None:
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        return None

    def with_camera(self, camera: Camera, scene_id: str) -> Scene:
        return Scene(id=scene_id, camera=camera, objects=list(self.objects))
