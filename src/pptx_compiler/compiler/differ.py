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

    if moved or (persistent and (entering or leaving)):
        # Con objetos que permanecen, Morph los deja quietos mientras el
        # resto entra o sale; un fade haría parpadear toda la diapositiva.
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
    """Decide si un objeto persistente cambió lo bastante para morphear.

    La geometría se compara **proyectada**, no en coordenadas de mundo:
    un objeto inmóvil bajo una cámara que se mueve sí cambia en la slide.

    Morph interpola además color, opacidad y texto, así que un cambio de
    estilo cuenta aunque el objeto no se mueva. Sin esto, atenuar un
    objeto no producía transición alguna.
    """
    old = before.get(object_id)
    new = after.get(object_id)
    if old is None or new is None:
        return False

    moved = project(old.at, before.camera) != project(new.at, after.camera)
    restyled = old.style != new.style or old.content != new.content
    return moved or restyled
