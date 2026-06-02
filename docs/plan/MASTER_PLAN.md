# Master Plan — mcp-editor

The point A → point Z roadmap for `mcp-editor`, from first commit to the first
fully functional and capable MVP. This is the single source of truth for what
the product is, what is built today, and what remains before MVP.

Each phase has a dedicated plan file in this directory (`phase-01-*.md` …
`phase-13-*.md`). This file is the index, the status dashboard, and the
statement of vision and principles. Update the phase table here whenever a
phase file's status changes.

---

## Vision

`mcp-editor` is a **headless, local-first MCP server that exposes video editing
as structured, deterministic tools**. A calling agent (Claude, Cursor, etc.)
makes the creative decisions; the server executes them precisely and returns
validated rendered video plus an OpenTimelineIO (OTIO) timeline.

The product turns existing footage, music, LUTs, and assets into:

- Rendered, validated `.mp4` outputs for 16:9, 9:16, and 1:1 platforms.
- A frame-accurate `.otio` timeline importable by any standard NLE.
- A structured delivery manifest the calling agent can reason about.

The server contains **no creative-director LLM and makes no external API calls
during editing.** Determinism and reproducibility are the product.

**Who uses it:** AI coding/creative agents that need to produce finished short-
form video from raw assets without a human operating an NLE.

---

## MVP Definition

The first "fully functional and capable MVP" is reached when **all** of the
following are true. This is a concrete gate, not an aspiration:

1. A calling agent can run `edit_video_from_prompt` with **real footage, real
   music, and a text prompt** and receive rendered, validated `.mp4` outputs
   for all three platforms (16:9, 9:16, 1:1).
2. The render pipeline runs against **real FFmpeg** (not monkeypatched) on at
   least 1080p footage and produces a playable file.
3. Beat sync produces a coherent rough cut on **steady-tempo music** (EDM,
   hip-hop, pop).
4. Color grading applies cleanly via at least the **6 built-in presets**
   (cinematic, vivid, flat, bw, warm, cool).
5. The validation gate correctly **rejects** black, silent, and frozen outputs
   on real renders.
6. The OTIO export is valid and **importable by a standard NLE**.
7. **All 192 unit tests pass** (`python -m pytest tests/unit/`).
8. **At least one real-media integration test passes** end-to-end
   (footage + music → validated `.mp4`).
9. The server is installable via **`pip install`** from PyPI or a tagged
   GitHub release.

Until criteria 2, 8, and 9 are met, the project is feature-complete on paper
but **not MVP-verified**. Those are the true gates.

---

## Status Dashboard

**Overall MVP readiness: ~85%**
**Core editing engine maturity (Phases 1–10): ~79%**

> Methodology: each phase is scored on implemented + tested + documented
> behavior, then weighted by effort/importance. The overall figure is lower
> than the previous plan's headline 81% because this plan promotes
> integration-testing and release/CI to first-class phases (rather than
> folding them into lightly weighted line items) and scores real-media
> verification — the actual MVP gate — honestly at ~55%.

| # | Phase | Status | % | One-line goal |
|---|-------|--------|---|---------------|
| 1 | Foundation & Contracts | Complete | 100% | Stable schemas, errors, IDs, config before any editing logic |
| 2 | Media Inspection | In Progress | 65% | Agent can reliably inspect footage before editing |
| 3 | Timeline & OTIO Core | In Progress | 65% | Produce valid frame-accurate timelines and `.otio` exports |
| 4 | Beat Sync & Edit Planning | In Progress | 50% | Generate a coherent beat-synced rough cut from music |
| 5 | FFmpeg Render Engine | In Progress | 60% | Turn timelines into real rendered video files |
| 6 | Effects Engine | In Progress | 72% | Stylized editing grammar via composable FFmpeg filters |
| 7 | Color Grading & LUTs | In Progress | 90% | Deterministic, reproducible grading |
| 8 | Self-Validation Gate | In Progress | 88% | No silent bad exports reach the agent |
| 9 | End-to-End Agent Workflow | In Progress | 80% | One-shot `edit_video_from_prompt` orchestration |
| 10 | Hardening & Scale | In Progress | 78% | Logging, retry, determinism, benchmarks for real use |
| 11 | Integration Testing (real media) | In Progress | 90% | Verify the pipeline against real FFmpeg + golden media |
| 12 | Release & CI/CD | In Progress | 70% | `pip install`-able, CI-gated, tagged releases |
| 13 | Media Intelligence & Sourcing | In Progress | 70% | Asset acquisition, reference library, media comprehension docs |

> Phases 11, 12, and 13 did not exist as named phases in the original
> `implementation-plan.md`. They are promoted here because each is a distinct,
> substantial body of work that the MVP depends on. Phase 13 in particular
> covers the single largest module in the codebase (`media_docs.py`, 622 LOC).

---

## Dependency Chain

