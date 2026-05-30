from __future__ import annotations

import argparse
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .beat_sync import analyze_beats as analyze_beats_impl
from .media import probe_media as probe_media_impl
from .media import scan_assets as scan_assets_impl
from .projects import load_manifest, save_manifest
from .schemas import Platform
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
    return {"ok": False, "error": str(exc), "error_type": exc.__class__.__name__}


@app.tool()
def scan_assets(input_dir: str = "data/input") -> dict[str, object]:
    """Scan a directory for local video assets and return FFprobe metadata."""
    assets = scan_assets_impl(input_dir, include_audio=False)
    return {"ok": True, "input_dir": str(Path(input_dir)), "assets": [asset.model_dump() for asset in assets]}


@app.tool()
def probe_media(path: str) -> dict[str, object]:
    """Probe one media file with FFprobe."""
    return probe_media_impl(path).model_dump()


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
