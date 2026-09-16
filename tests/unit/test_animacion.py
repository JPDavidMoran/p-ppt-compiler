"""Animación continua dentro de una diapositiva.

Morph solo mueve las cosas al cambiar de diapositiva. Un giro perpetuo
—una textura de fondo que nunca se detiene— necesita un bloque
`<p:timing>` con `animRot` y `repeatCount="indefinite"`.

Verificado en PowerPoint real antes de implementarlo: el sondeo de
`scripts/` reproduce el giro sin intervención del espectador.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pptx_compiler.dsl.schema import Document, StyleSpec


def doc(spin: dict | None) -> Document:
    style = {"shape": "star4", "line": "1B3A5C"}
    if spin is not None:
        style["spin"] = spin
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


def xml_de(document: Document, destino: Path) -> str:
    import zipfile

    from pptx_compiler.compiler.pipeline import compile_document

    out = compile_document(document, destino)
    with zipfile.ZipFile(out) as archive:
        return archive.read("ppt/slides/slide1.xml").decode()


class TestGiroContinuo:
    def test_por_defecto_no_hay_giro(self) -> None:
        assert StyleSpec().spin is None

    def test_sin_spin_no_se_emite_timing(self, tmp_path: Path) -> None:
        assert "<p:timing" not in xml_de(doc(None), tmp_path / "a.pptx")

    def test_con_spin_se_emite_animrot(self, tmp_path: Path) -> None:
        xml = xml_de(doc({"seconds": 4.0}), tmp_path / "b.pptx")
        assert "<p:timing" in xml
        assert "animRot" in xml
        assert 'repeatCount="indefinite"' in xml

    def test_la_duracion_va_en_milisegundos(self, tmp_path: Path) -> None:
        import re

        xml = xml_de(doc({"seconds": 2.5}), tmp_path / "c.pptx")
        assert re.search(r'dur="2500"', xml)

    def test_el_sentido_invierte_el_angulo(self, tmp_path: Path) -> None:
        horario = xml_de(doc({"seconds": 4.0}), tmp_path / "d.pptx")
        antihorario = xml_de(
            doc({"seconds": 4.0, "clockwise": False}), tmp_path / "e.pptx"
        )
        assert 'by="21600000"' in horario
        assert 'by="-21600000"' in antihorario

    def test_una_duracion_no_positiva_falla(self) -> None:
        with pytest.raises(ValidationError):
            StyleSpec.model_validate({"spin": {"seconds": 0}})

    def test_el_timing_va_despues_de_la_transicion(self, tmp_path: Path) -> None:
        """El orden de los hijos de p:sld es obligatorio en OOXML."""
        documento = Document.model_validate(
            {
                "scenes": [
                    {
                        "id": sid,
                        "objects": [
                            {
                                "id": "estrella",
                                "type": "shape",
                                "at": {"x": x, "y": 10, "w": 20, "h": 20},
                                "style": {"shape": "star4", "spin": {"seconds": 3.0}},
                            }
                        ],
                    }
                    for sid, x in (("a", 10), ("b", 40))
                ],
                "sequence": [{"scene": "a"}, {"scene": "b"}],
            }
        )
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(documento, tmp_path / "f.pptx")
        with zipfile.ZipFile(out) as archive:
            xml = archive.read("ppt/slides/slide2.xml").decode()
        assert xml.index("AlternateContent") < xml.index("<p:timing")
