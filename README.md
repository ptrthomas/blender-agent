# Blender Agent

Run Python in Blender via HTTP. No MCP, no protocol, no dependencies — just `curl`.

Give [Claude Code](https://docs.anthropic.com/en/docs/claude-code) full control over Blender to create 3D scenes, motion graphics, and video edits by describing what you want in plain English.

Targets **Blender 5.0+** only.

## Quick start

### 1. Install the addon

Symlink into Blender's extensions directory (one-time):

```bash
mkdir -p ~/Library/Application\ Support/Blender/5.0/extensions/user_default
ln -sf $(pwd)/blender_agent ~/Library/Application\ Support/Blender/5.0/extensions/user_default/blender_agent
```

Then enable it in Blender: **Edit > Preferences > Add-ons**, search for "Blender Agent" and check the box.

The symlink means edits to the addon source are live — just restart Blender to pick up changes.

### 2. Start Blender with the server

The easiest way is to launch from the command line, which auto-starts the HTTP server:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --python start_server.py &
```

You'll see `[Blender Agent] listening on http://localhost:5656` in the terminal when it's ready.

**Alternative — start manually from the UI:**
Open the 3D Viewport sidebar (press `N`), find the **Agent** tab, and click **Start**.

### 3. Verify it works

```bash
curl -s localhost:5656 --data-binary @- <<< 'bpy.app.version_string'
```

Should return: `{"ok": true, "result": "5.0.1", "output": ""}`

## Using with Claude Code

This is the primary use case. The repo includes [Agent Skills](https://docs.anthropic.com/en/docs/claude-code/skills) that teach Claude how to drive Blender:

| Skill | Triggers on |
|-------|-------------|
| `blender` | General Blender automation, screenshots, scene inspection |
| `blender-3d` | 3D objects, materials, cameras, lights, animation, rendering |
| `blender-vse` | Video editing, timelines, text overlays, transitions |

Skills are auto-loaded — just ask Claude what you want:

```
> create a glowing neon cube that rotates and render it to video with bloom

> add subtitles to output/video.mp4 at these timestamps: ...

> set up a 3-point lighting rig and render a turntable animation
```

Claude will send Python code to Blender, render frames, inspect the output visually, and iterate until it looks right.

### Tips

- **Start Blender first.** Claude can do this for you if you ask, but it's faster to have it running already.
- **Output goes to `output/<session>/`.** Each Blender start creates a timestamped session directory (e.g. `output/2026-02-26-1430/`). A `SESSION` variable is injected into all code, so use `f"{SESSION}/render.mp4"` for output paths. Previous sessions are preserved.
- **Visual feedback.** Claude renders test frames and inspects them to iterate on aesthetics — this is normal and useful.

## Manual usage (curl)

For multi-line Python, use a heredoc to avoid shell quoting issues:

```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
import bpy
bpy.ops.mesh.primitive_cube_add(location=(1, 2, 3))
bpy.data.objects.keys()
PYEOF
```

Or send a script file:

```bash
curl -s localhost:5656 --data-binary @script.py
```

### Response format

```json
{"ok": true, "result": "<last expression>", "output": "<stdout>"}
{"ok": false, "error": "<message>", "output": "<stdout before error>"}
```

- `result` — the return value of the last expression in your code (auto JSON-serialized)
- `output` — captured stdout from `print()` statements
- `error` — the exception message if something went wrong

## How it works

The addon starts a tiny HTTP server (default port 5656) inside Blender. When it receives a POST request, it queues the Python code to run in Blender's main thread via `bpy.app.timers`, waits for it to complete, and returns JSON with the result.

This means the code has full access to `bpy` and runs in the correct context for all Blender operations — no restrictions.

## One-time setup tips

Disable the splash screen (persists across restarts):

```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
bpy.context.preferences.view.show_splash = False
bpy.ops.wm.save_userpref()
PYEOF
```
