"""Orquesta la compilación completa: DSL -> escenas -> pptx."""

from __future__ import annotations

from pathlib import Path

from pptx_compiler.compiler.expander import expand
from pptx_compiler.dsl.loader import load_document, parse_document
from pptx_compiler.dsl.schema import Document
from pptx_compiler.render.builder import build


def compile_document(document: Document, output: Path) -> Path:
    scenes = expand(document)
    return build(
        scenes,
        world_w=document.world.w,
        output=output,
        title=document.presentation.title,
        transition_ms=document.presentation.transition_ms,
    )


def compile_file(source: Path, output: Path) -> Path:
    return compile_document(load_document(source), output)


def compile_dict(raw: dict, output: Path) -> Path:
    return compile_document(parse_document(raw), output)
