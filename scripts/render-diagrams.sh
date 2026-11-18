#!/usr/bin/env bash
# Render Mermaid .mmd diagrams to PNG with mermaid-cli.
# Usage: scripts/render-diagrams.sh [dir]
#   dir defaults to output/auto-001/diagrams
set -euo pipefail

DIR="${1:-output/auto-001/diagrams}"

if ! command -v mmdc >/dev/null 2>&1; then
  echo "ERROR: mmdc (mermaid-cli) not found. Install: npm i -g @mermaid-js/mermaid-cli" >&2
  exit 1
fi

if [ ! -d "$DIR" ]; then
  echo "ERROR: directory not found: $DIR" >&2
  exit 1
fi

shopt -s nullglob
files=("$DIR"/*.mmd)
if [ ${#files[@]} -eq 0 ]; then
  echo "No .mmd files in $DIR"
  exit 0
fi

for f in "${files[@]}"; do
  out="${f%.mmd}.png"
  echo "render: $f -> $out"
  mmdc -i "$f" -o "$out" -b white
done

echo "Done: ${#files[@]} diagram(s) rendered in $DIR"
