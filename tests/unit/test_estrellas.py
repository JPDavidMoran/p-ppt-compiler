"""Estrellas y grosor de línea.

Una figura de contorno fino y relleno vacío sirve de textura de fondo: se
percibe como patrón y no compite con el contenido. Necesita dos cosas que
el DSL no tenía: la forma en sí y el grosor del trazo.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pptx_compiler.dsl.schema import Document, StyleSpec


def doc(style: dict) -> Document:
    return Document.model_validate(
        {
            "scenes": [
                {
                    "id": "a",
                    "objects": [
                        {
                            "id": "estrella",
                            "type": "shape",
                            "at": {"x": 10, "y": 10, "w": 20, "h": 20},
                            "style": style,
                        }
                    ],
                }
            ],
            "sequence": [{"scene": "a"}],
        }
    )


class TestEstrellas:
    @pytest.mark.parametrize("forma", ["star4", "star5", "star6", "star8"])
    def test_las_estrellas_son_formas_validas(self, forma: str) -> None:
        assert doc({"shape": forma}).scenes[0].objects[0].style.shape == forma

    def test_la_forma_llega_al_pptx(self, tmp_path: Path) -> None:
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(doc({"shape": "star4"}), tmp_path / "e.pptx")
        with zipfile.ZipFile(out) as archive:
            xml = archive.read("ppt/slides/slide1.xml").decode()
        assert 'prst="star4"' in xml


class TestGrosorDeLinea:
    def test_por_defecto_no_se_declara(self) -> None:
        assert StyleSpec().line_width is None

    def test_un_grosor_valido_se_acepta(self) -> None:
        assert StyleSpec.model_validate({"lineWidth": 1.0}).line_width == 1.0

    def test_un_grosor_no_positivo_falla(self) -> None:
        with pytest.raises(ValidationError):
            StyleSpec.model_validate({"lineWidth": 0})

    def test_el_grosor_llega_al_pptx(self, tmp_path: Path) -> None:
        import re
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(
            doc({"shape": "star4", "line": "1B3A5C", "lineWidth": 1.0}),
            tmp_path / "g.pptx",
        )
        with zipfile.ZipFile(out) as archive:
            xml = archive.read("ppt/slides/slide1.xml").decode()
        assert re.search(r'<a:ln w="12700"', xml)   # 1 pt = 12700 EMU

    def test_sin_relleno_el_contorno_se_ve(self, tmp_path: Path) -> None:
        """Una estrella sin `fill` debe quedar hueca, no negra."""
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(
            doc({"shape": "star4", "line": "1B3A5C"}), tmp_path / "h.pptx"
        )
        with zipfile.ZipFile(out) as archive:
            xml = archive.read("ppt/slides/slide1.xml").decode()
        assert "<a:noFill/>" in xml
