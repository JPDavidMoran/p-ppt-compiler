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
        bold=spec.bold,
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
