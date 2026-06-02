# Planning Handoff — Opus 4.8 MAX

## Your Task

You are being asked to replace a single flat implementation plan file with a structured, multi-file planning system. The goal is a **long-term plan (point A → point Z)** covering the full lifetime of development to the first fully functional and capable MVP of this application — plus one dedicated plan file per phase.

**Delete** `docs/implementation-plan.md` and replace it with:

```
docs/
  plan/
    MASTER_PLAN.md          ← the A→Z lifetime development roadmap
    phase-01-foundation.md
    phase-02-media-inspection.md
    phase-03-timeline-otio.md
    phase-04-beat-sync.md
    phase-05-render-engine.md
    phase-06-effects.md
    phase-07-color-grading.md
    phase-08-validation.md
    phase-09-workflow.md
    phase-10-hardening.md
    phase-11-integration-testing.md
    phase-12-release.md
```

> Note: Phases 11 and 12 (integration testing and release) did not exist as named phases in the old plan but are clearly distinct bodies of work. Add them as full phases.

---

## What These Files Must Contain

### MASTER_PLAN.md

The top-level roadmap from zero to MVP. Must include:

- **Vision statement** — what this application does, who uses it, and what "MVP complete" means
- **MVP definition** — the exact capability threshold that defines the first fully functional and capable MVP (not an aspirational future; a concrete checklist)
- **Phase summary table** — all 12 phases with: phase number, name, current completion %, status (Not Started / In Progress / Complete), and a one-line goal
- **Dependency chain** — which phases must complete before others can start (as a text dependency graph or table)
- **Current overall completion** — honest engineering estimate
- **What is built today** — bulleted list of what actually works right now
- **What is missing for MVP** — bulleted list of the concrete gaps between today and MVP
- **Guiding principles** — the non-negotiable architecture decisions every contributor must follow

---

### Per-Phase Files (phase-01 through phase-12)

Each phase file must follow this structure exactly:

```
# Phase N — [Name]

## Status
[Not Started | In Progress | Complete] — [X]% complete

## Goal
One paragraph: what this phase builds and why it matters to the overall system.

## Depends On
List of phases that must be complete before this phase can start.

## Tools / Components Delivered
Table of every MCP tool or module this phase produces. Columns:
  Name | Description | Status (✓ Done / ⚠ Partial / ✗ Missing) | Notes

## Acceptance Criteria
Bulleted list of concrete, testable criteria that define "this phase is done."
Each criterion must be specific enough that another engineer can verify it without asking.

## Implementation Tasks
Numbered list of tasks. For each task:
  - Task name
  - What to build (module, function, or test file)
  - Definition of done for this task
  - Current status: Done / Partial / Not Started

## Test Coverage Requirements
What tests must exist for this phase to be considered complete:
  - Unit tests: list specific test files and what they must cover
  - Integration tests: what real-world scenario must pass
  - Edge cases: what failure modes must be tested

## Known Gaps
Anything in this phase that is implemented but incomplete, untested, or undocumented.

## Notes
Any architectural decisions, constraints, or rationale specific to this phase.
```

---

## Codebase Audit Findings

Use the following audit data to accurately fill in status, gaps, and completion percentages. Do not inflate completion numbers — if a feature is built but untested, it is partial, not done.

---

### Repository Overview

- **Location:** `src/mcp_editor/`
- **Total source files:** 22 files, ~5,393 lines
- **Test files:** 21 unit test files (107 tests), 1 integration test file (5 test classes)
- **MCP tools registered:** 51 tools across all phases
- **Python version:** 3.11+
- **Entry point:** `mcp-editor = mcp_editor.server:main`

---

### Source Modules (current state)

| File | LOC | Purpose |
|------|-----|---------|
| server.py | 914 | FastMCP app, all 51 @app.tool() registrations |
| schemas.py | 585 | All Pydantic models and utility functions |
| workflow.py | 444 | edit_video_from_prompt and project lifecycle |
| grading.py | 371 | LUT grading presets and FFmpeg color filter builders |
| validation.py | 314 | Post-render quality gate |
| effects.py | 293 | FFmpeg filter chain builders for clip effects |
| timeline.py | 274 | OTIO timeline model and clip operations |
| inspection.py | 274 | Media metadata analysis and project inspection |
| render.py | 221 | FFmpeg command planning, execution, manifest management |
| beat_sync.py | 218 | librosa beat analysis and beat-synced edit planning |
| media_docs.py | 622 | Media comprehension document generation |
| references.py | 126 | Reference asset library |
| sourcing.py | 112 | Asset download via HTTP and yt-dlp |
| diagnostics.py | 142 | Structured error contracts |
| timeline_ops.py | 131 | MCP-level wrappers for timeline edits |
| media.py | 134 | FFprobe wrapper and asset scanning |
| logging.py | 97 | Per-project JSON structured logging |
| projects.py | 39 | Manifest load/save, project directory helpers |
| config.py | 55 | Workspace root and data directory resolution |
| __main__.py | 5 | CLI entry point |

