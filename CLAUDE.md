# Blender Agent

Drive Blender via HTTP POST to `localhost:5656`. The addon runs Python code in Blender's main thread and returns JSON.

## How to send commands

Always use heredoc to avoid shell quoting issues with Python code:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
bpy.data.objects.keys()
PYEOF
```

Use `<<'PYEOF'` (quoted delimiter) so the shell doesn't expand `$variables` or backticks.

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

### Opening an existing scene

```bash
/Applications/Blender.app/Contents/MacOS/Blender /path/to/scene.blend --python start_server.py &
```

Or if Blender is already running with the server, open a file via code:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
bpy.ops.wm.open_mainfile(filepath="/path/to/scene.blend")
PYEOF
```

If the user already has Blender open without the server, they can start it from the
3D Viewport sidebar (press `N` > Agent tab > Start).

## Connecting to an existing scene

Before starting work, always check if Blender is already running:

1. `curl -s localhost:5656` — if it responds, the server is up
2. Inspect what's already there: `bpy.data.objects.keys()`
3. **Never assume a clean scene.** Don't delete objects or clear data unless the user
   asks for a fresh start. The user may have an in-progress scene they want help with.

If the server is not running, ask the user whether they want to start fresh or have
a scene they'd like to open.

## Restarting Blender

```bash
# Graceful quit (if server is responding)
curl -s localhost:5656 --data-binary @- <<< 'bpy.ops.wm.quit_blender()' || true
sleep 1
# Force kill if still running
pkill -x Blender 2>/dev/null || true
sleep 1
# Relaunch
/Applications/Blender.app/Contents/MacOS/Blender --python start_server.py &
sleep 5
# Verify
curl -s localhost:5656 --data-binary @- <<< 'bpy.app.version_string'
```

## Screenshots (visual feedback)

A `SESSION` variable is automatically injected into every code execution. It points to
the current session's output directory (e.g. `output/2026-02-26-1430`). Use it for all output.

Take a screenshot of the Blender UI and read it to see what's happening:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
bpy.ops.screen.screenshot(filepath=f"{SESSION}/blender_ui.png")
PYEOF
```
Then use the Read tool on the screenshot path to inspect the result visually.

For rendered frames (3D or VSE output), render to a file and read it:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
scene = bpy.context.scene
scene.render.filepath = f"{SESSION}/render.png"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 50
bpy.ops.render.render(write_still=True)
PYEOF
```
Then read the rendered image.

Use this feedback loop when iterating: make changes, screenshot/render, inspect, adjust.

## Crash reports

macOS crash dumps: `~/Library/Logs/DiagnosticReports/Blender-*.ips`

## Output directory

All render output goes to the gitignored `output/` directory, organized by session.

Each Blender start creates a timestamped session directory: `output/YYYY-MM-DD-HHMM/`.
The `SESSION` variable (available in all code sent to Blender) points to it. Use
`f"{SESSION}/filename.png"` for all output paths. Previous sessions are preserved.

Never render to `/tmp`. Always use `SESSION` paths.

## Project structure

```
blender_agent/__init__.py    # The Blender addon (HTTP server + exec engine)
blender_agent/blender_manifest.toml
start_server.py              # Auto-start script for CLI launch
output/                      # Render output (gitignored)
.claude/skills/              # Agent Skills (auto-loaded by Claude when relevant)
  blender/                   # General Blender automation
  blender-3d/                # 3D scenes, materials, animation, rendering
  blender-vse/               # Video Sequence Editor
  blender-geometry-nodes/    # Geometry Nodes (procedural geometry, instancing)
```

## Reference code

`../blender-mcp` contains a Blender MCP integration (by ahujasid). Useful as reference for:
- Blender Python API patterns (addon.py ~2600 lines)
- MCP server implementation (src/blender_mcp/server.py)
- How others structure Blender automation

## Blender version

Target **Blender 5.0+** only. No backwards compatibility needed.

The skills in `.claude/skills/` are the source of truth for Blender 5.0 API usage. Always follow the patterns in skills rather than relying on training data, which is mostly pre-5.0. When you hit an API error, fix it and update the relevant skill so it stays accurate.

**Do not use auto-memory for Blender API knowledge.** All API patterns, gotchas, and learnings must go into the skill files so they ship with the project. Memory files are not distributed with the skills.

If stuck, search the web. Key docs:
- Python API: https://docs.blender.org/api/5.0/
- Release notes (API changes): https://developer.blender.org/docs/release_notes/5.0/python_api/
- VSE changes: https://developer.blender.org/docs/release_notes/5.0/sequencer/

## Skill usability test

When asked to test a skill (e.g. "test the geometry nodes skill"), launch a background sub-agent
that builds something non-trivial using only the skill documentation. This validates that the
skills are accurate, complete, and usable by an agent without prior knowledge.

### How to run

1. **Pick a test project** appropriate to the skill being tested. It should exercise multiple
   sections of the skill (not just the basics). Example test projects:
   - `blender-3d`: animated scene with materials, lighting, camera, and rendered output
   - `blender-vse`: multi-strip timeline with text, transitions, and video render
   - `blender-geometry-nodes`: procedural scene with instancing, keyframed inputs, and render

2. **Launch a background sub-agent** (Task tool, `run_in_background: true`) with instructions to:
   - Read the relevant skill files from `.claude/skills/`
   - Verify Blender is running
   - Build the project step by step, checking for errors after each command
   - Render a test frame and report the path
   - Report: what it built, any skill docs that were confusing/wrong/missing, errors hit and how resolved

3. **Monitor progress** by tailing the agent's output file (returned in the Task result).
   Check in at milestones if the user wants visibility.

4. **Review the result**: inspect the rendered output, then fix any skill documentation bugs
   the sub-agent identified. Commit fixes if warranted.

### What the sub-agent should NOT do

- Modify any project files (skills, CLAUDE.md, code) — only send commands to Blender
- Use knowledge outside the skill files — the test validates the docs, not the agent's training data

## Known Blender 5.0.1 bugs

- **Strip modifiers crash**: `strip.modifiers.new()` segfaults. Avoid until fixed.
- **Render can crash**: threading segfault in `libIlmThread`. Use `resolution_percentage = 50` for test renders.
