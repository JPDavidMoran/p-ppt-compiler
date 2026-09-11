"""La opacidad es un atributo de estilo y la base de Spotlight.

En OOXML no es una propiedad del shape: se expresa como un alpha dentro
del relleno sólido, en milésimas de porcentaje.
"""

import pytest

from pptx_compiler.dsl.loader import parse_document
from pptx_compiler.errors import DSLValidationError
from pptx_compiler.ir.scene import ObjectStyle


def documento(opacity) -> dict:
    return {
        "scenes": [
            {
                "id": "a",
                "objects": [
                    {
                        "id": "caja",
                        "type": "shape",
                        "at": {"x": 10, "y": 10, "w": 20, "h": 15},
                        "style": {"fill": "2D6A4F", "opacity": opacity},
                    }
                ],
            }
        ],
        "sequence": [{"scene": "a"}],
    }


class TestSchema:
    def test_la_opacidad_por_defecto_es_opaco(self) -> None:
        assert ObjectStyle().opacity == 1.0

    def test_se_acepta_un_valor_intermedio(self) -> None:
        doc = parse_document(documento(0.3))
        assert doc.scenes[0].objects[0].style.opacity == 0.3

    def test_se_acepta_cero(self) -> None:
        assert parse_document(documento(0.0)).scenes[0].objects[0].style.opacity == 0.0

    @pytest.mark.parametrize("valor", [-0.1, 1.5, 2])
    def test_fuera_de_rango_falla(self, valor) -> None:
        with pytest.raises(DSLValidationError):
            parse_document(documento(valor))


class TestConversionAAlpha:
    """OOXML expresa el alpha en milésimas de porcentaje: 100000 es opaco."""

    def test_opaco_son_cien_mil(self) -> None:
        from pptx_compiler.render.shapes import alpha_value

        assert alpha_value(1.0) == 100000

    def test_la_mitad_son_cincuenta_mil(self) -> None:
        from pptx_compiler.render.shapes import alpha_value

        assert alpha_value(0.5) == 50000

    def test_transparente_es_cero(self) -> None:
        from pptx_compiler.render.shapes import alpha_value

        assert alpha_value(0.0) == 0
