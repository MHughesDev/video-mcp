# Phase 14 — Tool Production-Readiness & API Contract Certification

## Status
Not Started — 0%

## Goal
Certify that **every one of the 53 registered MCP tools is genuinely
production-ready**, not merely implemented. This is the gap between a
*feature-complete MVP* and a *fully provisioned release*: a calling agent must
be able to invoke any tool with bad, missing, or hostile input and always get a
structured `{ok: false, error: {...}}` back instead of a crash, a `None`, or an
unhandled traceback — and the tool's documented name and contract in
`docs/tools.md` must exactly match what `server.py` actually registers.

This phase exists because a documentation/contract drift was caught in practice:
a generated tool inventory listed tools that do not exist (`plan_render_timeline`,
`render_timeline`, `validate_render`, `remove_clip`, `get_validation_report`) and
omitted real ones (`inspect_project`, `validate_platform_outputs`,
`validate_output`, `plan_render`, `render_project`). If a hand-written summary
can drift that far, the canonical reference can too — so tool/contract accuracy
must become a **verified, test-enforced property**, not a manual promise.

## Depends On
Phase 1 (the error contract and `_error()` it certifies against) and all
tool-bearing phases (2–13). This is a cross-cutting certification pass over work
those phases delivered; it adds no new editing features.

## Tools / Components Delivered
This phase delivers **certification, fixes, and an automated contract guard** —
not new MCP tools.

| Component | Description | Status | Notes |
|-----------|-------------|--------|-------|
| Canonical tool inventory | The authoritative list of all 53 registered tool names, generated from `server.py` | ✗ Not Started | Source of truth for docs + tests |
| `docs/tools.md` reconciliation | Every documented tool name/signature matches a real `@app.tool` registration | ✗ Not Started | Known drift: 5 phantom names, 5 omissions |
| Error-handling certification | Each tool's body is wrapped; failure returns `_error(exc)`; no unhandled exception can escape | ✗ Not Started | Per-tool audit |
| Input-validation certification | Required params validated; bad/missing input returns a structured error, never a crash | ✗ Not Started | Per-tool audit |
| Return-contract certification | Every tool returns a dict with `ok: bool` on **both** success and failure | ✗ Not Started | Per-tool audit |
| Stub/placeholder sweep | Confirm no impl function is a stub, `pass`, or `NotImplementedError` | ✗ Not Started | Per-module sweep |
| Per-tool smoke tests | At least one success-path and one failure-path test per tool | ⚠ Partial | Many exist; coverage gaps to be mapped |
| Contract-drift guard | A test that fails CI if `docs/tools.md` and the registered tool set disagree | ✗ Not Started | Prevents future drift |

## Acceptance Criteria
- [ ] A canonical list of the **53 registered tool names** is generated directly from `server.py` and committed (or produced by a test fixture), and is the single source other docs are checked against.
- [ ] `docs/tools.md` documents **exactly** the registered tool set — no phantom tools, no omissions, no misnamed entries — verified by an automated test.
- [ ] Every tool handler returns `{ok: bool, ...}` on the success path **and** `_error(exc)` on every failure path; a fuzz/garbage-input pass over all 53 tools produces **zero** unhandled exceptions.
- [ ] Every tool with required parameters rejects missing/invalid input with a structured error (correct `code`, actionable `suggested_fix`) rather than a stack trace or a silent wrong result.
- [ ] A stub sweep confirms **no** impl function is a placeholder (`pass`, `...`, `raise NotImplementedError`, or a hardcoded fake return).
- [ ] Each of the 53 tools has at least one success-path test and one failure-path test; a coverage map lists tool → tests.
- [ ] A contract-drift guard test runs in CI (Phase 12) and **fails** if the registered tool set and `docs/tools.md` diverge.

## Implementation Tasks

1. **Generate the canonical inventory** — a small helper (e.g. `scripts/list_tools.py`
   or a test fixture) that imports `server.app` and emits the registered tool
   names. Done-when: it prints all 53 names and is used by the drift guard.
   **Status: Not Started.**
2. **Reconcile `docs/tools.md`** — diff the doc against the canonical inventory;
   fix the known 5 phantom names (`plan_render_timeline`, `render_timeline`,
   `validate_render`, `remove_clip`, `get_validation_report`) and add the 5
   omitted real tools (`inspect_project`, `validate_platform_outputs`,
   `validate_output`, `plan_render`, `render_project`); correct any signature
   drift. Done-when: doc == registrations. **Status: Not Started.**
3. **Error-handling audit** — read each of the 53 handlers in `server.py`;
   confirm the body is wrapped and every failure path returns `_error(exc)`. Fix
   any handler that can raise. Done-when: a garbage-input pass over all tools
   yields zero unhandled exceptions. **Status: Not Started.**
4. **Input-validation audit** — for each tool, confirm required params are
   checked before use and produce a structured error on bad input. Done-when:
   each tool's failure path is covered by a test. **Status: Not Started.**
5. **Return-contract audit** — assert every tool returns a dict containing
   `ok`. Done-when: a parametrized test iterates all tools and checks the shape.
   **Status: Not Started.**
6. **Stub/placeholder sweep** — grep + read impl modules (`effects.py`,
   `grading.py`, `inspection.py`, `sourcing.py`, `media_docs.py`, …) for stubs;
   confirm `detect_scenes`, `generate_thumbnails`, `apply_lut`, `download_asset`,
   and `auto_generate_doc` are real, not placeholders. Done-when: sweep is clean
   or gaps are filed. **Status: Not Started.**
7. **Per-tool smoke coverage map** — build a table of tool → (success test,
   failure test); write tests for any tool missing either. Done-when: all 53
   tools have both. **Status: Not Started.**
8. **Contract-drift guard** — `tests/unit/test_tool_contract.py` that (a) asserts
   the registered set has the expected count, (b) asserts every documented tool
   exists and every registered tool is documented, (c) asserts every tool returns
   an `ok`-bearing dict. Wire into CI. Done-when: green, and red if docs drift.
   **Status: Not Started.**

## Test Coverage Requirements
- A new `tests/unit/test_tool_contract.py` is the heart of this phase: it
  enforces the inventory count, the docs↔registrations bijection, and the
  return-shape contract for all 53 tools — all without real FFmpeg (introspection
  + monkeypatched calls only, so it runs in the default fast suite).
- Per-tool failure-path tests live alongside their phase's existing unit tests.
- This phase must not require real media; it certifies the *contract*, while
  Phase 11 certifies *behavior on real media*.

## Known Gaps
- **No automated contract guard exists today** — `docs/tools.md` accuracy is
  maintained by hand and has been shown to drift. Until task 8 lands, nothing
  catches a renamed/added/removed tool.
- **Failure-path coverage is uneven** — success paths are well tested across
  phases; structured-error paths for malformed input are tested inconsistently.
- **Stub status of a few tools is asserted but not independently re-verified
  here** — `detect_scenes`, `generate_thumbnails`, and `auto_generate_doc` are
  marked Partial in their phases pending real-media checks; this phase confirms
  they are not *stubs*, which is distinct from confirming they are *correct*.

## Notes
- This is a **certification** phase: its output is confidence + a guard, plus a
  bounded set of fixes. It deliberately adds no editing capability.
- Relationship to the rest of the plan: Phase 11 proves the pipeline *works* on
  real media; Phase 14 proves the *interface* to every tool is safe, honest, and
  accurately documented. Both are required for "fully provisioned," beyond the
  feature-complete MVP.
- Keep the contract-drift guard cheap and introspection-based so it stays in the
  default fast unit suite and runs on every push.
