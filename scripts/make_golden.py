"""Genera el golden file conduciendo PowerPoint real por COM.

El golden es la fuente de verdad del XML de Morph. La documentación
pública no deja claro en qué namespace vive el elemento, y la respuesta
resultó ser p159 (2015/09), no p14: un `p14:morph` se ignora en
silencio y la transición degrada a un corte abrupto.

Regenerar este archivo es la forma de verificar esa suposición contra la
versión de Office instalada.

Requiere Windows con PowerPoint. No forma parte de la suite normal.
"""

from __future__ import annotations

import os
import sys

import win32com.client

PP_LAYOUT_BLANK = 12
MSO_SHAPE_RECTANGLE = 1
PP_TRANSITION_MORPH = 3954
SLIDE_W_PT = 960
SLIDE_H_PT = 540
OUTPUT = os.path.join("fixtures", "golden", "morph_reference.pptx")


def main() -> int:
    out = os.path.abspath(OUTPUT)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)

    app = win32com.client.Dispatch("PowerPoint.Application")
    try:
        pres = app.Presentations.Add(WithWindow=False)
        pres.PageSetup.SlideWidth = SLIDE_W_PT
        pres.PageSetup.SlideHeight = SLIDE_H_PT

        first = pres.Slides.Add(1, PP_LAYOUT_BLANK)
        first.Shapes.AddShape(MSO_SHAPE_RECTANGLE, 100, 100, 200, 150).Name = "caja"

        second = pres.Slides.Add(2, PP_LAYOUT_BLANK)
        second.Shapes.AddShape(MSO_SHAPE_RECTANGLE, 500, 250, 400, 250).Name = "caja"
        second.SlideShowTransition.EntryEffect = PP_TRANSITION_MORPH

        pres.SaveAs(out)
        pres.Close()
    finally:
        app.Quit()

    print(f"golden: {out} ({os.path.getsize(out)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
