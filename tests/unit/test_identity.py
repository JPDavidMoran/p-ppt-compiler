"""La identidad es el riesgo principal del proyecto.

Si un objeto persistente no recibe el mismo identificador OOXML en todas
las slides, PowerPoint no lo empareja y degrada a un fade genérico sin
emitir ningún error. El fallo es silencioso, y por eso se testea aparte.
"""

import pytest

from pptx_compiler.errors import IdentityConflictError
from pptx_compiler.ir.identity import IdentityRegistry
from pptx_compiler.ir.scene import Scene, SceneObject
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect


def obj(oid: str) -> SceneObject:
    return SceneObject(id=oid, type="shape", at=Rect(0, 0, 10, 10))


class TestEstabilidad:
    def test_el_mismo_id_devuelve_el_mismo_ooxml_id(self) -> None:
        reg = IdentityRegistry()
        primero = reg.ooxml_id_for("dashboard")
        segundo = reg.ooxml_id_for("dashboard")
        assert primero == segundo

    def test_ids_distintos_no_colisionan(self) -> None:
        reg = IdentityRegistry()
        ids = {reg.ooxml_id_for(f"obj{i}") for i in range(50)}
        assert len(ids) == 50

    def test_los_ids_ooxml_empiezan_en_dos(self) -> None:
        """El id 1 lo reserva el grupo raíz de cada slide."""
        reg = IdentityRegistry()
        assert reg.ooxml_id_for("primero") >= 2

    def test_el_creation_id_tambien_es_estable(self) -> None:
        reg = IdentityRegistry()
        assert reg.creation_id_for("dashboard") == reg.creation_id_for("dashboard")

    def test_objetos_distintos_tienen_creation_id_distinto(self) -> None:
        reg = IdentityRegistry()
        assert reg.creation_id_for("a") != reg.creation_id_for("b")


class TestConflictos:
    def test_dos_objetos_con_el_mismo_id_en_una_escena_fallan(self) -> None:
        with pytest.raises(IdentityConflictError) as exc:
            Scene(
                id="intro",
                camera=Camera(0, 0, 100, 56.25),
                objects=[obj("titulo"), obj("titulo")],
            )
        assert "titulo" in str(exc.value)
        assert "intro" in str(exc.value)

    def test_el_mismo_id_en_escenas_distintas_es_valido(self) -> None:
        """Es justamente lo que permite el Morph."""
        cam = Camera(0, 0, 100, 56.25)
        a = Scene(id="uno", camera=cam, objects=[obj("titulo")])
        b = Scene(id="dos", camera=cam, objects=[obj("titulo")])
        assert a.object_ids == b.object_ids


class TestEscenaVacia:
    def test_una_escena_sin_objetos_es_valida(self) -> None:
        escena = Scene(id="negro", camera=Camera(0, 0, 100, 56.25), objects=[])
        assert escena.object_ids == set()
