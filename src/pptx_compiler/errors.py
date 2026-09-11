"""Jerarquía de errores del compilador.

Cada error lleva el contexto necesario para localizar el problema en el
DSL de origen: qué escena, qué objeto, qué mecanismo.
"""


class PresentationCompilerError(Exception):
    """Raíz de todos los errores del compilador."""


class DSLValidationError(PresentationCompilerError):
    """El documento DSL no cumple el schema."""


class UnknownMechanismError(PresentationCompilerError):
    def __init__(self, name: str, available: list[str]) -> None:
        self.name = name
        self.available = available
        super().__init__(
            f"Mecanismo desconocido: {name!r}. "
            f"Disponibles: {', '.join(sorted(available))}"
        )


class IdentityConflictError(PresentationCompilerError):
    def __init__(self, object_id: str, scene_id: str) -> None:
        self.object_id = object_id
        self.scene_id = scene_id
        super().__init__(
            f"Id de objeto duplicado {object_id!r} en la escena {scene_id!r}. "
            "Cada objeto de una escena debe tener un id único."
        )


class MissingTargetError(PresentationCompilerError):
    def __init__(self, target: str, mechanism: str, available: list[str]) -> None:
        self.target = target
        self.mechanism = mechanism
        super().__init__(
            f"El mecanismo {mechanism!r} referencia el objeto {target!r}, "
            f"que no existe en la escena. Objetos disponibles: "
            f"{', '.join(sorted(available)) or '(ninguno)'}"
        )


class ProjectionError(PresentationCompilerError):
    """Cámara degenerada: ancho o alto no positivo."""


class UnknownSceneError(PresentationCompilerError):
    def __init__(self, scene_id: str, available: list[str]) -> None:
        self.scene_id = scene_id
        super().__init__(
            f"La secuencia referencia la escena {scene_id!r}, que no está "
            f"declarada. Escenas disponibles: {', '.join(sorted(available))}"
        )


class EmptySequenceError(PresentationCompilerError):
    """La secuencia no produjo ninguna escena."""
