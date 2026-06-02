# Phase 3 — Timeline & OTIO Core

## Status
In Progress — 65%

## Goal
Build the non-rendering edit model: a frame-accurate timeline of clips, trims,
splits, moves, and transitions that can be validated and exported to
OpenTimelineIO. This is the editorial "source of truth" that the render engine
later turns into video. Producing a valid timeline must always precede
producing rendered video.

## Depends On
Phase 1 (Foundation) for schemas; Phase 2 (Media Inspection) for the asset
metadata that clips reference.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `create_project` | Build a `ProjectManifest` from local assets | ✓ Done | `workflow.py` / `projects.py` |
| `inspect_project` | Full project state inspection | ✓ Done | `inspection.py` |
| `create_timeline` | Simple sequential OTIO timeline | ✓ Done | `timeline.py` |
| `add_clip` | Append/insert a clip | ✓ Done | `timeline.py` / `timeline_ops.py` |
| `trim_clip` | Trim a clip by ID or index | ✓ Done | `timeline.py` |
| `split_clip` | Split a clip at a timecode | ✓ Done | `timeline.py` |
| `move_clip` | Reorder clips | ✓ Done | `timeline.py` |
| `add_transition` | Add/replace a transition between clips | ✓ Done | `timeline.py` |
| `export_timeline` | Export timeline to a `.otio` file | ⚠ Partial | Writes OTIO; not verified to import into a third-party NLE |
| `validate_timeline` | Validate missing media, overlaps, durations | ✓ Done | `timeline.py` |

## Acceptance Criteria
- [x] `create_timeline` builds a sequential timeline from manifest assets with frame-accurate start/duration per clip.
- [x] `add_clip` / `trim_clip` / `split_clip` / `move_clip` mutate the timeline correctly and persist to the manifest.
- [x] `add_transition` records a transition referencing valid from/to clip IDs; replacing an existing transition is idempotent.
- [x] `validate_timeline` flags missing source media, overlapping clips, zero/negative durations, and out-of-range trims.
- [x] `export_timeline` writes a `.otio` file to `data/projects/{id}/timeline_{platform}.otio`.
- [ ] The exported `.otio` **imports cleanly into a standard NLE** (e.g. via `otioview` or Resolve/Premiere OTIO import) with clips at the correct timecodes. **(MVP criterion 6 — unverified)**

## Implementation Tasks

1. **Timeline model** — `timeline.py: make_simple_timeline_plan()`, `timeline_duration()`, `find_clip_index()`.
   Done-when: a `TimelinePlan` of `TimelineClip`s with accurate cumulative
   timing. **Status: Done.**
2. **Clip operations** — `add_clip`, `trim_clip`, `split_clip`, `move_clip`.
   Done-when: each mutates the plan, revalidates timing, and persists. Covered
   by unit tests. **Status: Done.**
3. **Transitions** — `add_transition()`.
   Done-when: stores `TimelineTransition`; rejects dangling clip refs.
   **Status: Done.**
4. **Validation** — `validate_timeline()`.
   Done-when: returns structured issues for missing media/overlap/bad-duration.
   **Status: Done.**
5. **OTIO export** — `timeline.py: export_otio()`.
   Done-when: writes a `.otio` that opens in a third-party tool with correct
   clip ranges. **Status: Partial — file is written; third-party import is
   unverified. This is the gap holding the phase below 80%.**
6. **MCP wrappers** — `timeline_ops.py`.
   Done-when: thin project-scoped wrappers for each op return `ok`-shaped dicts.
   **Status: Done.**

## Test Coverage Requirements
- Unit tests: `test_timeline.py` (5), `test_timeline_ops.py` (1). Cover
  construction, clip ops, and OTIO export call path. **Present but thin** — only
  6 tests for 10 tools and the full validation matrix.
- Integration tests: `test_workflow_integration.py: TestBuildTimeline` (part of
  the 19 integration tests) exercises timeline construction within the workflow.
- Edge cases needed: split at clip boundary / at 0 / past end; move first↔last;
  trim to zero; transition between non-adjacent clips; overlapping clips
  detection. **Partially covered — expand `test_timeline.py`.**

## Known Gaps
- **OTIO round-trip is unverified.** We write `.otio` but have never confirmed a
  standard NLE imports it correctly. MVP criterion 6 depends on this.
- Clip-operation edge cases (boundary splits, zero-length trims, non-adjacent
  transitions) are under-tested relative to the number of operations.
- No multi-track timelines (single video track + music); acceptable for MVP but
  worth noting as a scope boundary.

## Notes
- Frame accuracy comes from OTIO `RationalTime`; keep all timing in OTIO's model
  rather than float seconds wherever possible to avoid drift.
- `create_project` and `inspect_project` straddle P2/P3; counted once each.
