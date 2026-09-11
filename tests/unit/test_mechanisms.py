"""Los mecanismos son macros puras: parámetros -> escenas.

No conocen PowerPoint, no generan XML y no asignan ids OOXML. Por eso se
testean sin generar un solo archivo.
"""

import pytest

from pptx_compiler.errors import (
    DSLValidationError,
    MissingTargetError,
    UnknownMechanismError,
)
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene, SceneObject
from pptx_compiler.mechanisms import MECHANISMS, expand_mechanism

WIDE = Camera(0, 0, 100, 56.25)
WORLD = Rect(0, 0, 100, 56.25)


def obj(oid: str, x: float = 10, y: float = 10, w: float = 10) -> SceneObject:
    return SceneObject(id=oid, type="shape", at=Rect(x, y, w, 10))


def base_scene() -> Scene:
    return Scene(
        id="base",
        camera=WIDE,
        objects=[obj("titulo", x=5), obj("dashboard", x=40), obj("modB", x=70)],
    )


class TestRegistro:
    def test_los_cuatro_mecanismos_estan_registrados(self) -> None:
        assert set(MECHANISMS) == {
            "CameraZoom",
            "BeforeAfter",
            "FocusTransition",
            "InfiniteCanvas",
        }

    def test_un_mecanismo_desconocido_falla_con_las_alternativas(self) -> None:
        with pytest.raises(UnknownMechanismError) as exc:
            expand_mechanism("NoExiste", {}, base_scene(), WORLD)
        assert "CameraZoom" in str(exc.value)


class TestCameraZoom:
    def test_emite_una_escena(self) -> None:
        escenas = expand_mechanism(
            "CameraZoom", {"target": "dashboard", "scale": 2.5}, base_scene(), WORLD
        )
        assert len(escenas) == 1

    def test_conserva_todos_los_objetos(self) -> None:
        escenas = expand_mechanism(
            "CameraZoom", {"target": "dashboard", "scale": 2.5}, base_scene(), WORLD
        )
        assert escenas[0].object_ids == base_scene().object_ids

    def test_la_camara_se_centra_en_el_objetivo(self) -> None:
        escenas = expand_mechanism(
            "CameraZoom", {"target": "dashboard", "scale": 2.0}, base_scene(), WORLD
        )
        objetivo = base_scene().get("dashboard")
        assert escenas[0].camera.center_x == pytest.approx(objetivo.at.center_x)

    def test_la_camara_se_acerca(self) -> None:
        escenas = expand_mechanism(
            "CameraZoom", {"target": "dashboard", "scale": 2.5}, base_scene(), WORLD
        )
        assert escenas[0].camera.w < WIDE.w

    def test_un_objetivo_inexistente_falla(self) -> None:
        with pytest.raises(MissingTargetError) as exc:
            expand_mechanism(
                "CameraZoom", {"target": "fantasma", "scale": 2.0}, base_scene(), WORLD
            )
        assert "fantasma" in str(exc.value)


class TestBeforeAfter:
    def _expand(self) -> list[Scene]:
        escena = Scene(
            id="base",
            camera=WIDE,
            objects=[obj("titulo"), obj("viejo", x=40), obj("nuevo", x=40)],
        )
        return expand_mechanism(
            "BeforeAfter",
            {"before": ["viejo"], "after": ["nuevo"], "keep": ["titulo"]},
            escena,
            WORLD,
        )

    def test_emite_dos_escenas(self) -> None:
        assert len(self._expand()) == 2

    def test_la_primera_tiene_los_objetos_previos(self) -> None:
        antes = self._expand()[0]
        assert antes.object_ids == {"titulo", "viejo"}

    def test_la_segunda_tiene_los_posteriores(self) -> None:
        despues = self._expand()[1]
        assert despues.object_ids == {"titulo", "nuevo"}

    def test_la_camara_no_cambia(self) -> None:
        antes, despues = self._expand()
        assert antes.camera == despues.camera

    def test_un_objeto_inexistente_falla(self) -> None:
        with pytest.raises(MissingTargetError):
            expand_mechanism(
                "BeforeAfter",
                {"before": ["fantasma"], "after": [], "keep": []},
                base_scene(),
                WORLD,
            )


class TestFocusTransition:
    def test_emite_una_escena_por_elemento(self) -> None:
        escenas = expand_mechanism(
            "FocusTransition",
            {"sequence": ["dashboard", "modB"], "scale": 2.0},
            base_scene(),
            WORLD,
        )
        assert len(escenas) == 2

    def test_cada_escena_encuadra_su_objetivo(self) -> None:
        escenas = expand_mechanism(
            "FocusTransition",
            {"sequence": ["dashboard", "modB"], "scale": 2.0},
            base_scene(),
            WORLD,
        )
        base = base_scene()
        for escena, oid in zip(escenas, ["dashboard", "modB"]):
            assert escena.camera.center_x == pytest.approx(base.get(oid).at.center_x)

    def test_una_secuencia_vacia_falla(self) -> None:
        with pytest.raises(DSLValidationError):
            expand_mechanism(
                "FocusTransition", {"sequence": [], "scale": 2.0}, base_scene(), WORLD
            )


class TestInfiniteCanvas:
    def _params(self) -> dict:
        return {
            "objects": [
                {"id": "zonaA", "type": "shape", "at": {"x": 5, "y": 5, "w": 20, "h": 15}},
                {"id": "zonaB", "type": "shape", "at": {"x": 150, "y": 5, "w": 20, "h": 15}},
            ],
            "tour": [{"at": "zonaA", "scale": 1.5}, {"at": "zonaB", "scale": 1.5}],
        }

    def test_emite_una_escena_por_parada(self) -> None:
        escenas = expand_mechanism("InfiniteCanvas", self._params(), base_scene(), WORLD)
        assert len(escenas) == 2

    def test_los_objetos_declarados_se_anaden_a_la_escena(self) -> None:
        escenas = expand_mechanism("InfiniteCanvas", self._params(), base_scene(), WORLD)
        assert {"zonaA", "zonaB"} <= escenas[0].object_ids

    def test_los_objetos_previos_persisten(self) -> None:
        escenas = expand_mechanism("InfiniteCanvas", self._params(), base_scene(), WORLD)
        assert "titulo" in escenas[0].object_ids

    def test_la_camara_recorre_hasta_zonas_lejanas(self) -> None:
        """El panning lateral: la segunda parada está lejos en el mundo."""
        escenas = expand_mechanism("InfiniteCanvas", self._params(), base_scene(), WORLD)
        assert escenas[1].camera.center_x > escenas[0].camera.center_x + 50

    def test_una_parada_hacia_un_objeto_inexistente_falla(self) -> None:
        params = self._params()
        params["tour"] = [{"at": "fantasma", "scale": 1.5}]
        with pytest.raises(MissingTargetError):
            expand_mechanism("InfiniteCanvas", params, base_scene(), WORLD)
