"""Deriva la transición entre dos escenas consecutivas.

El DSL da identidad explícita a los objetos, así que no hay que adivinar
qué objeto corresponde a cuál: el autor lo dijo con el id. Lo único que
decide el differ es si la geometría proyectada cambió.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pptx_compiler.ir.scene import Scene
from pptx_compiler.render.projection import project


class TransitionKind(Enum):
    NONE = "none"
    FADE = "fade"
    MORPH = "morph"


@dataclass(frozen=True)
class SceneDiff:
    kind: TransitionKind
    persistent: set[str]
    entering: set[str]
    leaving: set[str]
    moved: set[str]


def diff(before: Scene, after: Scene) -> SceneDiff:
    persistent = before.object_ids & after.object_ids
    entering = after.object_ids - before.object_ids
    leaving = before.object_ids - after.object_ids

    moved = {oid for oid in persistent if _changed(before, after, oid)}

    if moved:
        kind = TransitionKind.MORPH
    elif entering or leaving:
        kind = TransitionKind.FADE
    else:
        kind = TransitionKind.NONE

    return SceneDiff(
        kind=kind,
        persistent=persistent,
        entering=entering,
        leaving=leaving,
        moved=moved,
    )


def _changed(before: Scene, after: Scene, object_id: str) -> bool:
    """Compara la geometría proyectada, no la de mundo.

    Un objeto inmóvil bajo una cámara que se mueve sí cambia en la slide.
    """
    old = before.get(object_id)
    new = after.get(object_id)
    if old is None or new is None:
        return False
    return project(old.at, before.camera) != project(new.at, after.camera)
