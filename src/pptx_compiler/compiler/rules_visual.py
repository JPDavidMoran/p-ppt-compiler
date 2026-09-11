"""Reglas de presentación: cómo se ve cada escena por separado.

Ver docs/design-rules.md.
"""

from __future__ import annotations

from pptx_compiler.compiler.findings import (
    HEADER_BAND,
    WIDE_TEXT_RATIO,
    Finding,
    Severity,
    texts,
)
from pptx_compiler.ir.scene import Scene


def check_sustitucion_de_titulos(scenes: list[Scene]) -> list[Finding]:
    """R4: objetos distintos con la misma geometría se sustituyen en el sitio."""
    findings: list[Finding] = []
    for before, after in zip(scenes, scenes[1:]):
        for gone in texts(before):
            if gone.id in after.object_ids:
                continue
            for arrived in texts(after):
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



def check_alineacion(scenes: list[Scene]) -> list[Finding]:
    """R6: un título de sección sin alineación explícita se ve descentrado.

    Solo mira los textos anchos situados en la banda superior: un titular
    de portada alineado a la izquierda suele ser deliberado.
    """
    findings: list[Finding] = []
    seen: set[str] = set()
    for scene in scenes:
        for obj in texts(scene):
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

