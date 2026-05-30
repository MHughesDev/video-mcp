# Connecting mcp-editor To Coding Agents

`mcp-editor` runs as a local MCP server. The recommended MVP connection mode is stdio because it works well for Cursor, Claude Desktop, and other custom MCP clients.

## Install Locally

From the repository root:

```bash
uv venv --python 3.11 .venv
uv pip install -e ".[dev]"
```

FFmpeg must also be installed and available on `PATH`.

Windows:

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

## Cursor MCP Configuration

Use the absolute path to this repository as `MCP_EDITOR_ROOT`.

```json
{
  "mcpServers": {
    "mcp-editor": {
      "command": "C:\\Users\\Mason\\Desktop\\coding_projects\\video-mcp\\mcp-editor\\.venv\\Scripts\\mcp-editor.exe",
      "args": ["--transport", "stdio"],
      "env": {
        "MCP_EDITOR_ROOT": "C:\\Users\\Mason\\Desktop\\coding_projects\\video-mcp\\mcp-editor"
      }
    }
  }
}
```

If your client launches Python directly instead of console scripts:

```json
{
  "mcpServers": {
    "mcp-editor": {
      "command": "C:\\Users\\Mason\\Desktop\\coding_projects\\video-mcp\\mcp-editor\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_editor.server", "--transport", "stdio"],
      "env": {
        "MCP_EDITOR_ROOT": "C:\\Users\\Mason\\Desktop\\coding_projects\\video-mcp\\mcp-editor"
      }
    }
  }
}
```

## HTTP Mode

For clients that support streamable HTTP:

```bash
mcp-editor --transport streamable-http --host 127.0.0.1 --port 8000
```

The MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

## MVP Tool Surface

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
- `suggest_cut_points`
- `plan_beat_synced_edit`
- `apply_edit_plan`
- `create_timeline`
- `add_clip`
- `trim_clip`
- `split_clip`
- `move_clip`
- `add_transition`
- `export_timeline`
- `validate_timeline`
- `plan_render`
- `render_project`
- `render_platform_variant`
- `render_all_variants`
- `validate_output`
- `edit_video_from_prompt`

The first MVP is deterministic. The natural language prompt is stored in the manifest, while the calling agent remains responsible for creative interpretation.
