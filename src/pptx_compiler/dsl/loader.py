"""Carga y valida un documento DSL desde JSON."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from pptx_compiler.dsl.schema import Document
from pptx_compiler.errors import DSLValidationError


def load_document(path: Path) -> Document:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DSLValidationError(f"{path}: JSON inválido en la línea {exc.lineno}: {exc.msg}") from exc

    return parse_document(raw, origin=str(path))


def parse_document(raw: dict, origin: str = "<memoria>") -> Document:
    try:
        return Document.model_validate(raw)
    except ValidationError as exc:
        raise DSLValidationError(f"{origin}: {_format(exc)}") from exc


def _format(exc: ValidationError) -> str:
    lines = []
    for error in exc.errors():
        location = " -> ".join(str(part) for part in error["loc"]) or "(raíz)"
        lines.append(f"  {location}: {error['msg']}")
    return "el documento no cumple el schema:\n" + "\n".join(lines)
