"""CameraZoom: la cámara se acerca a un objeto; el mundo no se mueve.

Eje que ejercita: cámara móvil, mundo fijo. El differ verá todos los
objetos transformados porque cambió la proyección, y pedirá un Morph.
"""

from __future__ import annotations

from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.scene import Scene
from pptx_compiler.mechanisms.base import ExpansionContext
from pptx_compiler.mechanisms.camera_zoom.schema import CameraZoomParams

name = "CameraZoom"


def expand(params: dict, ctx: ExpansionContext) -> list[Scene]:
    args = CameraZoomParams.model_validate(params)
    target = ctx.require(args.target, name)
    camera = Camera.framing(target, scale=args.scale, aspect=ctx.aspect)
    return [ctx.current.with_camera(camera, ctx.scene_id(name))]
