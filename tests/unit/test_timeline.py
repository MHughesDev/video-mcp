from pathlib import Path

from mcp_editor.schemas import Platform
from mcp_editor.timeline import export_otio, make_simple_timeline_plan


def test_make_simple_timeline_plan_limits_target_duration(tmp_path):
    clip_a = tmp_path / "a.mp4"
    clip_b = tmp_path / "b.mp4"
    clip_a.write_bytes(b"")
    clip_b.write_bytes(b"")

    plan = make_simple_timeline_plan(
        project_id="demo",
        asset_paths=[str(clip_a), str(clip_b)],
        platform=Platform.square,
        target_duration=6,
        default_clip_duration=4,
    )

    assert [clip.duration for clip in plan.clips] == [4, 2]
    assert plan.platform == Platform.square


def test_export_otio_writes_file(tmp_path):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"")
    plan = make_simple_timeline_plan(
        project_id="demo",
        asset_paths=[str(clip)],
        target_duration=4,
    )
    output = export_otio(plan, tmp_path / "timeline.otio")

    assert output.exists()
    assert "clip-1" in output.read_text(encoding="utf-8")
