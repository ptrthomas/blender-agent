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

`start_server.py` handles everything — connecting to an existing instance or launching
a new one. It blocks until the server is ready and returns the Blender version.

```bash
python3 start_server.py                        # connect or launch
python3 start_server.py /path/to/scene.blend   # connect or launch, opening a file
```

If Blender is already running, it reuses the existing instance (opening the file if given).
If not, it launches Blender and waits until the HTTP server is accepting connections.

If the user already has Blender open without the server, they can start it from the
3D Viewport sidebar (press `N` > Agent tab > Start).

After starting, inspect the scene before making changes — never assume a clean scene.
The user may have work in progress. Run `bpy.data.objects.keys()` first.

## Restarting Blender

```bash
curl -s localhost:5656 --data-binary @- <<< 'bpy.ops.wm.quit_blender()' || true
sleep 1
pkill -x Blender 2>/dev/null || true
sleep 1
python3 start_server.py
```

## Screenshots (visual feedback)

An `OUTPUT` variable is automatically available in every code execution. It points to
the `output/` directory. Use it for all file output.

**CRITICAL: Screenshots are a TWO-STEP process. The server only returns JSON, never image data.**

**NEVER do this** (saves JSON as a fake PNG, crashes Claude Code session):
```bash
# WRONG — localhost:5656 returns JSON, not images. -o saves garbage as PNG.
curl -s localhost:5656/screenshot -o /tmp/screenshot.png   # BROKEN
curl -s localhost:5656 -o /tmp/screenshot.png              # BROKEN
```

**Correct pattern:**
```bash
# Step 1: Tell Blender to save screenshot to a file on disk
curl -s localhost:5656 --data-binary @- <<'PYEOF'
bpy.ops.screen.screenshot(filepath=f"{OUTPUT}/blender_ui.png")
PYEOF
# Step 2: Use the Read tool on the file path to view the screenshot
```
The curl response is JSON (`{"ok": true, ...}`). The actual PNG is saved to disk by Blender.
Then use the Read tool on the file path to inspect the result visually.

For rendered frames (3D or VSE output), render to a file and read it:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
scene = bpy.context.scene
scene.render.filepath = f"{OUTPUT}/render.png"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 50
bpy.ops.render.render(write_still=True)
PYEOF
```
Then read the rendered image.

Use this feedback loop when iterating: make changes, screenshot/render, inspect, adjust.

## Logging

All `print()` and Python `logging` output from executed code streams to `output/agent.log`
in real-time — even while a request is still running. Use `tail -f output/agent.log` to
debug long-running or hung operations. See the main blender skill for details.

## Crash reports

macOS crash dumps: `~/Library/Logs/DiagnosticReports/Blender-*.ips`

## Output directory

All render output goes to the gitignored `output/` directory. The `OUTPUT` variable
(available in all code sent to Blender) points to it. Use `f"{OUTPUT}/filename.png"`
for all output paths. Never render to `/tmp`.

If output/ gets cluttered, clean it up or back it up before continuing.

## Project structure

```
blender_agent/__init__.py    # The Blender addon (HTTP server + exec engine)
blender_agent/blender_manifest.toml
start_server.py              # Launcher: connects or starts Blender, blocks until ready
output/                      # Render output (gitignored)
.claude/skills/              # Agent Skills (auto-loaded by Claude when relevant)
  blender/                   # General Blender automation
  blender-3d/                # 3D scenes, materials, animation, rendering
  blender-vse/               # Video Sequence Editor
  blender-geometry-nodes/    # Geometry Nodes (procedural geometry, instancing)
  blender-laser/             # Laser beams with raycast reflection
```

## Reference code

`../blender-mcp` contains a Blender MCP integration (by ahujasid). Useful as reference for:
- Blender Python API patterns (addon.py ~2600 lines)
- MCP server implementation (src/blender_mcp/server.py)
- How others structure Blender automation

## Blender version

Target **Blender 5.0+** only. No backwards compatibility needed.

The skills in `.claude/skills/` are the source of truth for Blender 5.0 API usage. Always follow the patterns in skills rather than relying on training data, which is mostly pre-5.0. When you hit an API error, fix it and update the relevant skill so it stays accurate.

**Do not use auto-memory at all.** Do not create or write to MEMORY.md or any files in the memory directory. All project knowledge belongs in CLAUDE.md and the skill files in `.claude/skills/`, which ship with the project.

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
- **Never call `depsgraph.update()` in frame handlers**: Causes crashes (GIL contention →
  segfault) or severe playback stutter. For hiding objects from `ray_cast`, use
  `hide_viewport = True` without `depsgraph.update()` — it works. See the laser skill.
