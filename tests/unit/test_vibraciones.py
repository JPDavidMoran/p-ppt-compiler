"""Animaciones continuas de ida y vuelta.

`spin` da la vuelta completa; estas tres van y vuelven sobre el sitio.
Todas se apoyan en `autoRev`, que recorre la animación al revés antes de
repetirla, así que la figura regresa siempre a su posición original.

Verificadas en PowerPoint real antes de implementarlas.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pptx_compiler.dsl.schema import Document, StyleSpec


def doc(style_extra: dict) -> Document:
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
                            "style": {"shape": "star4", **style_extra},
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


class TestTemblor:
    """`shake`: la figura se desplaza y vuelve, muy rápido."""

    def test_por_defecto_no_tiembla(self) -> None:
        assert StyleSpec().shake is None

    def test_emite_un_desplazamiento_de_ida_y_vuelta(self, tmp_path: Path) -> None:
        xml = xml_de(doc({"shake": {"seconds": 0.1}}), tmp_path / "a.pptx")
        assert "animMotion" in xml
        assert 'autoRev="1"' in xml
        assert 'repeatCount="indefinite"' in xml

    def test_la_amplitud_entra_en_el_recorrido(self, tmp_path: Path) -> None:
        xml = xml_de(
            doc({"shake": {"seconds": 0.1, "amount": 0.5}}), tmp_path / "b.pptx"
        )
        assert "0.005" in xml   # amount va en unidades de mundo, path en fracción

    def test_una_amplitud_no_positiva_falla(self) -> None:
        with pytest.raises(ValidationError):
            StyleSpec.model_validate({"shake": {"seconds": 0.1, "amount": 0}})


class TestLatido:
    """`pulse`: la figura crece y encoge sobre su centro."""

    def test_por_defecto_no_late(self) -> None:
        assert StyleSpec().pulse is None

    def test_emite_un_cambio_de_escala(self, tmp_path: Path) -> None:
        xml = xml_de(doc({"pulse": {"seconds": 0.7}}), tmp_path / "c.pptx")
        assert "animScale" in xml
        assert 'autoRev="1"' in xml

    def test_el_porcentaje_llega_al_xml(self, tmp_path: Path) -> None:
        xml = xml_de(
            doc({"pulse": {"seconds": 0.7, "amount": 15.0}}), tmp_path / "d.pptx"
        )
        assert 'x="115000"' in xml   # 115% en milésimas de porcentaje


class TestBalanceo:
    """`sway`: la figura gira a un lado y al otro."""

    def test_por_defecto_no_se_balancea(self) -> None:
        assert StyleSpec().sway is None

    def test_emite_una_rotacion_de_ida_y_vuelta(self, tmp_path: Path) -> None:
        xml = xml_de(doc({"sway": {"seconds": 0.4}}), tmp_path / "e.pptx")
        assert "animRot" in xml
        assert 'autoRev="1"' in xml

    def test_los_grados_van_en_sesentamilavos(self, tmp_path: Path) -> None:
        xml = xml_de(
            doc({"sway": {"seconds": 0.4, "degrees": 15.0}}), tmp_path / "f.pptx"
        )
        assert 'by="900000"' in xml   # 15 grados x 60000


class TestCombinaciones:
    def test_dos_animaciones_a_la_vez_fallan(self) -> None:
        """Un objeto no puede girar y temblar: los efectos se pisarían."""
        with pytest.raises(ValidationError):
            StyleSpec.model_validate(
                {"spin": {"seconds": 4}, "shake": {"seconds": 0.1}}
            )

    def test_cada_figura_puede_llevar_la_suya(self, tmp_path: Path) -> None:
        documento = Document.model_validate(
            {
                "scenes": [
                    {
                        "id": "a",
                        "objects": [
                            {
                                "id": oid,
                                "type": "shape",
                                "at": {"x": x, "y": 10, "w": 15, "h": 15},
                                "style": {"shape": "star4", **estilo},
                            }
                            for oid, x, estilo in (
                                ("gira", 10, {"spin": {"seconds": 5}}),
                                ("tiembla", 40, {"shake": {"seconds": 0.1}}),
                                ("late", 70, {"pulse": {"seconds": 0.8}}),
                            )
                        ],
                    }
                ],
                "sequence": [{"scene": "a"}],
            }
        )
        xml = xml_de(documento, tmp_path / "g.pptx")
        assert "animRot" in xml and "animMotion" in xml and "animScale" in xml


class TestImagenAnimada:
    """Una imagen también puede animarse.

    Su `cNvPr` cuelga de `nvPicPr` y no de `nvSpPr`, así que buscarlo por
    el envoltorio equivocado rompe la compilación.
    """

    def test_una_imagen_con_latido_compila(self, tmp_path: Path) -> None:
        documento = Document.model_validate(
            {
                "scenes": [
                    {
                        "id": "a",
                        "objects": [
                            {
                                "id": "foto",
                                "type": "image",
                                "source": "examples/assets/parque.png",
                                "at": {"x": 10, "y": 10, "w": 20, "h": 20},
                                "style": {"pulse": {"seconds": 2.0}},
                            }
                        ],
                    }
                ],
                "sequence": [{"scene": "a"}],
            }
        )
        assert "animScale" in xml_de(documento, tmp_path / "img.pptx")
