#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

find_uv() {
  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return 0
  fi

  if [ -x "$HOME/.local/bin/uv" ]; then
    printf '%s\n' "$HOME/.local/bin/uv"
    return 0
  fi

  if [ -x "$HOME/.local/bin/uv.exe" ]; then
    printf '%s\n' "$HOME/.local/bin/uv.exe"
    return 0
  fi

  if command -v powershell.exe >/dev/null 2>&1; then
    local win_uv
    win_uv="$(powershell.exe -NoProfile -Command '$p = Join-Path $env:USERPROFILE ".local\bin\uv.exe"; if (Test-Path $p) { Write-Output $p }' 2>/dev/null | tr -d '\r' || true)"
    if [ -n "$win_uv" ]; then
      if command -v cygpath >/dev/null 2>&1; then
        win_uv="$(cygpath -u "$win_uv")"
      elif command -v wslpath >/dev/null 2>&1; then
        win_uv="$(wslpath -u "$win_uv")"
      fi
      printf '%s\n' "$win_uv"
      return 0
    fi
  fi

  return 1
}

UV_BIN="$(find_uv || true)"

if [ -z "$UV_BIN" ]; then
  echo "uv is not installed. Install it from https://docs.astral.sh/uv/ and rerun this script."
  exit 1
fi

"$UV_BIN" venv --python 3.11 .venv
"$UV_BIN" pip install -e ".[dev]"
