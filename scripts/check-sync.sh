#!/usr/bin/env bash
# Verify that skills, templates and scripts are wired into the pipeline and
# that all three modes (auto / chat / hybrid) are documented.
# Usage: scripts/check-sync.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0

# 1. Every skill is referenced by a role prompt or the start prompt.
for f in skills/*.md; do
  b="$(basename "$f")"
  [ "$b" = "README.md" ] && continue
  if ! grep -rq "$b" prompts/roles prompts/start.md; then
    echo "UNUSED SKILL: $b"
    fail=1
  fi
done

# 2. Every template is referenced by the start prompt or the diagram skill.
for f in templates/*; do
  b="$(basename "$f")"
  if ! grep -q "$b" prompts/start.md skills/diagram-generation.md; then
    echo "UNREFERENCED TEMPLATE: $b"
    fail=1
  fi
done

# 3. Every script is referenced by the Makefile.
for f in scripts/*.sh; do
  b="$(basename "$f")"
  if ! grep -q "$b" Makefile; then
    echo "UNREFERENCED SCRIPT: $b"
    fail=1
  fi
done

# 4. All three modes are documented in the start prompt.
for m in auto chat hybrid; do
  if ! grep -qi "\\b$m\\b" prompts/start.md; then
    echo "MODE NOT DOCUMENTED: $m"
    fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "check-sync: OK"
else
  echo "check-sync: FAILED" >&2
  exit 1
fi
