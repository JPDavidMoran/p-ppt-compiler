"""Compila documentos reales y afirma sobre el .pptx resultante.

Estos tests abren el archivo generado y leen su XML: es la única forma
de comprobar que la identidad sobrevive y que la transición quedó en el
sitio correcto.
"""

import zipfile

import pytest
from lxml import etree

from pptx_compiler.compiler.pipeline import compile_dict

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
P14 = "{http://schemas.microsoft.com/office/powerpoint/2010/main}"
P159 = "{http://schemas.microsoft.com/office/powerpoint/2015/09/main}"


def doc_zoom() -> dict:
    return {
        "presentation": {"title": "Zoom"},
        "scenes": [
            {
                "id": "intro",
                "objects": [
                    {
                        "id": "titulo",
                        "type": "text",
                        "content": "Áreas verdes",
                        "at": {"x": 10, "y": 15, "w": 60, "h": 10},
                    },
                    {
                        "id": "dash",
                        "type": "shape",
                        "at": {"x": 60, "y": 32, "w": 25, "h": 18},
                        "style": {"fill": "2D6A4F"},
                    },
                ],
            }
        ],
        "sequence": [
            {"scene": "intro"},
            {"mechanism": "CameraZoom", "target": "dash", "scale": 2.5},
        ],
    }


def slide_xml(path, number: int):
    with zipfile.ZipFile(path) as archive:
        return etree.fromstring(archive.read(f"ppt/slides/slide{number}.xml"))


def shape_ids(root) -> dict[str, str]:
    return {c.get("name"): c.get("id") for c in root.iter(P + "cNvPr") if c.get("name")}


@pytest.fixture
def compiled(tmp_path):
    return compile_dict(doc_zoom(), tmp_path / "out.pptx")


class TestArchivo:
    def test_se_genera_el_archivo(self, compiled) -> None:
        assert compiled.exists()
        assert compiled.stat().st_size > 0

    def test_es_un_zip_valido_con_las_partes_esperadas(self, compiled) -> None:
        with zipfile.ZipFile(compiled) as archive:
            nombres = archive.namelist()
        assert "ppt/presentation.xml" in nombres
        assert "ppt/slides/slide1.xml" in nombres
        assert "ppt/slides/slide2.xml" in nombres

    def test_una_escena_por_slide(self, compiled) -> None:
        with zipfile.ZipFile(compiled) as archive:
            slides = [n for n in archive.namelist() if n.startswith("ppt/slides/slide")]
        assert len(slides) == 2


class TestIdentidad:
    """El riesgo principal del proyecto: si esto falla, Morph degrada en silencio."""

    def test_el_id_de_un_objeto_persistente_es_el_mismo_en_ambas_slides(
        self, compiled
    ) -> None:
        assert shape_ids(slide_xml(compiled, 1)) == shape_ids(slide_xml(compiled, 2))

    def test_los_objetos_conservan_su_nombre_del_dsl(self, compiled) -> None:
        assert set(shape_ids(slide_xml(compiled, 1))) == {"titulo", "dash"}

    def test_objetos_distintos_tienen_ids_distintos(self, compiled) -> None:
        ids = shape_ids(slide_xml(compiled, 1))
        assert ids["titulo"] != ids["dash"]


class TestTransicion:
    def test_la_segunda_slide_lleva_morph(self, compiled) -> None:
        root = slide_xml(compiled, 2)
        morphs = list(root.iter(P159 + "morph"))
        assert len(morphs) == 1
        assert morphs[0].get("option") == "byObject"

    def test_el_morph_va_envuelto_en_alternate_content(self, compiled) -> None:
        root = slide_xml(compiled, 2)
        assert root.find(MC + "AlternateContent") is not None

    def test_hay_un_fallback_para_lectores_sin_p14(self, compiled) -> None:
        root = slide_xml(compiled, 2)
        fallback = root.find(f"{MC}AlternateContent/{MC}Fallback")
        assert fallback is not None
        assert fallback.find(f".//{P}fade") is not None

    def test_la_transicion_va_despues_de_clr_map_ovr(self, compiled) -> None:
        """El orden de hijos de p:sld es obligatorio en OOXML."""
        hijos = [e.tag.split("}")[-1] for e in slide_xml(compiled, 2)]
        assert hijos == ["cSld", "clrMapOvr", "AlternateContent"]

    def test_la_primera_slide_no_lleva_transicion(self, compiled) -> None:
        hijos = [e.tag.split("}")[-1] for e in slide_xml(compiled, 1)]
        assert "AlternateContent" not in hijos


class TestFade:
    def test_objetos_que_solo_entran_y_salen_producen_fade(self, tmp_path) -> None:
        documento = {
            "scenes": [
                {
                    "id": "base",
                    "objects": [
                        {"id": "t", "type": "text", "content": "x", "at": {"x": 1, "y": 1, "w": 9, "h": 9}},
                        {"id": "viejo", "type": "shape", "at": {"x": 20, "y": 1, "w": 9, "h": 9}},
                        {"id": "nuevo", "type": "shape", "at": {"x": 20, "y": 1, "w": 9, "h": 9}},
                    ],
                }
            ],
            "sequence": [
                {"scene": "base"},
                {
                    "mechanism": "BeforeAfter",
                    "before": ["viejo"],
                    "after": ["nuevo"],
                    "keep": ["t"],
                },
            ],
        }
        salida = compile_dict(documento, tmp_path / "fade.pptx")
        tercera = slide_xml(salida, 3)
        assert tercera.find(P + "transition") is not None
        assert not list(tercera.iter(P159 + "morph"))


class TestSlideUnica:
    def test_una_sola_escena_compila_sin_transicion(self, tmp_path) -> None:
        documento = {
            "scenes": [
                {
                    "id": "sola",
                    "objects": [
                        {"id": "t", "type": "text", "content": "hola", "at": {"x": 1, "y": 1, "w": 9, "h": 9}}
                    ],
                }
            ],
            "sequence": [{"scene": "sola"}],
        }
        salida = compile_dict(documento, tmp_path / "una.pptx")
        with zipfile.ZipFile(salida) as archive:
            slides = [n for n in archive.namelist() if n.startswith("ppt/slides/slide")]
        assert len(slides) == 1


class TestInspect:
    """La herramienta de diagnóstico debe reconocer lo que el compilador emite.

    Quedó desincronizada al migrar Morph de p14 a p159 y reportó "ninguna"
    sobre un XML correcto: una herramienta de diagnóstico que miente es
    peor que no tenerla.
    """

    def test_reporta_el_morph_de_la_segunda_slide(self, compiled) -> None:
        from pptx_compiler.cli.inspect import describe

        assert any("morph" in line for line in describe(compiled))

    def test_reporta_los_nombres_de_los_objetos(self, compiled) -> None:
        from pptx_compiler.cli.inspect import describe

        volcado = "\n".join(describe(compiled))
        assert "name=titulo" in volcado
        assert "name=dash" in volcado
