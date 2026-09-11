"""Inserta transiciones en el XML del slide.

python-pptx no expone transiciones, así que se manipula el árbol lxml
directamente. El bloque va envuelto en mc:AlternateContent para que los
lectores que no entienden la extensión caigan al Fallback en vez de
rechazar el archivo.

Morph vive en el namespace p159 (PowerPoint 2015/09), NO en p14 (2010).
Usar p14 hace que PowerPoint entre al Choice, no reconozca el elemento y
lo ignore en silencio: la transición degrada a un corte abrupto sin
emitir ningún error. El atributo de duración sí sigue en p14.

Estructura verificada contra fixtures/golden/morph_reference.pptx, que
genera PowerPoint real (scripts/make_golden.py).

El orden de los hijos de p:sld es obligatorio: cSld, clrMapOvr y
después la transición. Un elemento fuera de sitio hace que PowerPoint
declare el archivo dañado.
"""

from __future__ import annotations

from lxml import etree

from pptx_compiler.compiler.differ import TransitionKind

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
P159_NS = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"

MORPH_MATCH = {"byObject": "byObject", "byWord": "byWord", "byChar": "byChar"}
DEFAULT_DURATION_MS = 2000  # el mismo ritmo que aplica PowerPoint por defecto


def apply_transition(
    slide, kind: TransitionKind, match: str = "byObject", duration_ms: int = DEFAULT_DURATION_MS
) -> None:
    if kind is TransitionKind.NONE:
        return

    sld = slide._element
    _remove_existing(sld)

    if kind is TransitionKind.MORPH:
        sld.append(_morph(match, duration_ms))
    else:
        sld.append(_fade(duration_ms))


def _remove_existing(sld) -> None:
    for tag in (f"{{{P_NS}}}transition", f"{{{MC_NS}}}AlternateContent"):
        for node in sld.findall(tag):
            sld.remove(node)


def _fade(duration_ms: int):
    transition = etree.SubElement(etree.Element("root"), f"{{{P_NS}}}transition")
    transition.set("spd", "med")
    transition.set(f"{{{P14_NS}}}dur", str(duration_ms))
    etree.SubElement(transition, f"{{{P_NS}}}fade")
    return transition


def _morph(match: str, duration_ms: int):
    """Morph envuelto en AlternateContent, como lo escribe PowerPoint.

    El bloque Choice lleva la transición real y declara Requires="p159";
    el Fallback ofrece un fade a los lectores que no soportan Morph.
    """
    alternate = etree.Element(f"{{{MC_NS}}}AlternateContent", nsmap={"mc": MC_NS})

    choice = etree.SubElement(alternate, f"{{{MC_NS}}}Choice", nsmap={"p159": P159_NS})
    choice.set("Requires", "p159")
    transition = etree.SubElement(
        choice, f"{{{P_NS}}}transition", nsmap={"p14": P14_NS}
    )
    transition.set("spd", "slow")
    transition.set(f"{{{P14_NS}}}dur", str(duration_ms))
    morph = etree.SubElement(transition, f"{{{P159_NS}}}morph")
    morph.set("option", MORPH_MATCH.get(match, "byObject"))

    fallback = etree.SubElement(alternate, f"{{{MC_NS}}}Fallback")
    fade_transition = etree.SubElement(fallback, f"{{{P_NS}}}transition")
    fade_transition.set("spd", "slow")
    etree.SubElement(fade_transition, f"{{{P_NS}}}fade")

    return alternate
