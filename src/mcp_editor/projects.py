from __future__ import annotations

import json
import re
from pathlib import Path

from .config import projects_dir
from .schemas import ProjectManifest


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def project_dir(project_id: str) -> Path:
    path = projects_dir() / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def manifest_path(project_id: str) -> Path:
    return project_dir(project_id) / "manifest.json"


def save_manifest(manifest: ProjectManifest) -> Path:
    path = manifest_path(manifest.project_id)
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_manifest(project_id: str) -> ProjectManifest:
    path = manifest_path(project_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    return ProjectManifest.model_validate(data)
