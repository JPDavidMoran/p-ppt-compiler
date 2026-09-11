"""Regroup: los mismos objetos pasan a otra disposición.

Eje que ejercita: reorganización. Es donde Morph luce más, porque cada
objeto viaja a su nueva posición mientras conserva su identidad: una
fila que se convierte en cuadrícula se lee como un movimiento, no como
un cambio de diapositiva.

Los objetos no listados en `targets` no se tocan.
"""

from __future__ import annotations

import math

from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene
from pptx_compiler.mechanisms.base import ExpansionContext
from pptx_compiler.mechanisms.regroup.schema import RegroupParams

name = "Regroup"


def expand(params: dict, ctx: ExpansionContext) -> list[Scene]:
    args = RegroupParams.model_validate(params)
    for object_id in args.targets:
        ctx.require(object_id, name)

    area = _area(args, ctx)
    placements = _layout(args, area)

    return [
        Scene(
            id=ctx.scene_id(name),
            camera=ctx.current.camera,
            objects=[
                obj.moved_to(placements[obj.id]) if obj.id in placements else obj
                for obj in ctx.current.objects
            ],
        )
    ]


def _area(args: RegroupParams, ctx: ExpansionContext) -> Rect:
    if args.area:
        return Rect(**args.area)
    camera = ctx.current.camera
    inset_x, inset_y = camera.w * 0.12, camera.h * 0.22
    return Rect(
        x=camera.x + inset_x,
        y=camera.y + inset_y,
        w=camera.w - inset_x * 2,
        h=camera.h - inset_y * 2,
    )


def _layout(args: RegroupParams, area: Rect) -> dict[str, Rect]:
    count = len(args.targets)
    columns = _columns(args.layout, count)
    rows = math.ceil(count / columns)

    cell_w = (area.w - args.gap * (columns - 1)) / columns
    cell_h = (area.h - args.gap * (rows - 1)) / rows

    placements: dict[str, Rect] = {}
    for index, object_id in enumerate(args.targets):
        column, row = index % columns, index // columns
        placements[object_id] = Rect(
            x=area.x + column * (cell_w + args.gap),
            y=area.y + row * (cell_h + args.gap),
            w=cell_w,
            h=cell_h,
        )
    return placements


def _columns(layout: str, count: int) -> int:
    if layout == "row":
        return count
    if layout == "column":
        return 1
    return math.ceil(math.sqrt(count))
