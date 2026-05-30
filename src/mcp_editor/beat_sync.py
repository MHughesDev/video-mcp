from __future__ import annotations

from pathlib import Path

import librosa

from .schemas import as_path


def analyze_beats(music_path: str | Path) -> dict[str, object]:
    path = as_path(music_path)
    if not path.exists():
        return {"ok": False, "path": str(path), "error": "file not found"}

    y, sr = librosa.load(str(path), sr=None, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    return {
        "ok": True,
        "path": str(path),
        "sample_rate": sr,
        "tempo": float(tempo[0] if hasattr(tempo, "__len__") else tempo),
        "beat_count": int(len(beat_times)),
        "beat_times": [float(time) for time in beat_times],
    }
