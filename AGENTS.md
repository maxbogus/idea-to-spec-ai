# AGENTS.md — карта проекта

> **Что это.** Практический 2-часовой воркшоп «От идеи до спецификации с ИИ»:
> мультиагентная система (промпты + методы + скилы + шаблоны), которая
> превращает сырой бизнес-запрос в проверяемую спецификацию и показывает,
> где обязан вмешаться человек.
>
> **Зачем этот файл.** Единая точка входа для агента и человека: что где
> лежит, как устроен пайплайн, какие команды запускать, какие требования к
> окружению и где легко ошибиться. Детальная синхронизация ролей —
> `handout-index.md`; старт прогона — `prompts/start.md`.

## Стек

| Слой | Технология |
|---|---|
| Контент | Markdown (`.md`) |
| Диаграммы | Mermaid (`.mmd`) + BPMN 2.0 (`.bpmn`) |
| Рендер | `@mermaid-js/mermaid-cli` (`mmdc`) |
| Автоматизация | GNU Make + bash (`scripts/*.sh`) |

Внешних зависимостей приложения нет: репозиторий — это раздатка, промпты и
шаблоны.

## Архитектура (пайплайн)

Оркестратор ведёт по этапам, жёстко соблюдая порядок и гейты:

```
Intake (оркестратор)
  → Business (PM + BA)         → BA-gate
  → System (SA)                → SA-gate
  → Architecture (Architect)
  → Validation (fact-check)    → Spec-gate
  → Plan (PM)
  → Design (Designer)
```

- **Режимы:** `auto` (без вопросов, всё неизвестное — допущения), `chat`
  (диалог, ≤ 3 вопроса за гейт), `hybrid` (вопросы только на развилках).
- **Роли:** Product Manager, Business Analyst, System Analyst, Architect,
  Designer, Project Manager + субагент fact-check.
- **Артефакты** — в `output/<run-id>/` (см. блок «Артефакты прогона»).

## Структура

```
.
├── README.md               обзор воркшопа и содержания
├── AGENTS.md               этот файл — карта проекта
├── workshop-plan.md        план на 120 минут (блоки, упражнения, буфер)
├── transcript-breakdown.md разбор исходного транскрипта (тезисы, термины)
├── architecture.md         оркестратор, роли, режимы, артефакты, гейты
├── standards-mapping.md    наложение SDLC/PDLC и стандартов США/ЕС/РФ
├── handout-index.md        ЕДИНАЯ таблица роль → метод → скил → артефакт → гейт
├── faq-fuckups.md          факапы демо, fallback, буфер
├── Makefile                команды (см. «Команды»)
│
├── prompts/                КТО делает и в каком формате отвечает
│   ├── start.md            стартовый промпт (точка входа: каркас или диалог)
│   ├── rules.md            правила: формат вопросов, глоссарий, окружение, гейты
│   ├── orchestrator.md     роль оркестратора
│   └── roles/              6 ролевых промптов
│       ├── product-manager.md
│       ├── business-analyst.md
│       ├── system-analyst.md
│       ├── architect.md
│       ├── designer.md
│       └── project-manager.md
│
├── methods/                методики: по какому правилу решать
│   ├── fact-hypothesis-forecast.md   факт / гипотеза / прогноз
│   ├── variants.md                   содержательно разные варианты
│   ├── strategy-and-verification.md  стратегия и план проверки
│   └── decision-keeper.md            работа после решения
│
├── skills/                 процедуры: как сделать (пошагово + проверка)
│   ├── README.md
│   ├── collect-sources.md
│   ├── mock-respondents.md
│   ├── detect-contradictions.md
│   ├── analyze-data.md
│   └── diagram-generation.md
│
├── subagents/
│   └── fact-check.md       проверка оснований перед Spec-gate
│
├── templates/              шаблоны артефактов и скелеты диаграмм
│   ├── *.md                артефакты (brief, personas, jtbd, use-cases, cjm, spec, …)
│   ├── *.mmd               Mermaid-скелеты (use-case = usecase-beta, sequence, ER, DFD 0–3, C4, BPMN, activity, gantt)
│   ├── bpmn-process.bpmn   канонический BPMN 2.0 XML (bpmn.io / Camunda)
│   └── mermaid-config.json детерминированный рендер
│
├── agenda/                 сценарий двух частей воркшопа
│   ├── part1-before-spec.md
│   └── part2-handoff.md
│
├── exercises/              упражнения и домашние задания
│   ├── ex1-questions.md
│   ├── ex2-validation.md
│   ├── ex3-role-prompt.md
│   └── homework.md
│
├── scripts/
│   ├── check-prereqs.sh    preflight: node, mmdc >= 12, make, config
│   ├── scaffold-run.sh     развернуть output/<run-id>/ из templates/
│   ├── render-diagrams.sh  .mmd → .png через mmdc
│   ├── check-sync.sh       связность скилов/шаблонов/скриптов/режимов
│   ├── promptfoo_transform.py  собрать промпт роли для eval
│   ├── mock_provider.py        детерминированные ответы (eval-mock)
│   └── summarize_eval.py       метрики eval-прогона
│
├── eval/                   eval промптов (promptfoo)
│   ├── cases/roles.jsonl   кейсы: ORCH, PM, BA, SA, ARCH, DESIGN, PROJ, FC + DISC/NEG
│   ├── promptfooconfig.yaml       реальный прогон (Ollama qwen2.5:7b)
│   └── promptfooconfig.mock.yaml  детерминированный replay (без LLM)
│
├── tests/                  pytest-контракты eval (mock + slow xfail)
├── docs/evaluation/        отчёты eval и разбор находок
├── package.json            promptfoo (devDependency)
├── pyproject.toml          uv + pytest + ruff + mypy
│
└── output/                 прогоны (артефакты + диаграммы)
    └── auto-001/           демо-прогон (auto)
```

