from __future__ import annotations

import argparse
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .beat_sync import analyze_beats as analyze_beats_impl
from .beat_sync import apply_edit_plan as apply_edit_plan_impl
from .beat_sync import plan_beat_synced_edit as plan_beat_synced_edit_impl
from .beat_sync import suggest_cut_points as suggest_cut_points_impl
from .diagnostics import failed_tool_result
from .inspection import analyze_audio_metadata as analyze_audio_metadata_impl
from .inspection import analyze_video_metadata as analyze_video_metadata_impl
from .inspection import detect_scenes as detect_scenes_impl
from .inspection import generate_thumbnails as generate_thumbnails_impl
from .inspection import inspect_project as inspect_project_impl
from .inspection import scan_project_assets as scan_project_assets_impl
from .media import probe_media as probe_media_impl
from .media import scan_assets as scan_assets_impl
from .projects import load_manifest, save_manifest
from .schemas import Platform
from .timeline_ops import add_clip_to_project
from .timeline_ops import add_transition_to_project
from .timeline_ops import export_timeline_for_project
from .timeline_ops import move_clip_in_project
from .timeline_ops import split_clip_in_project
from .timeline_ops import trim_clip_in_project
from .timeline_ops import validate_timeline_for_project
from .validation import validate_render as validate_render_impl
from .workflow import (
    build_timeline_for_project,
    create_project as create_project_impl,
    edit_video_from_prompt as edit_video_from_prompt_impl,
    render_and_validate_project,
)

app = FastMCP(
    "mcp-editor",
    instructions=(
        "Local-first video editing MCP server. Tools inspect existing media, "
        "build simple OTIO timelines, render via FFmpeg, and validate outputs."
    ),
)


def _platforms(values: list[str] | None) -> list[Platform]:
    if not values:
        return [Platform.widescreen]
    return [Platform(value) for value in values]


def _error(exc: Exception) -> dict[str, object]:
    return failed_tool_result(exc)


@app.tool()
def scan_assets(input_dir: str = "data/input") -> dict[str, object]:
    """Scan a directory for local video assets and return FFprobe metadata."""
    try:
        assets = scan_assets_impl(input_dir, include_audio=False)
        return {"ok": True, "input_dir": str(Path(input_dir)), "assets": [asset.model_dump() for asset in assets]}
    except Exception as exc:
        return _error(exc)


@app.tool()
def scan_project_assets(input_dir: str = "data/input", include_audio: bool = True) -> dict[str, object]:
    """Scan project assets with aggregate media counts and probe diagnostics."""
    try:
        return scan_project_assets_impl(input_dir=input_dir, include_audio=include_audio)
    except Exception as exc:
        return _error(exc)


@app.tool()
def probe_media(path: str) -> dict[str, object]:
    """Probe one media file with FFprobe."""
    try:
        probe = probe_media_impl(path)
        return probe.model_dump()
    except Exception as exc:
        return _error(exc)


@app.tool()
def analyze_video_metadata(path: str) -> dict[str, object]:
    """Return video-focused metadata for one media file."""
    try:
        return analyze_video_metadata_impl(path)
    except Exception as exc:
        return _error(exc)


@app.tool()
def analyze_audio_metadata(path: str) -> dict[str, object]:
    """Return audio-focused metadata for one media file."""
    try:
        return analyze_audio_metadata_impl(path)
    except Exception as exc:
        return _error(exc)


@app.tool()
def detect_scenes(path: str, threshold: float = 0.35, min_scene_gap: float = 0.5) -> dict[str, object]:
    """Detect likely scene-cut timestamps with FFmpeg scene scoring."""
    try:
        return detect_scenes_impl(path, threshold=threshold, min_scene_gap=min_scene_gap)
    except Exception as exc:
        return _error(exc)


@app.tool()
def generate_thumbnails(path: str, output_directory: str | None = None, count: int = 5) -> dict[str, object]:
    """Generate representative thumbnails for a video file."""
    try:
        return generate_thumbnails_impl(path, output_directory=output_directory, count=count)
    except Exception as exc:
        return _error(exc)


