"""Крос-артефактные проверки согласованности прогонов (`scripts/check_run.py`)."""

from __future__ import annotations

from pathlib import Path

import pytest

from check_run import check_run
from idea_to_spec.paths import OUTPUT_DIR


@pytest.mark.parametrize("run_id", ["auto-001", "auto-002"])
def test_golden_runs_are_consistent(run_id: str) -> None:
    """Готовые демо-прогоны проходят структурную проверку без ошибок."""
    run_dir = OUTPUT_DIR / run_id
    if not run_dir.is_dir():
        pytest.skip(f"нет прогона {run_id}")
    assert check_run(run_dir) == []


def test_checker_detects_missing_br_source(tmp_path: Path) -> None:
    """FR без источника BR-* фиксируется как проблема."""
    run = tmp_path / "run"
    run.mkdir()
    (run / "functional-requirements.md").write_text(
        "| ID | Требование | Источник |\n|---|---|---|\n| FR-1 | x |  |\n",
        encoding="utf-8",
    )
    assert any("FR-1" in problem for problem in check_run(run))


def test_checker_detects_invented_diagram_node(tmp_path: Path) -> None:
    """Узел диаграммы, которого нет в артефактах, фиксируется как проблема."""
    run = tmp_path / "run"
    (run / "diagrams").mkdir(parents=True)
    (run / "personas.md").write_text("| P-1 | x |\n", encoding="utf-8")
    (run / "diagrams" / "use-case.mmd").write_text(
        'usecase-beta\n    actor A("P-9")\n', encoding="utf-8"
    )
    assert any("P-9" in problem for problem in check_run(run))


def test_missing_run_dir_reports_problem(tmp_path: Path) -> None:
    """Несуществующий каталог прогона — проблема, а не тихий успех."""
    assert check_run(tmp_path / "missing")
