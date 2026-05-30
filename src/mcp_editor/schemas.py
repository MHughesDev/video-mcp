from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Platform(str, Enum):
    widescreen = "16:9"
    vertical = "9:16"
    square = "1:1"


PLATFORM_DIMENSIONS: dict[Platform, tuple[int, int]] = {
    Platform.widescreen: (1920, 1080),
    Platform.vertical: (1080, 1920),
    Platform.square: (1080, 1080),
}


class MediaStream(BaseModel):
    index: int
    codec_type: str
    codec_name: str | None = None
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    r_frame_rate: str | None = None


class MediaProbe(BaseModel):
    path: str
    exists: bool
    ok: bool
    duration: float | None = None
    format_name: str | None = None
    bit_rate: int | None = None
    streams: list[MediaStream] = Field(default_factory=list)
    error: str | None = None
    error_code: str | None = None
    suggested_fix: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_video(self) -> bool:
        return any(stream.codec_type == "video" for stream in self.streams)

    @property
    def has_audio(self) -> bool:
        return any(stream.codec_type == "audio" for stream in self.streams)


class TimelineClip(BaseModel):
    clip_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    source: str
    start: float = 0
    duration: float
    label: str | None = None


class TimelineTransition(BaseModel):
    transition_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    from_clip_id: str
    to_clip_id: str
    transition_type: str = "crossfade"
    duration: float = 0.5


class TimelinePlan(BaseModel):
    project_id: str
    platform: Platform = Platform.widescreen
    clips: list[TimelineClip]
    transitions: list[TimelineTransition] = Field(default_factory=list)
    music_path: str | None = None
    target_duration: float | None = None
    otio_path: str | None = None


class RenderedOutput(BaseModel):
    platform: Platform
    path: str
    ok: bool
    validation: dict[str, Any] = Field(default_factory=dict)


class ProjectManifest(BaseModel):
    project_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    name: str
    prompt: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    input_dir: str = "data/input"
    music_path: str | None = None
    platforms: list[Platform] = Field(default_factory=lambda: [Platform.widescreen])
    assets: list[MediaProbe] = Field(default_factory=list)
    timelines: dict[str, TimelinePlan] = Field(default_factory=dict)
    outputs: dict[str, RenderedOutput] = Field(default_factory=dict)


def as_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()
