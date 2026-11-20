"""Детерминированный mock-провайдер для promptfoo (режим eval-mock).

Скрипт вызывается promptfoo как `exec:`-провайдер:

    exec:python3 ../scripts/mock_provider.py

promptfoo передаёт три аргумента:
    1. prompt  — отрендеренный текст запроса;
    2. options — JSON с конфигурацией провайдера;
    3. context — JSON с переменными тест-кейса (vars, metadata).

Скрипт определяет кейс по `context.vars.id` и печатает заранее зафиксированный
«идеальный» ответ, проходящий контракт кейса. Никаких сетевых вызовов и никакой
зависимости от модели — поэтому прогон воспроизводим и используется в CI.

Контракт ответа выведен из форматов ролей (`prompts/roles/*.md`,
`prompts/orchestrator.md`) и общего правила факт/гипотеза/прогноз
(`methods/fact-hypothesis-forecast.md`).
"""

from __future__ import annotations

import json
import sys
from typing import Any


def _load_context(raw: str) -> dict[str, Any]:
    """Разобрать JSON-аргумент context.

    Args:
        raw: Строка с JSON.

    Returns:
        Словарь (пустой, если разбор не удался).
    """
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _vars(context: dict[str, Any]) -> dict[str, Any]:
    """Извлечь переменные тест-кейса.

    Args:
        context: Разобранный context.

    Returns:
        Словарь переменных (пустой, если их нет).
    """
    vars_block = context.get("vars")
    if isinstance(vars_block, dict):
        return vars_block
    return {}


def _contract(vars_block: dict[str, Any]) -> dict[str, Any]:
    """Извлечь контракт кейса из переменной `contract`.

    Args:
        vars_block: Переменные тест-кейса.

    Returns:
        Словарь контракта (пустой, если контракт не передан).
    """
    raw = vars_block.get("contract")
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json(payload: dict[str, Any]) -> str:
    """Сериализовать ответ в JSON.

    Args:
        payload: Поля ответа роли.

    Returns:
        JSON-строка в UTF-8.
    """
    return json.dumps(payload, ensure_ascii=False)


def _orchestrator(
    mode: str,
    stage: str,
    next_stage: str,
    questions: list[str],
    artifacts: list[str],
    assumptions: list[str],
) -> str:
    """Собрать ответ оркестратора в формате из `prompts/orchestrator.md`.

    Args:
        mode: Режим прогона.
        stage: Текущий этап.
        next_stage: Следующий этап.
        questions: Вопросы (пустой список в режиме auto).
        artifacts: Пути созданных артефактов.
        assumptions: Явные допущения.

    Returns:
        JSON-строка ответа.
    """
    return _json(
        {
            "mode": mode,
            "stage": stage,
            "completeness": {"passed": not questions, "missing": [] if not questions else ["данные"]},
            "questions": questions,
            "artifacts": artifacts,
            "assumptions": assumptions,
            "next": next_stage,
        }
    )


def _orchestrator_auto() -> str:
    """Идеальный ответ оркестратора в режиме auto."""
    return _orchestrator(
        mode="auto",
        stage="intake",
        next_stage="business",
        questions=[],
        artifacts=["output/auto-001/brief.md", "output/auto-001/open-questions.md"],
        assumptions=["контур не указан — допущение", "платежи не указаны — нет данных"],
    )


def _orchestrator_chat() -> str:
    """Идеальный ответ оркестратора в режиме chat (три блока вопроса)."""
    question = (
        "Вопрос: какие платежи поддерживаем — карта, СБП, наличные? "
        "Зачем я это спрашиваю: от этого зависят интеграции, комиссия и "
        "юридические требования. "
        "Термины: эквайринг — приём платежей по карте; СБП — система быстрых платежей."
    )
    return _orchestrator(
        mode="chat",
        stage="business",
        next_stage="ba_gate",
        questions=[question],
        artifacts=["output/chat-001/brief.md"],
        assumptions=["контур B2C — допущение"],
    )


def _orchestrator_hybrid() -> str:
    """Идеальный ответ оркестратора в режиме hybrid (вопрос про развилку)."""
    question = (
        "Вопрос: какие внешние интеграции нужны — платежи, логистика, склад? "
        "Зачем я это спрашиваю: развилка по интеграциям меняет архитектуру и сроки. "
        "Термины: интеграция — подключение внешней системы по API."
    )
    return _orchestrator(
        mode="hybrid",
        stage="business",
        next_stage="ba_gate",
        questions=[question],
        artifacts=["output/hybrid-001/brief.md"],
        assumptions=["география — Россия — допущение"],
    )


