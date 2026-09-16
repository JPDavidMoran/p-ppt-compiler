"""La rotación es una propiedad del objeto, como la posición.

Un sector de círculo que gira es el mismo objeto en dos ángulos: si Morph
la interpola, la rueda gira; si no, salta. Que el compilador la emita es
condición necesaria para averiguarlo.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pptx_compiler.compiler.differ import TransitionKind, diff
from pptx_compiler.compiler.expander import expand
from pptx_compiler.dsl.schema import Document


def doc(angles: tuple[float, float]) -> Document:
    return Document.model_validate(
        {
            "scenes": [
                {
                    "id": scene_id,
                    "objects": [
                        {
                            "id": "sector",
                            "type": "shape",
                            "at": {"x": 10, "y": 10, "w": 40, "h": 40},
                            "style": {"shape": "pie", "rotation": angle},
                        }
                    ],
                }
                for scene_id, angle in zip(("a", "b"), angles)
            ],
            "sequence": [{"scene": "a"}, {"scene": "b"}],
        }
    )


class TestRotacion:
    def test_por_defecto_no_hay_giro(self) -> None:
        from pptx_compiler.dsl.schema import StyleSpec

        assert StyleSpec().rotation == 0.0

    def test_un_cambio_de_angulo_produce_morph(self) -> None:
        scenes = expand(doc((0.0, 120.0)))
        assert diff(*scenes).kind is TransitionKind.MORPH

    def test_el_mismo_angulo_no_produce_transicion(self) -> None:
        scenes = expand(doc((45.0, 45.0)))
        assert diff(*scenes).kind is TransitionKind.NONE

    def test_el_angulo_llega_al_pptx(self, tmp_path: Path) -> None:
        import re
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(doc((0.0, 120.0)), tmp_path / "giro.pptx")
        with zipfile.ZipFile(out) as archive:
            xml = archive.read("ppt/slides/slide2.xml").decode()
        assert re.search(r'rot="7200000"', xml)

    def test_un_angulo_fuera_de_rango_falla(self) -> None:
        with pytest.raises(ValidationError):
            doc((0.0, 400.0))
