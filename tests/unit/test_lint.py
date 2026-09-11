"""El linter detecta DSL que compila pero narra mal.

Cada regla corresponde a un defecto observado reproduciendo una
presentación real; ver docs/design-rules.md.
"""

from pptx_compiler.compiler.lint import Severity, lint
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene, SceneObject

WIDE = Camera(0, 0, 100, 56.25)
CLOSE = Camera(30, 20, 25, 14.06)


def obj(oid: str, x: float = 10, y: float = 10, w: float = 20, h: float = 15) -> SceneObject:
    return SceneObject(id=oid, type="shape", at=Rect(x, y, w, h))


def text(oid: str, content: str = "Título", x: float = 10, y: float = 9) -> SceneObject:
    return SceneObject(id=oid, type="text", at=Rect(x, y, 70, 8), content=content)


def scene(sid: str, camera: Camera, objects: list[SceneObject]) -> Scene:
    return Scene(id=sid, camera=camera, objects=objects)


def codes(scenes: list[Scene]) -> set[str]:
    return {finding.code for finding in lint(scenes)}


class TestR2ZoomQueNoCierra:
    def test_terminar_en_una_escena_acercada_avisa(self) -> None:
        scenes = [scene("a", WIDE, [obj("caja")]), scene("b", CLOSE, [obj("caja")])]
        assert "R2" in codes(scenes)

    def test_volver_al_plano_general_no_avisa(self) -> None:
        scenes = [
            scene("a", WIDE, [obj("caja")]),
            scene("b", CLOSE, [obj("caja")]),
            scene("c", WIDE, [obj("caja")]),
        ]
        assert "R2" not in codes(scenes)


class TestR3Parpadeo:
    def test_un_objeto_que_sale_y_otro_que_entra_en_la_misma_zona_avisa(self) -> None:
        scenes = [
            scene("a", WIDE, [text("t"), obj("viejo", x=30, y=24)]),
            scene("b", WIDE, [text("t"), obj("nuevo", x=30, y=24)]),
        ]
        assert "R3" in codes(scenes)

    def test_reutilizar_el_id_no_avisa(self) -> None:
        scenes = [
            scene("a", WIDE, [text("t"), obj("estado", x=30, y=24, w=40)]),
            scene("b", WIDE, [text("t"), obj("estado", x=22, y=20, w=56)]),
        ]
        assert "R3" not in codes(scenes)

    def test_objetos_en_zonas_distintas_no_avisan(self) -> None:
        scenes = [
            scene("a", WIDE, [obj("viejo", x=5, y=5)]),
            scene("b", WIDE, [obj("nuevo", x=70, y=40)]),
        ]
        assert "R3" not in codes(scenes)


class TestR4SustitucionEnElSitio:
    def test_dos_titulos_distintos_con_la_misma_geometria_avisan(self) -> None:
        scenes = [
            scene("a", WIDE, [text("tituloUno", "Impacto"), obj("x", x=40, y=30)]),
            scene("b", WIDE, [text("tituloDos", "Cobertura"), obj("y", x=40, y=30)]),
        ]
        assert "R4" in codes(scenes)

    def test_el_mismo_titulo_no_avisa(self) -> None:
        scenes = [
            scene("a", WIDE, [text("titulo", "Impacto")]),
            scene("b", WIDE, [text("titulo", "Impacto")]),
        ]
        assert "R4" not in codes(scenes)


class TestR5Arrastre:
    def test_un_objeto_aislado_del_tema_anterior_avisa(self) -> None:
        """despues sobrevive a un cambio de tema donde todo lo demás cambió."""
        scenes = [
            scene("a", WIDE, [text("tituloA"), obj("despues", x=30, y=24)]),
            scene("b", WIDE, [text("tituloB"), obj("despues", x=30, y=24), obj("nuevo", x=60, y=24)]),
        ]
        assert "R5" in codes(scenes)

    def test_una_escena_limpia_no_avisa(self) -> None:
        scenes = [
            scene("a", WIDE, [text("tituloA"), obj("viejo")]),
            scene("b", WIDE, [text("tituloB"), obj("nuevo")]),
        ]
        assert "R5" not in codes(scenes)


class TestR6Alineacion:
    def test_un_texto_ancho_sin_alineacion_avisa(self) -> None:
        ancho = SceneObject(id="titulo", type="text", at=Rect(12, 9, 76, 8), content="Título")
        assert "R6" in codes([scene("a", WIDE, [ancho])])

    def test_un_texto_centrado_no_avisa(self) -> None:
        from pptx_compiler.ir.scene import ObjectStyle

        centrado = SceneObject(
            id="titulo",
            type="text",
            at=Rect(12, 9, 76, 8),
            content="Título",
            style=ObjectStyle(align="center"),
        )
        assert "R6" not in codes([scene("a", WIDE, [centrado])])

    def test_un_texto_estrecho_no_avisa(self) -> None:
        estrecho = SceneObject(id="nota", type="text", at=Rect(10, 40, 20, 4), content="nota")
        assert "R6" not in codes([scene("a", WIDE, [estrecho])])


class TestSeveridad:
    def test_los_hallazgos_llevan_severidad_y_escena(self) -> None:
        scenes = [scene("a", WIDE, [obj("caja")]), scene("acercada", CLOSE, [obj("caja")])]
        hallazgos = lint(scenes)
        assert hallazgos
        assert all(h.severity in Severity for h in hallazgos)
        assert all(h.scene_id for h in hallazgos)

    def test_un_dsl_correcto_no_produce_hallazgos(self) -> None:
        from pptx_compiler.ir.scene import ObjectStyle

        titulo = SceneObject(
            id="titulo",
            type="text",
            at=Rect(12, 9, 76, 8),
            content="Tres módulos",
            style=ObjectStyle(align="center"),
        )
        scenes = [
            scene("base", WIDE, [titulo, obj("a", x=12, y=24), obj("b", x=40, y=24)]),
            scene("zoom", CLOSE, [titulo, obj("a", x=12, y=24), obj("b", x=40, y=24)]),
            scene("vuelta", WIDE, [titulo, obj("a", x=12, y=24), obj("b", x=40, y=24)]),
        ]
        assert lint(scenes) == []
