"""Inserta animaciones continuas en el XML del slide.

Una transición Morph solo mueve las cosas al cambiar de diapositiva. Un
giro perpetuo —una textura de fondo que no se detiene mientras se habla—
necesita un bloque `<p:timing>`, que es la maquinaria de animación que
PowerPoint usa para sus efectos de énfasis.

El árbol de tiempos tiene una anidación fija que no se puede simplificar:
la raíz `tmRoot`, una secuencia principal `mainSeq` y tres niveles de
`par` antes de llegar al comportamiento. PowerPoint la escribe así y
rechaza el archivo si falta un nivel.

El giro se expresa en 1/60000 de grado: una vuelta son 21600000. El signo
decide el sentido.

El orden de los hijos de `p:sld` es obligatorio: el timing va el último,
después de la transición.
"""

from __future__ import annotations

from lxml import etree

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

VUELTA_COMPLETA = 21600000  # 360 grados en 1/60000 de grado
PRESET_GIRO = "8"  # el identificador de "Spin" en el catálogo de PowerPoint


def apply_spins(slide, spins: dict[int, tuple[float, bool]]) -> None:
    """Hace girar indefinidamente los shapes indicados.

    `spins` mapea el id OOXML de cada shape a su duración en segundos y
    su sentido. Sin entradas no se emite nada: una diapositiva sin
    animación no debe llevar un bloque de tiempos vacío.
    """
    if not spins:
        return
    slide._element.append(_timing(spins))


def _timing(spins: dict[int, tuple[float, bool]]):
    efectos = "".join(
        _efecto(shape_id, seconds, clockwise)
        for shape_id, (seconds, clockwise) in sorted(spins.items())
    )
    xml = (
        f'<p:timing xmlns:p="{P_NS}" xmlns:a="{A_NS}">'
        '<p:tnLst><p:par>'
        '<p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
        '<p:childTnLst>'
        '<p:seq concurrent="1" nextAc="seek">'
        '<p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        '<p:par><p:cTn id="3" fill="hold"><p:childTnLst>'
        '<p:par><p:cTn id="4" fill="hold"><p:childTnLst>'
        f"{efectos}"
        '</p:childTnLst></p:cTn></p:par>'
        '</p:childTnLst></p:cTn></p:par>'
        '</p:childTnLst></p:cTn>'
        '<p:prevCondLst><p:cond evt="onPrev" delay="0">'
        '<p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '</p:seq>'
        '</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'
    )
    return etree.fromstring(xml)


def _efecto(shape_id: int, seconds: float, clockwise: bool) -> str:
    """Un giro que se repite para siempre sobre un shape.

    Todos arrancan a la vez (`withEffect`) y sin esperar a un clic, así
    que el patrón entero está en marcha desde que aparece la diapositiva.
    """
    giro = VUELTA_COMPLETA if clockwise else -VUELTA_COMPLETA
    base = shape_id * 10
    return (
        f'<p:par><p:cTn id="{base + 5}" presetID="{PRESET_GIRO}" '
        'presetClass="emph" fill="hold" nodeType="withEffect"><p:childTnLst>'
        f'<p:animRot by="{giro}"><p:cBhvr>'
        f'<p:cTn id="{base + 6}" dur="{round(seconds * 1000)}" '
        'repeatCount="indefinite"/>'
        f'<p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>'
        '<p:attrNameLst><p:attrName>r</p:attrName></p:attrNameLst>'
        '</p:cBhvr></p:animRot>'
        '</p:childTnLst></p:cTn></p:par>'
    )
