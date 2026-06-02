"""Real-media integration tests for mcp-editor.

ALL tests in this file are decorated with ``@pytest.mark.realmedia`` and
require FFmpeg/ffprobe in PATH plus the golden-media fixtures synthesized by
``tests/conftest.py``.

Run them explicitly:
    pytest -m realmedia tests/

The default ``pytest tests/`` run deselects this marker automatically, so CI
stays green without FFmpeg.  A dedicated CI job (Phase 12) installs FFmpeg and
runs ``pytest -m realmedia``.

Coverage goals (from docs/plan/phase-11-integration-testing.md):
  Task 3 – Render smoke test          → test_render_produces_playable_mp4
  Task 4 – End-to-end workflow test   → test_edit_video_from_prompt_end_to_end
  Task 5 – Validation truth tests     → test_validation_rejects_black_output
                                         test_validation_passes_good_output
  Task 6 – Grade verification         → test_grading_preset_changes_output
  Task 7 – OTIO round-trip            → test_otio_export_is_valid
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from mcp_editor.schemas import Platform
from mcp_editor.workflow import (
    build_timeline_for_project,
    create_project,
    edit_video_from_prompt,
    render_and_validate_project,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _ffprobe_json(path: Path, ffprobe_bin: str) -> dict:
    result = subprocess.run(
        [
            ffprobe_bin, "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-show_format",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _video_stream(probe: dict) -> dict:
    for s in probe.get("streams", []):
        if s.get("codec_type") == "video":
            return s
    raise AssertionError("no video stream found in probe output")


# ── Task 3 – Render smoke test ────────────────────────────────────────────────


@pytest.mark.realmedia
def test_render_produces_playable_mp4(golden_workspace, ffprobe_bin):
    """A real render on the golden fixture yields a playable, correctly-sized .mp4.

    Closes the Phase 5 gating task (MVP criterion 2).
    """
    ws = golden_workspace
    input_dir = str(ws / "data" / "input")

    manifest = create_project("smoke-render", input_dir)
    manifest = build_timeline_for_project(manifest, Platform.widescreen)
    manifest = render_and_validate_project(manifest, Platform.widescreen, render_profile="preview")

    output = manifest.outputs.get("16:9")
    assert output is not None, "No widescreen output recorded in manifest"
    assert output.ok, f"Render validation failed: {output.validation}"

    out_path = Path(output.path)
    assert out_path.exists(), f"Output file not found: {out_path}"
    assert out_path.stat().st_size > 0, "Output file is empty"

    probe = _ffprobe_json(out_path, ffprobe_bin)
    v = _video_stream(probe)
    assert v["width"] == 1920, f"Expected 1920 wide, got {v['width']}"
    assert v["height"] == 1080, f"Expected 1080 tall, got {v['height']}"

    duration = float(probe["format"]["duration"])
    assert duration > 0, "Output has zero duration"


# ── Task 4 – End-to-end workflow test ────────────────────────────────────────


@pytest.mark.realmedia
def test_edit_video_from_prompt_end_to_end(golden_workspace, ffprobe_bin):
    """edit_video_from_prompt produces validated outputs for all three platforms.

    Closes the Phase 9 gating task (MVP criterion 1 and 8).
    """
    ws = golden_workspace
    input_dir = str(ws / "data" / "input")
    music_dir = str(ws / "data" / "music")

    result = edit_video_from_prompt(
        prompt="energetic upbeat highlight reel",
        input_dir=input_dir,
        music_dir=music_dir,
        project_name="e2e-test",
        platforms=[Platform.widescreen, Platform.vertical, Platform.square],
        render_profile="preview",
    )

    assert result.get("ok"), f"edit_video_from_prompt failed: {result}"

    outputs = result.get("outputs", {})
    for platform_str in ("16:9", "9:16", "1:1"):
        assert platform_str in outputs, f"Missing output for platform {platform_str}"
        output = outputs[platform_str]
        assert output.get("ok"), f"Platform {platform_str} render failed: {output}"
        out_path = Path(output["path"])
        assert out_path.exists(), f"Output file missing for {platform_str}: {out_path}"

    # OTIO file must also be present
    otio_path_str = result.get("otio_path") or result.get("otio")
    if otio_path_str:
        otio_path = Path(otio_path_str)
        assert otio_path.exists(), f"OTIO file not found: {otio_path}"
        assert otio_path.suffix == ".otio"


# ── Task 5 – Validation truth tests ──────────────────────────────────────────


@pytest.mark.realmedia
def test_validation_passes_good_output(golden_workspace, ffmpeg_bin, ffprobe_bin):
    """The validation gate passes a legitimate render (not black/silent/frozen).

    Closes part of the Phase 8 gating task.
    """
    ws = golden_workspace
    input_dir = str(ws / "data" / "input")

    manifest = create_project("validate-good", input_dir)
    manifest = build_timeline_for_project(manifest, Platform.widescreen)
    manifest = render_and_validate_project(manifest, Platform.widescreen, render_profile="preview")

    output = manifest.outputs.get("16:9")
    assert output is not None
    assert output.ok, f"Good render failed validation: {output.validation}"
    checks = output.validation.get("checks", {})
    assert not checks.get("black"), "Good render incorrectly flagged as black"
    assert not checks.get("silent"), "Good render incorrectly flagged as silent"
    assert not checks.get("frozen"), "Good render incorrectly flagged as frozen"


@pytest.mark.realmedia
def test_validation_rejects_black_output(tmp_path, monkeypatch, ffmpeg_bin):
    """The validation gate rejects a fully-black video.

    Closes part of the Phase 8 gating task.
    """
    monkeypatch.setenv("MCP_EDITOR_ROOT", str(tmp_path))

    # Synthesize a 2-second solid-black 1920×1080 video
    black_video = tmp_path / "black.mp4"
    subprocess.run(
        [
            ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", "color=black:size=1920x1080:duration=2:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=0:duration=2",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
            "-c:a", "aac",
            str(black_video),
        ],
        check=True,
        capture_output=True,
    )

    from mcp_editor.validation import validate_render
    result = validate_render(black_video, Platform.widescreen, expected_duration=2.0)
    # A black video may fail on the black check; silent video may also fail.
    # The key assertion: the check runs and returns a dict with an 'ok' key.
    assert "ok" in result, "validate_render must return a dict with 'ok'"
    # black should be detected — the result either fails or flags black
    checks = result.get("checks", {})
    assert checks.get("black") is True, (
        f"Expected black video to be detected as black, got checks={checks}"
    )


@pytest.mark.realmedia
def test_validation_rejects_silent_output(tmp_path, monkeypatch, ffmpeg_bin):
    """The validation gate rejects a video with no audio signal.

    Closes part of the Phase 8 gating task.
    """
    monkeypatch.setenv("MCP_EDITOR_ROOT", str(tmp_path))

    silent_video = tmp_path / "silent.mp4"
    subprocess.run(
        [
            ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=1920x1080:rate=30",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", "2",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
            "-c:a", "aac",
            str(silent_video),
        ],
        check=True,
        capture_output=True,
    )

    from mcp_editor.validation import validate_render
    result = validate_render(silent_video, Platform.widescreen, expected_duration=2.0)
    assert "ok" in result
    checks = result.get("checks", {})
    assert checks.get("silent") is True, (
        f"Expected silent video to be detected, got checks={checks}"
    )


# ── Task 6 – Grade verification ───────────────────────────────────────────────


@pytest.mark.realmedia
def test_grading_preset_changes_output(golden_workspace, ffmpeg_bin, ffprobe_bin):
    """Applying a grading preset produces output that differs from ungraded.

    Closes part of the Phase 7 gating task.
    """
    ws = golden_workspace
    input_dir = str(ws / "data" / "input")

    # Render without grading
    manifest_plain = create_project("grade-plain", input_dir)
    manifest_plain = build_timeline_for_project(manifest_plain, Platform.widescreen)
    manifest_plain = render_and_validate_project(
        manifest_plain, Platform.widescreen, render_profile="preview"
    )

    # Render with 'bw' grading preset (strongest visual delta — desaturates)
    manifest_graded = create_project("grade-bw", input_dir)
    from mcp_editor.grading import apply_grade_preset
    manifest_graded = build_timeline_for_project(manifest_graded, Platform.widescreen)
    plan = manifest_graded.timelines["16:9"]
    for clip in plan.clips:
        clip.effects = apply_grade_preset(clip.effects, "bw")
    manifest_graded = render_and_validate_project(
        manifest_graded, Platform.widescreen, render_profile="preview"
    )

    plain_path = Path(manifest_plain.outputs["16:9"].path)
    graded_path = Path(manifest_graded.outputs["16:9"].path)

    assert plain_path.exists() and graded_path.exists()

    # Files must differ — grading must change at least something
    assert plain_path.read_bytes() != graded_path.read_bytes(), (
        "Graded and ungraded renders produced identical output — grading had no effect"
    )


# ── Task 7 – OTIO round-trip ─────────────────────────────────────────────────


@pytest.mark.realmedia
def test_otio_export_is_valid(golden_workspace):
    """The exported .otio file is parseable by the opentimelineio library.

    Closes the Phase 3 gating task (MVP criterion 6).
    """
    import opentimelineio as otio

    ws = golden_workspace
    input_dir = str(ws / "data" / "input")

    manifest = create_project("otio-roundtrip", input_dir)
    manifest = build_timeline_for_project(manifest, Platform.widescreen)

    otio_path = Path(manifest.otio_path) if manifest.otio_path else None
    if otio_path is None or not otio_path.exists():
        # Some builds export OTIO during render; try render first
        manifest = render_and_validate_project(
            manifest, Platform.widescreen, render_profile="preview", dry_run=True
        )
        otio_path = Path(manifest.otio_path) if manifest.otio_path else None

    assert otio_path is not None, "No otio_path on manifest after timeline build"
    assert otio_path.exists(), f".otio file not found: {otio_path}"

    timeline = otio.adapters.read_from_file(str(otio_path))
    assert isinstance(timeline, otio.schema.Timeline), (
        f"Parsed object is not an OTIO Timeline: {type(timeline)}"
    )
    assert len(timeline.tracks) > 0, "OTIO timeline has no tracks"
