#!/usr/bin/env bash
set -euo pipefail

PARTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSEMBLED_INPUT="${1:?validate_snapshots.sh requires the assembled output path}"

require_contains() {
  local file="$1" needle="$2" label="$3"
  if ! grep -Fq -- "$needle" "$file"; then
    echo "snapshot validation failed: $label missing in $file" >&2
    echo "expected: $needle" >&2
    exit 1
  fi
}

require_contains "$PARTS_DIR/_index.md" "**Designation:** ntl" "index designation"
require_contains "$PARTS_DIR/_index.md" 'Primary output: `doc/ntlSYSTEM.md`' "index primary output"

require_contains "$ASSEMBLED_INPUT" "**Designation:** ntl" "assembled designation"
require_contains "$ASSEMBLED_INPUT" 'Primary output: `doc/ntlSYSTEM.md`' "assembled primary output"

echo "snapshot validation passed"
