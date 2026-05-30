from __future__ import annotations

import subprocess
from pathlib import Path

from .config import output_dir
from .diagnostics import DiagnosticIssue, McpEditorError, command_failed
from .media import probe_media, require_binary
from .projects import project_dir
from .schemas import PLATFORM_DIMENSIONS, Platform, TimelinePlan, as_path


def _platform_filter(platform: Platform) -> str:
    width, height = PLATFORM_DIMENSIONS[platform]
    return f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1"


def _run_command(stage: str, cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise command_failed(stage, cmd, exc) from exc


def render_timeline(
    plan: TimelinePlan,
    output_path: str | Path | None = None,
    render_profile: str = "preview",
) -> Path:
    ffmpeg = require_binary("ffmpeg")
    if not plan.clips:
        raise ValueError("timeline has no clips to render")

    project_work_dir = project_dir(plan.project_id) / "segments" / plan.platform.value.replace(":", "x")
    project_work_dir.mkdir(parents=True, exist_ok=True)
    segment_paths: list[Path] = []
    width, height = PLATFORM_DIMENSIONS[plan.platform]
    crf = "28" if render_profile == "preview" else "20"

    for index, clip in enumerate(plan.clips, start=1):
        source = as_path(clip.source)
        probe = probe_media(source)
        if not probe.ok or not probe.has_video:
            raise McpEditorError(
                issue=DiagnosticIssue(
                    code=probe.error_code or "invalid_media",
                    message=f"Cannot render source as video: {source}",
                    suggested_fix=probe.suggested_fix or "Use a valid video file with a readable video stream.",
                    details={
                        "source": str(source),
                        "probe_ok": probe.ok,
                        "has_video": probe.has_video,
                        "probe_error": probe.error,
                        "probe_details": probe.details,
                    },
                )
            )

        segment = project_work_dir / f"segment_{index:04d}.mp4"
        cmd = [
            ffmpeg,
            "-y",
            "-ss",
            str(max(0, clip.start)),
            "-t",
            str(max(0.1, clip.duration)),
            "-i",
            str(source),
            "-map",
            "0:v:0",
        ]
        if probe.has_audio:
            cmd += ["-map", "0:a:0?", "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "160k"]
        else:
            cmd += ["-an"]
        cmd += [
            "-vf",
            _platform_filter(plan.platform),
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            crf,
            "-pix_fmt",
            "yuv420p",
            str(segment),
        ]
        _run_command(f"render_segment_{index}", cmd)
        segment_paths.append(segment)

    concat_file = project_work_dir / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in segment_paths),
        encoding="utf-8",
    )

    output = Path(output_path) if output_path else output_dir() / f"{plan.project_id}_{plan.platform.value.replace(':', 'x')}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(output),
    ]
    _run_command("concat_segments", cmd)

    if not output.exists():
        raise RuntimeError("render command completed without producing output")
    if width <= 0 or height <= 0:
        raise RuntimeError("invalid platform dimensions")
    return output
