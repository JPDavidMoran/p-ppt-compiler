"""Spotlight: destaca un objeto atenuando los demás, sin mover la cámara.

Eje que ejercita: énfasis sin desplazamiento. Antes la única forma de
enfatizar era acercarse, lo que obliga a perder de vista el conjunto.
Aquí el contexto permanece y solo cambia el peso visual.

Los objetos de `keep` conservan su opacidad: normalmente el título, que
no debería atenuarse junto con el contenido.
"""

from __future__ import annotations

from dataclasses import replace

from pptx_compiler.ir.scene import Scene
from pptx_compiler.mechanisms.base import ExpansionContext
from pptx_compiler.mechanisms.spotlight.schema import SpotlightParams

name = "Spotlight"


def expand(params: dict, ctx: ExpansionContext) -> list[Scene]:
    args = SpotlightParams.model_validate(params)
    ctx.require(args.target, name)
    for object_id in args.keep:
        ctx.require(object_id, name)

    untouched = {args.target, *args.keep}
    return [
        Scene(
            id=ctx.scene_id(name),
            camera=ctx.current.camera,
            objects=[
                obj if obj.id in untouched else _dimmed(obj, args.dim)
                for obj in ctx.current.objects
            ],
        )
    ]


def _dimmed(obj, opacity: float):
    return replace(obj, style=replace(obj.style, opacity=opacity))
