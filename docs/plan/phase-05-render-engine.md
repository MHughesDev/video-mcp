# Phase 5 — FFmpeg Render Engine

## Status
In Progress — 60%

## Goal
Turn validated timelines into actual video files. Convert timeline operations
into FFmpeg command plans, execute them with retry/backoff, render 16:9 / 9:16 /
1:1 variants with correct scaling/cropping/padding and audio mixing, and write
render manifests and logs. This is the **spine of the MVP** — every other phase
either feeds this or verifies its output.

## Depends On
Phase 3 (Timeline) for the edit model. Consumed by Phases 6, 7, 8, 9.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `plan_render` | Dry-run FFmpeg command planning | ✓ Done | `render.py: plan_render_timeline()` |
| `render_project` | Render timeline to MP4 (single platform) | ⚠ Partial | Logic complete; never run against real FFmpeg |
| `render_platform_variant` | Render a single declared platform | ⚠ Partial | Same — unverified on real media |
| `render_all_variants` | Render all declared platforms | ⚠ Partial | Same — unverified on real media |
| `RENDER_PROFILES` | preview / standard / high profiles | ✓ Done | In `render.py` |
| `_run_command()` | Subprocess exec with retry/backoff | ✓ Done | 2 retries, 1s/2s |

## Acceptance Criteria
- [x] `plan_render` returns a `RenderManifest` listing every FFmpeg command, segment paths, concat file, expected duration, and target dimensions — without executing anything (dry-run).
- [x] Render manifests and per-command timing are written to `data/projects/{id}/render_{platform}.json`.
- [x] `_run_command` retries transient FFmpeg failures up to 2× (1s, 2s) and surfaces a structured error on final failure.
- [x] Platform dimensions are driven solely by the `Platform` enum (1920×1080 / 1080×1920 / 1080×1080).
- [ ] `render_project` produces a **playable `.mp4`** from real 1080p footage with correct duration and dimensions. **(MVP criteria 1–2 — unverified)**
- [ ] `render_all_variants` produces all three platform outputs with correct per-platform scaling/cropping/padding, verified visually or by probe. **(unverified)**
- [ ] Audio is correctly mixed/attached (music bed + any clip audio) in the rendered output. **(unverified)**

## Implementation Tasks

1. **Command planner** — `render.py: plan_render_timeline()`.
   Done-when: emits an ordered `RenderManifest` (segment renders → concat →
   platform scale/crop → mux). Dry-run produces no files. **Status: Done.**
2. **Executor** — `render.py: execute_render_manifest()`, `_run_command()`.
   Done-when: runs commands in order with retry/backoff and per-command timing;
   writes the manifest. **Status: Done (code) — unverified on real FFmpeg.**
3. **Profiles** — `RENDER_PROFILES` (preview/standard/high).
   Done-when: profile selects codec/bitrate/preset params. **Status: Done.**
4. **Platform variants** — `render_platform_variant`, `render_all_variants`.
   Done-when: each platform scales/crops/pads correctly to its enum dimensions.
   **Status: Partial — planning done, real output unverified.**
5. **Audio path** — music bed mux + clip audio handling.
   Done-when: rendered file has the expected audio track(s) at correct levels.
   **Status: Partial — command exists; real mux unverified.**
6. **Real-media smoke render** — *gating task for MVP*.
   Done-when: a 1080p fixture renders to a playable, correctly-dimensioned
   `.mp4` under real FFmpeg. **Status: Not Started — owned jointly with P11.**

## Test Coverage Requirements
- Unit tests: `test_render.py` (4), `test_render_workflow.py` (2) — manifest
  planning and execution with monkeypatched `_run_command` /
  `execute_render_manifest`. **Present.**
- Integration tests: a **real-FFmpeg** render of a short fixture asserting the
  output exists, is playable, and matches target duration/dimensions.
  **Missing — the central P11 deliverable.**
- Edge cases needed: single-clip timeline; missing source mid-render; concat of
  differing resolutions; zero-audio timeline; profile selection.
  **Mostly uncovered.**

## Known Gaps
- **No real frame has ever been rendered in CI.** The entire executor path is
  monkeypatched. This is the largest single risk to the MVP and the reason a
  feature-complete engine is scored only 60%.
- **No 4K/large-file or long-timeline handling** — assumed HD; untested above.
- **No checkpoint/resume** — a mid-render crash restarts the whole job; only
  transient single-command retry exists.
- **No cross-project segment cache reuse** — segments cache per project under
  `segments/{16x9,9x16,1x1}/` but there is no invalidation or dedup logic.

## Notes
- The plan/execute split (dry-run `plan_render` vs. `execute_render_manifest`)
  is deliberate and valuable: it lets the agent inspect the FFmpeg plan before
  committing compute. Preserve this separation.
- Keep all command construction in `render.py`/`effects.py`/`grading.py`; never
  build FFmpeg strings inside `server.py`.
