# Phase 12 — Release & CI/CD

## Status
In Progress — 70%

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
| CI workflow | GitHub Actions: install + lint + unit + (mocked) integration | ✓ Done | `.github/workflows/ci.yml` — Linux/macOS/Windows × py3.11/3.12 |
| Real-media CI job | Runs `realmedia`-marked tests where FFmpeg is available | ✓ Done | `real-media` job in `ci.yml` — ubuntu, installs FFmpeg, runs `-m realmedia` |
| Cross-platform matrix | Linux/macOS/Windows test runs | ✓ Done | `unit` job matrix: ubuntu/macos/windows × py3.11/3.12 |
| Benchmark CI gate | Run `scripts/benchmark.py`, flag regressions | ✓ Done | `benchmark` job in `ci.yml` — runs `--runs 1 --json` |
| Release workflow | Tag → build sdist/wheel → publish (PyPI and/or GH release) | ✓ Done | `.github/workflows/release.yml` — build → smoke-test → PyPI OIDC → GitHub Release |
| Install verification | `pip install` from artifact imports + starts the server | ✓ Done | `smoke-test` job in `release.yml` installs wheel + verifies import + console script |

## Acceptance Criteria
- [x] A CI workflow runs on every push/PR: dependency install, lint, `pytest tests/unit`, and the monkeypatched integration suite — all green. (`.github/workflows/ci.yml`)
- [x] A real-media CI job runs the `realmedia`-marked tests on a runner with FFmpeg installed. (`real-media` job — ubuntu + FFmpeg)
- [x] The test matrix runs on Linux, macOS, and Windows. (`unit` job matrix)
- [x] `scripts/benchmark.py` runs in CI and surfaces timings. (`benchmark` job)
- [x] A tagged release builds an sdist + wheel and publishes to PyPI and creates a GitHub Release. (`release.yml` on `v*` tag)
- [x] Install smoke test: `pip install wheel → import + mcp-editor console script`. (`smoke-test` job in `release.yml`)
- [x] `pyproject.toml` has MIT license, classifiers, authors, keywords — passes `twine check`. 
- [ ] PyPI project registered and first `v0.8.0` tag published. **(Only remaining gate)**
- [ ] `README.md` install instructions updated for `pip install mcp-editor`. **(Follows first publish)**

## Implementation Tasks

1. **Base CI workflow** — `.github/workflows/ci.yml`.
   Done-when: install + lint + unit + mocked-integration green on push/PR.
   **Status: Done.** `unit` job (3-OS × 2-Python matrix) in `ci.yml`.
2. **Cross-platform matrix** — add `os: [ubuntu, macos, windows]` to CI.
   Done-when: suite green on all three.
   **Status: Done.** `unit` job matrix: ubuntu-latest / macos-latest / windows-latest.
3. **Real-media job** — CI step that installs FFmpeg and runs `-m realmedia`.
   Done-when: real-media tests execute where FFmpeg is present.
   **Status: Done.** `real-media` job in `ci.yml` — `apt-get install ffmpeg` + `pytest -m realmedia`.
4. **Benchmark gate** — run `scripts/benchmark.py --json` in CI.
   Done-when: timings recorded; optional regression threshold.
   **Status: Done.** `benchmark` job in `ci.yml` — `python scripts/benchmark.py --runs 1 --json`.
5. **Release workflow** — `.github/workflows/release.yml`.
   Done-when: on tag `v*`, build sdist/wheel and publish to PyPI (trusted
   publishing) and attach to a GitHub Release.
   **Status: Done.** Build → smoke-test → publish-pypi (OIDC) → github-release;
   `twine check` gate included.
6. **Packaging audit** — confirm `pyproject.toml` metadata.
   Done-when: `python -m build` produces a clean wheel/sdist with correct metadata.
   **Status: Done.** Added classifiers, license, authors, keywords; passes `twine check`.
7. **Install smoke test** — CI job that `pip install`s the built wheel.
   Done-when: import + `mcp-editor` console script succeeds.
   **Status: Done.** `smoke-test` job in `release.yml`.
8. **PyPI registration + first tag** — *new work*.
   Done-when: `mcp-editor` project exists on PyPI; `v0.8.0` tag pushed;
   release workflow runs end-to-end. **Status: Not Started.**
9. **README/install docs** — update once published.
   Done-when: `README.md` documents `pip install mcp-editor`. **Status: Not Started.**

## Test Coverage Requirements
- CI itself is the deliverable; its "tests" are the existing suites plus the
  install smoke test.
- The release workflow should be dry-run-tested (e.g. build artifacts on a
  branch) before the first real tag.

## Known Gaps
- **No PyPI project yet** — the release workflow is written but cannot run until
  `mcp-editor` is registered on PyPI and the GitHub environment `pypi` is
  configured with OIDC trusted publishing. The first `v0.8.0` tag push will
  complete MVP criterion 9.
- **README** — install instructions still say "from source"; needs a single
  `pip install mcp-editor` line once the package is live on PyPI.

## Notes
- Sequencing matters: build the base CI workflow first (cheap, immediate value),
  then the cross-platform matrix, then the real-media job (after P11 lands the
  markers), and finally the release workflow.
- Use GitHub Actions OIDC "trusted publishing" for PyPI to avoid storing API
  tokens.
- This phase is rated 25% because the only pieces in place are versioning,
  CHANGELOG discipline, and the single `mcp-editor` entry point — everything
  automation-related is unbuilt.
