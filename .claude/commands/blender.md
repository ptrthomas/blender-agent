# Blender — Main Skill

You can drive Blender by sending Python code via HTTP POST to `localhost:5656`.

## Sending commands

Use curl from Bash:
```bash
curl -s localhost:5656 -d '<python code here>'
```

For multi-line scripts, use a heredoc:
```bash
curl -s localhost:5656 -d @- <<'PYEOF'
import bpy
scene = bpy.context.scene
# ... your code ...
result_expression
PYEOF
```

## Response format

```json
{"ok": true, "result": "<last expression value>", "output": "<stdout>"}
{"ok": false, "error": "<error message>", "output": "<stdout before error>"}
```

## Before starting work

1. Verify the server is running: `curl -s localhost:5656 -d 'bpy.app.version_string'`
2. If not running, start Blender: `/Applications/Blender.app/Contents/MacOS/Blender --python start_server.py &`
3. Inspect current scene state before making changes

## Sub-skills

- `/project:blender-vse` — Video Sequence Editor: timelines, strips, text overlays, rendering video
- `/project:blender-3d` — 3D scene manipulation: objects, materials, animation, rendering stills

## Visual feedback loop

Screenshot the Blender UI:
```bash
curl -s localhost:5656 -d 'bpy.ops.screen.screenshot(filepath="/tmp/blender_ui.png")'
```
Then `Read /tmp/blender_ui.png` to see the full UI state.

Render a frame and inspect:
```bash
curl -s localhost:5656 -d '
scene = bpy.context.scene
scene.render.filepath = "/tmp/blender_render.png"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 50
bpy.ops.render.render(write_still=True)
'
```
Then `Read /tmp/blender_render.png` to see the output.

Use this for iterating: change → screenshot/render → inspect → adjust.

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

### Error recovery
If Blender crashes (connection refused), restart with:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --python start_server.py &
sleep 5
curl -s localhost:5656 -d 'bpy.app.version_string'
```

Check crash dumps at `~/Library/Logs/DiagnosticReports/Blender-*.ips`
