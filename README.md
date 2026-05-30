# mcp-editor

`mcp-editor` is a headless, local-first MCP video editing server for AI coding agents.

The project is intended to accept existing raw footage, music, LUTs, and project assets, then produce finished video exports and OpenTimelineIO timelines without a human review step between the initial prompt and final delivery.

The long-term system will focus on:

- Frame-precise NLE editing through OpenTimelineIO.
- Beat-synced cut planning from music analysis.
- FFmpeg-based rendering, visual effects, transitions, speed ramps, and zoom punches.
- LUT-backed color grading presets.
- Multi-platform exports for 9:16, 16:9, and 1:1.
- Automated output validation before delivery.
- MCP tools callable by agents such as Claude Code, Cursor, and Codex.

This repository currently contains the project scaffold, reference upstream sources, and environment verification scripts.
