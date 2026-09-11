"""FocusTransition: encadena focos sobre objetos existentes.

Se implementa reutilizando CameraZoom en lugar de duplicar su lógica.
Que eso sea posible es la prueba de que los mecanismos componen.
"""

from __future__ import annotations

from dataclasses import replace

from pptx_compiler.errors import DSLValidationError
from pptx_compiler.ir.scene import Scene
from pptx_compiler.mechanisms import camera_zoom
from pptx_compiler.mechanisms.base import ExpansionContext
from pptx_compiler.mechanisms.focus_transition.schema import FocusTransitionParams

name = "FocusTransition"


def expand(params: dict, ctx: ExpansionContext) -> list[Scene]:
    try:
        args = FocusTransitionParams.model_validate(params)
    except ValueError as exc:
        raise DSLValidationError(
            f"{name}: la secuencia debe tener al menos un objeto. {exc}"
        ) from exc

    scenes: list[Scene] = []
    for step, target in enumerate(args.sequence):
        step_ctx = replace(ctx, index=ctx.index * 100 + step)
        scenes.extend(
            camera_zoom.expand({"target": target, "scale": args.scale}, step_ctx)
        )
    return scenes
