# Phase 2 — Media Inspection

## Status
In Progress — 65%

## Goal
Give the calling agent everything it needs to understand source footage before
making any edit decision: durations, FPS, resolution, codecs, audio streams,
scene boundaries, and representative thumbnails. This is the agent's "eyes" on
the raw material. Without trustworthy inspection, every downstream edit decision
is a guess.

## Depends On
Phase 1 (Foundation) — uses `MediaProbe`, the error contract, and config.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `scan_assets` | Scan a directory for video assets with FFprobe metadata | ✓ Done | In `media.py` |
| `scan_project_assets` | Scan with aggregate counts + per-file probe diagnostics | ✓ Done | In `inspection.py` |
| `probe_media` | Probe a single media file with FFprobe | ✓ Done | Low-level wrapper in `media.py` |
| `analyze_video_metadata` | Video-focused metadata (fps, resolution, codec, aspect) | ✓ Done | In `inspection.py` |
| `analyze_audio_metadata` | Audio stream metadata | ✓ Done | In `inspection.py` |
| `detect_scenes` | FFmpeg scene detection, configurable threshold | ⚠ Partial | Implemented; not verified against real footage |
| `generate_thumbnails` | Representative thumbnail generation (Pillow) | ⚠ Partial | Implemented; not verified against real footage |

## Acceptance Criteria
- [x] `probe_media` returns a `MediaProbe` with `exists`, `ok`, `duration`, `format_name`, stream list, and structured error fields on failure.
- [x] Broken/unsupported files do not raise — they return `ok: false` with a code and `suggested_fix`.
- [x] `analyze_video_metadata` reports fps, width/height, codec, and derived aspect ratio.
- [x] `scan_project_assets` returns aggregate counts (total/video/audio/broken) and per-file diagnostics.
- [ ] `detect_scenes` produces correct cut timestamps verified against at least one real clip with known scene boundaries. **(blocked on P11 golden media)**
- [ ] `generate_thumbnails` writes valid image files at correct timestamps, verified against a real clip. **(blocked on P11 golden media)**

## Implementation Tasks

1. **FFprobe wrapper** — `media.py: probe_media()`, `require_binary()`.
   Done-when: returns structured `MediaProbe`; missing-binary yields
   `missing_dependency` error. **Status: Done.**
2. **Directory scan** — `media.py: scan_assets()`, `inspection.py: scan_project_assets()`.
   Done-when: returns counts + per-file probes; empty dir handled gracefully.
   **Status: Done.**
3. **Metadata analyzers** — `inspection.py: analyze_video_metadata()`, `analyze_audio_metadata()`.
   Done-when: fps/resolution/codec/aspect and audio stream fields populated.
   **Status: Done.**
4. **Scene detection** — `inspection.py: detect_scenes()`.
   Done-when: threshold-configurable; returns ordered cut timestamps; verified
   against a real multi-scene clip. **Status: Partial — logic implemented,
   real-media verification pending (P11).**
5. **Thumbnails** — `inspection.py: generate_thumbnails()`.
   Done-when: writes N evenly/representatively spaced thumbnails to a project
   dir; verified to produce valid images. **Status: Partial — logic implemented,
   real-media verification pending (P11).**
6. **Project inspection roll-up** — `inspection.py: inspect_project()` (registered as a tool; spans P2/P3).
   Done-when: returns full project state (assets, timelines, outputs).
   **Status: Done.**

## Test Coverage Requirements
- Unit tests: `test_inspection.py` (7) — covers metadata extraction, scene
  detection, and thumbnail logic with monkeypatched FFmpeg/ffprobe. **Present.**
- Integration tests: a real-media test that probes a known clip and asserts
  exact duration/fps/resolution. **Missing — owned by P11.**
- Edge cases: zero-byte file, audio-only file, image file, corrupt header,
  missing binary. **Partially covered; corrupt-header path relies on
  monkeypatched probe output.**

## Known Gaps
- `detect_scenes` and `generate_thumbnails` have **no real-media verification** —
  the FFmpeg invocations are mocked, so their actual output correctness is
  unproven. This is the main reason the phase is at 65% rather than higher.
- No handling/testing for very large (4K+) or very long (>1h) files; probing
  is assumed fast and is untested under slow I/O.
- Network/streaming media paths are not supported (local files only).

## Notes
- The completion percentage is gated by real-media verification, not by missing
  features. The 7 tools are all implemented; the doubt is whether the FFmpeg
  filter strings produce correct results, which only P11 can confirm.
- `inspect_project` is registered here but also serves Phase 3; it is counted in
  this phase to avoid double-counting.
