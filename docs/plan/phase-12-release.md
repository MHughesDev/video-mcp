# Phase 12 — Release & CI/CD

## Status
Not Started — 25%

## Goal
Make the server installable and continuously verified. Today the project can
only be installed from source, has **no `.github/workflows`**, and ships no
publish path. This phase delivers CI (lint + unit + integration on every push),
cross-platform test runs, automated release packaging, and a `pip install`-able
artifact. This is the final MVP gate (MVP criterion 9).

## Depends On
Phase 10 (Hardening) and Phase 11 (Integration Testing) — do not release before
the pipeline is proven on real media and hardening is in place.

## Tools / Components Delivered
This phase delivers **infrastructure**, not MCP tools.

| Component | Description | Status | Notes |
|-----------|-------------|--------|-------|
| Versioning + CHANGELOG | `pyproject.toml` at `0.8.0`; `CHANGELOG.md` maintained | ✓ Done | Good discipline already |
| `mcp-editor` entry point | Console script for the server | ✓ Done | `mcp-editor = mcp_editor.server:main` |
| CI workflow | GitHub Actions: install + lint + unit + (mocked) integration | ✗ Missing | No `.github/workflows` exists |
| Real-media CI job | Runs `realmedia`-marked tests where FFmpeg is available | ✗ Missing | Depends on P11 markers |
| Cross-platform matrix | Linux/macOS/Windows test runs | ✗ Missing | Validates P10 path handling |
| Release workflow | Tag → build sdist/wheel → publish (PyPI and/or GH release) | ✗ Missing | MVP criterion 9 |
| Benchmark CI gate | Run `scripts/benchmark.py`, flag regressions | ✗ Missing | Wires up the P10 benchmark suite |
| Install verification | `pip install` from artifact imports + starts the server | ✗ Missing | Smoke test of the published package |

## Acceptance Criteria
- [ ] A CI workflow runs on every push/PR: dependency install, lint, `pytest tests/unit`, and the monkeypatched integration suite — all green.
- [ ] A real-media CI job runs the `realmedia`-marked tests on a runner with FFmpeg installed.
- [ ] The test matrix runs on Linux, macOS, and Windows (validating `posix_path()` and `as_path()` cross-platform).
- [ ] A tagged release builds an sdist + wheel and publishes to PyPI (or attaches to a GitHub Release) automatically.
- [ ] `pip install mcp-editor` (from PyPI or the release artifact) succeeds, exposes the `mcp-editor` console script, and the server starts.
- [ ] `scripts/benchmark.py` runs in CI and surfaces timings (optionally failing on large regressions).
- [ ] `README.md` install instructions match the published artifact (not just "install from source").

## Implementation Tasks

1. **Base CI workflow** — `.github/workflows/ci.yml`.
   Done-when: install + lint + unit + mocked-integration green on push/PR.
   **Status: Not Started.**
2. **Cross-platform matrix** — add `os: [ubuntu, macos, windows]` to CI.
   Done-when: suite green on all three. **Status: Not Started.**
3. **Real-media job** — CI step that installs FFmpeg and runs `-m realmedia`.
   Done-when: real-media tests execute where FFmpeg is present. **Status: Not
   Started — depends on P11.**
4. **Release workflow** — `.github/workflows/release.yml`.
   Done-when: on tag `v*`, build sdist/wheel and publish to PyPI (trusted
   publishing) and/or attach to a GitHub Release. **Status: Not Started.**
5. **Packaging audit** — confirm `pyproject.toml` metadata (classifiers,
   readme, license, deps pinned appropriately), and decide whether to add a
   `mcp-editor-bench` entry point or document the script path.
   Done-when: `python -m build` produces a clean wheel/sdist. **Status: Not
   Started.**
6. **Install smoke test** — CI job that `pip install`s the built wheel in a
   clean env and starts the server.
   Done-when: import + `mcp-editor --help`/startup succeeds. **Status: Not
   Started.**
7. **Benchmark gate** — run `scripts/benchmark.py --json` in CI.
   Done-when: timings recorded; optional regression threshold. **Status: Not
   Started.**
8. **README/install docs** — update once published.
   Done-when: `README.md` documents `pip install`. **Status: Not Started.**

## Test Coverage Requirements
- CI itself is the deliverable; its "tests" are the existing suites plus the
  install smoke test.
- The release workflow should be dry-run-tested (e.g. build artifacts on a
  branch) before the first real tag.

## Known Gaps
- **No CI at all** — `.github/workflows` does not exist. This is the single
  largest infrastructure gap.
- **No publish path** — no PyPI project, no release automation; source-only
  install.
- **No cross-platform verification** — path handling is implemented but never
  exercised off Linux.
- **Benchmarks not gated** — they exist (P10) but nothing runs them in CI.

## Notes
- Sequencing matters: build the base CI workflow first (cheap, immediate value),
  then the cross-platform matrix, then the real-media job (after P11 lands the
  markers), and finally the release workflow.
- Use GitHub Actions OIDC "trusted publishing" for PyPI to avoid storing API
  tokens.
- This phase is rated 25% because the only pieces in place are versioning,
  CHANGELOG discipline, and the single `mcp-editor` entry point — everything
  automation-related is unbuilt.
