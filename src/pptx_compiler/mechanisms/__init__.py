"""Registro de mecanismos.

Añadir un mecanismo es añadir una carpeta y registrarla aquí; el
compilador no se modifica (Open/Closed).
"""

from __future__ import annotations

from types import ModuleType

from pptx_compiler.errors import UnknownMechanismError
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene
from pptx_compiler.mechanisms import (
    before_after,
    camera_zoom,
    focus_transition,
    infinite_canvas,
)
from pptx_compiler.mechanisms.base import ExpansionContext

MECHANISMS: dict[str, ModuleType] = {
    module.name: module
    for module in (camera_zoom, before_after, focus_transition, infinite_canvas)
}


def expand_mechanism(
    name: str, params: dict, current: Scene, world: Rect, index: int = 0
) -> list[Scene]:
    if name not in MECHANISMS:
        raise UnknownMechanismError(name, list(MECHANISMS))
    ctx = ExpansionContext(current=current, world=world, index=index)
    return MECHANISMS[name].expand(params, ctx)
