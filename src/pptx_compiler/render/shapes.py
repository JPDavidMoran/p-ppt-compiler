"""Dibuja los objetos de una escena sobre una slide de python-pptx.

Cada objeto recibe su identificador OOXML estable del registro de
identidad; sin eso PowerPoint no empareja nada entre slides.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Pt

from pptx_compiler.errors import IdentityError
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.identity import IdentityRegistry
from pptx_compiler.ir.scene import Scene, SceneObject
from pptx_compiler.render.projection import project, project_font_size

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
ALPHA_FULL = 100000  # OOXML expresa el alpha en milésimas de porcentaje
AUTO_SHAPES = {
    "rect": MSO_SHAPE.RECTANGLE,
    "ellipse": MSO_SHAPE.OVAL,
    "roundRect": MSO_SHAPE.ROUNDED_RECTANGLE,
}
ALIGNMENTS = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}


def draw_scene(slide, scene: Scene, identity: IdentityRegistry, world_w: float) -> None:
    for obj in scene.objects:
        shape = _draw(slide, obj, scene.camera, world_w)
        if shape is not None:
            _apply_identity(shape, obj.id, identity)


def _draw(slide, obj: SceneObject, camera: Camera, world_w: float):
    box = project(obj.at, camera)
    position = (Emu(box.x), Emu(box.y), Emu(box.w), Emu(box.h))

    if obj.type == "image":
        return _draw_image(slide, obj, position)
    if obj.type == "text":
        return _draw_text(slide, obj, position, camera, world_w)
    return _draw_shape(slide, obj, position, camera, world_w)


def _draw_image(slide, obj: SceneObject, position):
    source = Path(obj.source or "")
    if not source.is_file():
        raise FileNotFoundError(
            f"El objeto {obj.id!r} referencia la imagen {obj.source!r}, que no existe."
        )
    return slide.shapes.add_picture(str(source), *position)


def _draw_text(slide, obj: SceneObject, position, camera: Camera, world_w: float):
    shape = slide.shapes.add_textbox(*position)
    _fill_text(shape, obj, camera, world_w)
    return shape


def _draw_shape(slide, obj: SceneObject, position, camera: Camera, world_w: float):
    shape = slide.shapes.add_shape(AUTO_SHAPES[obj.style.shape], *position)

    if obj.style.fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(obj.style.fill)
        _apply_opacity(shape, obj.style.opacity)
    else:
        shape.fill.background()

    if obj.style.line:
        shape.line.color.rgb = RGBColor.from_string(obj.style.line)
    else:
        shape.line.fill.background()

    if obj.content:
        _fill_text(shape, obj, camera, world_w)
    return shape


def _fill_text(shape, obj: SceneObject, camera: Camera, world_w: float) -> None:
    frame = shape.text_frame
    frame.word_wrap = True
    paragraph = frame.paragraphs[0]
    paragraph.alignment = ALIGNMENTS[obj.style.align]

    run = paragraph.add_run()
    run.text = obj.content
    run.font.size = Pt(project_font_size(obj.style.font_size, camera, world_w))
    run.font.bold = obj.style.bold
    run.font.color.rgb = RGBColor.from_string(obj.style.color)


def alpha_value(opacity: float) -> int:
    """Convierte una opacidad 0..1 al alpha en milésimas de porcentaje."""
    return round(opacity * ALPHA_FULL)


def _apply_opacity(shape, opacity: float) -> None:
    """La opacidad no es propiedad del shape: es un alpha dentro del relleno."""
    if opacity >= 1.0:
        return
    color = shape.fill.fore_color._xFill.find(f"{{{A_NS}}}srgbClr")
    if color is None:
        return
    alpha = etree.SubElement(color, f"{{{A_NS}}}alpha")
    alpha.set("val", str(alpha_value(opacity)))


def _apply_identity(shape, dsl_id: str, identity: IdentityRegistry) -> None:
    """El paso crítico para el Morph: mismo id y mismo nombre en cada slide.

    El `cNvPr` cuelga de `nvSpPr` en una forma y de `nvPicPr` en una
    imagen, así que se busca por nombre en lugar de asumir el envoltorio.
    Vive en el namespace de PresentationML, no en el de DrawingML.
    """
    element = shape._element.find(f".//{{{P_NS}}}cNvPr")
    if element is None:
        raise IdentityError(
            f"El objeto {dsl_id!r} no expone cNvPr, así que no puede morphear."
        )
    element.set("id", str(identity.ooxml_id_for(dsl_id)))
    element.set("name", identity.shape_name_for(dsl_id))
