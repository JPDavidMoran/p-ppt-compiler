"""La cámara: un rectángulo sobre el mundo que define el encuadre.

Un objeto inmóvil en el mundo cambia de posición en la slide si la
cámara se mueve. De ahí sale el zoom cinematográfico, sin efectos
especiales: es pura geometría.
"""

from __future__ import annotations

from dataclasses import dataclass

from pptx_compiler.errors import ProjectionError
from pptx_compiler.ir.geometry import Rect


@dataclass(frozen=True)
class Camera:
    x: float
    y: float
    w: float
    h: float

    def __post_init__(self) -> None:
        if self.w <= 0 or self.h <= 0:
            raise ProjectionError(
                f"Cámara degenerada: ancho={self.w}, alto={self.h}. "
                "Ambos deben ser mayores que cero."
            )

    @property
    def center_x(self) -> float:
        return self.x + self.w / 2

    @property
    def center_y(self) -> float:
        return self.y + self.h / 2

    @classmethod
    def framing(cls, target: Rect, scale: float, aspect: float) -> Camera:
        """Encuadra la cámara sobre un objeto.

        `scale` mayor acerca la cámara. La proporción se conserva para
        que la proyección no deforme los objetos.
        """
        if scale <= 0:
            raise ProjectionError(
                f"La escala de encuadre debe ser mayor que cero, recibida {scale}."
            )

        width = max(target.w, target.h * aspect) / scale
        height = width / aspect
        return cls(
            x=target.center_x - width / 2,
            y=target.center_y - height / 2,
            w=width,
            h=height,
        )
