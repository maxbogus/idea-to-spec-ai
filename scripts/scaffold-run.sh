#!/usr/bin/env bash
# Materialize a run scaffold in output/<run-id>/ from templates/.
# Usage: scripts/scaffold-run.sh <run-id>
set -euo pipefail

RUN_ID="${1:-}"

if [ -z "$RUN_ID" ]; then
  echo "Usage: scripts/scaffold-run.sh <run-id>" >&2
  exit 1
fi

if ! [[ "$RUN_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "ERROR: invalid run-id '$RUN_ID' (allowed: letters, digits, dot, underscore, hyphen)" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TPL="$ROOT/templates"
OUT="$ROOT/output/$RUN_ID"

mkdir -p "$OUT/diagrams"

artifacts="brief open-questions personas jtbd business-requirements functional-requirements nonfunctional-requirements use-cases spec traceability-matrix risk-register human-oversight-plan validation-report hallucination-log cjm run-report"

created=0
skipped=0

for a in $artifacts; do
  case "$a" in
    brief) src="$TPL/brief-template.md" ;;
    spec)  src="$TPL/spec-template.md" ;;
    *)     src="$TPL/$a.md" ;;
  esac
  if [ ! -f "$src" ]; then
    echo "ERROR: template not found: $src" >&2
    exit 1
  fi
  dst="$OUT/$a.md"
  if [ -e "$dst" ]; then
    skipped=$((skipped + 1))
  else
    cp "$src" "$dst"
    created=$((created + 1))
  fi
done

shopt -s nullglob
for f in "$TPL"/*.mmd; do
  dst="$OUT/diagrams/$(basename "$f")"
  if [ -e "$dst" ]; then
    skipped=$((skipped + 1))
  else
    cp "$f" "$dst"
    created=$((created + 1))
  fi
done

# Канонический BPMN 2.0 XML копируется отдельно: templates/*.mmd его не покрывает.
for f in "$TPL"/*.bpmn; do
  dst="$OUT/diagrams/$(basename "$f")"
  if [ -e "$dst" ]; then
    skipped=$((skipped + 1))
  else
    cp "$f" "$dst"
    created=$((created + 1))
  fi
done

echo "Scaffold: output/$RUN_ID (created=$created, skipped=$skipped)"
