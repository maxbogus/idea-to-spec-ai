# Run Report — <run-id>

> Итоговый отчёт оркестратора. Режим `auto` (без human-in-the-loop).
> Заполняется по итогам прогона; ссылается на реальные артефакты
> `output/<run-id>/`.

## Вход

Сырая идея as-is и источник (если есть).

## Созданные артефакты

- `brief.md`, `open-questions.md`
- `personas.md`, `jtbd.md`, `business-requirements.md`
- `use-cases.md`, `functional-requirements.md`, `nonfunctional-requirements.md`
- `spec.md`
- `validation-report.md`, `hallucination-log.md`
- `traceability-matrix.md`, `risk-register.md`, `human-oversight-plan.md`
- `cjm.md`
- `diagrams/` (`.mmd` + `.bpmn` + PNG при рендере)

## Гейты

| Гейт | Статус | Что осталось |
|---|---|---|
| BA-gate |  |  |
| SA-gate |  |  |
| Spec-gate |  |  |

## Что подтверждено

- факт с источником (`[факт]`, ссылка).

## Что осталось допущением

- допущение (`[допущение]`) и почему не подтверждено.

## Главный вывод прогона

Один-два абзаца: что показал прогон, где разрыв.

## Следующий шаг для человека

1. Что валидировать первым.
2. Что закрыть до Spec-gate.
