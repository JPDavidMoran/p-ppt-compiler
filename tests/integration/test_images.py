"""Los objetos de tipo `image` nunca se habían ejecutado.

El tipo existía en el schema y en el renderer, pero sin un test ni un
ejemplo que lo usara: código no ejecutado es código roto mientras no se
demuestre lo contrario.
"""

import zipfile
from pathlib import Path

import pytest
from lxml import etree

from pptx_compiler.compiler.pipeline import compile_dict

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
P159 = "{http://schemas.microsoft.com/office/powerpoint/2015/09/main}"
IMAGEN = Path("tests/fixtures/verde.png")

pytestmark = pytest.mark.skipif(not IMAGEN.exists(), reason="falta la imagen de prueba")


def documento(source: str = str(IMAGEN)) -> dict:
    return {
        "scenes": [
            {
                "id": "intro",
                "objects": [
                    {
                        "id": "logo",
                        "type": "image",
                        "source": source,
                        "at": {"x": 20, "y": 15, "w": 30, "h": 22},
                    },
                    {
                        "id": "titulo",
                        "type": "text",
                        "content": "Con imagen",
                        "at": {"x": 20, "y": 40, "w": 60, "h": 8},
                    },
                ],
            }
        ],
        "sequence": [
            {"scene": "intro"},
            {"mechanism": "CameraZoom", "target": "logo", "scale": 2.0},
        ],
    }


@pytest.fixture
def compiled(tmp_path):
    return compile_dict(documento(), tmp_path / "con_imagen.pptx")


def slide_xml(path, number: int):
    with zipfile.ZipFile(path) as archive:
        return etree.fromstring(archive.read(f"ppt/slides/slide{number}.xml"))


class TestImagenEmbebida:
    def test_el_archivo_se_genera(self, compiled) -> None:
        assert compiled.exists()

    def test_la_imagen_queda_dentro_del_pptx(self, compiled) -> None:
        with zipfile.ZipFile(compiled) as archive:
            medios = [n for n in archive.namelist() if n.startswith("ppt/media/")]
        assert medios, "la imagen no se empaquetó en el .pptx"

    def test_la_imagen_aparece_en_ambas_slides(self, compiled) -> None:
        for numero in (1, 2):
            imagenes = list(slide_xml(compiled, numero).iter(P + "pic"))
            assert imagenes, f"la slide {numero} no contiene la imagen"


class TestIdentidadDeImagenes:
    """Una imagen debe morphear como cualquier otro objeto."""

    def test_conserva_el_mismo_id_entre_slides(self, compiled) -> None:
        def ids(numero):
            root = slide_xml(compiled, numero)
            return {
                c.get("name"): c.get("id")
                for c in root.iter(P + "cNvPr")
                if c.get("name")
            }

        assert ids(1) == ids(2)

    def test_la_imagen_lleva_el_id_del_dsl_como_nombre(self, compiled) -> None:
        nombres = {
            c.get("name") for c in slide_xml(compiled, 1).iter(P + "cNvPr")
        }
        assert "logo" in nombres

    def test_el_zoom_sobre_una_imagen_produce_morph(self, compiled) -> None:
        assert list(slide_xml(compiled, 2).iter(P159 + "morph"))


class TestErrores:
    def test_una_imagen_inexistente_falla_con_mensaje_claro(self, tmp_path) -> None:
        with pytest.raises(FileNotFoundError) as exc:
            compile_dict(documento("no_existe.png"), tmp_path / "roto.pptx")
        assert "logo" in str(exc.value)
        assert "no_existe.png" in str(exc.value)

    def test_una_imagen_sin_source_falla(self, tmp_path) -> None:
        doc = documento()
        del doc["scenes"][0]["objects"][0]["source"]
        with pytest.raises(Exception) as exc:
            compile_dict(doc, tmp_path / "roto.pptx")
        assert "logo" in str(exc.value)
