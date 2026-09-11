"""Modelo de un hallazgo del linter y utilidades compartidas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene, SceneObject

OVERLAP_THRESHOLD = 0.5
WIDE_TEXT_RATIO = 0.5
HEADER_BAND = 0.25  # banda superior donde vive un título de sección
CAMERA_ZOOM_TOLERANCE = 1.05


class Severity(Enum):
    WARNING = "aviso"
    INFO = "nota"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    scene_id: str
    message: str
    hint: str


def overlap_ratio(a: Rect, b: Rect) -> float:
    """Fracción del área del menor que comparten dos rectángulos."""
    dx = min(a.x + a.w, b.x + b.w) - max(a.x, b.x)
    dy = min(a.y + a.h, b.y + b.h) - max(a.y, b.y)
    if dx <= 0 or dy <= 0:
        return 0.0
    smaller = min(a.w * a.h, b.w * b.h)
    return (dx * dy) / smaller if smaller else 0.0


def texts(scene: Scene) -> list[SceneObject]:
    return [obj for obj in scene.objects if obj.type == "text"]