```
P1 Foundation ─┬─> P2 Media Inspection ─┬─> P3 Timeline/OTIO ─┬─> P5 Render ─┬─> P6 Effects ──┐
               │                        │                     │              ├─> P7 Grading ──┤
               │                        └─> P4 Beat Sync ─────┘              └─> P8 Validation┤
               │                                                                              │
               ├─> P13 Media Intelligence                              P4,P5,P6,P7,P8 ──> P9 Workflow
               │                                                                              │
               └─> P10 Hardening (cross-cutting)                       P5,P8,P9 ──> P11 Integration Tests
                                                                                              │
                                                                       P10,P11 ──> P12 Release
```

Plain-language rules:

- **P1 must be complete before anything** — every module imports the schemas,
  error contract, and config from it.
- **P5 (Render) is the spine of MVP** — P6/P7/P8 all bake into or verify the
  render output; it is weighted heaviest.
- **P11 (Integration tests) gates the MVP** — it cannot start until Render (P5),
  Validation (P8), and Workflow (P9) exist, and it is what proves the pipeline
  actually works on real media.
- **P12 (Release) is last** — never ship before P11 proves the pipeline and P10
  hardening is in place.

---

## What Is Built Today

- All **53 MCP tools** are registered and implemented (44 core pipeline tools +
  9 extension tools).
- The full A→Z editing pipeline exists: scan → probe → beat-analyze → timeline
  → effects → grade → render → OTIO → validate → deliver.
- **`edit_video_from_prompt`** runs the complete 9-step pipeline with
  prompt-driven style/grade inference.
- Deterministic project IDs via `deterministic_project_id()` (no `uuid4()`).
- Structured error contract (`_error(exc)` → `{ok, error{code, message,
  suggested_fix, details}}`) with 8+ error codes.
- Retry-with-backoff in the render pipeline (2 retries, 1s/2s).
- **211 automated tests pass**: 192 unit + 19 integration (FFmpeg monkeypatched).
- 6 built-in grading presets; LUT loading/application from `data/luts/`.
- Per-project append-only JSON logging.
- Full tool reference in `docs/tools.md` (714 lines) and pure-Python benchmark
  suite (`scripts/benchmark.py`).
- Extension capabilities: asset sourcing (HTTP + yt-dlp), a tagged reference
  library, and rich media comprehension documents (`VideoDoc`/`ImageDoc`/
  `AudioDoc`).

## What Is Missing For MVP

- **Real-media tests need CI to prove green (P11):** 9 `@pytest.mark.realmedia`
  tests are written and skip cleanly without FFmpeg. The `real-media` CI job
  (already in `ci.yml`) will exercise them. All fixture/marker/validation/grade/
  beat/OTIO tests are written; only CI execution is pending.
- **Release installability (P12):** CI + release workflows both exist; PyPI
  project registration and the first real tagged release are the only remaining
  items. Project can only be installed from source today.
- **No shipped LUTs was resolved:** 6 creative `.cube` LUTs now ship in
  `data/luts/`. `apply_lut` has assets out of the box.
- **Beat sync depth (P4):** works on steady tempo; variable-tempo handling is
  undocumented. Beat-BPM test written for CI verification.
- **Beat sync depth (P4):** works on steady tempo; variable-tempo and
  ambient/orchestral tracks are unhandled.
- **Large-file / 4K handling (P5, P10):** untested above 1080p; no streaming or
  checkpoint-resume render.
- **No shipped LUTs:** `data/luts/` is empty, so `apply_lut` has nothing to load
  out of the box.
- **Cross-platform CI:** POSIX path normalization is implemented but never
  exercised on Windows/macOS in CI.

---

## Guiding Principles (non-negotiable)

Every contributor and every agent working in this repo must hold these. They
are also enforced by `CLAUDE.md`.

1. **No LLM inside the server.** The calling agent makes creative decisions; the
   server executes them deterministically. No external API/HTTP calls inside any
   editing tool. (Asset sourcing in Phase 13 is the sole, explicit exception and
   is download-only.)
2. **Deterministic project IDs.** Use `deterministic_project_id(name,
   input_dir)` from `schemas.py`. Never `uuid4()`.
3. **POSIX paths in manifests.** All stored paths go through `posix_path()`.
4. **No unhandled exceptions in tool handlers.** Always return `_error(exc)`.
   Every tool returns a dict with at least `ok: bool`.
5. **Thin tool registrations.** Business logic lives in impl modules
   (`effects.py`, `grading.py`, …); `server.py` only validates, calls, and wraps
   errors.
6. **Fixed effect pipeline order.** `reframe → zoom_punch → speed_ramp →
   motion_blur → grade → platform scale/crop (always last)`.
7. **Tests must not require real media to exist.** Unit/integration tests
   monkeypatch FFmpeg. Real-media tests (P11) are opt-in and skip cleanly when
   fixtures or binaries are absent.

---

## How To Use This Plan

- To **check status**, read the dashboard table above.
- To **work a phase**, open its `phase-NN-*.md` file: it lists every tool/
  component with status, concrete acceptance criteria, numbered implementation
  tasks with definitions of done, and required test coverage.
- To **add a tool**, follow `CLAUDE.md` ("How to add a new MCP tool") and then
  update both the relevant phase file and this dashboard.
- Keep percentages **conservative**: only count behavior that is implemented,
  tested, and documented well enough for another agent to use unaided.
