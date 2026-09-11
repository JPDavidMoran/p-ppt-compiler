"""Interfaz de línea de comandos."""

from __future__ import annotations

from pathlib import Path

import typer

from pptx_compiler.cli.inspect import describe
from pptx_compiler.compiler.expander import expand
from pptx_compiler.dsl.loader import load_document
from pptx_compiler.errors import PresentationCompilerError
from pptx_compiler.compiler.pipeline import compile_file

app = typer.Typer(help="Compilador de un DSL de presentaciones a PPTX.")


@app.command()
def compile(
    source: Path = typer.Argument(..., exists=True, help="Documento DSL en JSON"),
    output: Path = typer.Option(Path("out.pptx"), "-o", "--output"),
) -> None:
    """Compila un DSL a .pptx."""
    try:
        result = compile_file(source, output)
    except PresentationCompilerError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    typer.secho(f"Generado {result}", fg=typer.colors.GREEN)


@app.command()
def validate(
    source: Path = typer.Argument(..., exists=True, help="Documento DSL en JSON")
) -> None:
    """Valida un DSL y muestra las escenas que produciría."""
    try:
        scenes = expand(load_document(source))
    except PresentationCompilerError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    typer.secho(f"Válido: {len(scenes)} escenas", fg=typer.colors.GREEN)
    for scene in scenes:
        typer.echo(f"  {scene.id}: {', '.join(sorted(scene.object_ids)) or '(vacía)'}")


@app.command()
def inspect(
    source: Path = typer.Argument(..., exists=True, help="Archivo .pptx")
) -> None:
    """Vuelca transiciones e identificadores de un .pptx."""
    for line in describe(source):
        typer.echo(line)


if __name__ == "__main__":
    app()
