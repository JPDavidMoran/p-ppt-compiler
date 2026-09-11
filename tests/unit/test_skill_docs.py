"""La skill del planificador debe seguir describiendo el sistema real.

Una skill que enseña mecanismos inexistentes o campos obsoletos produce
DSL que no compila. Estos tests no revisan la redacción: comprueban que
lo que afirma sigue siendo cierto.
"""

from pathlib import Path

import pytest

from pptx_compiler.dsl.schema import StyleSpec
from pptx_compiler.mechanisms import MECHANISMS

SKILL = Path(".claude/skills/presentation-planner")

pytestmark = pytest.mark.skipif(not SKILL.exists(), reason="skill ausente")


def skill_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in SKILL.rglob("*.md")
    )


class TestMecanismos:
    def test_menciona_todos_los_mecanismos_existentes(self) -> None:
        texto = skill_text()
        for nombre in MECHANISMS:
            assert nombre in texto, f"la skill no documenta {nombre}"

    def test_no_menciona_mecanismos_inexistentes(self) -> None:
        """Inventar un mecanismo produce DSL que falla al compilar."""
        texto = skill_text()
        for inventado in ("ProductReveal", "DataStory", "SplitScreen", "LayerReveal"):
            assert inventado not in texto, f"{inventado} no existe en el compilador"


class TestCampos:
    def test_documenta_los_campos_de_estilo(self) -> None:
        texto = skill_text()
        alias = {"font_size": "fontSize"}
        for campo in StyleSpec.model_fields:
            esperado = alias.get(campo, campo)
            assert esperado in texto, f"la skill no documenta style.{esperado}"

    def test_los_comandos_del_cli_son_los_reales(self) -> None:
        texto = skill_text()
        for comando in ("pptxc lint", "pptxc compile", "pptxc validate"):
            assert comando in texto


class TestReglas:
    def test_remite_a_las_reglas_en_vez_de_duplicarlas(self) -> None:
        """Duplicarlas garantiza que se desincronicen."""
        assert "docs/design-rules.md" in (SKILL / "SKILL.md").read_text(encoding="utf-8")

    def test_el_frontmatter_declara_nombre_y_descripcion(self) -> None:
        cabecera = (SKILL / "SKILL.md").read_text(encoding="utf-8").split("---")[1]
        assert "name: presentation-planner" in cabecera
        assert "description:" in cabecera
