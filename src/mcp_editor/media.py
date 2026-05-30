from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .schemas import MediaProbe, MediaStream, as_path

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def require_binary(name: str) -> str:
    binary = shutil.which(name)
    if not binary:
        raise RuntimeError(
            f"{name} was not found on PATH. Install FFmpeg and ensure {name} is available."
        )
    return binary


def _float_or_none(value: object) -> float | None:
    try:
        if value in (None, "N/A"):
            return None
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _int_or_none(value: object) -> int | None:
    try:
        if value in (None, "N/A"):
            return None
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def probe_media(path: str | Path) -> MediaProbe:
    media_path = as_path(path)
    if not media_path.exists():
        return MediaProbe(path=str(media_path), exists=False, ok=False, error="file not found")

    try:
        ffprobe = require_binary("ffprobe")
    except RuntimeError as exc:
        return MediaProbe(path=str(media_path), exists=True, ok=False, error=str(exc))

    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(media_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        payload = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        return MediaProbe(path=str(media_path), exists=True, ok=False, error=str(exc))

    streams = [
        MediaStream(
            index=int(stream.get("index", 0)),
            codec_type=str(stream.get("codec_type", "")),
            codec_name=stream.get("codec_name"),
            width=_int_or_none(stream.get("width")),
            height=_int_or_none(stream.get("height")),
            duration=_float_or_none(stream.get("duration")),
            r_frame_rate=stream.get("r_frame_rate"),
        )
        for stream in payload.get("streams", [])
    ]
    fmt = payload.get("format", {})
    return MediaProbe(
        path=str(media_path),
        exists=True,
        ok=True,
        duration=_float_or_none(fmt.get("duration")),
        format_name=fmt.get("format_name"),
        bit_rate=_int_or_none(fmt.get("bit_rate")),
        streams=streams,
    )


def scan_assets(input_dir: str | Path, include_audio: bool = True) -> list[MediaProbe]:
    root = as_path(input_dir)
    if not root.exists():
        return []

    extensions = VIDEO_EXTENSIONS | (AUDIO_EXTENSIONS if include_audio else set())
    paths = sorted(path for path in root.rglob("*") if path.suffix.lower() in extensions)
    return [probe_media(path) for path in paths]
