# Blender Agent

Drive Blender via HTTP POST to `localhost:5656`. The addon runs Python code in Blender's main thread and returns JSON.

## How to send commands

```bash
curl -s localhost:5656 -d 'bpy.data.objects.keys()'
```

Response: `{"ok": true, "result": ..., "output": "..."}` or `{"ok": false, "error": "..."}`

- `result` = return value of the last expression (auto JSON-serialized)
- `output` = captured stdout (print statements)
- Multi-line scripts work: the last expression's value is returned

## Starting Blender

```bash
/Applications/Blender.app/Contents/MacOS/Blender --python start_server.py &
```

This opens Blender and auto-starts the HTTP server on port 5656.
Splash screen is disabled via user preferences (`view.show_splash = False`).

## Restarting Blender

```bash
# Graceful quit (if server is responding)
curl -s localhost:5656 -d 'bpy.ops.wm.quit_blender()' || true
sleep 1
# Force kill if still running
pkill -x Blender 2>/dev/null || true
sleep 1
# Relaunch
/Applications/Blender.app/Contents/MacOS/Blender --python start_server.py &
sleep 5
# Verify
curl -s localhost:5656 -d 'bpy.app.version_string'
```

## Screenshots (visual feedback)

Take a screenshot of the Blender UI and read it to see what's happening:
```bash
curl -s localhost:5656 -d 'bpy.ops.screen.screenshot(filepath="/tmp/blender_ui.png")'
```
Then use the Read tool on `/tmp/blender_ui.png` to inspect the result visually.

For rendered frames (3D or VSE output), render to a file and read it:
```bash
curl -s localhost:5656 -d '
scene = bpy.context.scene
scene.render.filepath = "/tmp/blender_render.png"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 50
bpy.ops.render.render(write_still=True)
'
```
Then read `/tmp/blender_render.png`.

Use this feedback loop when iterating: make changes, screenshot/render, inspect, adjust.

## Crash reports

macOS crash dumps: `~/Library/Logs/DiagnosticReports/Blender-*.ips`

## Project structure

```
blender_agent/__init__.py    # The Blender addon (HTTP server + exec engine)
blender_agent/blender_manifest.toml
start_server.py              # Auto-start script for CLI launch
.claude/commands/             # Claude Code skills for Blender workflows
```

## Reference code

`../blender-mcp` contains a Blender MCP integration (by ahujasid). Useful as reference for:
- Blender Python API patterns (addon.py ~2600 lines)
- MCP server implementation (src/blender_mcp/server.py)
- How others structure Blender automation

## Blender version

Target **Blender 5.0+** only. No backwards compatibility needed.

### Key API differences in Blender 5.0

- Sequence editor strips: `scene.sequence_editor.strips` (not `.sequences`)
- Strip creation: `strips.new_effect()`, `strips.new_movie()`, etc. (not `sequences.new_effect()`)
- TRANSFORM is no longer a valid effect strip type — use `strip.transform` property instead
- Strip types renamed: classes like `TextSequence` → `TextStrip` in RNA
- **Video render**: must set `image_settings.media_type = 'VIDEO'` before `file_format = 'FFMPEG'`

## Known Blender 5.0.1 bugs

- **Strip modifiers crash**: calling `strip.modifiers.new()` causes a segfault in `rna_Strip_modifier_new`. Avoid until fixed.
- **Render can crash**: rendering with certain threading configurations can segfault in `libIlmThread`. Use `resolution_percentage = 50` or lower for safety during testing.
