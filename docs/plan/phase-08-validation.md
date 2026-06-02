# Phase 8 — Self-Validation Gate

## Status
In Progress — 88%

## Goal
Prevent silent bad exports. Before any render is reported as complete, verify it
exists and is playable, matches expected duration/resolution/FPS, has audio
unless intentionally muted, and is not fully black, unexpectedly silent, or
frozen. Validate the whole delivery package (all platforms + OTIO + manifest)
as the final quality gate.

## Depends On
Phase 5 (Render) produces the outputs this phase inspects; consumed by Phase 9
(Workflow) and Phase 11 (Integration tests).

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `validate_output` | Full render checks: exists, probe, video, resolution, fps, duration, black, silence, frozen | ✓ Done | `validation.py` |
| `validate_audio` | Audio-specific checks | ✓ Done | `validation.py` |
| `validate_platform_outputs` | Validate all platform outputs in the manifest | ✓ Done | `validation.py` |
| `validate_delivery_package` | Full delivery gate (all platforms rendered + OTIO exists + outputs valid + manifest complete) | ✓ Done | `validation.py` |
| `_check_fps` / `_check_not_black` / `_check_not_silent` / `_check_not_frozen` | Individual check primitives | ✓ Done | `validation.py` |

## Acceptance Criteria
- [x] `validate_output` returns a structured pass/fail per check (exists, playable, resolution, fps, duration, not-black, not-silent, not-frozen).
- [x] Resolution checks compare against the `Platform` enum target for the output.
- [x] Duration check compares rendered duration against the timeline's expected duration within a tolerance.
- [x] `validate_audio` flags missing audio unless the project is intentionally muted.
- [x] `validate_delivery_package` fails if any declared platform is missing, the OTIO export is absent, or the manifest doesn't match rendered outputs.
- [ ] The black/silence/frozen detectors **correctly reject a genuinely bad real render** and **pass a good one** (true-positive and true-negative confirmed on real media). **(blocked on P11 golden media)**

## Implementation Tasks

1. **Primitive checks** — `_check_fps`, `_check_not_black`, `_check_not_silent`, `_check_not_frozen`.
   Done-when: each parses the relevant FFmpeg/ffprobe signal and returns a
   boolean + detail. **Status: Done.**
2. **Output validator** — `validate_output()`.
   Done-when: aggregates all checks into a structured report. **Status: Done.**
3. **Audio validator** — `validate_audio()`.
   Done-when: detects missing/silent audio with a mute override. **Status:
   Done.**
4. **Platform sweep** — `validate_platform_outputs()`.
   Done-when: runs `validate_output` across every declared platform. **Status:
   Done.**
5. **Delivery gate** — `validate_delivery_package()`.
   Done-when: confirms all platforms + OTIO + manifest consistency. **Status:
   Done.**
6. **Real-render true/false-positive proof** — *gating task*.
   Done-when: a known-bad fixture (black/silent/frozen) is rejected and a
   known-good one passes. **Status: Not Started — owned with P11.**

## Test Coverage Requirements
- Unit tests: `test_validation_phase8.py` (**24** — strong) + `test_validation.py`
  (1) covering fps, duration, black, silence, freeze, and the delivery gate with
  monkeypatched probe signals. **Present and solid.**
- Integration tests: feed the detectors a real black/silent/frozen clip and a
  real good clip; assert correct verdicts. **Missing — owned by P11.**
- Edge cases needed: intentionally-muted project; near-tolerance duration; brief
  legitimate black frame (fade-in) not tripping the black detector. **Confirm
  these among the 24 tests; add the fade-in case if absent.**

## Known Gaps
- **Detector accuracy unproven on real media** — the checks are well-tested
  against synthetic signals, but their thresholds (how black is "black", how
  long silence must run, freeze sensitivity) have never been tuned against real
  footage. This is the only thing keeping the phase below ~95%.
- **No color-space, bitrate, or A/V-sync validation** — the original roadmap's
  more advanced checks are out of MVP scope; listed for completeness.

## Notes
- This is the most mature phase after Foundation (88%). It is also the phase that
  *defines* whether the MVP can be trusted: MVP criterion 5 lives here.
- Threshold tuning is the real remaining work and can only happen once P11
  supplies real good/bad fixtures.
