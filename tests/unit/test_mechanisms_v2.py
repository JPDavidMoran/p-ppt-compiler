"""Los cuatro mecanismos de la segunda tanda.

Cubren dos ejes que los primeros no tocaban: construcción progresiva
(Build, Reveal) y reorganización (Regroup, Spotlight).
"""

import pytest

from pptx_compiler.errors import DSLValidationError, MissingTargetError
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import ObjectStyle, Scene, SceneObject
from pptx_compiler.mechanisms import MECHANISMS, expand_mechanism

WIDE = Camera(0, 0, 100, 56.25)
WORLD = Rect(0, 0, 100, 56.25)


def obj(oid: str, x: float = 10, y: float = 20, w: float = 20, h: float = 15) -> SceneObject:
    return SceneObject(id=oid, type="shape", at=Rect(x, y, w, h))


def base() -> Scene:
    return Scene(
        id="base",
        camera=WIDE,
        objects=[
            SceneObject(id="titulo", type="text", at=Rect(12, 8, 76, 8), content="T"),
            obj("uno", x=12),
            obj("dos", x=40),
            obj("tres", x=68),
        ],
    )


class TestRegistro:
    def test_los_ocho_mecanismos_estan_registrados(self) -> None:
        assert set(MECHANISMS) == {
            "CameraZoom",
            "BeforeAfter",
            "FocusTransition",
            "InfiniteCanvas",
            "Build",
            "Regroup",
            "Spotlight",
            "Reveal",
        }


class TestBuild:
    def test_emite_una_escena_por_elemento(self) -> None:
        escenas = expand_mechanism(
            "Build", {"sequence": ["uno", "dos", "tres"]}, base(), WORLD
        )
        assert len(escenas) == 3

    def test_cada_escena_anade_un_objeto(self) -> None:
        escenas = expand_mechanism(
            "Build", {"sequence": ["uno", "dos", "tres"]}, base(), WORLD
        )
        assert "uno" in escenas[0].object_ids
        assert "dos" not in escenas[0].object_ids
        assert {"uno", "dos"} <= escenas[1].object_ids
        assert {"uno", "dos", "tres"} <= escenas[2].object_ids

    def test_los_objetos_no_listados_permanecen_visibles(self) -> None:
        """El título del contexto no desaparece mientras se construye."""
        escenas = expand_mechanism("Build", {"sequence": ["uno", "dos"]}, base(), WORLD)
        assert all("titulo" in e.object_ids for e in escenas)

    def test_la_camara_no_cambia(self) -> None:
        escenas = expand_mechanism("Build", {"sequence": ["uno", "dos"]}, base(), WORLD)
        assert all(e.camera == WIDE for e in escenas)

    def test_un_objetivo_inexistente_falla(self) -> None:
        with pytest.raises(MissingTargetError):
            expand_mechanism("Build", {"sequence": ["fantasma"]}, base(), WORLD)

    def test_una_secuencia_vacia_falla(self) -> None:
        with pytest.raises(DSLValidationError):
            expand_mechanism("Build", {"sequence": []}, base(), WORLD)


class TestRegroup:
    def test_emite_una_escena(self) -> None:
        escenas = expand_mechanism(
            "Regroup", {"targets": ["uno", "dos", "tres"], "layout": "grid"}, base(), WORLD
        )
        assert len(escenas) == 1

    def test_conserva_los_ids_para_que_morphee(self) -> None:
        escenas = expand_mechanism(
            "Regroup", {"targets": ["uno", "dos", "tres"], "layout": "grid"}, base(), WORLD
        )
        assert {"uno", "dos", "tres"} <= escenas[0].object_ids

    def test_la_disposicion_en_fila_alinea_verticalmente(self) -> None:
        escenas = expand_mechanism(
            "Regroup", {"targets": ["uno", "dos", "tres"], "layout": "row"}, base(), WORLD
        )
        ys = {escenas[0].get(o).at.y for o in ("uno", "dos", "tres")}
        assert len(ys) == 1

    def test_la_disposicion_en_columna_alinea_horizontalmente(self) -> None:
        escenas = expand_mechanism(
            "Regroup", {"targets": ["uno", "dos", "tres"], "layout": "column"}, base(), WORLD
        )
        xs = {escenas[0].get(o).at.x for o in ("uno", "dos", "tres")}
        assert len(xs) == 1

    def test_la_cuadricula_usa_varias_filas(self) -> None:
        escenas = expand_mechanism(
            "Regroup", {"targets": ["uno", "dos", "tres"], "layout": "grid"}, base(), WORLD
        )
        ys = {escenas[0].get(o).at.y for o in ("uno", "dos", "tres")}
        assert len(ys) > 1

    def test_los_objetos_no_listados_no_se_mueven(self) -> None:
        escenas = expand_mechanism(
            "Regroup", {"targets": ["uno", "dos"], "layout": "row"}, base(), WORLD
        )
        assert escenas[0].get("tres").at == base().get("tres").at

    def test_un_objetivo_inexistente_falla(self) -> None:
        with pytest.raises(MissingTargetError):
            expand_mechanism("Regroup", {"targets": ["fantasma"], "layout": "row"}, base(), WORLD)


