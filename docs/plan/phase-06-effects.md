# Phase 6 — Effects Engine

## Status
In Progress — 72%

## Goal
Move from basic clip assembly to stylized editing grammar. Provide composable
FFmpeg filter builders for speed ramps, punch zooms, hard cuts, platform
reframing, and motion effects, stored per-clip and composed into a single `-vf`
chain at render time in a fixed, predictable order.

## Depends On
Phase 3 (Timeline) for the clips effects attach to; Phase 5 (Render) bakes the
filters into output.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `apply_speed_ramp` | Playback speed multiplier (audio-aware via atempo) | ✓ Done | `effects.py` |
| `apply_zoom_punch` | Scale + crop punch-zoom | ✓ Done | `effects.py` |
| `apply_smash_cut` | Hard cut (remove transition between clips) | ✓ Done | `effects.py` |
| `apply_reframe` | Crop with center offset for platform reframing | ✓ Done | `effects.py` |
| `apply_motion_effects` | Apply multiple effects in one call | ✓ Done | `effects.py` |
| `remove_clip_effect` | Remove an effect by type | ✓ Done | `effects.py` |
| `build_clip_vf()` / `build_clip_af()` | Compose per-clip video/audio filter chains | ✓ Done | The composition core |

## Acceptance Criteria
- [x] Effects are stored on `TimelineClip.effects: list[ClipEffect]` and composed by `build_clip_vf()` at render time.
- [x] The filter chain is built in the fixed order: **reframe → zoom_punch → speed_ramp → motion_blur → grade → platform scale/crop (last)**.
- [x] `apply_speed_ramp` adjusts audio tempo (`atempo`) consistently with the video `setpts` change.
- [x] `remove_clip_effect` removes only the named effect type and leaves others intact.
- [x] `apply_motion_effects` composes multiple effects without duplicating or reordering them incorrectly.
- [ ] Each effect produces the **visually correct result on real footage** (e.g. zoom_punch actually zooms and re-crops to frame). **(blocked on P11 golden media)**
- [ ] Speed ramp audio stays in sync with video on a real render. **(unverified)**

## Implementation Tasks

1. **Filter composition core** — `effects.py: build_clip_vf()`, `build_clip_af()`.
   Done-when: composes stored `ClipEffect`s into ordered `-vf`/`-af` strings
   following the fixed pipeline order. **Status: Done.**
2. **Speed ramp** — `apply_speed_ramp()`.
   Done-when: `setpts` for video + matching `atempo` for audio; covered by unit
   test. **Status: Done.**
3. **Zoom punch** — `apply_zoom_punch()`.
   Done-when: scale-up + center crop preserves output dimensions. **Status:
   Done.**
4. **Reframe** — `apply_reframe()`.
   Done-when: crop with configurable center offset for vertical/square reframing.
   **Status: Done.**
5. **Smash cut** — `apply_smash_cut()`.
   Done-when: removes any transition between two clips for a hard cut. **Status:
   Done.**
6. **Batch + remove** — `apply_motion_effects()`, `remove_clip_effect()`.
   Done-when: batch apply and targeted removal both round-trip correctly.
   **Status: Done.**
7. **Visual verification** — *gating task*.
   Done-when: each effect verified on a real clip (the rendered frame matches
   intent). **Status: Not Started — owned with P11.**

## Test Coverage Requirements
- Unit tests: `test_effects.py` (**18** — strong) covering filter-string
  construction, ordering, batch apply, and removal. **Present and solid.**
- Integration tests: real-render verification that each effect changes the
  output as intended (e.g. probe confirms speed change; visual check for zoom).
  **Missing — owned by P11.**
- Edge cases needed: stacking all effects on one clip; speed_ramp of 1.0 (no-op);
  removing an effect that isn't present; reframe offset out of bounds.
  **Largely covered by the 18 unit tests; confirm the out-of-bounds case.**

## Known Gaps
- **No real-footage visual verification.** The filter *strings* are well-tested;
  whether they *look right* is unverified. This caps the phase at 72% despite
  strong unit coverage.
- The original roadmap listed whip/glitch transitions and freeze frames as
  effects-engine candidates; these are **not implemented**. Out of MVP scope but
  noted for completeness.
- FFmpeg filter parameters are not documented for tuning (a Phase 6 doc gap).

## Notes
- This is one of the better-tested phases (18 unit tests). The gap is purely
  real-media confirmation, not missing logic.
- The fixed pipeline order is an architectural invariant (see `CLAUDE.md` and
  `MASTER_PLAN.md` principle 6). Do not reorder; downstream grading assumes
  effects are already applied when the LUT/eq stage runs.
