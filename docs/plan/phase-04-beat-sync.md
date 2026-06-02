# Phase 4 — Beat Sync & Edit Planning

## Status
In Progress — 40%

## Goal
Automatically plan a coherent rough cut from music and footage analysis: detect
tempo and beats with librosa, derive cut points, match clip lengths to beat
intervals, and emit a deterministic `BeatEditPlan` the agent can apply to a
timeline. This is what lets the agent produce a rhythmically-aware edit instead
of arbitrary cuts. It is the **least mature** core phase.

## Depends On
Phase 2 (Media Inspection) for footage metadata; Phase 3 (Timeline) as the
target the plan is applied to.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `analyze_beats` | librosa beat + tempo detection | ⚠ Partial | Works on steady tempo; no real-audio verification |
| `suggest_cut_points` | Beat-driven cut planning with style presets | ⚠ Partial | Deterministic grid; style multipliers in `STYLE_BEAT_MULTIPLIERS` |
| `plan_beat_synced_edit` | Deterministic beat-synced edit plan | ⚠ Partial | Emits `BeatEditPlan` |
| `apply_edit_plan` | Apply plan to timeline + export OTIO | ✓ Done | Bridges to Phase 3 |
| `validate_timeline` | (shared with Phase 3) | ✓ Done | Counted in P3 |

## Acceptance Criteria
- [x] `analyze_beats` returns tempo (BPM) and an ordered list of beat times for a given track.
- [x] `suggest_cut_points` maps beats to a cut grid modulated by pacing style (slow/medium/fast/trailer/social/documentary).
- [x] `plan_beat_synced_edit` produces a `BeatEditPlan` whose clip durations sum to ~target duration and align to beat intervals.
- [x] The same music + same footage + same style produces the **identical** plan (determinism).
- [x] Beat detection test written: `test_beat_detection_tempo_accuracy` — 120 BPM click-track fixture via P11; tolerance ±10 BPM (accounts for librosa half/double-tempo detection). Runs in CI under `realmedia` marker.
- [ ] Graceful, documented behavior on **variable-tempo / ambient / orchestral** tracks (currently undefined). **(not implemented)**

## Implementation Tasks

1. **Beat analysis** — `beat_sync.py: analyze_beats()`.
   Done-when: librosa `beat_track` wrapped; returns BPM + beat times; verified
   against a known-BPM clip within ±2 BPM. **Status: Partial — implemented, not
   verified on real audio.**
2. **Cut-point planner** — `beat_sync.py: suggest_cut_points()` + `STYLE_BEAT_MULTIPLIERS`.
   Done-when: deterministic grid per style; documented multiplier table.
   **Status: Done (logic) / multipliers undocumented in `docs/`.**
3. **Edit-plan builder** — `beat_sync.py: plan_beat_synced_edit()`, `plan_beat_synced_edit_for_manifest()`.
   Done-when: emits `BeatEditPlan` with clips matched to beats and total ≈
   target. **Status: Done (logic).**
4. **Apply plan** — `beat_sync.py: apply_edit_plan()`.
   Done-when: writes plan into the timeline and exports OTIO. **Status: Done.**
5. **Variable-tempo handling** — *new work*.
   Done-when: detect low beat-confidence / non-steady tempo and either fall back
   to a fixed BPM grid with a warning or document the limitation explicitly in
   the tool return. **Status: Not Started.**
6. **Energy-aware pacing** — *new work* (the original plan mentioned
   `analyze_music_energy` / energy peaks; not implemented).
   Done-when: optional energy curve influences cut density. **Status: Not
   Started — out of MVP scope, listed for completeness.**

## Test Coverage Requirements
- Unit tests: `test_beat_sync.py` (5) — analysis, cut suggestion, plan building,
  determinism, apply. **Present** but all on synthetic/monkeypatched audio.
- Integration tests: real-audio BPM verification against a fixture with known
  tempo. **Missing — owned by P11.**
- Edge cases needed: silence/no detectable beat; very short track; tempo far
  outside typical range; target duration longer than available footage.
  **Not covered.**

## Known Gaps
- **No real-audio verification** — librosa output correctness is unproven in CI.
- **Variable-tempo tracks unhandled** — explicitly an MVP-acceptance gap
  (criterion in this file). MVP only requires steady-tempo success, but the
  failure mode on non-steady tracks must at least be defined and tested.
- **Style multiplier table is undocumented** in `docs/tools.md`.
- `analyze_music_energy` from the original roadmap was never built; energy-peak
  driven pacing does not exist.

## Notes
- This is the lowest-confidence core phase. The risk is not "is it built" (it is)
  but "does librosa give us musically correct cuts on real tracks" — unknown
  until P11 supplies golden audio.
- Determinism is a hard requirement: librosa must be pinned and seeded so the
  same inputs always yield the same plan. Verify pinning during P12 release prep.
