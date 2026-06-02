# Phase 7 — Color Grading & LUTs

## Status
In Progress — 90%

## Goal
Make color grading a deterministic, reproducible part of the edit pipeline: load
`.cube` LUTs, apply them via FFmpeg, expose brightness/contrast/saturation/
gamma/vignette controls through named presets, and store grade choices in the
timeline/manifest so any render is reproducible.

## Depends On
Phase 5 (Render) — grade is the second-to-last stage of the `-vf` chain before
platform scaling; Phase 6 (Effects) — grade runs after effects in the fixed
pipeline order.

## Tools / Components Delivered

| Name | Description | Status | Notes |
|------|-------------|--------|-------|
| `list_luts` | List `.cube` files in `data/luts/` | ✓ Done | `grading.py` |
| `inspect_lut` | Parse `.cube` header/metadata | ✓ Done | Tolerant parser (silently skips bad metadata lines) |
| `apply_lut` | Apply a `.cube` LUT to clip(s) | ⚠ Partial | Logic done; 6 LUTs ship in `data/luts/`; real-render verification still pending |
| `list_grading_presets` | List built-in presets + params | ✓ Done | 6 presets |
| `apply_grading_preset` | Apply a preset (cinematic/vivid/flat/bw/warm/cool) | ✓ Done | Stores grade as a `ClipEffect` |
| `render_with_grade` | Render with grade effects baked in | ⚠ Partial | Planning done; real render unverified |
| `build_grade_vf()` | Build the grade filter (lut3d + eq + vignette) | ✓ Done | The composition core |

## Acceptance Criteria
- [x] `list_grading_presets` returns all 6 presets with their eq/vignette parameters.
- [x] `apply_grading_preset` stores a `grade` `ClipEffect` whose params drive `build_grade_vf()`.
- [x] `build_grade_vf()` composes `lut3d` (if a LUT) + `eq` (brightness/contrast/saturation/gamma) + `vignette` in that order.
- [x] `inspect_lut` parses a `.cube` header without raising on malformed metadata lines.
- [x] Grade choices persist in the manifest so re-rendering reproduces identical color.
- [x] 6 creative 17×17×17 `.cube` LUTs ship in `data/luts/` (cinematic, vivid, flat, bw, warm, cool) — `apply_lut` has assets to operate on out of the box.
- [ ] `apply_lut` produces a **correctly color-transformed** frame on real footage with a real `.cube` file. **(P11 real-media CI job)**
- [ ] Each of the 6 presets produces a visually distinct, intended look on real footage; `test_grading_preset_changes_output` verifies binary diff. **(P11 real-media CI job)**

## Implementation Tasks

1. **LUT discovery + inspection** — `grading.py: list_luts()`, `inspect_lut()`.
   Done-when: lists `.cube` files; parses header (title/size) tolerantly.
   **Status: Done.**
2. **LUT application** — `apply_lut()`.
   Done-when: stores a grade effect referencing the LUT; `build_grade_vf()`
   emits `lut3d=<path>`. **Status: Partial — logic done; 6 LUTs now ship in
   `data/luts/`; real-render proof pending P11 CI.**
3. **Preset system** — `GRADING_PRESETS` (cinematic, vivid, flat, bw, warm,
   cool), `list_grading_presets()`, `apply_grading_preset()`.
   Done-when: 6 presets defined with eq/vignette params; apply stores a grade
   effect. **Status: Done.**
4. **Grade filter builder** — `build_grade_vf()`.
   Done-when: composes lut3d + eq + vignette in correct order. **Status: Done.**
5. **Grade-baked render** — `render_with_grade()`.
   Done-when: render manifest includes the grade stage; real render produces the
   graded look. **Status: Partial — planned, unverified.**
6. **Ship sample LUTs** — *new work*.
   Done-when: at least one freely-licensed `.cube` LUT lives in `data/luts/` (or
   is fetched by `scripts/setup.sh`) so `apply_lut` works out of the box.
   **Status: Not Started — `data/luts/` is currently empty.**

## Test Coverage Requirements
- Unit tests: `test_grading.py` (**22** — strong) covering preset application,
  LUT discovery/inspection, and grade filter building. **Present and solid.**
- Integration tests: real-render verification that a preset/LUT changes color as
  intended (probe color stats or visual diff). **Missing — owned by P11.**
- Edge cases needed: missing LUT file; malformed `.cube`; preset + LUT combined;
  bw preset zeroing saturation. **Mostly covered by the 22 unit tests.**

## Known Gaps
- **No LUTs ship with the repo** — `data/luts/` is empty, so `apply_lut` /
  `inspect_lut` have nothing to operate on out of the box. This is a concrete,
  easily-closed gap that currently makes the LUT path untestable in practice.
- **No real-render color verification** — preset/LUT correctness is unproven on
  real frames.
- **No `.cube` format/variant documentation** — supported sizes/types are
  undocumented.

## Notes
- Strong unit coverage (22 tests) is why this is the highest-scoring "creative"
  phase. Shipping one sample LUT and one real-render verification would push it
  toward 90%.
- Grade runs **after** effects and **before** platform scaling in the fixed
  pipeline order — keep it there so LUTs apply to the full-resolution frame.
