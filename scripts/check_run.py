"""Проверка внутренней согласованности прогона `output/<run-id>/`.

Читает артефакты прогона и проверяет структурные инварианты, которые не
ловятся рендером диаграмм и eval ролей:

- каждый `FR-*` ссылается на существующий `BR-*`;
- каждый `J-*` ссылается на существующую персону `P-*`;
- каждый `UC-*` трассируется до `J-*` (в своей строке или в `jtbd.md`);
- узлы диаграмм (`P-/J-/UC-/BR-/FR-/NFR-/R-`) существуют в артефактах;
- traceability-matrix покрывает все `BR-*` и `FR-*`.

Запуск: `python3 scripts/check_run.py output/auto-002` или
`make check-run RUN=auto-002`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

#: Регулярки идентификаторов семейств артефактов.
ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "P": re.compile(r"\bP-\d+\b"),
    "J": re.compile(r"\bJ-\d+\b"),
    "UC": re.compile(r"\bUC-\d+\b"),
    "BR": re.compile(r"\bBR-\d+\b"),
    "FR": re.compile(r"\bFR-\d+\b"),
    "NFR": re.compile(r"\bNFR-\d+\b"),
    "R": re.compile(r"\bR-\d+\b"),
}

#: Файл-источник определений для каждого семейства.
ARTIFACT_FILES: dict[str, str] = {
    "P": "personas.md",
    "J": "jtbd.md",
    "UC": "use-cases.md",
    "BR": "business-requirements.md",
    "FR": "functional-requirements.md",
    "NFR": "nonfunctional-requirements.md",
    "R": "risk-register.md",
}

#: Семейства, которые могут встречаться в диаграммах-источниках.
DIAGRAM_FAMILIES: tuple[str, ...] = ("P", "J", "UC", "BR", "FR", "NFR", "R")


def _read(path: Path) -> str:
    """Прочитать файл в UTF-8 (пустая строка, если файла нет).

    Args:
        path: Путь к файлу.

    Returns:
        Содержимое файла или пустая строка.
    """
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _defined(text: str, family: str) -> set[str]:
    """Собрать все ID семейства, встречающиеся в тексте.

    Args:
        text: Текст артефакта.
        family: Семейство идентификаторов (P, J, UC, BR, ...).

    Returns:
        Множество найденных ID.
    """
    return set(ID_PATTERNS[family].findall(text))


def _rows(text: str) -> list[list[str]]:
    """Разобрать markdown-таблицы в список строк ячеек.

    Args:
        text: Текст артефакта.

    Returns:
        Список строк таблиц; каждая строка — список ячеек.
    """
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def _check_fr_sources(text: str, br_defined: set[str], problems: list[str]) -> None:
    """Каждый FR-* ссылается на существующий BR-*."""
    for cells in _rows(text):
        if not cells:
            continue
        match = re.match(r"FR-\d+", cells[0])
        if match is None:
            continue
        fr = match.group(0)
        refs = ID_PATTERNS["BR"].findall(" | ".join(cells))
        if not refs:
            problems.append(f"{fr}: нет источника BR-* в functional-requirements.md")
            continue
        for ref in refs:
            if ref not in br_defined:
                problems.append(f"{fr}: источник {ref} не определён в business-requirements.md")


def _check_j_persons(text: str, p_defined: set[str], problems: list[str]) -> None:
    """Каждый J-* ссылается на существующую персону P-*."""
    for cells in _rows(text):
        if not cells:
            continue
        match = re.match(r"J-\d+", cells[0])
        if match is None:
            continue
        j = match.group(0)
        refs = ID_PATTERNS["P"].findall(" | ".join(cells))
        if not refs:
            problems.append(f"{j}: нет ссылки на персону P-* в jtbd.md")
            continue
        for ref in refs:
            if ref not in p_defined:
                problems.append(f"{j}: персона {ref} не определена в personas.md")


def _check_uc_trace(uc_text: str, jtbd_text: str, j_defined: set[str], problems: list[str]) -> None:
    """Каждый UC-* трассируется до J-* (в строке UC или в jtbd.md)."""
    for cells in _rows(uc_text):
        if not cells:
            continue
        match = re.match(r"UC-\d+", cells[0])
        if match is None:
            continue
        uc = match.group(0)
        refs = ID_PATTERNS["J"].findall(" | ".join(cells))
        if not refs:
            if uc not in jtbd_text:
                problems.append(f"{uc}: не трассируется до J-* (ни в use-cases.md, ни в jtbd.md)")
            continue
        for ref in refs:
            if ref not in j_defined:
                problems.append(f"{uc}: трассируется в {ref}, которого нет в jtbd.md")


def _check_diagrams(diagrams: Path, defined: dict[str, set[str]], problems: list[str]) -> None:
    """Узлы диаграмм ссылаются только на определённые ID."""
    if not diagrams.is_dir():
        return
    for path in sorted(diagrams.glob("*.mmd")):
        text = path.read_text(encoding="utf-8")
        for family in DIAGRAM_FAMILIES:
            for ref in ID_PATTERNS[family].findall(text):
                if ref not in defined[family]:
                    problems.append(f"{path.name}: узел {ref} не найден в {ARTIFACT_FILES[family]}")


def _check_traceability(trac_text: str, defined: dict[str, set[str]], problems: list[str]) -> None:
    """Traceability-matrix покрывает все BR-* и FR-*."""
    if not trac_text.strip():
        problems.append("traceability-matrix.md отсутствует или пуст")
        return
    for family in ("BR", "FR"):
        for ref in sorted(defined[family]):
            if ref not in trac_text:
                problems.append(f"{ref}: не покрыт в traceability-matrix.md")


def check_run(run_dir: Path) -> list[str]:
    """Проверить согласованность прогона.

    Args:
        run_dir: Каталог прогона (`output/<run-id>`).

    Returns:
        Список проблем; пустой список означает, что прогон согласован.
    """
    if not run_dir.is_dir():
        return [f"нет каталога прогона: {run_dir}"]

    defined: dict[str, set[str]] = {}
    for family, filename in ARTIFACT_FILES.items():
        defined[family] = _defined(_read(run_dir / filename), family)

    problems: list[str] = []
    _check_fr_sources(_read(run_dir / "functional-requirements.md"), defined["BR"], problems)
    _check_j_persons(_read(run_dir / "jtbd.md"), defined["P"], problems)
    _check_uc_trace(
        _read(run_dir / "use-cases.md"),
        _read(run_dir / "jtbd.md"),
        defined["J"],
        problems,
    )
    _check_diagrams(run_dir / "diagrams", defined, problems)
    _check_traceability(_read(run_dir / "traceability-matrix.md"), defined, problems)
    return problems


def main(argv: list[str]) -> int:
    """Точка входа CLI.

    Args:
        argv: Аргументы командной строки (путь к прогону).

    Returns:
        0 — проблем нет; 1 — найдены проблемы; 2 — неверные аргументы.
    """
    if len(argv) < 2:
        print("Использование: check_run.py <output/run-id>")
        return 2
    run_dir = Path(argv[1])
    problems = check_run(run_dir)
    if not problems:
        print(f"check-run: OK ({run_dir})")
        return 0
    print(f"check-run: FAILED ({run_dir}) — {len(problems)} проблем:")
    for problem in problems:
        print(f"  - {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
