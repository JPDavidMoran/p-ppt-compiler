"""InfiniteCanvas: un lienzo mayor que el encuadre, recorrido por la cámara.

Eje que ejercita: panning lateral y objetos fuera del encuadre. Los
objetos declarados aquí se añaden a la escena igual que si estuvieran
escritos en el DSL; es azúcar para no declarar a mano una escena con
muchos objetos dispersos.
"""

from __future__ import annotations

from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.dsl.convert import to_style
from pptx_compiler.ir.scene import Scene, SceneObject
from pptx_compiler.mechanisms.base import ExpansionContext
from pptx_compiler.mechanisms.infinite_canvas.schema import (
    CanvasObject,
    InfiniteCanvasParams,
)

name = "InfiniteCanvas"


def expand(params: dict, ctx: ExpansionContext) -> list[Scene]:
    args = InfiniteCanvasParams.model_validate(params)

    populated = Scene(
        id=ctx.scene_id(name),
        camera=ctx.current.camera,
        objects=[*ctx.current.objects, *(_to_object(o) for o in args.objects)],
    )
    stop_ctx = ExpansionContext(current=populated, world=ctx.world, index=ctx.index)

    scenes: list[Scene] = []
    for step, stop in enumerate(args.tour):
        target = stop_ctx.require(stop.at, name)
        camera = Camera.framing(target, scale=stop.scale, aspect=ctx.aspect)
        scenes.append(populated.with_camera(camera, ctx.scene_id(name, step)))
    return scenes


def _to_object(spec: CanvasObject) -> SceneObject:
    return SceneObject(
        id=spec.id,
        type=spec.type,
        at=Rect(x=spec.at.x, y=spec.at.y, w=spec.at.w, h=spec.at.h),
        content=spec.content,
        source=spec.source,
        style=to_style(spec.style),
    )
