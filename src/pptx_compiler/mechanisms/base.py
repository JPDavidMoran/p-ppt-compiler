"""Contrato común de los mecanismos.

Un mecanismo es una macro pura: recibe parámetros y la escena actual, y
emite escenas. No conoce PowerPoint, no genera XML y no asigna ids
OOXML. Ese contrato es lo que hace barato añadir el quinto mecanismo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pptx_compiler.errors import MissingTargetError
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene

DEFAULT_ASPECT = 16 / 9


@dataclass(frozen=True)
class ExpansionContext:
    """Lo que un mecanismo puede ver del estado de la compilación."""

    current: Scene
    world: Rect
    index: int = 0

    @property
    def aspect(self) -> float:
        return self.world.w / self.world.h

    def require(self, object_id: str, mechanism: str) -> Rect:
        """Devuelve la geometría de un objeto, o falla con contexto."""
        obj = self.current.get(object_id)
        if obj is None:
            raise MissingTargetError(
                object_id, mechanism, sorted(self.current.object_ids)
            )
        return obj.at

    def scene_id(self, mechanism: str, step: int = 0) -> str:
        return f"{mechanism}_{self.index}_{step}"


class Mechanism(Protocol):
    name: str

    def expand(self, params: dict, ctx: ExpansionContext) -> list[Scene]: ...
