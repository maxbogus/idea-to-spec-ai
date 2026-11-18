# Стартовый промпт — «идея → спецификация»

> Одна точка входа. Скопируй этот файл целиком в новый чат LLM, вставь
> сырую идею в блок «Идея» — и либо получишь весь каркас в `output/`, либо
> пройдёшь в диалоге. Больше ничего вводить не нужно: промпты, правила,
> методы, скилы и шаблоны уже в репозитории.

## Шаг 0. Режим

Спроси пользователя, если он не указал режим в самой идее. Вопрос — по
формату из Шага 4 (три блока: вопрос / зачем / термины):

> **Вопрос:** «В каком режиме работаем: `auto` (без вопросов, всё
> неизвестное — допущения), `chat` (спрашиваю по ходу, не больше 3
> вопросов за гейт) или `hybrid` (вопросы только на критичных развилках:
> контур, пользователи, платежи, интеграции)?»
>
> **Зачем я это спрашиваю:** режим определяет, сколько допущений появится
> без вашего участия и где вы будете валидировать. Ошибка здесь — либо
> молчаливые галлюцинации (`auto`), либо лишние вопросы.
>
> **Термины:** `auto` — ИИ решает сам; `chat` — диалог; `hybrid` — диалог
> только на развилках. «Контур» — границы продукта по типу клиента и
> географии (см. «Глоссарий терминов» в `prompts/rules.md`).

Если ответа нет и режим не указан — по умолчанию `auto` и явно это
сообщи.

## Шаг 1. Вход

Единственный обязательный вход — **сырая идея as-is** (можно «плохая», по
типу «сделайте красиво»). Если идея пустая — это единственное исключение,
когда вопрос допустим даже в `auto`: попроси одну строку и не начинай
прогон.

## Шаг 2. Каркас в `output/`

До содержательных шагов создай структуру:

```
output/<run-id>/
  brief.md
  open-questions.md
  personas.md
  jtbd.md
  business-requirements.md
  functional-requirements.md
  nonfunctional-requirements.md
  use-cases.md
  spec.md
  traceability-matrix.md
  risk-register.md
  human-oversight-plan.md
  validation-report.md
  hallucination-log.md
  cjm.md
  diagrams/
    use-case.mmd
    sequence.mmd
    er.mmd
    dfd-context.mmd
    dfd-level1.mmd
    dfd-level2.mmd
    dfd-level3.mmd
    c4-context.mmd
    c4-container.mmd
    c4-component.mmd
    c4-deployment.mmd
    bpmn-process.mmd
    bpmn-process.bpmn
    activity.mmd
    gantt.mmd
```

`<run-id>` = `auto-001` / `chat-001` / `hybrid-001` (или дата-время).
Файлы создаются из `templates/` (для `brief.md` — `brief-template.md`, для
`spec.md` — `spec-template.md`, JTBD — `jtbd.md`, CJM — `cjm.md`, диаграммы — `*.mmd`,
остальные — одноимённые) и заполняются по мере прохождения этапов. В `auto`
создаются все; в `chat`/`hybrid` можно создавать по этапу, но структура та же.

Каркас можно развернуть командой `make scaffold RUN=<run-id>` (скрипт
`scripts/scaffold-run.sh`), а диаграммы отрендерить `make render
RUN=<run-id>` (скрипт `scripts/render-diagrams.sh`).

## Шаг 3. Конвейер

