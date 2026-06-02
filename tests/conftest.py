"""Root conftest for the mcp-editor test suite.

Registers the ``realmedia`` pytest marker and provides session-scoped
fixtures that synthesize tiny golden-media files using FFmpeg
``testsrc``/``sine`` filters.  If FFmpeg is absent the fixtures are
skipped automatically, keeping the default ``pytest tests/unit`` run
hermetic and fast.

Usage:
    # default – no real media required
    pytest tests/

    # opt-in to real-media tests (requires FFmpeg in PATH)
    pytest -m realmedia tests/

Fixtures provided
-----------------
ffmpeg_bin          – path to the ``ffmpeg`` executable (skips if absent)
ffprobe_bin         – path to the ``ffprobe`` executable (skips if absent)
golden_video        – path to a 5-second 1920×1080 synthetic H.264 clip
golden_audio        – path to a 10-second 120-BPM sine-wave audio file
golden_lut          – path to a minimal identity 3D LUT (.cube)
golden_workspace    – tmp_path workspace with the above assets in place
"""
from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest


# ── marker registration ───────────────────────────────────────────────────────


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "realmedia: tests that require real FFmpeg and synthesized media fixtures "
        "(deselect with -m 'not realmedia')",
    )


# ── binary availability ───────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def ffmpeg_bin():
    path = shutil.which("ffmpeg")
    if path is None:
        pytest.skip("ffmpeg not found in PATH – skipping real-media test")
    return path


@pytest.fixture(scope="session")
def ffprobe_bin():
    path = shutil.which("ffprobe")
    if path is None:
        pytest.skip("ffprobe not found in PATH – skipping real-media test")
    return path


# ── golden-media synthesis ────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def golden_video(tmp_path_factory, ffmpeg_bin):
    """5-second 1920×1080 30 fps H.264/AAC clip generated with FFmpeg testsrc."""
    out = tmp_path_factory.mktemp("golden") / "clip.mp4"
    subprocess.run(
        [
            ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=5:size=1920x1080:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "35",
            "-c:a", "aac", "-b:a", "64k",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


@pytest.fixture(scope="session")
def golden_audio(tmp_path_factory, ffmpeg_bin):
    """10-second 120-BPM click-track audio file (sine bursts at beat positions)."""
    out = tmp_path_factory.mktemp("golden") / "music.mp3"
    # 120 BPM = 2 Hz click track: use aevalsrc to generate a simple pulse wave
    subprocess.run(
        [
            ffmpeg_bin, "-y",
            "-f", "lavfi",
            "-i", "aevalsrc=sin(2*PI*440*t)*between(mod(t,0.5),0,0.05):s=44100:d=10",
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


@pytest.fixture(scope="session")
def golden_lut(tmp_path_factory):
    """Minimal 2×2×2 identity .cube LUT (no real transformation)."""
    out = tmp_path_factory.mktemp("golden") / "identity.cube"
    out.write_text(
        textwrap.dedent("""\
            TITLE "Identity"
            LUT_3D_SIZE 2
            0.0 0.0 0.0
            1.0 0.0 0.0
            0.0 1.0 0.0
            1.0 1.0 0.0
            0.0 0.0 1.0
            1.0 0.0 1.0
            0.0 1.0 1.0
            1.0 1.0 1.0
        """)
    )
    return out


@pytest.fixture()
def golden_workspace(tmp_path, monkeypatch, golden_video, golden_audio, golden_lut):
    """Full workspace with golden media in the expected directory layout.

    Sets ``MCP_EDITOR_ROOT`` so all mcp_editor modules resolve paths here.
    Returns the workspace root Path.
    """
    monkeypatch.setenv("MCP_EDITOR_ROOT", str(tmp_path))

    input_dir = tmp_path / "data" / "input"
    music_dir = tmp_path / "data" / "music"
    luts_dir = tmp_path / "data" / "luts"
    for d in (input_dir, music_dir, luts_dir):
        d.mkdir(parents=True)

    shutil.copy(golden_video, input_dir / "clip.mp4")
    shutil.copy(golden_audio, music_dir / "music.mp3")
    shutil.copy(golden_lut, luts_dir / "identity.cube")

    return tmp_path
