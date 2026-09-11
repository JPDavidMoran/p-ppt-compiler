"""Vuelca transiciones e identificadores de un .pptx existente.

Es la herramienta con la que se disecciona el golden file y se depura un
Morph que no funciona.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree

P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
P159 = "{http://schemas.microsoft.com/office/powerpoint/2015/09/main}"


def describe(path: Path) -> list[str]:
    lines: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            (n for n in archive.namelist() if n.startswith("ppt/slides/slide")),
            key=_slide_number,
        )
        for name in names:
            root = etree.fromstring(archive.read(name))
            lines.append(f"{name}")
            lines.append(f"  transición: {_transition(root)}")
            for shape_id, shape_name in _shapes(root):
                lines.append(f"  shape id={shape_id} name={shape_name}")
    return lines


def _slide_number(name: str) -> int:
    digits = "".join(c for c in Path(name).stem if c.isdigit())
    return int(digits or 0)


def _transition(root) -> str:
    if list(root.iter(P159 + "morph")):
        option = next(root.iter(P159 + "morph")).get("option", "?")
        return f"morph (option={option})"
    node = root.find(P + "transition")
    if node is not None:
        kinds = [c.tag.split("}")[-1] for c in node]
        return kinds[0] if kinds else "desconocida"
    return "ninguna"


def _shapes(root) -> list[tuple[str, str]]:
    return [
        (c.get("id", "?"), c.get("name", ""))
        for c in root.iter(P + "cNvPr")
        if c.get("name")
    ]