@app.tool()
def inspect_project(project_id: str) -> dict[str, object]:
    """Inspect a saved project manifest, timelines, outputs, and asset state."""
    try:
        return inspect_project_impl(project_id)
    except Exception as exc:
        return _error(exc)


@app.tool()
def create_project(
    name: str,
    input_dir: str = "data/input",
    music_path: str | None = None,
    platforms: list[str] | None = None,
    prompt: str | None = None,
) -> dict[str, object]:
    """Create a project manifest from local assets."""
    try:
        manifest = create_project_impl(
            name=name,
            input_dir=input_dir,
            music_path=music_path,
            platforms=_platforms(platforms),
            prompt=prompt,
        )
        return {"ok": True, "manifest": manifest.model_dump(), "manifest_path": str(save_manifest(manifest))}
    except Exception as exc:
        return _error(exc)


@app.tool()
def analyze_beats(music_path: str) -> dict[str, object]:
    """Analyze music tempo and beat timestamps with librosa."""
    try:
        return analyze_beats_impl(music_path)
    except Exception as exc:
        return _error(exc)


@app.tool()
def suggest_cut_points(
    beat_times: list[float] | None = None,
    target_duration: float = 30,
    style: str = "medium",
    tempo: float | None = None,
) -> dict[str, object]:
    """Suggest timeline cut points from beat times, tempo, target duration, and pacing style."""
    try:
        return suggest_cut_points_impl(
            beat_times=beat_times,
            target_duration=target_duration,
            style=style,
            tempo=tempo,
        )
    except Exception as exc:
        return _error(exc)


@app.tool()
def plan_beat_synced_edit(
    project_id: str,
    platform: str = "16:9",
    target_duration: float = 30,
    style: str = "medium",
    beat_times: list[float] | None = None,
    tempo: float | None = None,
) -> dict[str, object]:
    """Create and save a deterministic beat-synced edit plan for a project."""
    try:
        return plan_beat_synced_edit_impl(
            project_id=project_id,
            platform=Platform(platform),
            target_duration=target_duration,
            style=style,
            beat_times=beat_times,
            tempo=tempo,
        )
    except Exception as exc:
        return _error(exc)


@app.tool()
def apply_edit_plan(project_id: str, platform: str = "16:9") -> dict[str, object]:
    """Apply a saved beat edit plan to a project timeline and export OTIO."""
    try:
        return apply_edit_plan_impl(project_id=project_id, platform=Platform(platform))
    except Exception as exc:
        return _error(exc)


@app.tool()
def create_timeline(project_id: str, platform: str = "16:9", target_duration: float = 30) -> dict[str, object]:
    """Create a simple sequential OTIO timeline for a project."""
    try:
        manifest = load_manifest(project_id)
        manifest = build_timeline_for_project(manifest, Platform(platform), target_duration=target_duration)
        plan = manifest.timelines[platform]
        return {"ok": True, "project_id": project_id, "timeline": plan.model_dump(), "manifest_path": str(save_manifest(manifest))}
    except Exception as exc:
        return _error(exc)


@app.tool()
def add_clip(
    project_id: str,
    source: str,
    platform: str = "16:9",
    start: float = 0,
    duration: float = 4,
    label: str | None = None,
    index: int | None = None,
) -> dict[str, object]:
    """Add a clip to a project timeline and refresh the OTIO export."""
    try:
        return add_clip_to_project(
            project_id=project_id,
            platform=Platform(platform),
            source=source,
            start=start,
            duration=duration,
            label=label,
            index=index,
        )
    except Exception as exc:
        return _error(exc)


@app.tool()
def trim_clip(
    project_id: str,
    platform: str = "16:9",
    clip_id: str | None = None,
    index: int | None = None,
    start: float | None = None,
    duration: float | None = None,
) -> dict[str, object]:
    """Trim a clip by clip_id or index and refresh the OTIO export."""
    try:
        return trim_clip_in_project(
            project_id=project_id,
            platform=Platform(platform),
            clip_id=clip_id,
            index=index,
            start=start,
            duration=duration,
        )
    except Exception as exc:
        return _error(exc)


