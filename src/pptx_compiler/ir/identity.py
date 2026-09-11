"""Mapa estable entre ids del DSL e identificadores OOXML.

Existe un único registro por compilación, de modo que un objeto presente
en varias escenas reciba el mismo identificador en todas las slides. Sin
esta estabilidad, PowerPoint no empareja los objetos y el Morph degrada
a un fade genérico, en silencio.
"""

from __future__ import annotations

FIRST_SHAPE_ID = 2  # el 1 lo reserva el grupo raíz de cada slide
CREATION_ID_BASE = 0x10000000


class IdentityRegistry:
    def __init__(self) -> None:
        self._ooxml_ids: dict[str, int] = {}
        self._next_id = FIRST_SHAPE_ID

    def ooxml_id_for(self, dsl_id: str) -> int:
        if dsl_id not in self._ooxml_ids:
            self._ooxml_ids[dsl_id] = self._next_id
            self._next_id += 1
        return self._ooxml_ids[dsl_id]

    def creation_id_for(self, dsl_id: str) -> int:
        """Identificador de creación que PowerPoint usa para emparejar Morph.

        Derivado del id OOXML para que ambos permanezcan sincronizados.
        """
        return CREATION_ID_BASE + self.ooxml_id_for(dsl_id)

    def shape_name_for(self, dsl_id: str) -> str:
        """Nombre visible del shape; PowerPoint lo usa como criterio alterno."""
        return dsl_id
