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


class TestSector:
    """Un `pie` sin ángulos declarados dibuja el sector por defecto de
    PowerPoint (0 a 162 grados), que no es un cuarto ni una mitad. Para
    una rueda por sectores hay que poder decir dónde empieza y acaba."""

    def _doc(self, start: float, end: float) -> Document:
        return Document.model_validate(
            {
                "scenes": [
                    {
                        "id": "a",
                        "objects": [
                            {
                                "id": "sector",
                                "type": "shape",
                                "at": {"x": 0, "y": 0, "w": 40, "h": 40},
                                "style": {
                                    "shape": "pie",
                                    "sectorStart": start,
                                    "sectorEnd": end,
                                },
                            }
                        ],
                    }
                ],
                "sequence": [{"scene": "a"}],
            }
        )

    def test_por_defecto_es_un_cuarto(self) -> None:
        from pptx_compiler.dsl.schema import StyleSpec

        style = StyleSpec()
        assert (style.sector_start, style.sector_end) == (0.0, 90.0)

    def test_los_angulos_llegan_al_pptx(self, tmp_path: Path) -> None:
        import re
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(self._doc(0.0, 90.0), tmp_path / "sector.pptx")
        with zipfile.ZipFile(out) as archive:
            xml = archive.read("ppt/slides/slide1.xml").decode()
        # python-pptx escala este ajuste a 100000 por grado.
        assert re.search(r'name="adj1" fmla="val 0"', xml)
        assert re.search(r'name="adj2" fmla="val 9000000"', xml)

    def test_un_sector_invertido_falla(self) -> None:
        with pytest.raises(ValidationError):
            self._doc(180.0, 90.0)


class TestSectorContinuo:
    """Los ángulos de un sector pueden salirse de 0..360.

    Una rueda que avanza siempre en el mismo sentido necesita ángulos
    monótonos: si al pasar de 0 se vuelve a 270, el sector recorre la
    pantalla entera en sentido contrario y se ve una segunda ola.
    """

    def test_un_sector_en_angulos_negativos_es_valido(self) -> None:
        from pptx_compiler.dsl.schema import StyleSpec

        style = StyleSpec.model_validate({"sectorStart": -270.0, "sectorEnd": -180.0})
        assert (style.sector_start, style.sector_end) == (-270.0, -180.0)

    def test_sigue_exigiendo_que_el_final_sea_mayor(self) -> None:
        from pptx_compiler.dsl.schema import StyleSpec

        with pytest.raises(ValidationError):
            StyleSpec.model_validate({"sectorStart": -90.0, "sectorEnd": -180.0})
