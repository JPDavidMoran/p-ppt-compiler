"""Rectángulos en coordenadas de mundo y en EMU de slide."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    """Rectángulo en coordenadas de mundo."""

    x: float
    y: float
    w: float
    h: float

    @property
    def center_x(self) -> float:
        return self.x + self.w / 2

    @property
    def center_y(self) -> float:
        return self.y + self.h / 2


@dataclass(frozen=True)
class EmuRect:
    """Rectángulo proyectado, en EMU, listo para OOXML.

    Los valores pueden ser negativos o exceder el área de la slide: un
    objeto fuera de encuadre se emite igualmente para que conserve su
    identidad y pueda entrar desde fuera del marco.
    """

    x: int
    y: int
    w: int
    h: int
