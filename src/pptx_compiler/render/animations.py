"""Inserta animaciones continuas en el XML del slide.

Una transición Morph solo mueve las cosas al cambiar de diapositiva. Para
que algo se mueva mientras se habla —una textura de fondo, una figura que
llama la atención— hace falta un bloque `<p:timing>`, la maquinaria con
la que PowerPoint reproduce sus efectos de énfasis.

Hay cuatro animaciones. `spin` da vueltas completas; las otras tres van y
vuelven sobre el sitio gracias a `autoRev`, que recorre la animación al
revés antes de repetirla:

- `spin`  vuelta completa, sin retorno
- `shake` desplazamiento mínimo y muy rápido: un temblor
- `pulse` la figura crece y encoge sobre su centro
- `sway`  giro corto a un lado y al otro

El árbol de tiempos tiene una anidación fija que no se puede simplificar:
la raíz `tmRoot`, una secuencia `mainSeq` y dos niveles de `par` antes de
llegar a los efectos. PowerPoint la escribe así y rechaza el archivo si
falta un nivel.

Los ángulos van en 1/60000 de grado (una vuelta son 21600000) y las
escalas en milésimas de porcentaje (100000 es el tamaño original). Un
`presetID` debe ser un entero: cualquier otra cosa invalida el archivo.

El orden de los hijos de `p:sld` es obligatorio: el timing va el último,
después de la transición.
"""

from __future__ import annotations

from lxml import etree

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

VUELTA_COMPLETA = 21600000  # 360 grados en 1/60000 de grado
GRADO = 60000
ESCALA_ORIGINAL = 100000  # 100% en milésimas de porcentaje
UNIDADES_MUNDO = 100.0  # el ancho del mundo por defecto

PRESET_GIRO, PRESET_ESCALA, PRESET_VAIVEN = "8", "6", "26"


def apply_animations(slide, pedidos: dict[int, tuple[str, dict]]) -> None:
    """Anima indefinidamente los shapes indicados.

    `pedidos` mapea el id OOXML de cada shape al nombre de su animación y
    sus parámetros. Sin entradas no se emite nada: una diapositiva sin
    animación no debe llevar un bloque de tiempos vacío.
    """
    if not pedidos:
        return
    slide._element.append(_timing(pedidos))


def _timing(pedidos: dict[int, tuple[str, dict]]):
    efectos = "".join(
        _efecto(shape_id, nombre, params)
        for shape_id, (nombre, params) in sorted(pedidos.items())
    )
    return etree.fromstring(
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


def _efecto(shape_id: int, nombre: str, params: dict) -> str:
    base = shape_id * 10
    cuerpo, preset = _CONSTRUCTORES[nombre](shape_id, base, params)
    return (
        f'<p:par><p:cTn id="{base + 5}" presetID="{preset}" '
        'presetClass="emph" fill="hold" nodeType="withEffect">'
        f"<p:childTnLst>{cuerpo}</p:childTnLst></p:cTn></p:par>"
    )


def _comportamiento(base: int, shape_id: int, seconds: float, auto_rev: bool) -> str:
    vuelta = ' autoRev="1"' if auto_rev else ""
    return (
        f'<p:cTn id="{base + 6}" dur="{round(seconds * 1000)}" '
        f'repeatCount="indefinite"{vuelta}/>'
        f'<p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>'
    )


def _spin(shape_id: int, base: int, params: dict) -> tuple[str, str]:
    giro = VUELTA_COMPLETA if params.get("clockwise", True) else -VUELTA_COMPLETA
    return (
        f'<p:animRot by="{giro}"><p:cBhvr>'
        f"{_comportamiento(base, shape_id, params['seconds'], auto_rev=False)}"
        '<p:attrNameLst><p:attrName>r</p:attrName></p:attrNameLst>'
        '</p:cBhvr></p:animRot>',
        PRESET_GIRO,
    )


def _shake(shape_id: int, base: int, params: dict) -> tuple[str, str]:
    """El recorrido va en fracción del lienzo, no en unidades de mundo."""
    salto = round(params["amount"] / UNIDADES_MUNDO, 4)
    return (
        f'<p:animMotion origin="layout" path="M 0 0 L {salto} {salto} L 0 0" '
        'pathEditMode="relative"><p:cBhvr>'
        f"{_comportamiento(base, shape_id, params['seconds'], auto_rev=True)}"
        '<p:attrNameLst><p:attrName>ppt_x</p:attrName>'
        '<p:attrName>ppt_y</p:attrName></p:attrNameLst>'
        '</p:cBhvr></p:animMotion>',
        PRESET_VAIVEN,
    )


def _pulse(shape_id: int, base: int, params: dict) -> tuple[str, str]:
    destino = round(ESCALA_ORIGINAL * (1 + params["amount"] / 100))
    return (
        '<p:animScale><p:cBhvr>'
        f"{_comportamiento(base, shape_id, params['seconds'], auto_rev=True)}"
        f'</p:cBhvr><p:by x="{destino}" y="{destino}"/></p:animScale>',
        PRESET_ESCALA,
    )


def _sway(shape_id: int, base: int, params: dict) -> tuple[str, str]:
    return (
        f'<p:animRot by="{round(params["degrees"] * GRADO)}"><p:cBhvr>'
        f"{_comportamiento(base, shape_id, params['seconds'], auto_rev=True)}"
        '<p:attrNameLst><p:attrName>r</p:attrName></p:attrNameLst>'
        '</p:cBhvr></p:animRot>',
        PRESET_VAIVEN,
    )


_CONSTRUCTORES = {"spin": _spin, "shake": _shake, "pulse": _pulse, "sway": _sway}
