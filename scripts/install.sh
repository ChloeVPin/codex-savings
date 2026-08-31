#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${CODEX_HOME:-$HOME/.codex}/skills/codex-savings"

if [ "$SRC_DIR" = "$TARGET" ]; then
  echo "codex-savings is already installed at $TARGET"
  exit 0
fi

mkdir -p "$TARGET"
find "$SRC_DIR" -mindepth 1 -maxdepth 1 \
  ! -name .git \
  ! -name .DS_Store \
  -exec cp -R {} "$TARGET"/ \;

echo "installed codex-savings -> $TARGET"
echo "restart Codex, then invoke: \$codex-savings"