No TODO, FIXME, or NotImplementedError markers exist in the codebase.

---

### All 51 MCP Tools by Phase

**Phase 2 — Media Inspection (7 tools):**
- `scan_assets` — scan directory for video assets with FFprobe metadata
- `scan_project_assets` — scan with aggregate counts and per-file diagnostics
- `probe_media` — probe single media file with FFprobe
- `analyze_video_metadata` — fps, resolution, codec, aspect ratio
- `analyze_audio_metadata` — audio stream metadata
- `detect_scenes` — FFmpeg scene detection with configurable threshold
- `generate_thumbnails` — representative thumbnail generation

**Phase 3 — Timeline & OTIO (9 tools):**
- `create_project` — manifest from local assets
- `inspect_project` — full project state inspection
- `create_timeline` — simple sequential OTIO timeline
- `add_clip` — append/insert clip to timeline
- `trim_clip` — trim clip by ID or index
- `split_clip` — split clip at timecode
- `move_clip` — reorder clips
- `add_transition` — add/replace transition between clips
- `export_timeline` — export to OTIO file

**Phase 4 — Beat Sync & Planning (5 tools):**
- `analyze_beats` — librosa beat/tempo detection
- `suggest_cut_points` — beat-driven cut planning with style presets
- `plan_beat_synced_edit` — deterministic beat-synced edit plan
- `apply_edit_plan` — apply edit plan to timeline, export OTIO
- `validate_timeline` — validate timeline for missing media/overlaps

**Phase 5 — Render Engine (4 tools):**
- `plan_render` — dry-run FFmpeg command planning
- `render_project` — render timeline to MP4 (single platform)
- `render_platform_variant` — render single platform variant
- `render_all_variants` — render all declared platforms

**Phase 6 — Effects Engine (6 tools):**
- `apply_speed_ramp` — playback speed multiplier (audio-aware via atempo)
- `apply_zoom_punch` — scale and crop for punch-zoom
- `apply_smash_cut` — hard cut (remove transition)
- `apply_reframe` — crop with center offset for platform reframing
- `apply_motion_effects` — apply multiple effects in one call
- `remove_clip_effect` — remove effect by type

**Phase 7 — Color Grading & LUTs (6 tools):**
- `list_luts` — all .cube files in data/luts/
- `inspect_lut` — parse .cube header and metadata
- `apply_lut` — apply .cube LUT to clip(s)
- `list_grading_presets` — all built-in presets with params
- `apply_grading_preset` — apply preset (cinematic/vivid/flat/bw/warm/cool)
- `render_with_grade` — render with grade effects baked in

**Phase 8 — Validation Gate (4 tools):**
- `validate_output` — exists, probe, video, resolution, fps, duration, black, silence, frozen checks
- `validate_audio` — audio-specific checks
- `validate_platform_outputs` — validate all platform outputs in manifest
- `validate_delivery_package` — full delivery gate (all platforms rendered, OTIO, manifest)

**Phase 9 — Workflow & Observability (3 tools):**
- `edit_video_from_prompt` — full 9-step pipeline (scan → probe → music → plan → effects → grade → render → OTIO → validate)
- `get_workflow_status` — pipeline-stage checklist with next_step hint
- `get_project_logs` — project log summary and recent records

**Extension Tools (included in Phase 3/9 coverage):**
- `download_asset` — download from HTTP or YouTube via yt-dlp
- `add_reference`, `list_references`, `get_reference`, `remove_reference` — reference asset library
- `create_media_doc`, `get_media_doc`, `list_media_docs`, `auto_generate_doc` — media comprehension docs

---

### Pydantic Models (schemas.py)

- **Platform** — enum: widescreen (1920×1080), vertical (1080×1920), square (1080×1080)
- **MediaStream** — FFprobe stream metadata
- **MediaProbe** — FFprobe output wrapper with diagnostics
- **ClipEffect** — per-clip effect storage (effect_type, params{})
- **TimelineClip** — clip_id, source, start, duration, label, effects[]
- **TimelineTransition** — from_clip_id, to_clip_id, transition_type, duration
- **TimelinePlan** — project_id, platform, clips[], transitions[], music_path, target_duration, otio_path
- **EditPlanClip** — source, start, duration, beat_time, label
- **BeatEditPlan** — project_id, platform, style, tempo, cut_points[], clips[]
- **RenderedOutput** — platform, path, ok, validation{}, render_manifest_path
- **RenderCommand** — stage, command[], output_path
- **RenderManifest** — full render plan and execution log
- **ProjectManifest** — master project record (ID, name, prompt, created_at, input_dir, music_path, platforms[], assets[], timelines{}, edit_plans{}, outputs{})
- **ReferenceAsset** / **ReferencesManifest** — reference library
- **VideoDoc** / **ImageDoc** / **AudioDoc** — rich media comprehension documents (dozens of sub-fields covering shot, movement, color, lighting, audio, emotional register, narrative role, creative utility)
- `deterministic_project_id(name, input_dir) → str` — SHA-256 hash (12 chars); never use uuid4()
- `as_path(value) → Path` — expanduser + resolve
- `posix_path(value) → str` — POSIX forward-slash normalization

