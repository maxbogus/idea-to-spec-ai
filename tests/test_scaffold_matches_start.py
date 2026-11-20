"""Контракт: `make scaffold` разворачивает ровно то, что обещает prompts/start.md."""

from __future__ import annotations

import re
import shutil
import subprocess

from idea_to_spec.paths import REPO_ROOT

#: Имя файла артефакта в блоке структуры start.md.
FILE_RE = re.compile(r"([\w-]+\.(?:md|mmd|bpmn))$")
#: Блок кода под «## Шаг 2. Каркас в output/».
STEP2_RE = re.compile(r"## Шаг 2\..*?```(.*?)```", re.DOTALL)


def _declared_files() -> set[str]:
    """Имена файлов, объявленных в структуре `output/<run-id>/` из start.md.

    Returns:
        Множество basename'ов (например, `brief.md`, `use-case.mmd`).
    """
    start = (REPO_ROOT / "prompts" / "start.md").read_text(encoding="utf-8")
    match = STEP2_RE.search(start)
    assert match is not None, "не найден блок структуры в prompts/start.md"
    declared: set[str] = set()
    for line in match.group(1).splitlines():
        found = FILE_RE.search(line.strip())
        if found is not None:
            declared.add(found.group(1))
    return declared


def test_scaffold_matches_start_declaration() -> None:
    """Scaffold создаёт ровно файлы, объявленные в структуре start.md."""
    declared = _declared_files()
    assert declared, "структура start.md пуста"

    run_id = "pytest-scaffold-contract"
    out = REPO_ROOT / "output" / run_id
    try:
        subprocess.run(
            ["bash", "scripts/scaffold-run.sh", run_id],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
        produced = {path.name for path in out.rglob("*") if path.is_file()}
    finally:
        shutil.rmtree(out, ignore_errors=True)

    assert produced == declared, (
        "scaffold ≠ start.md. "
        f"Лишние: {sorted(produced - declared)}; "
        f"недостающие: {sorted(declared - produced)}"
    )