| Этап | Роль + промпт | Метод / скил | Артефакт | Гейт |
|---|---|---|---|---|
| Intake | `prompts/orchestrator.md` | бриф | `brief.md`, `open-questions.md` | — |
| Business | `prompts/roles/product-manager.md`, `prompts/roles/business-analyst.md` | `methods/variants.md`, `methods/strategy-and-verification.md`, `skills/collect-sources.md`, `skills/mock-respondents.md` | `personas.md`, `jtbd.md`, `business-requirements.md` | **BA-gate** (`prompts/rules.md`) |
| System | `prompts/roles/system-analyst.md` | `methods/fact-hypothesis-forecast.md`, `skills/detect-contradictions.md`, `skills/analyze-data.md` | `use-cases.md`, `functional-requirements.md`, `nonfunctional-requirements.md` | **SA-gate** |
| Architecture | `prompts/roles/architect.md` | `methods/decision-keeper.md`, `skills/detect-contradictions.md` | `spec.md` (архитектурные ссылки) | — |
| Validation | `subagents/fact-check.md` | `methods/fact-hypothesis-forecast.md` | `validation-report.md`, `hallucination-log.md` | **Spec-gate** |
| Plan | `prompts/roles/project-manager.md` | `methods/decision-keeper.md`, `methods/strategy-and-verification.md` | `traceability-matrix.md`, `risk-register.md`, `human-oversight-plan.md` | **Spec-gate** |
| Design | `prompts/roles/designer.md` | `skills/mock-respondents.md` | user flow в `spec.md` | — |

Порядок жёсткий: не переходи к System, пока не закрыт BA-gate; не переходи
к Spec-gate, пока не прогнан fact-check.

## Шаг 3a. Диаграммы

Диаграммы строятся из тех же ID, что и требования (см.
`skills/diagram-generation.md`): JTBD — из `personas.md` (в `jtbd.md`);
use case — из `UC-*` (нативные `usecase-beta`, актор = человечек; нужен
`mermaid-cli >= 12.0.0`); sequence — из шагов UC, ER и DFD (L0–L3) — из
`spec.md §6/§9`, C4 (C1–C4) — из §9, BPMN — из ключевого UC,
Gantt — из roadmap, CJM — из персон × JTBD × UC.
Файлы — в `output/<run-id>/diagrams/` (`*.mmd`; канонический BPMN —
`bpmn-process.bpmn`). Скелеты — `templates/*.mmd` и `templates/*.bpmn`.
PNG рендерится опционально: `mmdc -i x.mmd -o x.png -b white`.

## Шаг 4. Поведение по режимам

- **`auto`** — вопросов не задаёшь. Всё неизвестное → **гипотеза/допущение**
  с пометкой. В конце — отчёт: что сгенерировано, какие допущения, сколько
  открытых вопросов.
- **`chat`** — на каждом гейте не больше 3 вопросов, только те, что меняют
  следующий шаг. Ответы вставляешь в артефакты до перехода дальше.
- **`hybrid`** — вопросы только на развилках: контур, пользователи,
  платежи, интеграции.

### Формат каждого вопроса

Каждый вопрос задаёшь тремя блоками (как в референсном интервью):

1. **Вопрос** — конкретный, можно с микро-подсказками.
2. **Зачем я это спрашиваю** — 2–4 предложения: что этим закрываем, какой
   риск снижаем, что появится на выходе.
3. **Термины** — расшифровка терминов из вопроса (формулировки — из
   «Глоссария терминов» в `prompts/rules.md`).

Правило действует для любого вопроса, включая Шаг 0.

## Шаг 5. Формат каждого шага

После этапа возвращай JSON в формате из `prompts/orchestrator.md`
(поля: `mode`, `stage`, `completeness`, `questions`, `artifacts`,
`assumptions`, `next`). В `artifacts` указывай реальные пути
`output/<run-id>/…`.

## Шаг 6. Финал

Отчёт в конце прогона:

1. список созданных артефактов;
2. что подтверждено, что осталось допущением;
3. `hallucination-log.md` — где ИИ «додумал»;
4. чеклист Spec-gate (`prompts/rules.md`) — пройден или нет;
5. следующий шаг для человека — что валидировать в первую очередь.

## Правила, которые нельзя нарушать

- Факт без источника — не факт (`methods/fact-hypothesis-forecast.md`).
- Пробел — результат, а не провал.
- Не смешивать бизнес- и системный анализ.
- Не выдавать гипотезу о решении за потребность.
- Не пропускать fact-check перед Spec-gate.
