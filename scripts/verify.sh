#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILURES=0

pass() {
  printf '[PASS] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
  FAILURES=$((FAILURES + 1))
}

find_project_python() {
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    printf '%s\n' "$ROOT_DIR/.venv/bin/python"
    return 0
  fi

  if [ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]; then
    printf '%s\n' "$ROOT_DIR/.venv/Scripts/python.exe"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  return 1
}

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

  if [ -x "$HOME/.cargo/bin/uv" ]; then
    printf '%s\n' "$HOME/.cargo/bin/uv"
    return 0
  fi

  if [ -x "$HOME/.cargo/bin/uv.exe" ]; then
    printf '%s\n' "$HOME/.cargo/bin/uv.exe"
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

PYTHON_BIN="$(find_project_python || true)"

if [ -n "$PYTHON_BIN" ]; then
  PY_VERSION_OUTPUT="$("$PYTHON_BIN" --version 2>&1)"
  if "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
    pass "Python 3.11+ ($PY_VERSION_OUTPUT)"
  else
    fail "Python 3.11+ required; found $PY_VERSION_OUTPUT"
  fi
else
  fail "Python 3.11+ required; no python executable found"
fi

if command -v ffmpeg >/dev/null 2>&1; then
  FFMPEG_VERSION="$(ffmpeg -version 2>&1 | head -n 1)"
  pass "FFmpeg ($FFMPEG_VERSION)"
else
  fail "FFmpeg not found on PATH. Install it, then rerun this script. macOS: brew install ffmpeg. Ubuntu/Debian: sudo apt install ffmpeg. Windows: winget install Gyan.FFmpeg or install from https://www.gyan.dev/ffmpeg/builds/ and add ffmpeg/bin to PATH."
fi

UV_BIN="$(find_uv || true)"
if [ -n "$UV_BIN" ]; then
  UV_VERSION="$("$UV_BIN" --version 2>&1)"
  pass "uv ($UV_VERSION)"
else
  fail "uv not found. Install from https://docs.astral.sh/uv/getting-started/installation/"
fi

if command -v git >/dev/null 2>&1; then
  GIT_VERSION="$(git --version 2>&1)"
  pass "git ($GIT_VERSION)"
else
  fail "git not found on PATH"
fi

check_python_package() {
  local import_name="$1"
  local label="$2"
  local code="$3"

  if [ -z "$PYTHON_BIN" ]; then
    fail "$label Python package could not be checked because Python was not found"
    return
  fi

  local output
  if output="$("$PYTHON_BIN" -c "$code" 2>&1)"; then
    pass "$label ($output)"
  else
    fail "$label Python package import failed: $output"
  fi
}

check_python_package "opentimelineio" "opentimelineio" "import opentimelineio; print(opentimelineio.__version__)"
check_python_package "librosa" "librosa" "import librosa; print(librosa.__version__)"
check_python_package "mcp" "mcp" "import mcp; print('mcp ok')"

if [ "$FAILURES" -eq 0 ]; then
  echo "All checks passed"
else
  echo "$FAILURES checks failed — see above"
fi

exit "$FAILURES"
