# Handout Index — синхронизация промптов, скилов и методов

> Единый источник правды: какая роль какой метод и скил применяет, какой
> артефакт создаёт и на каком гейте проверяется. Если роль, метод, скил и
> артефакт расходятся — правим здесь, а не в пяти файлах по отдельности.

## Три слоя знаний

| Слой | Папка | Что это | Пример |
|---|---|---|---|
| Промпты | `prompts/` | роли и правила | `prompts/roles/system-analyst.md` |
| Навыки (методы) | `methods/` | методики, общие для ролей | `fact-hypothesis-forecast.md` |
| Скилы | `skills/` | повторяемые процедуры | `detect-contradictions.md` |

## Сквозная таблица

| Роль | Промпт | Методы (навыки) | Скилы | Артефакты | Гейт |
|---|---|---|---|---|---|
| Оркестратор | `prompts/orchestrator.md` | все (диспетчер) | все (диспетчер) | `brief.md`, `open-questions.md`, отчёт | — |
| Product Manager | `prompts/roles/product-manager.md` | `variants.md`, `strategy-and-verification.md`, `decision-keeper.md` | `collect-sources.md`, `analyze-data.md` | `business-requirements.md` (ценность, варианты) | BA-gate |
| Business Analyst | `prompts/roles/business-analyst.md` | `fact-hypothesis-forecast.md` | `mock-respondents.md`, `collect-sources.md` | `personas.md`, `business-requirements.md` | BA-gate |
| System Analyst | `prompts/roles/system-analyst.md` | `fact-hypothesis-forecast.md` | `detect-contradictions.md`, `analyze-data.md`, `diagram-generation.md` | `use-cases.md`, `functional-requirements.md`, `nonfunctional-requirements.md`, `spec.md`, `diagrams/use-case.mmd`, `sequence.mmd`, `er.mmd` | SA-gate |
| Architect | `prompts/roles/architect.md` | `decision-keeper.md` | `detect-contradictions.md`, `diagram-generation.md` | ADR и интеграции в `spec.md`, `diagrams/c4-context.mmd`, `c4-container.mmd`, `activity.mmd` | Spec-gate |
| Designer | `prompts/roles/designer.md` | — | `mock-respondents.md`, `diagram-generation.md` | `cjm.md`, user flow / wireframe в `spec.md` | — |
| Project Manager | `prompts/roles/project-manager.md` | `decision-keeper.md`, `strategy-and-verification.md` | `analyze-data.md`, `diagram-generation.md` | `traceability-matrix.md`, `risk-register.md`, `human-oversight-plan.md`, `diagrams/gantt.mmd` | Spec-gate |
| Fact-check (субагент) | `subagents/fact-check.md` | `fact-hypothesis-forecast.md` | — | `validation-report.md`, `hallucination-log.md` | Spec-gate |

## Диаграммы

Диаграмма — производная от артефакта, а не отдельный рисунок
(`skills/diagram-generation.md`). Каталог «источник → диаграмма»:

| Источник | Диаграмма | Файл |
|---|---|---|
| `personas.md` + `use-cases.md` + user flow | CJM | `cjm.md` |
| `use-cases.md` (`UC-*`) | Use Case | `diagrams/use-case.mmd` |
| шаги `UC-*` | Sequence | `diagrams/sequence.mmd` |
| `spec.md §6` данные | ER | `diagrams/er.mmd` |
| `spec.md §9` компоненты | C4 context / container | `diagrams/c4-context.mmd`, `c4-container.mmd` |
| ключевой поток | Activity | `diagrams/activity.mmd` |
| `roadmap` | Gantt | `diagrams/gantt.mmd` |

Рендер (опционально): `mmdc -i x.mmd -o x.png -b white`. PNG не коммитится
по умолчанию — только source `.mmd`.

## Проверка синхронизации

- [ ] каждая роль из `prompts/roles/` есть в таблице;
- [ ] каждый метод из `methods/` используется хотя бы одной ролью;
- [ ] каждый скил из `skills/` используется хотя бы одной ролью;
- [ ] каждый артефакт из `templates/` имеет владельца-роль;
- [ ] каждая диаграмма из `templates/*.mmd` выводится из артефакта-источника;
- [ ] у каждого гейта есть владелец и чеклист в `prompts/rules.md`;
- [ ] стартовый промпт `prompts/start.md` ссылается только на существующие
      файлы.

## Терминология

- **Факт / гипотеза / прогноз** — единая триада из
  `methods/fact-hypothesis-forecast.md`. «Допущение» — частный случай
  гипотезы, а не отдельное состояние.
- **Скил** — «как сделать»; **метод (навык)** — «по какому правилу решать»;
  **промпт** — «кто делает и в каком формате отвечает».
