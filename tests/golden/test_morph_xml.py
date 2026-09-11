"""Contrasta el XML que generamos con el que escribe PowerPoint real.

El golden file se regenera con `python scripts/make_golden.py` en una
máquina con Office. Estos tests son la defensa contra la suposición que
rompió el Morph la primera vez: el elemento vive en el namespace p159
(2015/09), no en p14, y usar el equivocado hace que PowerPoint lo ignore
en silencio.
"""

import re
import zipfile
from pathlib import Path

import pytest

GOLDEN = Path("fixtures/golden/morph_reference.pptx")
P159_NS = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"

pytestmark = pytest.mark.skipif(
    not GOLDEN.exists(), reason="golden ausente; genéralo con scripts/make_golden.py"
)


def golden_slide2() -> str:
    with zipfile.ZipFile(GOLDEN) as archive:
        return archive.read("ppt/slides/slide2.xml").decode("utf-8")


def generated_slide2(tmp_path) -> str:
    from pptx_compiler.compiler.pipeline import compile_dict

    documento = {
        "scenes": [
            {
                "id": "intro",
                "objects": [
                    {"id": "caja", "type": "shape", "at": {"x": 10, "y": 10, "w": 20, "h": 15}}
                ],
            }
        ],
        "sequence": [
            {"scene": "intro"},
            {"mechanism": "CameraZoom", "target": "caja", "scale": 2.0},
        ],
    }
    salida = compile_dict(documento, tmp_path / "gen.pptx")
    with zipfile.ZipFile(salida) as archive:
        return archive.read("ppt/slides/slide2.xml").decode("utf-8")


class TestGolden:
    """Qué escribe PowerPoint de verdad."""

    def test_el_morph_vive_en_el_namespace_p159(self) -> None:
        assert P159_NS in golden_slide2()

    def test_el_elemento_es_p159_morph(self) -> None:
        assert re.search(r"<p159:morph\b", golden_slide2())

    def test_el_choice_requiere_p159(self) -> None:
        assert re.search(r'Requires="p159"', golden_slide2())

    def test_va_envuelto_en_alternate_content(self) -> None:
        assert "<mc:AlternateContent" in golden_slide2()

    def test_el_fallback_es_un_fade(self) -> None:
        fallback = re.search(r"<mc:Fallback>.*?</mc:Fallback>", golden_slide2(), re.S)
        assert fallback is not None
        assert "<p:fade/>" in fallback.group(0)

    def test_la_duracion_sigue_en_el_namespace_p14(self) -> None:
        """dur es de 2010; solo el morph migró a 2015/09."""
        assert re.search(r"p14:dur=", golden_slide2())


class TestGeneradoCoincide:
    """Lo que generamos debe coincidir con el golden en lo que importa."""

    def test_usamos_el_namespace_p159(self, tmp_path) -> None:
        assert P159_NS in generated_slide2(tmp_path)

    def test_no_usamos_p14_morph(self, tmp_path) -> None:
        """El bug original: PowerPoint ignora p14:morph en silencio."""
        assert not re.search(r"<p14:morph\b", generated_slide2(tmp_path))

    def test_nuestro_choice_requiere_p159(self, tmp_path) -> None:
        assert re.search(r'Requires="p159"', generated_slide2(tmp_path))

    def test_nuestro_morph_declara_la_opcion_de_emparejamiento(self, tmp_path) -> None:
        assert re.search(r'<p159:morph option="byObject"\s*/>', generated_slide2(tmp_path))

    def test_nuestro_fallback_es_un_fade(self, tmp_path) -> None:
        fallback = re.search(
            r"<mc:Fallback>.*?</mc:Fallback>", generated_slide2(tmp_path), re.S
        )
        assert fallback is not None
        assert "fade" in fallback.group(0)
