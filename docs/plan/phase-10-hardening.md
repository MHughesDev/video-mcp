# Phase 10 — Hardening & Scale

## Status
In Progress — 78%

## Goal
Move from prototype to reliable local production system: structured logging,
retry behavior, deterministic IDs, cross-platform path handling, a benchmark
suite, and documentation for every tool. This is a cross-cutting phase that
reinforces all the others rather than adding pipeline features.

## Depends On
The core pipeline (Phases 1–9) must exist to be hardened. Hardening work is
ongoing and parallel.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `logging.py` (`ProjectLogger`) | Per-project append-only JSON logs; never raises on `OSError` | ✓ Done | `info/timed/warning/error` |
| `get_project_logs` | Structured log summary + last 20 records | ✓ Done | Also surfaced in Phase 9 |
| Retry/backoff | FFmpeg retried up to 2× (1s/2s) on transient failure | ✓ Done | `render.py: _run_command` |
| Per-command timing | `RenderManifest.timing` records each command's duration | ✓ Done | `render.py` |
| `deterministic_project_id()` | Stable IDs, re-run reuses the same dir | ✓ Done | `schemas.py` |
| `posix_path()` | Cross-platform POSIX path normalization | ✓ Done | `schemas.py` |
| `scripts/benchmark.py` | Pure-Python benchmark suite (no FFmpeg) | ✓ Done | filter build, serialization, beat plan, timeline, grading |
| `docs/tools.md` | Full 53-tool reference (714 lines) | ✓ Done | Keep in sync per `CLAUDE.md` |

## Acceptance Criteria
- [x] Every project writes append-only JSON log lines under `data/projects/{id}/logs/`, and logging never raises (OSError swallowed).
- [x] `get_project_logs` returns a summary with error/warning counts and recent records.
- [x] FFmpeg transient failures retry up to 2× with 1s/2s backoff before surfacing a structured error.
- [x] Re-running the same project (same name + input dir) reuses the same project directory via deterministic IDs.
- [x] All manifest paths are POSIX on every OS.
- [x] `scripts/benchmark.py` runs without FFmpeg or real media and reports timings for the hot paths.
- [x] `docs/tools.md` documents all 53 tools.
- [ ] Path handling and the full suite are **verified green on Windows and macOS in CI**. **(blocked on P12 CI)**
- [ ] Large-file (4K+) and long-timeline (>1h) behavior is characterized (even if only documented as a limit). **(not done)**

## Implementation Tasks

1. **Structured logging** — `logging.py: ProjectLogger`.
   Done-when: append-only JSONL, OSError-safe, with `info/timed/warning/error`.
   **Status: Done.**
2. **Retry/backoff** — `render.py: _run_command`.
   Done-when: 2 retries, 1s/2s, structured final error. **Status: Done.**
3. **Per-command timing** — `execute_render_manifest`.
   Done-when: durations recorded in `RenderManifest.timing` and serialized.
   **Status: Done.**
4. **Determinism + paths** — `deterministic_project_id()`, `posix_path()`.
   Done-when: covered by `test_hardening.py`. **Status: Done.**
5. **Benchmark suite** — `scripts/benchmark.py`.
   Done-when: runs offline; `--json`/`--runs` flags. **Status: Done** (note: no
   `mcp-editor-bench` console entry point exists — it runs via `python
   scripts/benchmark.py`).
6. **Per-tool timing/observability** — *partial work*.
   Done-when: every MCP tool emits a timed log record. **Status: Partial — render
   is timed; not all tools log timing.**
7. **Large-file handling** — *new work*.
   Done-when: documented limits and/or streaming/segmented handling for 4K+ and
   long timelines. **Status: Not Started.**
8. **Cross-platform CI** — *handoff to P12*.
   Done-when: suite green on Linux/macOS/Windows. **Status: Not Started.**
9. **Documentation-accuracy discipline** — *new work; pairs with P14*.
   Done-when: a cheap, introspection-based check keeps `docs/tools.md` and the
   plan's tool counts in sync with the registered `@app.tool` set, so they
   cannot silently drift. The check itself is built and CI-wired in Phase 14
   (contract-drift guard); this item is the hardening *principle* that no
   human-maintained tool list is trusted without an automated guard behind it.
   **Status: Not Started — see Phase 14.**

## Test Coverage Requirements
- Unit tests: `test_hardening.py` (**24** — strong) covering error handling,
  path normalization, and deterministic IDs. **Present and solid.**
- Benchmarks: `scripts/benchmark.py` serves as a performance regression guard
  (not wired into CI yet — see P12).
- Edge cases needed: log dir unwritable (must not crash); retry exhaustion path;
  ID collision avoidance. **Covered by the 24 hardening tests.**

## Known Gaps
- **Per-tool timing is incomplete** — only the render path records timing
  comprehensively; other tools log events but not durations.
- **No large-file/long-timeline characterization** — behavior above 1080p / 1h
  is unknown and undocumented.
- **Benchmarks aren't CI-gated** — they exist but nothing fails a build on
  regression (deferred to P12).
- **No `mcp-editor-bench` entry point** despite earlier references; benchmarks
  run only via the script path.
- **No guard against docs/tool drift** — `docs/tools.md` and generated tool
  summaries have drifted from the real `@app.tool` registrations in practice
  (phantom and omitted tool names). The fix lives in Phase 14; flagged here as a
  hardening gap because it is a reliability/contract concern, not a feature.

## Notes
- This phase is intentionally cross-cutting; its percentage reflects breadth of
  hardening already in place (logging, retry, determinism, paths, benchmarks,
  docs) against the remaining scale/observability work.
- The cross-platform and benchmark-CI items are deliberately handed to Phase 12,
  where the CI infrastructure they need will be built.