@app.tool()
def split_clip(
    project_id: str,
    split_at: float,
    platform: str = "16:9",
    clip_id: str | None = None,
    index: int | None = None,
) -> dict[str, object]:
    """Split a clip into two timeline clips and refresh the OTIO export."""
    try:
        return split_clip_in_project(
            project_id=project_id,
            platform=Platform(platform),
            split_at=split_at,
            clip_id=clip_id,
            index=index,
        )
    except Exception as exc:
        return _error(exc)


@app.tool()
def move_clip(project_id: str, from_index: int, to_index: int, platform: str = "16:9") -> dict[str, object]:
    """Move a clip within a project timeline and refresh the OTIO export."""
    try:
        return move_clip_in_project(
            project_id=project_id,
            platform=Platform(platform),
            from_index=from_index,
            to_index=to_index,
        )
    except Exception as exc:
        return _error(exc)


@app.tool()
def add_transition(
    project_id: str,
    from_clip_id: str,
    to_clip_id: str,
    platform: str = "16:9",
    transition_type: str = "crossfade",
    duration: float = 0.5,
) -> dict[str, object]:
    """Add a transition between adjacent timeline clips and refresh the OTIO export."""
    try:
        return add_transition_to_project(
            project_id=project_id,
            platform=Platform(platform),
            from_clip_id=from_clip_id,
            to_clip_id=to_clip_id,
            transition_type=transition_type,
            duration=duration,
        )
    except Exception as exc:
        return _error(exc)


@app.tool()
def export_timeline(project_id: str, platform: str = "16:9") -> dict[str, object]:
    """Export the current project timeline to OTIO."""
    try:
        return export_timeline_for_project(project_id=project_id, platform=Platform(platform))
    except Exception as exc:
        return _error(exc)


@app.tool()
def validate_timeline(project_id: str, platform: str = "16:9") -> dict[str, object]:
    """Validate a project timeline without rendering it."""
    try:
        return validate_timeline_for_project(project_id=project_id, platform=Platform(platform))
    except Exception as exc:
        return _error(exc)


@app.tool()
def render_project(project_id: str, platform: str = "16:9", render_profile: str = "preview") -> dict[str, object]:
    """Render a project timeline with FFmpeg and validate the output."""
    try:
        manifest = load_manifest(project_id)
        manifest = render_and_validate_project(manifest, Platform(platform), render_profile=render_profile)
        output = manifest.outputs[platform]
        return {"ok": output.ok, "project_id": project_id, "output": output.model_dump(), "manifest_path": str(save_manifest(manifest))}
    except Exception as exc:
        return _error(exc)


@app.tool()
def validate_output(path: str, platform: str = "16:9", expected_duration: float | None = None) -> dict[str, object]:
    """Validate a rendered video file."""
    try:
        return validate_render_impl(path, Platform(platform), expected_duration=expected_duration)
    except Exception as exc:
        return _error(exc)


@app.tool()
def edit_video_from_prompt(
    prompt: str,
    project_name: str = "mvp-edit",
    input_dir: str = "data/input",
    music_path: str | None = None,
    platforms: list[str] | None = None,
    target_duration: float = 30,
    render: bool = True,
) -> dict[str, object]:
    """Run the MVP end-to-end edit workflow from a natural language request."""
    try:
        return edit_video_from_prompt_impl(
            prompt=prompt,
            project_name=project_name,
            input_dir=input_dir,
            music_path=music_path,
            platforms=_platforms(platforms),
            target_duration=target_duration,
            render=render,
        )
    except Exception as exc:
        return _error(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the mcp-editor MCP server.")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "stdio":
        app.run("stdio")
        return

    app.settings.host = args.host
    app.settings.port = args.port
    app.run(args.transport)


if __name__ == "__main__":
    main()
