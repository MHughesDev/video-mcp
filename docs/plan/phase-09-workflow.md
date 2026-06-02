# Phase 9 — End-to-End Agent Workflow

## Status
In Progress — 80%

## Goal
Tie every phase together into a single autonomous tool. A calling agent invokes
`edit_video_from_prompt` with a natural-language request and receives finished,
validated video plus an OTIO timeline. This is the product's headline capability;
everything else exists to make this one call trustworthy.

## Depends On
Phases 4 (Beat Sync), 5 (Render), 6 (Effects), 7 (Grading), 8 (Validation) — the
workflow orchestrates all of them.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `edit_video_from_prompt` | Full 9-step pipeline orchestrator | ⚠ Partial | All steps wired; never run end-to-end on real media |
| `get_workflow_status` | Pipeline-stage checklist with `next_step` hint | ✓ Done | `workflow.py` |
| `get_project_logs` | Project log summary + recent records | ✓ Done | `logging.py` (also Phase 10) |
| `_infer_style()` / `_infer_grade()` | Prompt-keyword inference for pacing/grade | ✓ Done | Longest-match wins |

## The 9-Step Pipeline
1. Scan assets → 2. Probe/analyze footage → 3. Analyze music (beats) →
4. Build edit plan → 5. Create timeline → 6. Apply effects + grading →
7. Render variants → 8. Export OTIO → 9. Validate delivery → return manifest.

## Acceptance Criteria
- [x] `edit_video_from_prompt` accepts a prompt plus optional `style` and `grade` overrides and runs all 9 steps in order.
- [x] Prompt keywords infer pacing style and grading preset (longest-match wins) when not explicitly overridden.
- [x] Each step's failure is caught and returned as a structured error with the failing stage identified (no unhandled exceptions escape).
- [x] `get_workflow_status` reports which stages are complete and the recommended `next_step`.
- [ ] A single call with **real footage + real music + a prompt** returns validated `.mp4`s for all three platforms + a valid `.otio`. **(MVP criterion 1 — unverified end-to-end on real media)**
- [ ] The returned delivery manifest accurately reflects the real rendered/validated outputs. **(unverified on real media)**

## Implementation Tasks

1. **Orchestrator** — `workflow.py: edit_video_from_prompt()`.
   Done-when: runs all 9 steps, threading the project manifest through; returns a
   delivery manifest. **Status: Done (wired) — never executed end-to-end on real
   media.**
2. **Prompt inference** — `_infer_style()`, `_infer_grade()`.
   Done-when: keyword tables map prompt text to a pacing style and grade preset;
   explicit params override. **Status: Done.**
3. **Project lifecycle helpers** — `create_project()`,
   `build_timeline_for_project()`, `render_and_validate_project()`.
   Done-when: reusable building blocks the orchestrator composes. **Status:
   Done.**
4. **Status/observability** — `get_workflow_status()`, `get_project_logs()`.
   Done-when: stage checklist + `next_step`; log summary with error/warning
   counts. **Status: Done.**
5. **Real end-to-end run** — *gating task for MVP*.
   Done-when: one real-media invocation produces all three validated outputs +
   OTIO and a correct delivery manifest. **Status: Not Started — owned with
   P11.**

## Test Coverage Requirements
- Unit tests: `test_workflow_phase9.py` (**21** — strong) covering style/grade
  inference, step sequencing, error propagation, and workflow status with
  monkeypatched render/validate. **Present and solid.**
- Integration tests: `test_workflow_integration.py` (19, monkeypatched FFmpeg)
  exercises create-project and build-timeline paths. **Present** but not real
  media.
- Edge cases needed: prompt with no recognizable keywords (defaults applied);
  failure at each individual stage surfaces the correct stage; no-asset project
  fails cleanly. **Mostly covered by the 21 unit tests.**

## Known Gaps
- **Never run end-to-end on real media.** Every step is individually wired and
  unit-tested, but the full chain has only ever run with FFmpeg monkeypatched.
  MVP criterion 1 cannot be claimed until P11 proves a real run.
- **No partial-failure recovery / resume** — if step 7 (render) fails midway, the
  whole call fails; there is no resume from a completed earlier stage.
- **Inference is keyword-only** — acceptable (the agent supplies creativity and
  can override), but the keyword tables are not documented in `docs/tools.md`.

## Notes
- Strong unit coverage (21 tests) makes this phase look healthy, and structurally
  it is. The 80% reflects that the *integration* of the steps is unproven on real
  media — which is precisely what the MVP is about.
- Keep the orchestrator a pure composition of phase functions; do not let it grow
  business logic that belongs in the phase modules.
