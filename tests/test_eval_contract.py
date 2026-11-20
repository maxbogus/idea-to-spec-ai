"""Контрактные проверки eval-набора idea-to-spec-ai.

Разделены на две группы:
1. `mock` — детерминированные проверки контракта, зелёные всегда.
2. `slow` — реальный прогон микро-LLM; провалы фиксируются как
   xfail(strict=True) по конвенции hh-matcher, а не маскируются.

Известные провалы модели перечислены в KNOWN_MODEL_FAILURES. Если модель
начнёт проходить кейс, xfail(strict=True) превратится в XPASS-ошибку — это
сигнал обновить список, а не тихо убрать проверку.

Кейсы вне KNOWN_MODEL_FAILURES обязаны проходить: их провал — настоящая
регрессия контракта промпта, а не свойство слабой модели.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from idea_to_spec.paths import EVAL_CASES_FILE, EVAL_REPORT_FILE

#: Допустимые роли и виды кейсов.
ALLOWED_ROLES = {
    "orchestrator",
    "product-manager",
    "business-analyst",
    "system-analyst",
    "architect",
    "designer",
    "project-manager",
    "fact-check",
}
ALLOWED_KINDS = {"role", "discipline", "negative"}
ALLOWED_MODES = {"auto", "chat", "hybrid"}


def _load_cases() -> list[dict[str, Any]]:
    """Загрузить кейсы eval-набора.

    Returns:
        Список контрактов кейсов (JSON `contract` распакован).
    """
    cases: list[dict[str, Any]] = []
    for line in EVAL_CASES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        cases.append(json.loads(item["vars"]["contract"]))
    return cases


CASES = _load_cases()
CASE_IDS = [str(case["id"]) for case in CASES]

#: Кейсы, которые микро-LLM не проходит. Заполняется после `make eval`.
#:
#: Провал фиксируется, а не скрывается: внезапный XPASS означает, что список
#: надо пересмотреть. Кейс вне списка, который провалился, — регрессия.
KNOWN_MODEL_FAILURES: set[str] = {
    # chat: модель задаёт 4 вопроса вместо ≤ 3 за гейт. Плавающий провал:
    # при temperature=0 число вопросов меняется между прогонами.
    "ORCH-02-chat-three-block-questions",
    # Пустая идея: модель всё равно начинает прогон и пишет артефакты
    # (иногда на другом языке); правило из prompts/orchestrator.md игнорируется.
    "NEG-01-empty-idea",
}

#: Кейсы, не входящие в KNOWN_MODEL_FAILURES: их провал — настоящая регрессия.
KNOWN_MODEL_PASSES: set[str] = set(CASE_IDS) - KNOWN_MODEL_FAILURES


def _contract_problems(case: dict[str, Any], output: str) -> list[str]:
    """Проверить ответ по контракту кейса (must_contain / not_contain / поля).

    Args:
        case: Контракт кейса.
        output: Текст ответа.

    Returns:
        Список проблем (пустой, если контракт выполнен).
    """
    problems: list[str] = []
    lower = output.lower()
    for needle in case.get("must_contain", []):
        # Регистронезависимо: маркеры естественного языка («потребность»)
        # могут стоять в начале предложения с заглавной буквы. ID (BR-1, UC-1)
        # при этом всё равно совпадают.
        if str(needle).lower() not in lower:
            problems.append(f"must_contain отсутствует: {needle!r}")
    for needle in case.get("must_not_contain", []):
        if str(needle).lower() in lower:
            problems.append(f"must_not_contain присутствует: {needle!r}")
    for field in case.get("expected_fields", []):
        if f'"{field}"' not in output and f"{field}:" not in output:
            problems.append(f"нет обязательного поля: {field}")
    # Ответ должен быть на русском: кириллица обязательна (см. JS-проверку).
    cyrillic = sum(1 for ch in output if "а" <= ch.lower() <= "я" or ch.lower() == "ё")
    if cyrillic < 20:
        problems.append("ответ не на русском языке (нет кириллицы)")
    return problems


def _mode_problems(case: dict[str, Any], output: str) -> list[str]:
    """Проверить дисциплину режима по контракту кейса.

    Args:
        case: Контракт кейса.
        output: Текст ответа.

    Returns:
        Список проблем режима (пустой, если режим соблюдён).
    """
    check = case.get("mode_check")
    lower = output.lower()
    if check == "auto_no_questions":
        if "зачем я это спрашиваю" in lower:
            return ["auto: задан вопрос, хотя auto = 0 вопросов"]
        return []
    if check == "chat_three_blocks":
        problems = [
            f"chat: нет блока {block!r}"
            for block in ("вопрос", "зачем я это спрашиваю", "термины")
            if block not in lower
        ]
        if output.count("Вопрос") > 3:
            problems.append("chat: больше 3 вопросов за гейт")
        return problems
    if check == "hybrid_forks_only" and "вопрос" in lower:
        forks = ("контур", "пользовател", "платеж", "интеграц")
        if not any(fork in lower for fork in forks):
            return ["hybrid: вопрос не про критичную развилку"]
    return []


def test_eval_set_has_expected_size() -> None:
    """Набор содержит 20 кейсов: MVP + Architect/Designer/Project Manager/fact-check."""
    assert len(CASES) == 20, f"Ожидалось 20 кейсов, получено {len(CASES)}"
    by_scenario: dict[str, int] = {}
    for case in CASES:
        scenario = str(case["scenario"])
        by_scenario[scenario] = by_scenario.get(scenario, 0) + 1
    assert by_scenario == {
        "ORCH": 3,
        "PM": 2,
        "BA": 2,
        "SA": 2,
        "DISC": 1,
        "NEG": 2,
        "ARCH": 2,
        "DESIGN": 2,
        "PROJ": 2,
        "FC": 2,
    }


def test_case_ids_are_unique() -> None:
    """Идентификаторы кейсов уникальны."""
    assert len(CASE_IDS) == len(set(CASE_IDS))


def test_known_lists_cover_all_cases() -> None:
    """Списки известных провалов и проходов покрывают весь набор без пересечений."""
    assert not (KNOWN_MODEL_FAILURES & KNOWN_MODEL_PASSES), "Кейс попал в оба списка"
    covered = KNOWN_MODEL_FAILURES | KNOWN_MODEL_PASSES
    assert set(CASE_IDS) <= covered, f"Кейсы не покрыты: {sorted(set(CASE_IDS) - covered)}"
    assert covered <= set(CASE_IDS), f"Несуществующие кейсы: {sorted(covered - set(CASE_IDS))}"


def test_case_contract_is_complete() -> None:
    """Каждый кейс содержит полный контракт и допустимые значения."""
    for case in CASES:
        for field in (
            "id",
            "role",
            "scenario",
            "kind",
            "title",
            "mode",
            "input",
            "expected_fields",
            "must_contain",
            "must_not_contain",
            "notes",
        ):
            assert field in case, f"В кейсе {case.get('id')} нет поля {field}"
        assert case["role"] in ALLOWED_ROLES, f"{case['id']}: неизвестная роль {case['role']}"
        assert case["kind"] in ALLOWED_KINDS, f"{case['id']}: неизвестный вид {case['kind']}"
        assert case["mode"] in ALLOWED_MODES, f"{case['id']}: неизвестный режим {case['mode']}"


def test_forbidden_phrases_absent_in_contracts() -> None:
    """Запрещённые формулировки не попадают в must_contain; записи не пустые."""
    forbidden = {"вернём", "верну", "возврат одобрен", "одобрим кредит", "выдадим кредит"}
    for case in CASES:
        for needle in case["must_contain"]:
            assert needle.strip(), f"{case['id']}: пустой must_contain"
            assert needle.lower() not in forbidden, (
                f"{case['id']}: в must_contain нельзя требовать запрещённую формулировку {needle!r}"
            )


@pytest.mark.mock
def test_mock_provider_returns_ideal_answers() -> None:
    """Mock-провайдер возвращает ответ, проходящий контракт каждого кейса."""
    from mock_provider import build_answer

    for case in CASES:
        output = build_answer(dict(case))
        problems = _contract_problems(case, output) + _mode_problems(case, output)
        assert not problems, f"{case['id']}: mock-ответ не выполнил контракт: {problems}"


@pytest.mark.slow
def test_known_failures_match_report() -> None:
    """Список известных провалов соответствует фактическому отчёту.

    Список провалов — не «состояние на дату», а утверждение о том, какие
    кейсы модель заведомо не выполняет. Если отчёт разошёлся со списком —
    это ошибка, которую надо увидеть сразу.
    """
    if not EVAL_REPORT_FILE.exists():
        pytest.skip("Нет отчёта реального прогона — выполните `make eval`")

    from summarize_eval import summarize

    summary = summarize(EVAL_REPORT_FILE)
    failed = set(summary["failed_cases"])
    assert failed == KNOWN_MODEL_FAILURES, (
        "Список известных провалов разошёлся с отчётом. "
        f"Провалы в отчёте, которых нет в списке: {sorted(failed - KNOWN_MODEL_FAILURES)}. "
        f"Кейсы в списке, которые прошли: {sorted(KNOWN_MODEL_FAILURES - failed)}"
    )


@pytest.mark.slow
@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_real_model_meets_contract(case: dict[str, Any]) -> None:
    """Реальный микро-LLM проверяется по контракту кейса.

    Провал микро-LLM — ожидаемое состояние, зафиксированное как
    xfail(strict=True). Случайный XPASS означает, что список
    KNOWN_MODEL_FAILURES надо обновить.
    """
    if not EVAL_REPORT_FILE.exists():
        pytest.skip("Нет отчёта реального прогона — выполните `make eval`")

    payload = json.loads(EVAL_REPORT_FILE.read_text(encoding="utf-8"))
    results = payload.get("results", {}).get("results", [])
    matching = [item for item in results if item.get("vars", {}).get("id") == case["id"]]
    if not matching:
        pytest.skip(f"Кейс {case['id']} отсутствует в отчёте")

    result = matching[0]
    success = bool(result.get("success"))
    components = (result.get("gradingResult") or {}).get("componentResults") or []
    reason = str(components[0].get("reason", "")) if components else ""

    case_id = str(case["id"])
    if case_id in KNOWN_MODEL_FAILURES:
        if success:
            pytest.fail(
                f"XPASS (strict): {case_id} теперь проходит микро-LLM — "
                "обновите KNOWN_MODEL_FAILURES в tests/test_eval_contract.py"
            )
        pytest.xfail(f"Известный провал микро-LLM: {reason}")
    if not success:
        pytest.fail(
            f"РЕГРЕССИЯ: кейс {case_id} вне KNOWN_MODEL_FAILURES, но микро-LLM "
            f"не выполнил контракт: {reason}"
        )
    assert success, f"{case_id}: микро-LLM не выполнил контракт: {reason}"
