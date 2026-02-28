---
name: blender
description: Drive Blender via HTTP by sending Python code to localhost:5656. Use when the user wants to automate Blender, inspect scenes, take screenshots, or perform general Blender operations. For video editing (VSE) or 3D scene manipulation, the specialized blender-vse and blender-3d skills provide deeper guidance.
---

# Blender — Main Skill

You can drive Blender by sending Python code via HTTP POST to `localhost:5656`.

## Sending commands

Always use heredoc to avoid shell quoting issues with Python code:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
import bpy
scene = bpy.context.scene
# ... your code ...
result_expression
PYEOF
```

For simple one-expression queries, heredoc still works fine:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
bpy.data.objects.keys()
PYEOF
```

**Important**: Always use `<<'PYEOF'` (quoted delimiter) so the shell doesn't
expand `$variables` or backticks inside the Python code.

## Response format

```json
{"ok": true, "result": "<last expression value>", "output": "<stdout>"}
{"ok": false, "error": "<error message>", "output": "<stdout before error>"}
```

## Before starting work

Start Blender (or connect to an already-running instance) with:
```bash
python3 start_server.py                        # connect or launch
python3 start_server.py /path/to/scene.blend   # connect or launch, opening a file
```
This blocks until the server is ready and returns the Blender version. It never launches
a second instance — if Blender is already running, it reuses it.

After starting, inspect the scene before making changes — never assume a clean scene.
The user may have work in progress. Run `bpy.data.objects.keys()` first.

## Output directory

An `OUTPUT` variable is automatically available in every code execution. It points to
the `output/` directory. Use it for all file output — screenshots, renders, exports:

```python
f"{OUTPUT}/screenshot.png"
f"{OUTPUT}/render.mp4"
```

## Visual feedback loop

**CRITICAL: Screenshots are a TWO-STEP process. The server only returns JSON, never image data.**

**NEVER** use `curl -o` to save a screenshot — the response is JSON, not an image. Saving it as PNG
will produce a corrupt file that crashes Claude Code when read. Always use the pattern below.

Screenshot the Blender UI:
```bash
# Step 1: Tell Blender to save screenshot to disk
curl -s localhost:5656 --data-binary @- <<'PYEOF'
bpy.ops.screen.screenshot(filepath=f"{OUTPUT}/blender_ui.png")
PYEOF
# Step 2: Use the Read tool on the file path to view the screenshot
```

Render a frame and inspect:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
scene = bpy.context.scene
scene.render.filepath = f"{OUTPUT}/render.png"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 50
bpy.ops.render.render(write_still=True)
PYEOF
```
Then read the rendered image to see the output.

Use this for iterating: change -> screenshot/render -> inspect -> adjust.

### Fast iteration

Rendering is slow. Minimize render calls and use the lowest quality that answers your question:

- **Layout/positioning** — use screenshots (`bpy.ops.screen.screenshot`), no render needed
- **Quick composition check** — `resolution_percentage = 25` and `BLENDER_WORKBENCH` engine
- **Lighting/materials check** — `resolution_percentage = 25` with EEVEE
- **Final output** — full resolution, intended engine

Only increase quality once the scene is right. Don't render after every small change — batch adjustments and render once to verify.

## Common patterns

### Inspect scene
```python
bpy.data.objects.keys()
```

### Get object properties
```python
obj = bpy.data.objects["Cube"]
{"location": list(obj.location), "rotation": list(obj.rotation_euler), "scale": list(obj.scale)}
```

### Check output path
```bash
curl -s localhost:5656
```
Returns `{"ok": true, "output": "output/"}`.

### Error recovery
If Blender crashes (connection refused), restart with:
```bash
pkill -x Blender 2>/dev/null || true; sleep 1
python3 start_server.py
```

Check crash dumps at `~/Library/Logs/DiagnosticReports/Blender-*.ips`
