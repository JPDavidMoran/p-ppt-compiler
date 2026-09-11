"""Reveal: una tapa se aparta y deja ver lo que había debajo.

Eje que ejercita: descubrimiento. La tapa conserva su id, así que Morph
la desplaza en lugar de desvanecerla, y el gesto se lee como apartar
algo y no como un cambio de contenido.

La tapa sale del encuadre: el objeto sigue existiendo fuera de la
diapositiva, que es lo que permite el movimiento continuo.
"""

from __future__ import annotations

from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene
from pptx_compiler.mechanisms.base import ExpansionContext
from pptx_compiler.mechanisms.reveal.schema import RevealParams

name = "Reveal"

MARGIN = 1.15  # cuánto sale la tapa más allá del borde


def expand(params: dict, ctx: ExpansionContext) -> list[Scene]:
    args = RevealParams.model_validate(params)
    cover = ctx.require(args.cover, name)
    ctx.require(args.target, name)

    closed = Scene(
        id=ctx.scene_id(name, 0),
        camera=ctx.current.camera,
        objects=list(ctx.current.objects),
    )

    moved = _displaced(cover, args.direction, ctx)
    opened = Scene(
        id=ctx.scene_id(name, 1),
        camera=ctx.current.camera,
        objects=[
            obj.moved_to(moved) if obj.id == args.cover else obj
            for obj in ctx.current.objects
        ],
    )
    return [closed, opened]


def _displaced(cover: Rect, direction: str, ctx: ExpansionContext) -> Rect:
    camera = ctx.current.camera
    if direction == "up":
        return Rect(cover.x, camera.y - cover.h * MARGIN, cover.w, cover.h)
    if direction == "down":
        return Rect(cover.x, camera.y + camera.h * MARGIN, cover.w, cover.h)
    if direction == "left":
        return Rect(camera.x - cover.w * MARGIN, cover.y, cover.w, cover.h)
    return Rect(camera.x + camera.w * MARGIN, cover.y, cover.w, cover.h)
