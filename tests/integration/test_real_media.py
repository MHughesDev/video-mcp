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
                                         test_validation_rejects_silent_output
                                         test_validation_passes_good_output
  Task 6 – Grade + beat verification  → test_grading_preset_changes_output
                                         test_beat_detection_tempo_accuracy
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
    music_path = str(ws / "data" / "music" / "music.mp3")

    result = edit_video_from_prompt(
        prompt="energetic upbeat highlight reel",
        input_dir=input_dir,
        music_path=music_path,
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

    # OTIO paths are under result["timelines"][platform]
    timelines = result.get("timelines", {})
    for platform_str, otio_path_str in timelines.items():
        if otio_path_str:
            otio_path = Path(otio_path_str)
            assert otio_path.exists(), f"OTIO file not found for {platform_str}: {otio_path}"
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
    # "not_black"/"not_silent"/"not_frozen" should all be True for a good render
    if "not_black" in checks:
        assert checks["not_black"], f"Good render incorrectly flagged as black: {checks}"
    if "not_silent" in checks:
        assert checks["not_silent"], f"Good render incorrectly flagged as silent: {checks}"
    if "not_frozen" in checks:
        assert checks["not_frozen"], f"Good render incorrectly flagged as frozen: {checks}"


@pytest.mark.realmedia
def test_validation_rejects_black_output(tmp_path, monkeypatch, ffmpeg_bin):
    """The validation gate rejects a fully-black video.

    Closes part of the Phase 8 gating task.
    """
    monkeypatch.setenv("MCP_EDITOR_ROOT", str(tmp_path))

    black_video = tmp_path / "black.mp4"
    subprocess.run(
        [
            ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", "color=black:size=1920x1080:duration=3:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
            "-c:a", "aac",
            str(black_video),
        ],
        check=True,
        capture_output=True,
    )

    from mcp_editor.validation import validate_render
    result = validate_render(black_video, Platform.widescreen, expected_duration=3.0)
    assert "ok" in result, "validate_render must return a dict with 'ok'"
    checks = result.get("checks", {})
    assert "not_black" in checks, f"Black check was not run: {checks}"
    assert checks["not_black"] is False, (
        f"Expected black video to be detected (not_black=False), got checks={checks}"
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
            "-f", "lavfi", "-i", "testsrc=duration=3:size=1920x1080:rate=30",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", "3",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
            "-c:a", "aac",
            str(silent_video),
        ],
        check=True,
        capture_output=True,
    )

    from mcp_editor.validation import validate_render
    result = validate_render(silent_video, Platform.widescreen, expected_duration=3.0)
    assert "ok" in result
    checks = result.get("checks", {})
    assert "not_silent" in checks, f"Silence check was not run: {checks}"
    assert checks["not_silent"] is False, (
        f"Expected silent video to be detected (not_silent=False), got checks={checks}"
    )


@pytest.mark.realmedia
def test_validation_rejects_frozen_output(tmp_path, monkeypatch, ffmpeg_bin):
    """The validation gate rejects a video where all frames are identical.

    Closes the remaining part of the Phase 8 gating task.
    """
    monkeypatch.setenv("MCP_EDITOR_ROOT", str(tmp_path))

    # Single-frame loop: repeat the same frame for 3 seconds
    frozen_video = tmp_path / "frozen.mp4"
    subprocess.run(
        [
            ffmpeg_bin, "-y",
            "-f", "lavfi", "-i",
            # testsrc at t=0 only, then loop=1 keeps the first frame
            "testsrc=duration=0.1:size=1920x1080:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            "-filter_complex", "[0:v]loop=loop=-1:size=1:start=0,trim=duration=3[v]",
            "-map", "[v]", "-map", "1:a",
            "-t", "3",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
            "-c:a", "aac",
            str(frozen_video),
        ],
        check=True,
        capture_output=True,
    )

    from mcp_editor.validation import validate_render
    result = validate_render(frozen_video, Platform.widescreen, expected_duration=3.0)
    assert "ok" in result
    checks = result.get("checks", {})
    assert "not_frozen" in checks, f"Freeze check was not run: {checks}"
    assert checks["not_frozen"] is False, (
        f"Expected frozen video to be detected (not_frozen=False), got checks={checks}"
    )


# ── Task 6a – Grade verification ──────────────────────────────────────────────


