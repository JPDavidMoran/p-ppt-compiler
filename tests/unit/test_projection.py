"""La proyección cámara -> slide es el corazón geométrico del compilador."""

import pytest

from pptx_compiler.errors import ProjectionError
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.render.projection import EMU_PER_INCH, SLIDE_H_EMU, SLIDE_W_EMU, project


def full_camera() -> Camera:
    return Camera(x=0, y=0, w=100, h=56.25)


class TestCameraCompleta:
    def test_objeto_que_llena_el_mundo_llena_la_slide(self) -> None:
        rect = Rect(x=0, y=0, w=100, h=56.25)
        out = project(rect, full_camera())
        assert out.x == 0
        assert out.y == 0
        assert out.w == SLIDE_W_EMU
        assert out.h == SLIDE_H_EMU

    def test_objeto_centrado_queda_centrado(self) -> None:
        rect = Rect(x=25, y=14.0625, w=50, h=28.125)
        out = project(rect, full_camera())
        assert out.x == pytest.approx(SLIDE_W_EMU / 4, rel=1e-6)
        assert out.w == pytest.approx(SLIDE_W_EMU / 2, rel=1e-6)

    def test_la_slide_mide_13_33_por_7_5_pulgadas(self) -> None:
        assert SLIDE_W_EMU == pytest.approx(13.333 * EMU_PER_INCH, rel=1e-3)
        assert SLIDE_H_EMU == 7.5 * EMU_PER_INCH


class TestZoom:
    def test_camara_a_la_mitad_duplica_el_tamano_proyectado(self) -> None:
        rect = Rect(x=25, y=14.0625, w=10, h=5)
        ancha = project(rect, full_camera())
        cerca = project(rect, Camera(x=25, y=14.0625, w=50, h=28.125))
        assert cerca.w == pytest.approx(ancha.w * 2, rel=1e-6)
        assert cerca.h == pytest.approx(ancha.h * 2, rel=1e-6)

    def test_objeto_en_la_esquina_de_la_camara_queda_en_el_origen(self) -> None:
        rect = Rect(x=30, y=10, w=5, h=5)
        out = project(rect, Camera(x=30, y=10, w=50, h=28.125))
        assert out.x == 0
        assert out.y == 0


class TestFueraDeEncuadre:
    """Un objeto fuera de cámara se emite con coordenadas fuera del área.

    No se recorta ni se descarta: es el mecanismo por el que un objeto
    entra desde fuera del marco, y descartarlo rompería su identidad.
    """

    def test_objeto_a_la_izquierda_da_x_negativa(self) -> None:
        rect = Rect(x=-20, y=10, w=5, h=5)
        out = project(rect, full_camera())
        assert out.x < 0

    def test_objeto_a_la_derecha_excede_el_ancho(self) -> None:
        rect = Rect(x=200, y=10, w=5, h=5)
        out = project(rect, full_camera())
        assert out.x > SLIDE_W_EMU


class TestCamaraDegenerada:
    def test_ancho_cero_falla(self) -> None:
        with pytest.raises(ProjectionError):
            Camera(x=0, y=0, w=0, h=10)

    def test_alto_negativo_falla(self) -> None:
        with pytest.raises(ProjectionError):
            Camera(x=0, y=0, w=10, h=-5)


class TestEncuadreSobreObjeto:
    def test_framing_centra_la_camara_en_el_objeto(self) -> None:
        rect = Rect(x=40, y=20, w=20, h=10)
        cam = Camera.framing(rect, scale=2.0, aspect=16 / 9)
        assert cam.center_x == pytest.approx(50.0)
        assert cam.center_y == pytest.approx(25.0)

    def test_mayor_escala_da_camara_mas_pequena(self) -> None:
        rect = Rect(x=40, y=20, w=20, h=10)
        lejos = Camera.framing(rect, scale=1.0, aspect=16 / 9)
        cerca = Camera.framing(rect, scale=3.0, aspect=16 / 9)
        assert cerca.w < lejos.w

    def test_la_camara_conserva_la_proporcion(self) -> None:
        rect = Rect(x=40, y=20, w=20, h=10)
        cam = Camera.framing(rect, scale=2.0, aspect=16 / 9)
        assert cam.w / cam.h == pytest.approx(16 / 9, rel=1e-6)
