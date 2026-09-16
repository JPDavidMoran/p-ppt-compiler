"""Velo de legibilidad: una capa entre el fondo y el texto.

Cuando el texto cae sobre un fondo con figuras o imágenes, un velo
semitransparente y desenfocado lo separa de lo que hay detrás sin ocultar
la escena.

El color no se elige a ojo: depende de la luminancia del texto. Texto
claro pide velo oscuro, y al revés. Ese es el contraste que sobrevive a
un fondo cualquiera.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pptx_compiler.dsl.schema import StyleSpec
from pptx_compiler.render.contrast import luminance, veil_color_for


class TestLuminancia:
    """La luminancia percibida no es el promedio de los canales: el ojo
    es mucho más sensible al verde que al azul."""

    def test_el_negro_es_cero_y_el_blanco_uno(self) -> None:
        assert luminance("000000") == pytest.approx(0.0, abs=0.01)
        assert luminance("FFFFFF") == pytest.approx(1.0, abs=0.01)

    def test_el_verde_pesa_mas_que_el_azul(self) -> None:
        assert luminance("00FF00") > luminance("0000FF")

    def test_acepta_la_almohadilla(self) -> None:
        assert luminance("#FFFFFF") == pytest.approx(luminance("FFFFFF"))

    def test_un_hex_invalido_falla(self) -> None:
        with pytest.raises(ValueError):
            luminance("nohex")


class TestEleccionDelVelo:
    def test_texto_claro_pide_velo_oscuro(self) -> None:
        assert veil_color_for("FFFFFF") == "000000"
        assert veil_color_for("E8EEF4") == "000000"

    def test_texto_oscuro_pide_velo_claro(self) -> None:
        assert veil_color_for("202020") == "FFFFFF"
        assert veil_color_for("1B3A5C") == "FFFFFF"

    def test_el_umbral_esta_a_media_luz(self) -> None:
        """Un gris medio cae del lado claro: el velo oscuro da más margen."""
        assert veil_color_for("808080") == "000000"


class TestVeloEnElEstilo:
    def test_por_defecto_no_hay_velo(self) -> None:
        assert StyleSpec().veil is None

    def test_se_declara_con_opacidad_y_desenfoque(self) -> None:
        style = StyleSpec.model_validate(
            {"veil": {"opacity": 0.45, "blur": 12.0}}
        )
        assert (style.veil.opacity, style.veil.blur) == (0.45, 12.0)

    def test_el_color_es_opcional_y_se_deduce(self) -> None:
        assert StyleSpec.model_validate({"veil": {}}).veil.color is None

    def test_una_opacidad_fuera_de_rango_falla(self) -> None:
        with pytest.raises(ValidationError):
            StyleSpec.model_validate({"veil": {"opacity": 1.5}})


class TestVeloCompilado:
    def _doc(self, style: dict):
        from pptx_compiler.dsl.schema import Document

        return Document.model_validate(
            {
                "scenes": [
                    {
                        "id": "a",
                        "objects": [
                            {
                                "id": "texto",
                                "type": "text",
                                "content": "Legible",
                                "at": {"x": 10, "y": 10, "w": 40, "h": 8},
                                "style": style,
                            }
                        ],
                    }
                ],
                "sequence": [{"scene": "a"}],
            }
        )

    def _xml(self, style: dict, destino: Path) -> str:
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(self._doc(style), destino)
        with zipfile.ZipFile(out) as archive:
            return archive.read("ppt/slides/slide1.xml").decode()

    def test_sin_velo_no_hay_capa_extra(self, tmp_path: Path) -> None:
        xml = self._xml({"color": "FFFFFF"}, tmp_path / "a.pptx")
        assert "<a:blur" not in xml

    def test_el_velo_emite_desenfoque_y_transparencia(self, tmp_path: Path) -> None:
        xml = self._xml(
            {"color": "FFFFFF", "veil": {"opacity": 0.45, "blur": 12.0}},
            tmp_path / "b.pptx",
        )
        assert "<a:blur" in xml
        assert "<a:alpha" in xml

    def test_el_velo_va_detras_del_texto(self, tmp_path: Path) -> None:
        """Dibujado después taparía el texto que debe hacer legible."""
        xml = self._xml(
            {"color": "FFFFFF", "veil": {"opacity": 0.4}}, tmp_path / "c.pptx"
        )
        assert xml.index("<a:blur") < xml.index("Legible")

    def test_el_color_se_deduce_del_texto(self, tmp_path: Path) -> None:
        claro = self._xml(
            {"color": "FFFFFF", "veil": {"opacity": 0.4}}, tmp_path / "d.pptx"
        )
        oscuro = self._xml(
            {"color": "101010", "veil": {"opacity": 0.4}}, tmp_path / "e.pptx"
        )
        assert 'val="000000"' in claro
        assert 'val="FFFFFF"' in oscuro


class TestDesenfoqueDeForma:
    """El desenfoque no es exclusivo del velo automático.

    Un panel de legibilidad que cubre varios textos se declara como una
    forma más, y necesita el mismo borde difuminado para no leerse como
    una caja pegada sobre el fondo.
    """

    def _doc(self, style: dict):
        from pptx_compiler.dsl.schema import Document

        return Document.model_validate(
            {
                "scenes": [
                    {
                        "id": "a",
                        "objects": [
                            {
                                "id": "panel",
                                "type": "shape",
                                "at": {"x": 0, "y": 8, "w": 60, "h": 40},
                                "style": style,
                            }
                        ],
                    }
                ],
                "sequence": [{"scene": "a"}],
            }
        )

    def test_por_defecto_una_forma_no_se_desenfoca(self) -> None:
        assert StyleSpec().blur is None

    def test_el_desenfoque_llega_al_pptx(self, tmp_path: Path) -> None:
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(
            self._doc({"fill": "000000", "opacity": 0.4, "blur": 18.0}),
            tmp_path / "p.pptx",
        )
        with zipfile.ZipFile(out) as archive:
            xml = archive.read("ppt/slides/slide1.xml").decode()
        assert '<a:blur rad="228600"' in xml   # 18 pt x 12700

    def test_un_desenfoque_negativo_falla(self) -> None:
        with pytest.raises(ValidationError):
            StyleSpec.model_validate({"blur": -1.0})


class TestEfectoDelTema:
    """El `p:style` que python-pptx añade a cada forma trae un
    `effectRef` del tema que gana al `effectLst` propio: PowerPoint
    aplica el del tema y descarta el desenfoque sin avisar.

    Es el mismo fallo silencioso que el namespace de Morph: el XML es
    válido, el archivo abre, y el efecto no está.
    """

    def _doc(self, style: dict):
        from pptx_compiler.dsl.schema import Document

        return Document.model_validate(
            {
                "scenes": [
                    {
                        "id": "a",
                        "objects": [
                            {
                                "id": "figura",
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

    def _xml(self, style: dict, destino: Path) -> str:
        import zipfile

        from pptx_compiler.compiler.pipeline import compile_document

        out = compile_document(self._doc(style), destino)
        with zipfile.ZipFile(out) as archive:
            return archive.read("ppt/slides/slide1.xml").decode()

    def test_una_forma_con_blur_no_lleva_style(self, tmp_path: Path) -> None:
        xml = self._xml({"fill": "1B3A5C", "blur": 30.0}, tmp_path / "a.pptx")
        assert "<a:blur" in xml
        assert "<p:style>" not in xml

    def test_una_forma_sin_blur_conserva_su_style(self, tmp_path: Path) -> None:
        """Quitarlo sin motivo cambiaría el aspecto de todo lo demás."""
        assert "<p:style>" in self._xml({"fill": "1B3A5C"}, tmp_path / "b.pptx")
