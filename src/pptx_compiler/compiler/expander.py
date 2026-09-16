"""Expande la secuencia del DSL a una lista plana de escenas.

Es donde las macros dejan de existir: a partir de aquí el compilador
solo ve escenas, y los mecanismos son invisibles.
"""

from __future__ import annotations

from pptx_compiler.dsl.convert import to_object
from pptx_compiler.dsl.schema import Document, MechanismCall, SceneRef, SceneSpec
from pptx_compiler.errors import EmptySequenceError, UnknownSceneError
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene
from pptx_compiler.mechanisms import expand_mechanism


def expand(document: Document) -> list[Scene]:
    world = Rect(0, 0, document.world.w, document.world.h)
    declared = {spec.id: spec for spec in document.scenes}
    default_camera = Camera(0, 0, world.w, world.h)

    scenes: list[Scene] = []
    current = Scene(id="__empty__", camera=default_camera, objects=[])

    for index, entry in enumerate(document.sequence):
        if isinstance(entry, SceneRef):
            if entry.scene not in declared:
                raise UnknownSceneError(entry.scene, list(declared))
            current = _to_scene(declared[entry.scene], default_camera)
            if entry.emit:
                scenes.append(current)
        else:
            produced = expand_mechanism(
                entry.mechanism, _params(entry), current, world, index
            )
            scenes.extend(produced)
            current = produced[-1]

    if not scenes:
        raise EmptySequenceError("La secuencia no produjo ninguna escena.")
    return scenes


def _params(call: MechanismCall) -> dict:
    return call.model_dump(exclude={"mechanism"}, by_alias=True)


def _to_scene(spec: SceneSpec, default_camera: Camera) -> Scene:
    camera = default_camera
    if spec.camera is not None:
        camera = Camera(spec.camera.x, spec.camera.y, spec.camera.w, spec.camera.h)
    return Scene(
        id=spec.id,
        camera=camera,
        objects=[to_object(obj) for obj in spec.objects],
    )

