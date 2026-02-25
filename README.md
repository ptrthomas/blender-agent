# Blender Agent

Run Python in Blender via HTTP POST. No MCP, no protocol, no dependencies — just `curl`.

Targets **Blender 5.0+** only.

## Setup

Symlink into Blender's extensions directory (one-time):

```bash
mkdir -p ~/Library/Application\ Support/Blender/5.0/extensions/user_default
ln -sf $(pwd)/blender_agent ~/Library/Application\ Support/Blender/5.0/extensions/user_default/blender_agent
```

Then in Blender: **Edit → Preferences → Add-ons** → enable "Blender Agent".

The symlink means edits to `blender_agent/__init__.py` are live — just restart Blender to pick up changes.

In the 3D Viewport sidebar → **Blender Agent** tab → click **Start**.

### CLI launch (auto-start server)

```bash
/Applications/Blender.app/Contents/MacOS/Blender --python start_server.py &
```

This opens Blender and starts the HTTP server automatically — no need to click Start in the UI.

Disable the splash screen once (persists across restarts):

```bash
curl -s localhost:5656 -d '
bpy.context.preferences.view.show_splash = False
bpy.ops.wm.save_userpref()
'
```

## Usage

```bash
curl localhost:5656 -d 'bpy.data.objects.keys()'
curl localhost:5656 -d 'bpy.ops.mesh.primitive_cube_add(location=(1, 2, 3))'
curl localhost:5656 -d @script.py
```

## Response

```json
{"ok": true, "result": "<last expression>", "output": "<stdout>"}
{"ok": false, "error": "<message>"}
```
