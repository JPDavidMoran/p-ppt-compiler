"""El differ decide la transición comparando dos escenas consecutivas.

La comparación es sobre geometría proyectada, no de mundo: un objeto
inmóvil bajo una cámara que se mueve sí cambia en la slide, y debe
morphear.
"""

from dataclasses import replace

from pptx_compiler.compiler.differ import TransitionKind, diff
from pptx_compiler.ir.camera import Camera
from pptx_compiler.ir.geometry import Rect
from pptx_compiler.ir.scene import Scene, SceneObject

WIDE = Camera(0, 0, 100, 56.25)
CLOSE = Camera(25, 14, 50, 28.125)


def obj(oid: str, x: float = 10, y: float = 10) -> SceneObject:
    return SceneObject(id=oid, type="shape", at=Rect(x, y, 10, 10))


def scene(sid: str, camera: Camera, objects: list[SceneObject]) -> Scene:
    return Scene(id=sid, camera=camera, objects=objects)


class TestMorph:
    def test_objeto_que_se_mueve_produce_morph(self) -> None:
        a = scene("a", WIDE, [obj("caja", x=10)])
        b = scene("b", WIDE, [obj("caja", x=60)])
        assert diff(a, b).kind is TransitionKind.MORPH

    def test_camara_que_se_mueve_produce_morph_aunque_nada_se_mueva(self) -> None:
        """El caso central del zoom cinematográfico."""
        a = scene("a", WIDE, [obj("caja")])
        b = scene("b", CLOSE, [obj("caja")])
        assert diff(a, b).kind is TransitionKind.MORPH

    def test_el_morph_lista_los_objetos_persistentes(self) -> None:
        a = scene("a", WIDE, [obj("caja", x=10), obj("otro", x=30)])
        b = scene("b", WIDE, [obj("caja", x=60), obj("otro", x=30)])
        assert diff(a, b).persistent == {"caja", "otro"}


class TestFade:
    def test_solo_entradas_y_salidas_produce_fade(self) -> None:
        a = scene("a", WIDE, [obj("viejo")])
        b = scene("b", WIDE, [obj("nuevo")])
        assert diff(a, b).kind is TransitionKind.FADE

    def test_un_persistente_inmovil_con_entradas_y_salidas_morphea(self) -> None:
        """El objeto que permanece debe quedarse quieto, no parpadear."""
        a = scene("a", WIDE, [obj("titulo"), obj("viejo", x=30)])
        b = scene("b", WIDE, [obj("titulo"), obj("nuevo", x=30)])
        resultado = diff(a, b)
        assert resultado.kind is TransitionKind.MORPH
        assert resultado.entering == {"nuevo"}
        assert resultado.leaving == {"viejo"}


class TestSinCambios:
    def test_escenas_identicas_no_producen_transicion(self) -> None:
        a = scene("a", WIDE, [obj("caja")])
        b = scene("b", WIDE, [obj("caja")])
        assert diff(a, b).kind is TransitionKind.NONE


class TestEscenasVacias:
    def test_de_vacia_a_vacia_no_produce_transicion(self) -> None:
        a = scene("a", WIDE, [])
        b = scene("b", WIDE, [])
        assert diff(a, b).kind is TransitionKind.NONE

    def test_de_vacia_a_con_objetos_produce_fade(self) -> None:
        a = scene("a", WIDE, [])
        b = scene("b", WIDE, [obj("caja")])
        assert diff(a, b).kind is TransitionKind.FADE


class TestRegresoAlPlanoGeneral:
    """Repetir una escena tras un zoom debe morphear de vuelta.

    Es la forma correcta de cerrar un recorrido: CameraZoom siempre
    encuadra su objetivo, así que no sirve para alejarse. Se repite la
    escena original y el differ ve el cambio de cámara.
    """

    def test_repetir_la_escena_tras_un_zoom_produce_morph(self) -> None:
        acercada = scene("zoom", CLOSE, [obj("caja")])
        general = scene("base", WIDE, [obj("caja")])
        assert diff(acercada, general).kind is TransitionKind.MORPH


