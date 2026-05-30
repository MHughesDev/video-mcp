from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .config import output_dir
from .diagnostics import DiagnosticIssue, McpEditorError, command_failed
from .effects import build_clip_af, build_clip_vf, source_read_duration
from .media import probe_media, require_binary
from .projects import project_dir
from .schemas import PLATFORM_DIMENSIONS, Platform, RenderCommand, RenderManifest, TimelinePlan, as_path


RENDER_PROFILES: dict[str, dict[str, str]] = {
    "preview": {"crf": "28", "preset": "veryfast", "audio_bitrate": "128k"},
    "standard": {"crf": "23", "preset": "fast", "audio_bitrate": "160k"},
    "high": {"crf": "18", "preset": "slow", "audio_bitrate": "192k"},
}


def _run_command(stage: str, cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise command_failed(stage, cmd, exc) from exc


def _profile(render_profile: str) -> dict[str, str]:
    if render_profile not in RENDER_PROFILES:
        raise ValueError(f"unknown render_profile: {render_profile}")
    return RENDER_PROFILES[render_profile]


def plan_render_timeline(
    plan: TimelinePlan,
    output_path: str | Path | None = None,
    render_profile: str = "preview",
    ffmpeg_binary: str = "ffmpeg",
    validate_sources: bool = True,
) -> RenderManifest:
    profile = _profile(render_profile)
    if not plan.clips:
        raise ValueError("timeline has no clips to render")

    project_work_dir = project_dir(plan.project_id) / "segments" / plan.platform.value.replace(":", "x")
    width, height = PLATFORM_DIMENSIONS[plan.platform]
    output = Path(output_path) if output_path else output_dir() / f"{plan.project_id}_{plan.platform.value.replace(':', 'x')}.mp4"
    concat_file = project_work_dir / "concat.txt"
    commands: list[RenderCommand] = []
    segment_paths: list[str] = []

    for index, clip in enumerate(plan.clips, start=1):
        source = as_path(clip.source)
        has_audio = True
        if validate_sources:
            probe = probe_media(source)
            has_audio = probe.has_audio
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
        read_duration = source_read_duration(clip)
        cmd = [
            ffmpeg_binary,
            "-y",
            "-ss",
            str(max(0, clip.start)),
            "-t",
            str(max(0.1, read_duration)),
            "-i",
            str(source),
            "-map",
            "0:v:0",
        ]
        extra_af = build_clip_af(clip)
        if has_audio:
            af_chain = ",".join(["aresample=async=1"] + extra_af)
            cmd += ["-map", "0:a:0?", "-af", af_chain, "-c:a", "aac", "-b:a", profile["audio_bitrate"]]
        else:
            cmd += ["-an"]
        cmd += [
            "-vf",
            build_clip_vf(clip, plan.platform),
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            profile["preset"],
            "-crf",
            profile["crf"],
            "-pix_fmt",
            "yuv420p",
            str(segment),
        ]
        commands.append(RenderCommand(stage=f"render_segment_{index}", command=cmd, output_path=str(segment)))
        segment_paths.append(str(segment))

    concat_cmd = [
        ffmpeg_binary,
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
    commands.append(RenderCommand(stage="concat_segments", command=concat_cmd, output_path=str(output)))

    return RenderManifest(
        project_id=plan.project_id,
        platform=plan.platform,
        render_profile=render_profile,
        output_path=str(output),
        work_dir=str(project_work_dir),
        expected_duration=sum(clip.duration for clip in plan.clips),
        dimensions=(width, height),
        commands=commands,
        segment_paths=segment_paths,
        concat_file=str(concat_file),
    )


def write_render_manifest(manifest: RenderManifest, path: str | Path | None = None) -> Path:
    output = Path(path) if path else project_dir(manifest.project_id) / f"render_{manifest.platform.value.replace(':', 'x')}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return output


def execute_render_manifest(manifest: RenderManifest) -> Path:
    work_dir = Path(manifest.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    if manifest.concat_file:
        concat_path = Path(manifest.concat_file)
        concat_path.parent.mkdir(parents=True, exist_ok=True)
        concat_path.write_text(
            "\n".join(f"file '{Path(path).as_posix()}'" for path in manifest.segment_paths),
            encoding="utf-8",
        )

    for command in manifest.commands:
        _run_command(command.stage, command.command)

    output = Path(manifest.output_path)

    if not output.exists():
        raise RuntimeError("render command completed without producing output")
    if manifest.dimensions[0] <= 0 or manifest.dimensions[1] <= 0:
        raise RuntimeError("invalid platform dimensions")
    return output


def render_timeline(
    plan: TimelinePlan,
    output_path: str | Path | None = None,
    render_profile: str = "preview",
    dry_run: bool = False,
) -> Path | RenderManifest:
    ffmpeg = "ffmpeg" if dry_run else require_binary("ffmpeg")
    manifest = plan_render_timeline(
        plan,
        output_path=output_path,
        render_profile=render_profile,
        ffmpeg_binary=ffmpeg,
        validate_sources=not dry_run,
    )
    manifest.dry_run = dry_run
    if dry_run:
        write_render_manifest(manifest)
        return manifest
    output = execute_render_manifest(manifest)
    write_render_manifest(manifest)
    return output


def render_manifest_summary(manifest: RenderManifest) -> dict[str, Any]:
    return {
        "ok": True,
        "project_id": manifest.project_id,
        "platform": manifest.platform.value,
        "render_profile": manifest.render_profile,
        "dry_run": manifest.dry_run,
        "output_path": manifest.output_path,
        "work_dir": manifest.work_dir,
        "expected_duration": manifest.expected_duration,
        "dimensions": manifest.dimensions,
        "command_count": len(manifest.commands),
        "commands": [command.model_dump() for command in manifest.commands],
        "segment_paths": manifest.segment_paths,
        "concat_file": manifest.concat_file,
    }
