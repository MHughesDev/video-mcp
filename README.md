# mcp-editor

`mcp-editor` is a headless, local-first MCP video editing server for AI coding agents.

It is designed to run on your own machine, accept existing footage and assets, expose deterministic editing operations as MCP tools, and return rendered video outputs plus OpenTimelineIO timelines. There is no UI and no hosted cloud dependency.

## MVP Status

The first MVP includes:

- A Python package and `mcp-editor` console entry point.
- A FastMCP server that runs over stdio or streamable HTTP.
- Asset scanning and FFprobe metadata tools.
- Richer media inspection tools for video metadata, audio metadata, scene detection, thumbnails, and project inspection.
- Project manifest creation under `data/projects/`.
- Basic OpenTimelineIO export.
- Optional `librosa` beat analysis for music files.
- A simple FFmpeg render path for 16:9, 9:16, and 1:1 variants.
- Output validation for existence, probe success, duration, and platform resolution.
- A one-shot `edit_video_from_prompt` tool that runs the MVP pipeline deterministically.

The prompt is stored in the manifest, but creative interpretation remains the responsibility of the calling agent.

## Requirements

- Python 3.11+
- `uv`
- FFmpeg and FFprobe on `PATH`
- Git

Install FFmpeg:

```powershell
winget install Gyan.FFmpeg
```

macOS:

```bash
brew install ffmpeg
```

Ubuntu/Debian:

```bash
sudo apt install ffmpeg
```

## Setup

```bash
uv venv --python 3.11 .venv
uv pip install -e ".[dev]"
./scripts/verify.sh
```

On Windows PowerShell, if `uv` was installed to the default user directory but is not on `PATH`, use:

```powershell
& "$env:USERPROFILE\.local\bin\uv.exe" pip install -e ".[dev]"
```

## Run As A Custom MCP Server

Stdio mode is the recommended mode for Cursor and other coding agents:

```bash
mcp-editor --transport stdio
```

Or with Python directly:

```bash
python -m mcp_editor.server --transport stdio
```

Streamable HTTP mode is also available:

```bash
mcp-editor --transport streamable-http --host 127.0.0.1 --port 8000
```

See [docs/custom-mcp-server.md](docs/custom-mcp-server.md) for Cursor/custom MCP configuration examples.

## MVP Tools

- `scan_assets`
- `scan_project_assets`
- `probe_media`
- `analyze_video_metadata`
- `analyze_audio_metadata`
- `detect_scenes`
- `generate_thumbnails`
- `inspect_project`
- `create_project`
- `analyze_beats`
- `create_timeline`
- `render_project`
- `validate_output`
- `edit_video_from_prompt`

See [docs/tools.md](docs/tools.md) for tool details.

## Data Layout

- `data/input/`: raw footage and assets
- `data/music/`: music tracks
- `data/luts/`: LUT files
- `data/projects/`: manifests and OTIO files
- `data/output/`: rendered videos

Data subdirectories are tracked, but their contents are ignored by git.
