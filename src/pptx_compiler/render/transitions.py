"""Inserta transiciones en el XML del slide.

python-pptx no expone transiciones, así que se manipula el árbol lxml
directamente. Morph vive en la extensión p14 de PowerPoint, envuelta en
mc:AlternateContent para que los lectores que no la entienden caigan al
Fallback en vez de rechazar el archivo.

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

MORPH_MATCH = {"byObject": "byObject", "byWord": "byWord", "byChar": "byChar"}
DEFAULT_DURATION_MS = 1000


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

    El bloque Choice lleva la transición real; el Fallback ofrece un fade
    a los lectores que no soportan la extensión p14.
    """
    alternate = etree.Element(f"{{{MC_NS}}}AlternateContent", nsmap={"mc": MC_NS})

    choice = etree.SubElement(alternate, f"{{{MC_NS}}}Choice", nsmap={"p14": P14_NS})
    choice.set("Requires", "p14")
    transition = etree.SubElement(choice, f"{{{P_NS}}}transition")
    transition.set("spd", "slow")
    transition.set(f"{{{P14_NS}}}dur", str(duration_ms))
    morph = etree.SubElement(transition, f"{{{P14_NS}}}morph")
    morph.set("option", MORPH_MATCH.get(match, "byObject"))

    fallback = etree.SubElement(alternate, f"{{{MC_NS}}}Fallback")
    fade_transition = etree.SubElement(fallback, f"{{{P_NS}}}transition")
    fade_transition.set("spd", "slow")
    etree.SubElement(fade_transition, f"{{{P_NS}}}fade")

    return alternate
