SHELL := /bin/bash
.DEFAULT_GOAL := help

RUN ?= auto-001
OUT_ROOT ?= output
MMDC ?= mmdc
MERMAID_CFG ?= templates/mermaid-config.json
CONFIRM ?=
SCRIPTS := $(CURDIR)/scripts

.PHONY: help scaffold render render-all check check-refs check-fences check-diagrams check-bpmn list-runs clean-png clean-run start

help: ## Показать список целей
	@echo "Использование: make <target> [RUN=<id>]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'
	@echo ""
	@echo "Переменные: RUN=$(RUN) OUT_ROOT=$(OUT_ROOT)"

scaffold: ## Развернуть каркас прогона: make scaffold RUN=auto-002
	@bash $(SCRIPTS)/scaffold-run.sh "$(RUN)"

render: ## Отрендерить .mmd -> .png: make render RUN=auto-001
	@bash $(SCRIPTS)/render-diagrams.sh "$(OUT_ROOT)/$(RUN)/diagrams" "$(MERMAID_CFG)"

render-all: ## Отрендерить диаграммы всех прогонов
	@shopt -s nullglob; \
	found=0; \
	for d in $(OUT_ROOT)/*/diagrams; do \
	  if compgen -G "$$d/*.mmd" >/dev/null; then \
	    echo "== $$d"; \
	    bash $(SCRIPTS)/render-diagrams.sh "$$d" "$(MERMAID_CFG)"; \
	    found=1; \
	  fi; \
	done; \
	if [ $$found -eq 0 ]; then echo "Нет прогонов с диаграммами в $(OUT_ROOT)/"; fi

check: check-refs check-fences check-diagrams check-bpmn ## Полная проверка раздатки и диаграмм

check-refs: ## Проверить, что все ссылки на md/mmd резолвятся
	@ok=1; \
	for ref in $$(grep -rhoE '(prompts|methods|skills|subagents|templates)/[a-zA-Z0-9_*.-]+\.(md|mmd|bpmn|json)' . --include='*.md' --include='*.mmd' | sort -u); do \
	  case "$$ref" in *'*'*) continue;; esac; \
	  if [ ! -f "$$ref" ]; then echo "MISSING: $$ref"; ok=0; fi; \
	done; \
	if [ $$ok -eq 1 ]; then echo "check-refs: OK"; else echo "check-refs: FAILED" >&2; exit 1; fi

check-fences: ## Проверить парность ``` во всех .md
	@ok=1; \
	for f in $$(find . -path ./.git -prune -o -name '*.md' -print); do \
	  n=$$(grep -c '^```' "$$f" || true); \
	  if [ $$((n % 2)) -ne 0 ]; then echo "ODD FENCE: $$f ($$n)"; ok=0; fi; \
	done; \
	if [ $$ok -eq 1 ]; then echo "check-fences: OK"; else echo "check-fences: FAILED" >&2; exit 1; fi

check-diagrams: ## Проверить синтаксис всех .mmd рендером в temp
	@command -v $(MMDC) >/dev/null 2>&1 || { echo "ERROR: $(MMDC) не найден (npm i -g @mermaid-js/mermaid-cli)" >&2; exit 1; }; \
	tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	ok=1; \
	for f in $$(find . -path ./.git -prune -o -name '*.mmd' -print); do \
	  name=$$(echo "$$f" | tr '/' '_'); \
	  if $(MMDC) -i "$$f" -o "$$tmp/$${name%.mmd}.png" -b white >/dev/null 2>&1; then \
	    echo "diagram OK: $$f"; \
	  else echo "diagram FAIL: $$f"; ok=0; fi; \
	done; \
	if [ $$ok -eq 1 ]; then echo "check-diagrams: OK"; else echo "check-diagrams: FAILED" >&2; exit 1; fi

check-bpmn: ## Проверить, что .bpmn — well-formed XML
	@ok=1; \
	found=0; \
	for f in $$(find . -path ./.git -prune -o -name '*.bpmn' -print); do \
	  found=1; \
	  if python3 -c "import sys, xml.etree.ElementTree as ET; ET.parse(sys.argv[1])" "$$f" 2>/dev/null; then \
	    echo "bpmn OK: $$f"; \
	  else echo "bpmn FAIL: $$f"; ok=0; fi; \
	done; \
	if [ $$found -eq 0 ]; then echo "check-bpmn: нет .bpmn"; exit 0; fi; \
	if [ $$ok -eq 1 ]; then echo "check-bpmn: OK"; else echo "check-bpmn: FAILED" >&2; exit 1; fi

list-runs: ## Список прогонов в output/
	@ls -1 $(OUT_ROOT) 2>/dev/null || echo "нет прогонов"

clean-png: ## Удалить отрендеренные PNG (source остаются)
	@shopt -s nullglob; \
	n=0; \
	for f in $(OUT_ROOT)/*/diagrams/*.png; do rm -f "$$f"; n=$$((n + 1)); done; \
	echo "clean-png: удалено $$n PNG"

clean-run: ## Удалить прогон (нужно CONFIRM=yes): make clean-run RUN=auto-002 CONFIRM=yes
	@if [ "$(CONFIRM)" != "yes" ]; then \
	  echo "Отказ. Предпросмотр: make -n clean-run RUN=$(RUN)"; \
	  echo "Затем: make clean-run RUN=$(RUN) CONFIRM=yes"; \
	  exit 1; \
	fi; \
	if [ -z "$(RUN)" ] || [ "$(RUN)" = "*" ] || [ "$(RUN)" = "/" ]; then \
	  echo "ERROR: укажи конкретный RUN" >&2; exit 1; \
	fi; \
	if [ ! -d "$(OUT_ROOT)/$(RUN)" ]; then \
	  echo "ERROR: нет $(OUT_ROOT)/$(RUN)" >&2; exit 1; \
	fi; \
	rm -rf "$(OUT_ROOT)/$(RUN)"; \
	echo "clean-run: удалён $(OUT_ROOT)/$(RUN)"

start: ## Показать стартовый промпт prompts/start.md
	@cat prompts/start.md
