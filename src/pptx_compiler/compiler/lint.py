"""Detecta DSL que compila pero narra mal.

El compilador valida la estructura; el linter revisa la composición: si
la presentación termina en un primer plano, si un antes/después va a
parpadear, si un objeto se arrastra de un tema a otro.

Las reglas viven en rules.py, una función por regla. Registrarlas aquí
es lo único que hace falta para añadir una.
"""

from __future__ import annotations

from pptx_compiler.compiler.rules import (
    Finding,
    Severity,
    check_alineacion,
    check_arrastre,
    check_parpadeo,
    check_sustitucion_de_titulos,
    check_zoom_cierra,
)
from pptx_compiler.ir.scene import Scene

RULES = (
    check_zoom_cierra,
    check_parpadeo,
    check_sustitucion_de_titulos,
    check_arrastre,
    check_alineacion,
)

__all__ = ["Finding", "Severity", "lint"]


def lint(scenes: list[Scene]) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(scenes))
    return findings