---

### Test Coverage Summary

**Unit tests (tests/unit/) — 107 tests across 21 files:**

| File | Tests | Coverage Quality |
|------|-------|-----------------|
| test_media_docs.py | 17 | Good — doc generation, parsing, serialization |
| test_references.py | 17 | Good — full CRUD and manifest persistence |
| test_sourcing.py | 12 | Good — direct download, yt-dlp fallback |
| test_auto_generate.py | 5 | Moderate — auto-doc generation paths |
| test_beat_sync.py | 5 | Moderate — analysis, cut points, planning |
| test_grading.py | 6 | Good — presets, LUT loading, filter building |
| test_hardening.py | 6 | Good — error handling, path normalization, IDs |
| test_inspection.py | 7 | Good — video/audio metadata, scene detection |
| test_timeline.py | 5 | Moderate — construction, clip ops, OTIO export |
| test_validation_phase8.py | 5 | Moderate — fps, duration, black, silence, freeze |
| test_workflow_phase9.py | 3 | Thin — style/grade inference, workflow status |
| test_diagnostics.py | 4 | Good — error issue construction and serialization |
| test_effects.py | 4 | Moderate — filter chain building |
| test_projects.py | 1 | Thin — single manifest save/load test |
| test_schemas.py | 2 | Thin — validation and serialization |
| test_render.py | 4 | Moderate — manifest planning and execution |
| test_render_workflow.py | 2 | Thin — pipeline integration |
| test_timeline_ops.py | 1 | Thin — MCP-level wrappers |
| test_validation.py | 1 | Thin — validation gate |

**Integration tests (tests/integration/) — 5 test classes, 302 lines:**
- `test_workflow_integration.py` — TestCreateProject (3 tests), TestBuildTimeline (2 tests)
- All use monkeypatched FFmpeg/ffprobe — no real media required or tested

**Test infrastructure:** pytest, pytest-asyncio, MediaProbe stub fixtures, monkeypatched subprocess

---

### Dependencies

```
Runtime:
  opentimelineio>=0.17    OTIO timeline model and export
  mcp>=1.0                FastMCP server framework
  librosa>=0.10           Beat and tempo detection
  pydantic>=2.0           Schema validation
  yt-dlp>=2024.1          YouTube/platform video downloads
  requests>=2.31          HTTP downloads
  Pillow>=10.0            Thumbnail generation

Dev:
  pytest>=8.0
  pytest-asyncio>=0.23
```

---

### Scripts and Entry Points

- `scripts/setup.sh` — install deps via uv pip
- `scripts/verify.sh` — check Python version, FFmpeg, imports, health checks
- `scripts/benchmark.py` — pure-Python benchmarks for hot paths (filter building, manifest serialization, beat planning, timeline construction, grading)
- Entry points: `mcp-editor` (server), `mcp-editor-bench` (benchmark runner)

---

### Data Directory Layout

```
data/
  input/       ← user footage
  music/       ← music for beat analysis
  luts/        ← .cube LUT files (user-supplied; none included)
  output/      ← rendered MP4 files
  projects/    ← auto-managed
    {project_id}/
      manifest.json
      logs/*.jsonl
      segments/{16x9,9x16,1x1}/
      render_{16x9,9x16,1x1}.json
      timeline_{16x9,9x16,1x1}.otio
  references/
    references.json
```

---

### Complete Gap Analysis

**What is done and solid:**
- All 51 MCP tools are registered and implemented
- Full A→Z editing pipeline: scan → probe → beat analyze → timeline → effects → grade → render → OTIO → validate → deliver
- Deterministic project IDs (no uuid4 collisions)
- Retry logic with exponential backoff in render (2 retries, 1s/2s delays)
- Structured error diagnostics: 8+ error codes, suggested fixes
- 107 unit tests + 5 integration tests (monkeypatched FFmpeg)
- Full API documentation (tools.md, 714 lines)
- Architecture and phase documentation
- Benchmark suite for pure-Python hotpaths
- 6 built-in grading presets (cinematic, vivid, flat, bw, warm, cool)
- Per-project structured JSON logging
- Platform scaling for all 3 aspect ratios

