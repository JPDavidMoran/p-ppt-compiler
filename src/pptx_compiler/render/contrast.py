"""Decide el color de un velo a partir del texto que debe hacer legible.

La elección no es estética sino de contraste: un texto claro necesita un
velo oscuro detrás y uno oscuro lo necesita claro. Cualquier otra
combinación reduce la diferencia entre ambos justo donde hacía falta
aumentarla.

La luminancia percibida no es el promedio de los canales. El ojo humano
es mucho más sensible al verde que al azul, y los coeficientes de la
recomendación ITU-R BT.601 recogen esa diferencia.
"""

from __future__ import annotations

ROJO, VERDE, AZUL = 0.299, 0.587, 0.114  # ITU-R BT.601
MEDIA_LUZ = 0.5

OSCURO, CLARO = "000000", "FFFFFF"


def luminance(hex_color: str) -> float:
    """Luminancia percibida, de 0 (negro) a 1 (blanco)."""
    limpio = hex_color.lstrip("#")
    if len(limpio) != 6:
        raise ValueError(
            f"{hex_color!r} no es un color hexadecimal de seis dígitos."
        )
    try:
        r, g, b = (int(limpio[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError as exc:
        raise ValueError(f"{hex_color!r} contiene dígitos no hexadecimales.") from exc
    return (ROJO * r + VERDE * g + AZUL * b) / 255


def veil_color_for(text_color: str) -> str:
    """El velo que más contraste da bajo ese texto.

    Un gris medio cae del lado claro a propósito: el velo oscuro conserva
    algo más de margen cuando el texto es ambiguo.
    """
    return OSCURO if luminance(text_color) >= MEDIA_LUZ else CLARO