def _pm() -> str:
    """Идеальный ответ Product Manager (метрика + варианты)."""
    return _json(
        {
            "problem_statement": (
                "Пользователю нужно быстро создавать и синхронизировать заметки "
                "между устройствами; текущий способ теряет мысли."
            ),
            "success_metric": {
                "name": "Доля активных пользователей (WAU/MAU)",
                "target": "+5 п.п. к базе",
                "baseline": "текущая база — требует проверки (допущение)",
            },
            "constraints": ["бюджет не указан — допущение", "сроки не указаны — допущение"],
            "risk_appetite": "medium",
            "out_of_scope": ["офлайн-редактирование", "совместная работа"],
            "assumptions": [
                "база метрики не указана — допущение",
                "бюджет и сроки не указаны — допущение",
            ],
            "open_questions": ["какой контур: B2C или B2B?", "какая модель монетизации?"],
            "variants": [
                {
                    "name": "Оставить как есть",
                    "objections": [
                        "Возражение: не решает запрос роста активных пользователей",
                        "Возражение: не проверяет реальный спрос",
                    ],
                },
                {
                    "name": "Закрыть направление",
                    "objections": [
                        "Возражение: спрос не проверен, отказ может быть преждевременным",
                        "Возражение: аудитория может быть большой",
                    ],
                },
                {
                    "name": "Основной — приложение заметок",
                    "objections": [
                        "Возражение: конкуренция высокая, дифференциация не показана",
                        "Возражение: модель монетизации не определена",
                    ],
                },
            ],
        }
    )


def _ba(assumptions: list[str] | None = None) -> str:
    """Идеальный ответ Business Analyst (персоны, JTBD, BR, AC).

    Args:
        assumptions: Явные допущения; по умолчанию — контур и аудитория.

    Returns:
        JSON-строка ответа.
    """
    return _json(
        {
            "personas": [{"id": "P-1", "name": "Студент", "contour": "B2C"}],
            "contour": "B2C",
            "jobs_to_be_done": [
                {
                    "id": "J-1",
                    "persona": "P-1",
                    "when": "на паре или в дороге",
                    "want": "быстро записать мысль",
                    "so_that": "не потерять идею",
                }
            ],
            "as_is": "заметки в мессенджере (допущение)",
            "to_be": "приложение с синхронизацией между устройствами",
            "business_requirements": [
                {
                    "id": "BR-1",
                    "text": (
                        "Пользователь создаёт заметку за ≤ 30 секунд. Потребность — "
                        "не терять мысли; блокчейн — гипотеза о решении (допущение)."
                    ),
                    "source": "допущение",
                }
            ],
            "acceptance_criteria": [{"id": "AC-1", "text": "Заметка создаётся за ≤ 30 секунд"}],
            "assumptions": assumptions
            or ["контур B2C — допущение", "целевая аудитория — студенты — допущение"],
            "open_questions": ["какая модель монетизации?"],
        }
    )


def _sa() -> str:
    """Идеальный ответ System Analyst (use cases, FR/NFR, интеграции)."""
    return _json(
        {
            "use_cases": [
                {
                    "id": "UC-1",
                    "actor": "P-1",
                    "goal": "создать заметку",
                    "steps": ["открыть приложение", "ввести текст", "сохранить"],
                }
            ],
            "functional_requirements": [
                {
                    "id": "FR-1",
                    "text": "Система сохраняет заметку за ≤ 30 секунд",
                    "source": "BR-1",
                }
            ],
            "nonfunctional_requirements": [
                {
                    "id": "NFR-1",
                    "category": "производительность",
                    "text": "Синхронизация между устройствами ≤ 2 секунд",
                }
            ],
            "integrations": ["сервис синхронизации"],
            "data": ["текст заметок — персональные данные; срок хранения — до удаления"],
            "spec": "черновик спецификации: цели, UC-1, FR-1, NFR-1",
            "open_questions": ["какой контур: B2C или B2B?"],
        }
    )