**Gaps and incomplete areas:**

| Gap | Phase | Severity | Detail |
|-----|-------|----------|--------|
| Golden media integration tests | 11 | High | No tests run real FFmpeg; can't verify render pipeline end-to-end |
| PyPI / GitHub Actions release | 12 | High | No automated publish; must install from source |
| 4K+ large file handling | 5, 10 | Medium | No streaming render; untested above HD |
| Variable-tempo beat detection | 4 | Medium | librosa works for steady tempo; complex music may miss beats |
| Cache invalidation | 5, 10 | Medium | Segment cache exists per-project; no cross-project dedup or invalidation |
| Partial render recovery | 5, 10 | Medium | Retry on transient failures; no checkpoint-resume for mid-project crash |
| Windows/macOS path CI | 10 | Medium | POSIX normalization implemented; not tested in CI |
| Color space validation | 8 | Low | No checks for BT.709 vs. P3 vs. BT.2020 |
| Bitrate validation | 8 | Low | No min/max bitrate checks in delivery gate |
| Audio sync validation | 8 | Low | No A/V sync drift detection post-render |
| Per-tool timing logs | 9, 10 | Low | ProjectLogger exists; not all tools log timing |
| FFmpeg filter documentation | 6 | Low | Filter parameter tuning not documented in-code |
| LUT format specification | 7 | Low | No docs on supported .cube variants |

---

### Phase Completion Data (honest engineering estimates)

| Phase | Name | Completion | Status |
|-------|------|-----------|--------|
| 1 | Foundation & Contracts | 100% | Complete |
| 2 | Media Inspection | 60% | In Progress |
| 3 | Timeline & OTIO | 60% | In Progress |
| 4 | Beat Sync & Planning | 35% | In Progress |
| 5 | FFmpeg Render Engine | 60% | In Progress |
| 6 | Effects Engine | 65% | In Progress |
| 7 | Color Grading & LUTs | 70% | In Progress |
| 8 | Self-Validation Gate | 85% | In Progress |
| 9 | End-to-End Workflow | 80% | In Progress |
| 10 | Hardening & Scale | 75% | In Progress |
| 11 | Integration Testing (real media) | 55% | In Progress |
| 12 | Release & CI/CD | 30% | Not Started |

**Overall: 81% toward MVP**

---

### MVP Definition (for MASTER_PLAN.md)

An honest "first fully functional and capable MVP" means:

1. A calling agent can run `edit_video_from_prompt` with real footage, real music, and a text prompt and receive a rendered, validated MP4 for all 3 platforms (16:9, 9:16, 1:1)
2. The render pipeline works with real FFmpeg (not mocked) on at least 1080p footage
3. Beat sync works on steady-tempo music tracks (EDM, hip-hop, pop)
4. Color grading applies cleanly via at least the 6 built-in presets
5. The validation gate correctly catches and rejects black/silent/frozen outputs
6. The OTIO export is valid and importable by a standard NLE
7. All 107 unit tests pass
8. At least one real-media integration test passes (footage + music → rendered MP4)
9. The server can be installed via `pip install` from PyPI or a GitHub release

---

### Architectural Non-Negotiables (must appear in MASTER_PLAN.md principles)

1. **No LLM inside the server** — the calling agent makes creative decisions; the server executes them deterministically
2. **No uuid4() for project IDs** — use `deterministic_project_id(name, input_dir)` from schemas.py
3. **All paths in manifests use posix_path()** — forward slashes on all platforms
4. **No unhandled exceptions in tool handlers** — always return `_error(exc)` which produces the structured error JSON contract
5. **Business logic belongs in impl modules** — tool registrations in server.py are thin wrappers only
6. **Every tool returns `ok: bool`** — this is the top-level contract for all calling agents
7. **Effect pipeline order is fixed** — reframe → zoom_punch → speed_ramp → motion_blur → grade → platform scale/crop

---

## Output Requirements

When you write these files:

- **Be specific** — name actual files, functions, and test names where relevant
- **Be honest about status** — if something is partial, say it's partial; do not inflate
- **Every task must have a definition of done** — "implement X" is not enough; specify what observable outcome proves it's done
- **Every acceptance criterion must be verifiable** — another engineer should be able to check it without asking anyone
- **Do not invent tools or features** that aren't described here or in the existing codebase
- **Maintain the architectural principles** throughout — especially no LLM in the server, deterministic IDs, structured errors

The resulting files are the single source of truth for what this project is, what it does, and how to complete it. Write them as if handing off to a fresh engineer who has never seen this code.
