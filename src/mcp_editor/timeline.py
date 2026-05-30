from __future__ import annotations

from pathlib import Path

import opentimelineio as otio

from .projects import project_dir
from .schemas import Platform, TimelineClip, TimelinePlan, as_path


def make_simple_timeline_plan(
    project_id: str,
    asset_paths: list[str],
    platform: Platform = Platform.widescreen,
    target_duration: float | None = 30,
    default_clip_duration: float = 4,
    music_path: str | None = None,
) -> TimelinePlan:
    clips: list[TimelineClip] = []
    remaining = target_duration

    for asset in asset_paths:
        if remaining is not None and remaining <= 0:
            break
        duration = default_clip_duration if remaining is None else min(default_clip_duration, remaining)
        clips.append(TimelineClip(source=str(as_path(asset)), start=0, duration=duration))
        if remaining is not None:
            remaining -= duration

    return TimelinePlan(
        project_id=project_id,
        platform=platform,
        clips=clips,
        music_path=str(as_path(music_path)) if music_path else None,
        target_duration=target_duration,
    )


def export_otio(plan: TimelinePlan, output_path: str | Path | None = None) -> Path:
    output = Path(output_path) if output_path else project_dir(plan.project_id) / f"timeline_{plan.platform.value.replace(':', 'x')}.otio"
    timeline = otio.schema.Timeline(name=f"{plan.project_id}-{plan.platform.value}")
    track = otio.schema.Track(name="Video 1", kind=otio.schema.TrackKind.Video)

    cursor = 0.0
    for index, clip in enumerate(plan.clips, start=1):
        source = as_path(clip.source)
        media_ref = otio.schema.ExternalReference(
            target_url=source.as_uri(),
            available_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, 30),
                duration=otio.opentime.RationalTime(clip.duration * 30, 30),
            ),
        )
        otio_clip = otio.schema.Clip(name=clip.label or f"clip-{index}", media_reference=media_ref)
        otio_clip.source_range = otio.opentime.TimeRange(
            start_time=otio.opentime.RationalTime(clip.start * 30, 30),
            duration=otio.opentime.RationalTime(clip.duration * 30, 30),
        )
        otio_clip.metadata["mcp_editor"] = {"timeline_start": cursor}
        track.append(otio_clip)
        cursor += clip.duration

    timeline.tracks.append(track)
    output.parent.mkdir(parents=True, exist_ok=True)
    otio.adapters.write_to_file(timeline, str(output))
    return output