def _architect() -> str:
    """Идеальный ответ Architect (компоненты, интеграции, ADR, контроли)."""
    return _json(
        {
            "components": [
                {"name": "Notes API", "responsibility": "создание и чтение заметок"},
                {"name": "Sync Service", "responsibility": "синхронизация между устройствами"},
            ],
            "integrations": [
                {"from": "Notes API", "to": "Sync Service", "contract": "REST/JSON"},
            ],
            "adr": [
                {
                    "id": "ADR-1",
                    "decision": "синхронизация через очередь событий",
                    "context": "нужна доставка ≤ 2 с при офлайн-устройствах",
                    "consequences": "возникает eventual consistency",
                }
            ],
            "observability": ["лог запросов API", "метрика sync_latency"],
            "risk_controls": [
                {"risk": "R-1", "control": "ретраи, таймауты и идемпотентность"},
            ],
            "open_questions": ["какой контур: B2C или B2B?"],
        }
    )


def _designer() -> str:
    """Идеальный ответ Designer (поток, экраны, трения, доступность)."""
    return _json(
        {
            "user_flows": [
                {
                    "actor": "P-1",
                    "steps": ["открыть приложение", "создать заметку", "сохранить"],
                }
            ],
            "screens": [
                {
                    "name": "Список заметок",
                    "purpose": "просмотр и создание заметок",
                    "elements": ["кнопка создать", "список заметок"],
                }
            ],
            "friction_points": ["долгий ввод текста на телефоне"],
            "accessibility": ["контраст текста", "размер шрифта"],
            "localization": ["русский язык", "формат даты"],
        }
    )


def _project_manager() -> str:
    """Идеальный ответ Project Manager (задачи, риски, roadmap)."""
    return _json(
        {
            "tasks": [
                {"id": "T-1", "title": "API заметок", "estimate": "3 дня", "depends_on": []},
            ],
            "risks": [
                {
                    "id": "R-1",
                    "description": "задержка синхронизации",
                    "likelihood": "medium",
                    "impact": "high",
                    "owner": "tech lead",
                }
            ],
            "roadmap": ["MVP: создание и синхронизация", "beta: офлайн"],
            "review_points": ["после MVP", "после beta"],
            "open_questions": ["какая модель монетизации?"],
        }
    )


def _fact_check() -> str:
    """Идеальный ответ fact-check (три статуса + причины отклонения)."""
    return _json(
        {
            "findings": [
                {
                    "claim": "Комиссия 299 ₽",
                    "status": "подтверждено",
                    "source": "tariff@2024-01-01",
                    "reason": "",
                },
                {
                    "claim": "Клиенты любят приложение",
                    "status": "допущение",
                    "reason": "нет источника, требует проверки",
                },
                {
                    "claim": "Срок хранения 5 лет",
                    "status": "нет данных",
                    "reason": "нет данных в брифе",
                },
            ]
        }
    )


def build_answer(merged: dict[str, Any]) -> str:
    """Собрать эталонный ответ для кейса.

    Args:
        merged: Объединённые переменные кейса (контракт поверх vars).

    Returns:
        Текст ответа роли.
    """
    case_id = str(merged.get("id", ""))

    if case_id.startswith("ORCH-01"):
        return _orchestrator_auto()
    if case_id.startswith("ORCH-02"):
        return _orchestrator_chat()
    if case_id.startswith("ORCH-03"):
        return _orchestrator_hybrid()
    if case_id.startswith("NEG-01"):
        return "Пришлите, пожалуйста, одну строку с идеей — и я начну прогон."
    if case_id.startswith("NEG-02"):
        return _orchestrator_auto()
    if case_id.startswith("PM-"):
        return _pm()
    if case_id.startswith("BA-02"):
        return _ba(
            [
                "10 млн пользователей и выручка 5 млрд — требует проверки "
                "(допущение), а не факт",
            ]
        )
    if case_id.startswith("BA-"):
        return _ba()
    if case_id.startswith("DISC-"):
        return _ba()
    if case_id.startswith("SA-"):
        return _sa()
    if case_id.startswith("ARCH-"):
        return _architect()
    if case_id.startswith("DESIGN-"):
        return _designer()
    if case_id.startswith("PROJ-"):
        return _project_manager()
    if case_id.startswith("FC-"):
        return _fact_check()

    return f"не удалось определить кейс: {case_id or '<пусто>'}"


def main() -> int:
    """Точка входа exec-провайдера.

    Returns:
        Всегда 0 — ответ печатается в stdout.
    """
    context_raw = sys.argv[3] if len(sys.argv) > 3 else "{}"
    context = _load_context(context_raw)
    vars_block = _vars(context)
    contract = _contract(vars_block)
    merged = {**vars_block, **contract}
    print(build_answer(merged))
    return 0


if __name__ == "__main__":
    sys.exit(main())