## Артефакты прогона `output/<run-id>/`

Ключевые `.md`:
`brief.md`, `open-questions.md`, `personas.md`, `jtbd.md`,
`business-requirements.md`, `functional-requirements.md`,
`nonfunctional-requirements.md`, `use-cases.md`, `spec.md`,
`traceability-matrix.md`, `risk-register.md`, `human-oversight-plan.md`,
`validation-report.md`, `hallucination-log.md`, `cjm.md`.

Диаграммы — в `diagrams/`: `use-case.mmd`, `sequence.mmd`, `er.mmd`,
`dfd-context.mmd`, `dfd-level1.mmd`, `dfd-level2.mmd`, `dfd-level3.mmd`, `c4-context.mmd`,
`c4-container.mmd`, `c4-component.mmd`, `c4-deployment.mmd`,
`bpmn-process.mmd` + `bpmn-process.bpmn`, `activity.mmd`, `gantt.mmd`.

## Команды

```bash
make setup                 # preflight: node, mmdc >= 12.0.0, make
make help                  # список целей
make scaffold RUN=auto-002 # развернуть каркас прогона
make render RUN=auto-002   # .mmd -> .png
make render-all            # все прогоны
make check                 # ПОЛНЫЙ гейт: prereqs + refs + fences + diagrams + bpmn + sync
make check-refs            # ссылки на md/mmd/bpmn резолвятся
make check-fences          # парность code-fences во всех .md
make check-diagrams        # синтаксис всех .mmd (рендер в temp)
make check-bpmn            # well-formed XML для .bpmn
make check-sync            # скилы/шаблоны/скрипты используются, режимы описаны
make list-runs             # прогоны в output/
make start                 # показать prompts/start.md
make eval-setup            # uv sync + npm install (зависимости eval)
make test-eval             # pytest-контракты eval без модели
make eval-mock             # детерминированный replay eval (без LLM)
make eval                  # реальный прогон eval на Ollama (qwen2.5:7b)
make lint-py               # ruff + mypy для eval-обвязки
make clean-png             # удалить PNG (source .mmd остаются)
make clean-run RUN=x CONFIRM=yes  # удалить прогон (защищено от случайного запуска)
```

## Требования к окружению

| Инструмент | Версия | Зачем |
|---|---|---|
| `node` | 18+ | рантайм для mermaid-cli |
| `@mermaid-js/mermaid-cli` (`mmdc`) | **>= 12.0.0** | рендер `usecase-beta` (actors = человечки) |
| `make` | GNU make | команды |
| `uv` | >= 0.5 | Python-зависимости eval (pytest, ruff, mypy) |
| `npm` | 18+ | promptfoo для eval (`make eval-setup`) |
| Ollama + `qwen2.5:7b` | — | реальный прогон `make eval` |

Проверка: **`make setup`** (`scripts/check-prereqs.sh`). Если `mmdc` ниже 12 —
рендер use case-диаграмм упадёт. Обновление:
`npm i -g @mermaid-js/mermaid-cli@^12`.

## Eval промптов

- Обвязка: `eval/` (кейсы + конфиги promptfoo), `scripts/*.py`, `tests/`.
- Кейсы хранят контракт: обязательные поля, `must_contain` / `must_not_contain`,
  дисциплина режима (`auto`/`chat`/`hybrid`), маркеры допущений.
- `make eval-mock` — детерминированный replay (без LLM, зелёный).
- `make eval` — реальный прогон на `qwen2.5:7b`; отчёт в `docs/evaluation/`.
- Провалы модели фиксируются как `xfail(strict=True)` (`KNOWN_MODEL_FAILURES`),
  а не маскируются. Внезапный XPASS — сигнал обновить список.
- Находки первого прогона — `docs/evaluation/README.md`.

## Соглашения и типичные ошибки

- **Факт без источника — не факт.** Всё неподтверждённое — гипотеза/допущение
  с явной пометкой.
- **Не смешивать бизнес- и системный анализ.** BA — потребность/требования,
  SA — use cases/спека.
- **Не выдавать гипотезу о решении за потребность.**
- **Диаграмма — производная.** Узлы строятся из ID артефактов (`UC-*`,
  `J-*`, `BR-*`), новых сущностей не придумывать.
- **JTBD → use cases → CJM.** JTBD (`jtbd.md`) — «зачем»; каждый `UC-*`
  трассируется до `J-*`; CJM = персоны × JTBD × UC × user flow.
- **Use case-диаграмма — нативный `usecase-beta`** (актор = человечек,
  use case = овал). Требует `mmdc >= 12`.
- **Каждый вопрос (chat/hybrid) — три блока:** Вопрос / «Зачем я это
  спрашиваю» / «Термины» (см. `prompts/rules.md`, «Формат вопроса» и
  «Глоссарий терминов»).
- **Синхронизация.** Добавил скил/шаблон/скрипт — обнови `handout-index.md`
  и убедись, что `make check-sync` проходит.
- **Гейты не пропускать:** BA-gate → SA-gate → fact-check → Spec-gate.
