"""Traduce los schemas del DSL a objetos del IR.

Vive aquí y no en cada consumidor para que la traducción de alias
(fontSize -> font_size) ocurra en un único sitio.
"""

from __future__ import annotations

from pptx_compiler.dsl.schema import ObjectSpec, StyleSpec
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import ObjectStyle, SceneObject


def to_style(spec: StyleSpec) -> ObjectStyle:
    return ObjectStyle(
        font_size=spec.font_size,
        color=spec.color,
        fill=spec.fill,
        line=spec.line,
        line_width=spec.line_width,
        animation=_animation(spec),
        veil=spec.veil.model_dump() if spec.veil else None,
        blur=spec.blur,
        bold=spec.bold,
        opacity=spec.opacity,
        rotation=spec.rotation,
        sector_start=spec.sector_start,
        sector_end=spec.sector_end,
        align=spec.align,
        shape=spec.shape,
    )


def to_object(spec: ObjectSpec) -> SceneObject:
    return SceneObject(
        id=spec.id,
        type=spec.type,
        at=Rect(spec.at.x, spec.at.y, spec.at.w, spec.at.h),
        content=spec.content,
        source=spec.source,
        style=to_style(spec.style),
    )


def _animation(spec) -> tuple[str, dict] | None:
    """La animación continua declarada, si la hay.

    El schema garantiza que solo haya una, así que la primera que
    aparezca es la definitiva.
    """
    for nombre in ("spin", "shake", "pulse", "sway"):
        valor = getattr(spec, nombre, None)
        if valor is not None:
            return nombre, valor.model_dump()
    return None
