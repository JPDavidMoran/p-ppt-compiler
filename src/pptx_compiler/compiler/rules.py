"""Reglas de composición, una función por regla.

Cada regla nació de un defecto observado reproduciendo una presentación:
DSL que compilaba sin errores pero narraba mal. Ver docs/design-rules.md.

Una regla recibe la lista de escenas y emite hallazgos. Son funciones
puras, sin estado compartido, así que añadir una no toca a las demás.
"""

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


def check_zoom_cierra(scenes: list[Scene]) -> list[Finding]:
    """R2: la presentación no debería terminar en un primer plano."""
    if len(scenes) < 2:
        return []

    widest = max(scene.camera.w for scene in scenes)
    last = scenes[-1]
    if last.camera.w * CAMERA_ZOOM_TOLERANCE < widest:
        return [
            Finding(
                code="R2",
                severity=Severity.WARNING,
                scene_id=last.id,
                message="la presentación termina en una escena acercada",
                hint="repite la escena del plano general para cerrar el recorrido",
            )
        ]
    return []


def check_parpadeo(scenes: list[Scene]) -> list[Finding]:
    """R3: un objeto que sale y otro que entra en la misma zona parpadea.

    Solo aplica dentro de un mismo tema: si la escena entera se renueva
    es un cambio de sección, y ahí el fade es lo correcto.
    """
    findings: list[Finding] = []
    for before, after in zip(scenes, scenes[1:]):
        if _es_cambio_de_tema(before, after):
            continue
        leaving = [o for o in before.objects if o.id not in after.object_ids]
        entering = [o for o in after.objects if o.id not in before.object_ids]
        for gone in leaving:
            for arrived in entering:
                if overlap_ratio(gone.at, arrived.at) < OVERLAP_THRESHOLD:
                    continue
                findings.append(
                    Finding(
                        code="R3",
                        severity=Severity.WARNING,
                        scene_id=after.id,
                        message=f"{gone.id!r} desaparece y {arrived.id!r} ocupa su lugar",
                        hint="reutiliza un mismo id para que el objeto morphee",
                    )
                )
    return findings


def _es_cambio_de_tema(before: Scene, after: Scene) -> bool:
    """Ningún objeto sobrevive: es una sección nueva, no un parpadeo."""
    return not (before.object_ids & after.object_ids)


def check_sustitucion_de_titulos(scenes: list[Scene]) -> list[Finding]:
    """R4: objetos distintos con la misma geometría se sustituyen en el sitio."""
    findings: list[Finding] = []
    for before, after in zip(scenes, scenes[1:]):
        for gone in _texts(before):
            if gone.id in after.object_ids:
                continue
            for arrived in _texts(after):
                if arrived.id in before.object_ids:
                    continue
                if gone.at == arrived.at and gone.content != arrived.content:
                    findings.append(
                        Finding(
                            code="R4",
                            severity=Severity.WARNING,
                            scene_id=after.id,
                            message=(
                                f"{gone.id!r} y {arrived.id!r} comparten geometría: "
                                "parecerá que el texto cambia en el sitio"
                            ),
                            hint="dales geometría distinta, o reutiliza el id si es intencionado",
                        )
                    )
    return findings


def check_arrastre(scenes: list[Scene]) -> list[Finding]:
    """R5: un objeto aislado que sobrevive a un cambio de tema."""
    findings: list[Finding] = []
    for before, after in zip(scenes, scenes[1:]):
        persisting = before.object_ids & after.object_ids
        if not persisting or len(persisting) >= len(before.object_ids):
            continue
        renewed = after.object_ids - before.object_ids
        if len(renewed) < len(persisting):
            continue
        for stray in sorted(persisting):
            findings.append(
                Finding(
                    code="R5",
                    severity=Severity.WARNING,
                    scene_id=after.id,
                    message=f"{stray!r} sobrevive a un cambio de tema",
                    hint="declara una escena propia antes del mecanismo",
                )
            )
    return findings


def check_alineacion(scenes: list[Scene]) -> list[Finding]:
    """R6: un título de sección sin alineación explícita se ve descentrado.

    Solo mira los textos anchos situados en la banda superior: un titular
    de portada alineado a la izquierda suele ser deliberado.
    """
    findings: list[Finding] = []
    seen: set[str] = set()
    for scene in scenes:
        for obj in _texts(scene):
            if obj.id in seen or obj.style.align != "left":
                continue
            if obj.at.w < scene.camera.w * WIDE_TEXT_RATIO:
                continue
            if obj.at.y > scene.camera.y + scene.camera.h * HEADER_BAND:
                continue
            seen.add(obj.id)
            findings.append(
                Finding(
                    code="R6",
                    severity=Severity.INFO,
                    scene_id=scene.id,
                    message=f"{obj.id!r} ocupa casi todo el ancho y se alinea a la izquierda",
                    hint='añade "align": "center" si es un título',
                )
            )
    return findings


def _texts(scene: Scene) -> list[SceneObject]:
    return [obj for obj in scene.objects if obj.type == "text"]
