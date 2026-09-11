"""Proyección de coordenadas de mundo al área de la slide, en EMU.

Toda la aritmética interna es en EMU (914400 por pulgada) para evitar
redondeo acumulado entre escenas: dos objetos que no se mueven deben
proyectarse a valores idénticos, o el differ los vería como cambiados.
"""

from __future__ import annotations

from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import EmuRect, Rect

EMU_PER_INCH = 914400
SLIDE_W_EMU = 12192000
SLIDE_H_EMU = 6858000


def project(rect: Rect, camera: Camera) -> EmuRect:
    """Proyecta un rectángulo de mundo al área de la slide.

    El resultado puede caer fuera del área visible; eso es deliberado y
    permite las entradas desde fuera del marco.
    """
    scale_x = SLIDE_W_EMU / camera.w
    scale_y = SLIDE_H_EMU / camera.h

    return EmuRect(
        x=round((rect.x - camera.x) * scale_x),
        y=round((rect.y - camera.y) * scale_y),
        w=round(rect.w * scale_x),
        h=round(rect.h * scale_y),
    )


def project_font_size(size_pt: float, camera: Camera, world_w: float) -> float:
    """Escala el tamaño de fuente con el zoom de la cámara.

    Sin esto, un texto mantendría su tamaño en puntos mientras todo lo
    demás crece, y el zoom se vería roto.
    """
    zoom = world_w / camera.w
    return size_pt * zoom
