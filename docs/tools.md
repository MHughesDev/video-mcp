# MCP Tool Reference

This is the first MVP tool surface for `mcp-editor`. The server is intentionally deterministic: agents provide creative direction, and this server performs local media operations, timeline export, rendering, and validation.

## Failure Contract

Every MCP tool should return a structured failure instead of an opaque exception:

```json
{
  "ok": false,
  "error": {
    "code": "missing_dependency",
    "message": "ffmpeg was not found on PATH.",
    "suggested_fix": "Install FFmpeg and make sure both ffmpeg and ffprobe are available on PATH.",
    "details": {
      "binary": "ffmpeg"
    }
  }
}
```

Long-running workflow tools may also return callback-style events:

```json
{
  "ok": false,
  "events": [
    {"stage": "create_project", "status": "completed"},
    {"stage": "create_timeline", "status": "started"},
    {"stage": "workflow", "status": "failed"}
  ],
  "error": {
    "code": "no_video_assets",
    "message": "No usable video assets were found in data/input."
  }
}
```

Common error codes:

- `missing_dependency`: `ffmpeg` or `ffprobe` is not installed or not on `PATH`.
- `media_not_found`: a requested media file does not exist.
- `project_not_found`: a requested project manifest does not exist.
- `no_video_assets`: no usable source footage was found.
- `command_failed`: FFmpeg or FFprobe returned a non-zero exit code. Details include command, return code, stdout, and stderr.
- `invalid_probe_output`: FFprobe did not return parseable JSON.
- `invalid_request`: the tool arguments are invalid.
- `internal_error`: unexpected server-side failure.

## `scan_assets`

Scan a local input directory for video assets and return FFprobe metadata.

Parameters:

- `input_dir`: directory to scan. Defaults to `data/input`.

Returns:

- `ok`
- `input_dir`
- `assets`

## `probe_media`

Probe one media file with FFprobe.

Parameters:

- `path`: local media file path.

Returns:

- `path`
- `exists`
- `ok`
- `duration`
- `format_name`
- `bit_rate`
- `streams`
- `error`

## `create_project`

Create a project manifest from local assets.

Parameters:

- `name`: project name.
- `input_dir`: asset directory. Defaults to `data/input`.
- `music_path`: optional music file.
- `platforms`: optional list of `16:9`, `9:16`, or `1:1`.
- `prompt`: optional natural language request to store in the manifest.

Returns:

- `ok`
- `manifest`
- `manifest_path`

## `analyze_beats`

Analyze music tempo and beat timestamps with `librosa`.

Parameters:

- `music_path`: local music file path.

Returns:

- `ok`
- `path`
- `sample_rate`
- `tempo`
- `beat_count`
- `beat_times`
- `error`

## `create_timeline`

Create a simple sequential OTIO timeline for a project.

Parameters:

- `project_id`: existing project ID.
- `platform`: `16:9`, `9:16`, or `1:1`. Defaults to `16:9`.
- `target_duration`: requested timeline duration in seconds. Defaults to `30`.

Returns:

- `ok`
- `project_id`
- `timeline`
- `manifest_path`

## `render_project`

Render a project timeline with FFmpeg and validate the output.

Parameters:

- `project_id`: existing project ID.
- `platform`: `16:9`, `9:16`, or `1:1`. Defaults to `16:9`.
- `render_profile`: `preview` or higher quality profile. Defaults to `preview`.

Returns:

- `ok`
- `project_id`
- `output`
- `manifest_path`

## `validate_output`

Validate a rendered video file.

Parameters:

- `path`: rendered video path.
- `platform`: `16:9`, `9:16`, or `1:1`. Defaults to `16:9`.
- `expected_duration`: optional expected duration in seconds.

Returns:

- `ok`
- `path`
- `platform`
- `checks`
- `duration`
- `error`

## `edit_video_from_prompt`

Run the MVP end-to-end edit workflow from a natural language request.

Parameters:

- `prompt`: natural language editing request.
- `project_name`: optional project name. Defaults to `mvp-edit`.
- `input_dir`: asset directory. Defaults to `data/input`.
- `music_path`: optional music file for beat analysis.
- `platforms`: optional list of `16:9`, `9:16`, or `1:1`.
- `target_duration`: requested timeline duration in seconds. Defaults to `30`.
- `render`: whether to render outputs. Defaults to `true`.

Workflow:

1. Scan assets.
2. Create a project manifest.
3. Optionally analyze music beats.
4. Create OTIO timelines.
5. Optionally render platform outputs.
6. Validate rendered outputs.
7. Return a delivery manifest summary.

Returns:

- `ok`
- `project_id`
- `manifest_path`
- `beat_report`
- `timelines`
- `outputs`
