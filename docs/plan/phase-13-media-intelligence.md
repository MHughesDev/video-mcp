# Phase 13 — Media Intelligence & Sourcing

## Status
In Progress — 70%

## Goal
Give the agent richer asset capabilities beyond raw probing: acquire assets from
URLs (HTTP and yt-dlp), maintain a tagged reference library for
inspiration/comparison, and generate structured media-comprehension documents
(`VideoDoc` / `ImageDoc` / `AudioDoc`) that describe footage in editorial terms
(shot scale, movement, color, lighting, energy, emotional register, creative
utility). This phase did not exist in the original 10-phase roadmap but is a
substantial, distinct body of work — `media_docs.py` (622 LOC) is the single
largest module in the codebase.

## Depends On
Phase 1 (Foundation) for schemas; Phase 2 (Media Inspection) for the underlying
metadata that comprehension docs build on.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `download_asset` | Download video/audio/image from HTTP or YouTube (yt-dlp) | ⚠ Partial | Network-dependent; success path tested via mocks only |
| `add_reference` | Register a media reference with tags + notes | ✓ Done | `references.py` |
| `list_references` | Filter references by tags | ✓ Done | `references.py` |
| `get_reference` | Fetch a reference by ID | ✓ Done | `references.py` |
| `remove_reference` | Remove a reference + clean up its doc | ✓ Done | `references.py` |
| `create_media_doc` | Create a structured markdown media document | ✓ Done | `media_docs.py` |
| `get_media_doc` | Fetch a media document | ✓ Done | `media_docs.py` |
| `list_media_docs` | List all media documents | ✓ Done | `media_docs.py` |
| `auto_generate_doc` | Auto-generate a doc from media analysis | ⚠ Partial | Generation heuristics; real-media verification pending |

## Acceptance Criteria
- [x] `download_asset` resolves direct HTTP downloads and falls back to yt-dlp for platform URLs, mapping content-type to asset kind.
- [x] The reference library supports add/list(filter by tag)/get/remove with manifest persistence in `data/references/references.json`.
- [x] Removing a reference also removes its associated media doc.
- [x] `create_media_doc` produces a structured `VideoDoc`/`ImageDoc`/`AudioDoc` (markdown-rendered) covering the documented field set.
- [x] `auto_generate_doc` populates a doc from available probe/analysis data without raising on missing fields.
- [ ] `download_asset` is verified against a **real** URL and a **real** yt-dlp fetch (currently mocked only). **(network/integration gap)**
- [ ] `auto_generate_doc` produces editorially-accurate fields on **real footage** (e.g. shot scale/movement inferred correctly). **(unverified — and partly inherently heuristic)**

## Implementation Tasks

1. **Asset sourcing** — `sourcing.py: download_asset()`, `_download_direct()`, `_download_via_ytdlp()`.
   Done-when: HTTP + yt-dlp paths, content-type→kind mapping, structured errors.
   **Status: Done (logic) — real network fetch unverified in CI (intentionally,
   to keep tests hermetic).**
2. **Reference library** — `references.py` (add/list/get/remove + manifest).
   Done-when: full CRUD with tag filtering and doc cleanup on remove. **Status:
   Done.**
3. **Comprehension schemas** — `VideoDoc`/`ImageDoc`/`AudioDoc` (+ enums) in
   `schemas.py`. Done-when: nested models cover identity/technical/shot/color/
   lighting/content/audio/emotional/narrative/creative-utility fields.
   **Status: Done.**
4. **Doc generation + persistence** — `media_docs.py` (`create_media_doc`,
   `get_media_doc`, `list_media_docs`, `auto_generate_doc`, the `_render_*` and
   `_generate_*` helpers). Done-when: docs are created, rendered to markdown,
   persisted, and round-trip. **Status: Done (create/get/list); auto-generate
   Partial pending real-media verification.**
5. **Real-source verification** — *new work*.
   Done-when: an opt-in test (under the P11 `realmedia` marker) fetches a real
   asset and auto-generates a doc whose technical fields match ffprobe.
   **Status: Not Started.**

## Test Coverage Requirements
- Unit tests: `test_sourcing.py` (12), `test_references.py` (17),
  `test_media_docs.py` (17), `test_auto_generate.py` (5) — **51 tests, strong**
  coverage of CRUD, serialization, download fallback, and generation paths
  (all mocked). **Present and solid.**
- Integration tests: a `realmedia`-marked test that downloads a small real
  asset and auto-generates a doc with verifiable technical fields. **Missing —
  align with P11.**
- Edge cases needed: unreachable URL; unsupported content-type; yt-dlp absent;
  doc for a file with no audio/odd aspect. **Mostly covered among the 51 tests;
  confirm the yt-dlp-absent path.**

## Known Gaps
- **`download_asset` is the one principled exception to "no network in tools"**
  (it is download-only and agent-invoked). It is **never exercised against a
  real network** in CI by design, so real-world robustness (timeouts, partial
  downloads, yt-dlp version drift) is unproven.
- **`auto_generate_doc` editorial accuracy is inherently heuristic** — fields
  like shot scale, camera movement, and emotional register are best-effort
  inferences, not ground truth. The doc structure is solid; the *quality* of
  inferred creative fields is unvalidated and may always be approximate.
- These tools are **not part of the core MVP pipeline** — the MVP can ship
  without verified sourcing/comprehension. They are listed as a full phase for
  completeness and because they represent significant existing surface area.

## Notes
- This phase exists to satisfy the user's requirement that *everything* in the
  codebase be represented in the plan. Without it, the largest module
  (`media_docs.py`) and 51 tests would be unaccounted for.
- Relationship to MVP: **adjacent, not gating.** Keep it healthy but do not let
  it block Phases 11–12, which are the true MVP gates.
- The "no LLM in the server" principle still holds: `auto_generate_doc` infers
  from deterministic probe/heuristic signals, not from a model call.