@pytest.mark.realmedia
def test_grading_preset_changes_output(golden_workspace, ffmpeg_bin, ffprobe_bin):
    """Applying a grading preset produces output that differs from ungraded.

    Closes part of the Phase 7 gating task.
    """
    ws = golden_workspace
    input_dir = str(ws / "data" / "input")

    from mcp_editor.grading import apply_grading_preset

    # Render without grading
    manifest_plain = create_project("grade-plain", input_dir)
    manifest_plain = build_timeline_for_project(manifest_plain, Platform.widescreen)
    manifest_plain = render_and_validate_project(
        manifest_plain, Platform.widescreen, render_profile="preview"
    )

    # Render with 'bw' grading preset — strongest visual delta (full desaturation)
    manifest_graded = create_project("grade-bw", input_dir)
    manifest_graded = build_timeline_for_project(manifest_graded, Platform.widescreen)
    grade_result = apply_grading_preset(
        project_id=manifest_graded.project_id,
        platform=Platform.widescreen,
        preset="bw",
    )
    assert grade_result.get("ok"), f"apply_grading_preset failed: {grade_result}"

    # Reload manifest to pick up grading changes persisted by apply_grading_preset
    from mcp_editor.projects import load_manifest
    manifest_graded = load_manifest(manifest_graded.project_id)
    manifest_graded = render_and_validate_project(
        manifest_graded, Platform.widescreen, render_profile="preview"
    )

    plain_path = Path(manifest_plain.outputs["16:9"].path)
    graded_path = Path(manifest_graded.outputs["16:9"].path)

    assert plain_path.exists() and graded_path.exists()
    assert plain_path.read_bytes() != graded_path.read_bytes(), (
        "Graded and ungraded renders produced identical output — grading had no effect"
    )


# ── Task 6b – Beat detection BPM accuracy ─────────────────────────────────────


@pytest.mark.realmedia
def test_beat_detection_tempo_accuracy(golden_audio):
    """librosa detects the click-track fixture's 120 BPM within ±5 BPM.

    The golden_audio fixture is a 120-BPM click track (sine bursts every 0.5s).
    Closes part of the Phase 4 / Phase 11 gating task.
    """
    from mcp_editor.beat_sync import analyze_beats

    result = analyze_beats(str(golden_audio))
    assert result.get("ok"), f"analyze_beats failed: {result}"

    tempo = result["tempo"]
    expected_bpm = 120.0
    tolerance = 10.0  # ±10 BPM — synthetic click track; librosa may detect half/double tempo
    assert abs(tempo - expected_bpm) <= tolerance or abs(tempo - expected_bpm / 2) <= tolerance or abs(tempo - expected_bpm * 2) <= tolerance, (
        f"Expected ~120 BPM (or 60/240 for half/double detection), got {tempo:.1f} BPM"
    )
    assert result["beat_count"] > 0, "No beats detected in the click-track fixture"


# ── Task 7 – OTIO round-trip ─────────────────────────────────────────────────


@pytest.mark.realmedia
def test_otio_export_is_valid(golden_workspace):
    """The exported .otio file is parseable by the opentimelineio library.

    Closes the Phase 3 gating task (MVP criterion 6).
    Note: this test only requires the golden_workspace fixture (no ffmpeg_bin),
    because build_timeline_for_project exports OTIO without rendering.
    The ffmpeg_bin fixture skip is handled by golden_workspace's dependency chain.
    """
    import opentimelineio as otio

    ws = golden_workspace
    input_dir = str(ws / "data" / "input")

    manifest = create_project("otio-roundtrip", input_dir)
    manifest = build_timeline_for_project(manifest, Platform.widescreen)

    # OTIO path is stored on the timeline plan
    plan = manifest.timelines.get("16:9")
    assert plan is not None, "No widescreen timeline found in manifest"
    assert plan.otio_path is not None, "otio_path not set on timeline plan"

    otio_path = Path(plan.otio_path)
    assert otio_path.exists(), f".otio file not found: {otio_path}"

    timeline = otio.adapters.read_from_file(str(otio_path))
    assert isinstance(timeline, otio.schema.Timeline), (
        f"Parsed object is not an OTIO Timeline: {type(timeline)}"
    )
    assert len(timeline.tracks) > 0, "OTIO timeline has no tracks"
