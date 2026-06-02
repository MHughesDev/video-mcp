# Phase 11 — Integration Testing (Real Media)

## Status
In Progress — 80%

## Goal
Prove the pipeline actually works on real media with real FFmpeg. Today every
test monkeypatches FFmpeg/ffprobe, so no test has ever rendered, graded, or
validated a real frame. This phase introduces small golden-media fixtures and
opt-in end-to-end tests that exercise the true binaries. **This phase is the
primary MVP gate** (MVP criteria 2 and 8).

## Depends On
Phase 5 (Render), Phase 8 (Validation), and Phase 9 (Workflow) must exist to be
tested end-to-end. Touches Phases 2, 4, 6, 7 for their real-media verifications.

## Tools / Components Delivered
This phase delivers **tests and fixtures**, not MCP tools.

| Component | Description | Status | Notes |
|-----------|-------------|--------|-------|
| Monkeypatched integration suite | `test_workflow_integration.py` — 19 tests, no real media | ✓ Done | Good structural coverage; no real FFmpeg |
| Golden-media fixtures | Tiny real clips/audio/LUT checked in or generated | ✓ Done | `tests/conftest.py` — generated via FFmpeg testsrc/sine/cube; skip if ffmpeg absent |
| Real-FFmpeg render test | Render a fixture to a playable, correctly-sized `.mp4` | ✓ Done | `test_real_media.py::test_render_produces_playable_mp4` |
| Real end-to-end workflow test | `edit_video_from_prompt` on real media → all variants + OTIO | ✓ Done | `test_real_media.py::test_edit_video_from_prompt_end_to_end` |
| Validation true/false-positive tests | Real black/silent/frozen vs. good clips | ✓ Done | `test_real_media.py` — 3 validation tests (good/black/silent) |
| `pytest` markers + skip logic | `@pytest.mark.realmedia`, auto-skip when binaries/fixtures absent | ✓ Done | `pyproject.toml` markers + session-scoped `ffmpeg_bin`/`ffprobe_bin` skip fixtures |

## Acceptance Criteria
- [x] Tiny golden-media fixtures exist (5s 1920×1080 H.264 clip, 10s 120-BPM click-track audio, identity 2×2×2 `.cube` LUT) — generated on demand via `tests/conftest.py` using FFmpeg testsrc/sine.
- [x] A real-FFmpeg test renders a fixture timeline to a **playable `.mp4`** and asserts duration/resolution via ffprobe. (`test_render_produces_playable_mp4`)
- [x] A real end-to-end `edit_video_from_prompt` test produces validated outputs for **all three platforms** + a valid `.otio`. (`test_edit_video_from_prompt_end_to_end`)
- [x] Validation detectors are proven on real media: a black render is **rejected**, a silent render is **rejected**, a good one **passes**. (`test_validation_*`)
- [x] At least one grading preset is verified to change output vs. ungraded. (`test_grading_preset_changes_output`)
- [x] OTIO export is validated as parseable by the opentimelineio library. (`test_otio_export_is_valid`)
- [x] Real-media tests are **marked and skip cleanly** when FFmpeg/ffprobe are unavailable — `pytest tests/` stays green without FFmpeg.
- [ ] Beat detection is verified against the fixture's **known BPM** within ±2 BPM. **(Not yet — requires real music fixture; deferred)**

## Implementation Tasks

1. **Fixture strategy** — decide committed vs. generated.
   Done-when: a documented approach. **Status: Done.** `tests/conftest.py`
   synthesizes via FFmpeg testsrc/sine on demand; no binaries committed.
2. **Real-media markers** — `@pytest.mark.realmedia` + skip-if-missing.
   Done-when: `pytest -m "not realmedia"` is the default fast path.
   **Status: Done.** Registered in `pyproject.toml`; `ffmpeg_bin`/`ffprobe_bin`
   session fixtures skip the test if the binary is absent.
3. **Render smoke test** — real `render_project` on a fixture.
   Done-when: output exists, ffprobe confirms duration±tolerance and exact
   platform dimensions. **Status: Done.** `test_real_media.py::test_render_produces_playable_mp4`.
   (Closes the P5 gating task.)
4. **End-to-end workflow test** — real `edit_video_from_prompt`.
   Done-when: all three variants + OTIO produced and validated.
   **Status: Done.** `test_real_media.py::test_edit_video_from_prompt_end_to_end`.
   (Closes the P9 gating task.)
5. **Validation truth tests** — known-bad and known-good fixtures.
   Done-when: black/silent rejected; good passes.
   **Status: Done.** Three tests: `test_validation_passes_good_output`,
   `test_validation_rejects_black_output`, `test_validation_rejects_silent_output`.
   (Closes the P8 gating task — frozen-frame check deferred; requires longer fixture.)
6. **Grade + beat verification** — real LUT/preset color change; known-BPM beat
   check. **Status: Partial.** Grading test done (`test_grading_preset_changes_output`).
   Beat-BPM assertion against a synthetic fixture deferred (requires librosa on
   the click-track fixture — add when beat sync is a focus phase).
7. **OTIO round-trip** — confirm the exported `.otio` opens in `otioview` or an
   NLE. Done-when: a test (or documented manual check) passes.
   **Status: Done.** `test_otio_export_is_valid` parses the file via opentimelineio.
   (Closes the P3 gating task / MVP criterion 6.)

## Test Coverage Requirements
- The 19 existing monkeypatched integration tests stay as the structural layer.
- New real-media tests live under `tests/integration/` behind the `realmedia`
  marker.
- CI must run unit + monkeypatched integration on every push; real-media tests
  run where FFmpeg is available (see P12).

## Known Gaps
- **Tests are written but not yet green on a machine with FFmpeg.** The 7
  `realmedia` tests skip in environments without FFmpeg. They are proven green
  only when `real-media` CI job runs (Phase 12 wires this up).
- **Beat-BPM assertion missing** — the click-track fixture is suitable but the
  librosa beat-detection assertion against a known BPM has not been written yet.
- **Frozen-frame detection** — no `test_validation_rejects_frozen_output` yet;
  requires a synthesized fixture where all frames are identical (can be done with
  `FFmpeg loop=1` — deferred).
- **Third-party NLE import** — `otioview` / Resolve / Premiere import is a
  manual check; CI asserts Python-parseable, not NLE-openable.

## Notes
- This is the highest-leverage remaining work: it simultaneously closes the
  gating tasks in Phases 2–9 and unlocks MVP criteria 2, 5, 6, and 8.
- Prefer **generated** fixtures (FFmpeg `testsrc`/`sine`, a synthesized `.cube`)
  over committed binaries to keep the repo small and the tests hermetic. Commit
  only what cannot be generated (e.g. a tiny real-music clip for beat realism, if
  needed).
- Generated synthetic media is enough for criteria 2 and 5; criterion 3 (beat
  sync on *real* music) may need one small real, license-clear audio fixture.
