from __future__ import annotations

from pathlib import Path

from .media import probe_media
from .schemas import PLATFORM_DIMENSIONS, Platform


def validate_render(path: str | Path, platform: Platform, expected_duration: float | None = None) -> dict[str, object]:
    probe = probe_media(path)
    checks: dict[str, bool] = {
        "exists": probe.exists,
        "probe_ok": probe.ok,
        "has_video": probe.has_video,
    }

    video_stream = next((stream for stream in probe.streams if stream.codec_type == "video"), None)
    expected_width, expected_height = PLATFORM_DIMENSIONS[platform]
    checks["resolution_matches"] = bool(
        video_stream and video_stream.width == expected_width and video_stream.height == expected_height
    )

    if expected_duration is not None and probe.duration is not None:
        checks["duration_close"] = abs(probe.duration - expected_duration) <= 1.0
    else:
        checks["duration_close"] = probe.duration is not None and probe.duration > 0

    return {
        "ok": all(checks.values()),
        "path": probe.path,
        "platform": platform.value,
        "checks": checks,
        "duration": probe.duration,
        "error": probe.error,
    }