class TestObjetoQueCambiaDeEstado:
    """Un antes/después con un solo objeto morphea; con dos, parpadea.

    Reutilizar el id hace que PowerPoint interpole entre ambos estados en
    lugar de desvanecer uno y aparecer el otro.
    """

    def test_un_objeto_que_cambia_de_tamano_morphea(self) -> None:
        antes = scene("a", WIDE, [SceneObject(id="estado", type="shape", at=Rect(30, 24, 40, 18))])
        despues = scene("b", WIDE, [SceneObject(id="estado", type="shape", at=Rect(22, 20, 56, 24))])
        assert diff(antes, despues).kind is TransitionKind.MORPH

    def test_dos_objetos_distintos_solo_se_desvanecen(self) -> None:
        antes = scene("a", WIDE, [obj("viejo")])
        despues = scene("b", WIDE, [obj("nuevo")])
        assert diff(antes, despues).kind is TransitionKind.FADE


class TestCambioDeEstilo:
    """Morph interpola color y opacidad, no solo posición.

    Sin esto, Spotlight no producía transición alguna: atenúa el resto de
    objetos sin mover nada, y el differ no veía ningún cambio.
    """

    def _con_opacidad(self, oid: str, opacity: float) -> SceneObject:
        from pptx_compiler.ir.scene import ObjectStyle

        return SceneObject(
            id=oid,
            type="shape",
            at=Rect(10, 10, 20, 15),
            style=ObjectStyle(fill="2D6A4F", opacity=opacity),
        )

    def test_un_cambio_de_opacidad_produce_morph(self) -> None:
        a = scene("a", WIDE, [self._con_opacidad("caja", 1.0)])
        b = scene("b", WIDE, [self._con_opacidad("caja", 0.25)])
        assert diff(a, b).kind is TransitionKind.MORPH

    def test_un_cambio_de_relleno_produce_morph(self) -> None:
        from pptx_compiler.ir.scene import ObjectStyle

        base = SceneObject(id="caja", type="shape", at=Rect(10, 10, 20, 15))
        a = scene("a", WIDE, [replace(base, style=ObjectStyle(fill="2D6A4F"))])
        b = scene("b", WIDE, [replace(base, style=ObjectStyle(fill="B7B7A4"))])
        assert diff(a, b).kind is TransitionKind.MORPH

    def test_un_cambio_de_contenido_produce_morph(self) -> None:
        a = scene("a", WIDE, [SceneObject(id="t", type="text", at=Rect(10, 10, 40, 8), content="Antes")])
        b = scene("b", WIDE, [SceneObject(id="t", type="text", at=Rect(10, 10, 40, 8), content="Después")])
        assert diff(a, b).kind is TransitionKind.MORPH

    def test_sin_cambios_de_estilo_ni_geometria_no_hay_transicion(self) -> None:
        a = scene("a", WIDE, [self._con_opacidad("caja", 0.5)])
        b = scene("b", WIDE, [self._con_opacidad("caja", 0.5)])
        assert diff(a, b).kind is TransitionKind.NONE


class TestConstruccionProgresiva:
    """Si hay objetos que permanecen, entrar uno nuevo debe morphear.

    Un fade atenúa toda la diapositiva, así que los elementos ya visibles
    parpadean cada vez que aparece el siguiente. Con Morph se quedan
    quietos y solo entra el nuevo.
    """

    def test_anadir_un_objeto_manteniendo_otros_produce_morph(self) -> None:
        a = scene("a", WIDE, [obj("uno", x=10)])
        b = scene("b", WIDE, [obj("uno", x=10), obj("dos", x=40)])
        assert diff(a, b).kind is TransitionKind.MORPH

    def test_sin_objetos_persistentes_sigue_siendo_fade(self) -> None:
        """Un cambio de tema completo no debe morphear."""
        a = scene("a", WIDE, [obj("viejo")])
        b = scene("b", WIDE, [obj("nuevo")])
        assert diff(a, b).kind is TransitionKind.FADE
