"""Reglas de continuidad: cómo encadenan las escenas entre sí.

Cada regla nació de un defecto observado reproduciendo una presentación:
DSL que compilaba sin errores pero narraba mal. Ver docs/design-rules.md.
"""

from __future__ import annotations

from pptx_compiler.compiler.findings import (
    CAMERA_ZOOM_TOLERANCE,
    OVERLAP_THRESHOLD,
    Finding,
    Severity,
    overlap_ratio,
    texts,
)
from pptx_compiler.ir.scene import Scene


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

