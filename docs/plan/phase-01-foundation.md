# Phase 1 — Foundation & Contracts

## Status
Complete — 100%

## Goal
Establish the stable internal data contracts that every other phase depends on:
the Pydantic schema layer, the structured error contract, deterministic project
IDs, cross-platform path handling, workspace/config resolution, and manifest
persistence. Nothing in the editing pipeline can be built reliably until these
contracts are frozen, because every downstream module imports them.

## Depends On
Nothing. This is the root of the dependency graph.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `schemas.py` | All Pydantic models + utility functions (585 LOC) | ✓ Done | Platform enum, MediaProbe, TimelineClip, ProjectManifest, RenderManifest, BeatEditPlan, etc. |
| `diagnostics.py` | Structured error contract (142 LOC) | ✓ Done | `McpEditorError`, `failed_tool_result()`, issue constructors |
| `config.py` | Workspace root + data dir resolution (55 LOC) | ✓ Done | `workspace_root()`, `data_dir()`, `projects_dir()`, etc. |
| `projects.py` | Manifest load/save + dir helpers (39 LOC) | ✓ Done | `load_manifest()`, `save_manifest()`, `slugify()` |
| `deterministic_project_id()` | Stable 12-char SHA-256 project ID | ✓ Done | In `schemas.py`; replaces `uuid4()` |
| `as_path()` / `posix_path()` | Path normalization helpers | ✓ Done | expanduser+resolve / POSIX forward slashes |

## Acceptance Criteria
- [x] Every tool return value is a dict with at least `ok: bool`.
- [x] `_error(exc)` produces `{ok: false, error: {code, message, suggested_fix, details}}` and is the only failure path tool handlers use.
- [x] `deterministic_project_id(name, input_dir)` returns the same 12-char hex for the same inputs and differs for different inputs; no code path uses `uuid4()` for project IDs.
- [x] All manifest-stored paths are POSIX (forward slashes) regardless of host OS, via `posix_path()`.
- [x] `Platform` enum is the only source of aspect-ratio/dimension truth: widescreen=1920×1080, vertical=1080×1920, square=1080×1080.
- [x] A `ProjectManifest` round-trips through `save_manifest`/`load_manifest` without data loss.

## Implementation Tasks

1. **Schema layer** — `schemas.py`. Define all data contracts.
   Definition of done: models for Platform, MediaStream, MediaProbe, ClipEffect,
   TimelineClip, TimelineTransition, TimelinePlan, EditPlanClip, BeatEditPlan,
   RenderedOutput, RenderCommand, RenderManifest, ProjectManifest exist and
   validate. **Status: Done.**
2. **Error contract** — `diagnostics.py`. Single structured failure shape.
   Definition of done: `failed_tool_result(exc)` returns the canonical error
   dict; named issue constructors exist for common cases (missing_dependency,
   media_not_found, project_not_found, no_video_assets, etc.). **Status: Done.**
3. **Deterministic IDs** — `deterministic_project_id()`.
   Definition of done: SHA-256(name+input_dir)[:12]; covered by a unit test
   asserting stability and uniqueness. **Status: Done.**
4. **Path handling** — `as_path()` / `posix_path()`.
   Definition of done: round-trip tests confirm POSIX output on all inputs.
   **Status: Done.**
5. **Config resolution** — `config.py`.
   Definition of done: workspace root honors `MCP_EDITOR_ROOT`; all data
   subdirs resolve relative to it. **Status: Done.**
6. **Manifest persistence** — `projects.py`.
   Definition of done: save/load round-trip test passes. **Status: Done.**

## Test Coverage Requirements
- Unit tests: `test_schemas.py` (2), `test_diagnostics.py` (4),
  `test_projects.py` (1), and `test_hardening.py` (24, covers IDs + path
  normalization + error handling). **Present and passing.**
- Integration tests: workspace isolation via `monkeypatch.setenv("MCP_EDITOR_ROOT", tmp_path)` — exercised across the integration suite. **Present.**
- Edge cases: bad/missing manifest fields, non-existent input dirs, mixed-
  separator paths. **Covered in `test_hardening.py`.**

## Known Gaps
- `test_schemas.py` (2 tests) and `test_projects.py` (1 test) are thin relative
  to the size of the schema surface. The schemas are exercised transitively by
  other suites, but direct edge-case coverage of the richer models
  (`RenderManifest`, `ProjectManifest`) is light. Low priority — these contracts
  are stable.

## Notes
- This phase is the only one rated 100%. Treat its contracts as frozen: changing
  a schema field or the error shape is a breaking change that ripples through
  every other phase and `docs/tools.md`.
- The `VideoDoc`/`ImageDoc`/`AudioDoc` comprehension models also live in
  `schemas.py` but belong to Phase 13; they are listed there.
