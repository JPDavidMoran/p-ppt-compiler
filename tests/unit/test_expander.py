"""La secuencia se expande a una lista plana de escenas.

Una entrada de escena normalmente emite una slide. Con `emit: false`
carga el estado sin dibujarlo: es lo que permite que un mecanismo tome
una escena como punto de partida sin que el espectador vea antes el
estado que el mecanismo va a ir revelando.
"""

import pytest

from pptx_compiler.compiler.expander import expand
from pptx_compiler.dsl.schema import Document
from pptx_compiler.errors import EmptySequenceError


def doc(sequence: list[dict], objects: list[str] | None = None) -> Document:
    names = objects if objects is not None else ["a", "b"]
    return Document.model_validate(
        {
            "scenes": [
                {
                    "id": "base",
                    "objects": [
                        {
                            "id": name,
                            "type": "shape",
                            "at": {"x": 10 + index * 20, "y": 10, "w": 10, "h": 10},
                        }
                        for index, name in enumerate(names)
                    ],
                }
            ],
            "sequence": sequence,
        }
    )


class TestEmitFalse:
    """Una escena silenciosa carga estado sin producir slide."""

    def test_una_escena_normal_emite_slide(self) -> None:
        scenes = expand(doc([{"scene": "base"}]))
        assert [s.id for s in scenes] == ["base"]

    def test_una_escena_silenciosa_no_emite_slide(self) -> None:
        scenes = expand(
            doc([{"scene": "base", "emit": False}, {"scene": "base"}])
        )
        assert [s.id for s in scenes] == ["base"]

    def test_el_mecanismo_parte_de_la_escena_silenciosa(self) -> None:
        """Build revela de uno en uno sin mostrar antes el conjunto."""
        scenes = expand(
            doc(
                [
                    {"scene": "base", "emit": False},
                    {"mechanism": "Build", "sequence": ["a", "b"]},
                ]
            )
        )
        assert [sorted(s.object_ids) for s in scenes] == [["a"], ["a", "b"]]

    def test_una_secuencia_de_solo_silenciosas_falla(self) -> None:
        with pytest.raises(EmptySequenceError):
            expand(doc([{"scene": "base", "emit": False}]))


class TestDuracion:
    """La presentación declara el ritmo de sus transiciones."""

    def test_por_defecto_son_2000_ms(self) -> None:
        from pptx_compiler.dsl.schema import Document

        assert Document.model_validate(
            {"sequence": [{"scene": "base"}], "scenes": [{"id": "base"}]}
        ).presentation.transition_ms == 2000

    def test_se_puede_declarar_otro_ritmo(self) -> None:
        from pptx_compiler.dsl.schema import Document

        doc = Document.model_validate(
            {
                "presentation": {"transitionMs": 700},
                "scenes": [{"id": "base"}],
                "sequence": [{"scene": "base"}],
            }
        )
        assert doc.presentation.transition_ms == 700

    def test_una_duracion_no_positiva_falla(self) -> None:
        import pytest as _pytest
        from pydantic import ValidationError

        from pptx_compiler.dsl.schema import Document

        with _pytest.raises(ValidationError):
            Document.model_validate(
                {
                    "presentation": {"transitionMs": 0},
                    "scenes": [{"id": "base"}],
                    "sequence": [{"scene": "base"}],
                }
            )
