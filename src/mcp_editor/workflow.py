from __future__ import annotations

from pathlib import Path

from .beat_sync import analyze_beats
from .beat_sync import apply_edit_plan as apply_beat_edit_plan
from .beat_sync import plan_beat_synced_edit
from .diagnostics import McpEditorError, WorkflowError, event, exception_issue, no_video_assets
from .media import scan_assets
from .projects import save_manifest, slugify
from .projects import load_manifest
from .render import render_timeline
from .schemas import Platform, ProjectManifest, RenderedOutput
from .timeline import export_otio, make_simple_timeline_plan
from .validation import validate_render


def create_project(
    name: str,
    input_dir: str = "data/input",
    music_path: str | None = None,
    platforms: list[Platform] | None = None,
    prompt: str | None = None,
) -> ProjectManifest:
    manifest = ProjectManifest(
        name=slugify(name),
        input_dir=input_dir,
        music_path=music_path,
        platforms=platforms or [Platform.widescreen],
        prompt=prompt,
        assets=scan_assets(input_dir, include_audio=False),
    )
    save_manifest(manifest)
    return manifest


def build_timeline_for_project(
    manifest: ProjectManifest,
    platform: Platform,
    target_duration: float = 30,
) -> ProjectManifest:
    video_assets = [asset.path for asset in manifest.assets if asset.ok and asset.has_video]
    if not video_assets:
        raise McpEditorError(no_video_assets(manifest.input_dir))

    plan = make_simple_timeline_plan(
        project_id=manifest.project_id,
        asset_paths=video_assets,
        platform=platform,
        target_duration=target_duration,
        music_path=manifest.music_path,
    )
    otio_path = export_otio(plan)
    plan.otio_path = str(otio_path)
    manifest.timelines[platform.value] = plan
    save_manifest(manifest)
    return manifest


def render_and_validate_project(
    manifest: ProjectManifest,
    platform: Platform,
    render_profile: str = "preview",
) -> ProjectManifest:
    plan = manifest.timelines.get(platform.value)
    if plan is None:
        manifest = build_timeline_for_project(manifest, platform)
        plan = manifest.timelines[platform.value]

    output = render_timeline(plan, render_profile=render_profile)
    expected_duration = sum(clip.duration for clip in plan.clips)
    validation = validate_render(output, platform, expected_duration=expected_duration)
    manifest.outputs[platform.value] = RenderedOutput(
        platform=platform,
        path=str(output),
        ok=bool(validation["ok"]),
        validation=validation,
    )
    save_manifest(manifest)
    return manifest


def edit_video_from_prompt(
    prompt: str,
    project_name: str = "mvp-edit",
    input_dir: str = "data/input",
    music_path: str | None = None,
    platforms: list[Platform] | None = None,
    target_duration: float = 30,
    render: bool = True,
) -> dict[str, object]:
    selected_platforms = platforms or [Platform.widescreen]
    events: list[dict[str, object]] = []

    try:
        events.append(event("create_project", "started", input_dir=input_dir))
        manifest = create_project(
            name=project_name,
            input_dir=input_dir,
            music_path=music_path,
            platforms=selected_platforms,
            prompt=prompt,
        )
        events.append(
            event(
                "create_project",
                "completed",
                project_id=manifest.project_id,
                asset_count=len(manifest.assets),
                usable_video_count=len([asset for asset in manifest.assets if asset.ok and asset.has_video]),
            )
        )

        beat_report = None
        if music_path:
            events.append(event("analyze_beats", "started", music_path=music_path))
            beat_report = analyze_beats(music_path)
            events.append(
                event(
                    "analyze_beats",
                    "completed" if beat_report.get("ok") else "failed",
                    beat_count=beat_report.get("beat_count"),
                    error=beat_report.get("error"),
                )
            )

        for platform in selected_platforms:
            if beat_report and beat_report.get("ok"):
                events.append(event("plan_beat_synced_edit", "started", platform=platform.value))
                plan_result = plan_beat_synced_edit(
                    project_id=manifest.project_id,
                    platform=platform,
                    target_duration=target_duration,
                    style="medium",
                    beat_times=[float(value) for value in beat_report.get("beat_times", [])],
                    tempo=float(beat_report["tempo"]),
                )
                events.append(
                    event(
                        "plan_beat_synced_edit",
                        "completed",
                        platform=platform.value,
                        clip_count=len(plan_result["edit_plan"]["clips"]),
                    )
                )
                events.append(event("apply_edit_plan", "started", platform=platform.value))
                apply_result = apply_beat_edit_plan(project_id=manifest.project_id, platform=platform)
                manifest = load_manifest(manifest.project_id)
                events.append(
                    event(
                        "apply_edit_plan",
                        "completed" if apply_result.get("ok") else "failed",
                        platform=platform.value,
                        otio_path=apply_result.get("otio_path"),
                        validation=apply_result.get("validation"),
                    )
                )
            else:
                events.append(event("create_timeline", "started", platform=platform.value))
                manifest = build_timeline_for_project(manifest, platform, target_duration=target_duration)
                events.append(
                    event(
                        "create_timeline",
                        "completed",
                        platform=platform.value,
                        otio_path=manifest.timelines[platform.value].otio_path,
                        clip_count=len(manifest.timelines[platform.value].clips),
                    )
                )

            if render:
                events.append(event("render_project", "started", platform=platform.value))
                manifest = render_and_validate_project(manifest, platform)
                output = manifest.outputs[platform.value]
                events.append(
                    event(
                        "render_project",
                        "completed" if output.ok else "failed",
                        platform=platform.value,
                        output_path=output.path,
                        validation=output.validation,
                    )
                )

        return {
            "ok": all(output.ok for output in manifest.outputs.values()) if render else True,
            "project_id": manifest.project_id,
            "manifest_path": str(save_manifest(manifest)),
            "events": events,
            "beat_report": beat_report,
            "timelines": {key: plan.otio_path for key, plan in manifest.timelines.items()},
            "outputs": {key: output.model_dump() for key, output in manifest.outputs.items()},
        }
    except Exception as exc:
        events.append(event("workflow", "failed", error=exception_issue(exc).model_dump()))
        raise WorkflowError(exception_issue(exc), events) from exc