class TestSpotlight:
    def test_emite_una_escena(self) -> None:
        escenas = expand_mechanism("Spotlight", {"target": "dos"}, base(), WORLD)
        assert len(escenas) == 1

    def test_el_destacado_queda_opaco(self) -> None:
        escenas = expand_mechanism("Spotlight", {"target": "dos"}, base(), WORLD)
        assert escenas[0].get("dos").style.opacity == 1.0

    def test_los_demas_se_atenuan(self) -> None:
        escenas = expand_mechanism("Spotlight", {"target": "dos", "dim": 0.25}, base(), WORLD)
        assert escenas[0].get("uno").style.opacity == 0.25
        assert escenas[0].get("tres").style.opacity == 0.25

    def test_conserva_todos_los_objetos(self) -> None:
        escenas = expand_mechanism("Spotlight", {"target": "dos"}, base(), WORLD)
        assert escenas[0].object_ids == base().object_ids

    def test_no_mueve_la_camara(self) -> None:
        escenas = expand_mechanism("Spotlight", {"target": "dos"}, base(), WORLD)
        assert escenas[0].camera == WIDE

    def test_se_puede_eximir_objetos_de_la_atenuacion(self) -> None:
        escenas = expand_mechanism(
            "Spotlight", {"target": "dos", "keep": ["titulo"]}, base(), WORLD
        )
        assert escenas[0].get("titulo").style.opacity == 1.0

    def test_un_objetivo_inexistente_falla(self) -> None:
        with pytest.raises(MissingTargetError):
            expand_mechanism("Spotlight", {"target": "fantasma"}, base(), WORLD)


class TestReveal:
    def _scene(self) -> Scene:
        return Scene(
            id="base",
            camera=WIDE,
            objects=[
                SceneObject(id="tapa", type="shape", at=Rect(30, 20, 40, 25)),
                SceneObject(
                    id="secreto",
                    type="shape",
                    at=Rect(30, 20, 40, 25),
                    style=ObjectStyle(fill="2D6A4F"),
                ),
            ],
        )

    def test_emite_dos_escenas(self) -> None:
        escenas = expand_mechanism(
            "Reveal", {"cover": "tapa", "target": "secreto", "direction": "up"},
            self._scene(), WORLD,
        )
        assert len(escenas) == 2

    def test_la_primera_muestra_la_tapa_sobre_el_objetivo(self) -> None:
        escenas = expand_mechanism(
            "Reveal", {"cover": "tapa", "target": "secreto", "direction": "up"},
            self._scene(), WORLD,
        )
        assert {"tapa", "secreto"} <= escenas[0].object_ids

    def test_la_tapa_se_aparta_en_la_segunda(self) -> None:
        escenas = expand_mechanism(
            "Reveal", {"cover": "tapa", "target": "secreto", "direction": "up"},
            self._scene(), WORLD,
        )
        assert escenas[1].get("tapa").at.y < escenas[0].get("tapa").at.y

    def test_la_direccion_determina_hacia_donde_se_aparta(self) -> None:
        params = {"cover": "tapa", "target": "secreto", "direction": "left"}
        escenas = expand_mechanism("Reveal", params, self._scene(), WORLD)
        assert escenas[1].get("tapa").at.x < escenas[0].get("tapa").at.x

    def test_el_objetivo_no_se_mueve(self) -> None:
        escenas = expand_mechanism(
            "Reveal", {"cover": "tapa", "target": "secreto", "direction": "up"},
            self._scene(), WORLD,
        )
        assert escenas[0].get("secreto").at == escenas[1].get("secreto").at

    def test_una_tapa_inexistente_falla(self) -> None:
        with pytest.raises(MissingTargetError):
            expand_mechanism(
                "Reveal", {"cover": "fantasma", "target": "secreto", "direction": "up"},
                self._scene(), WORLD,
            )
