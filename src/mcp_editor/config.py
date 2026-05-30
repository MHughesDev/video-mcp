from __future__ import annotations

import os
from pathlib import Path


def workspace_root() -> Path:
    """Return the active mcp-editor workspace root."""
    configured = os.environ.get("MCP_EDITOR_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()

    cwd = Path.cwd().resolve()
    if (cwd / "data").is_dir() and (cwd / "pyproject.toml").is_file():
        return cwd

    for parent in cwd.parents:
        if (parent / "data").is_dir() and (parent / "pyproject.toml").is_file():
            return parent

    return cwd


def data_dir() -> Path:
    return workspace_root() / "data"


def projects_dir() -> Path:
    path = data_dir() / "projects"
    path.mkdir(parents=True, exist_ok=True)
    return path


def output_dir() -> Path:
    path = data_dir() / "output"
    path.mkdir(parents=True, exist_ok=True)
    return path
