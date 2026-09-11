"""BeforeAfter: cámara fija; unos objetos se sustituyen por otros.

Eje que ejercita: mundo móvil, cámara fija. Es el complemento exacto de
CameraZoom; juntos validan que la abstracción de escenas es general en
ambos ejes.
"""

from __future__ import annotations

from pptx_compiler.ir.scene import Scene
from pptx_compiler.mechanisms.base import ExpansionContext
from pptx_compiler.mechanisms.before_after.schema import BeforeAfterParams

name = "BeforeAfter"


def expand(params: dict, ctx: ExpansionContext) -> list[Scene]:
    args = BeforeAfterParams.model_validate(params)

    for object_id in (*args.before, *args.after, *args.keep):
        ctx.require(object_id, name)

    return [
        _subset(ctx, args.keep + args.before, step=0),
        _subset(ctx, args.keep + args.after, step=1),
    ]


def _subset(ctx: ExpansionContext, ids: list[str], step: int) -> Scene:
    """Una escena con los mismos objetos de siempre, filtrada por id.

    Conserva el orden de la escena original para que el apilado visual
    no cambie entre el antes y el después.
    """
    wanted = set(ids)
    return Scene(
        id=ctx.scene_id(name, step),
        camera=ctx.current.camera,
        objects=[obj for obj in ctx.current.objects if obj.id in wanted],
    )
