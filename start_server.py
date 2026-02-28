"""
Blender Agent launcher.

  python3 start_server.py                      # connect or launch
  python3 start_server.py /path/to/file.blend   # connect or launch, opening a file

Connects to an already-running Blender, or launches a new one.
Blocks until the server is ready and prints the Blender version as JSON.
"""

import subprocess, urllib.request, time, json, sys, os

BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
PORT = 5656
URL = f"http://localhost:{PORT}"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")


def _query(code="bpy.app.version_string"):
    req = urllib.request.Request(URL, data=code.encode())
    try:
        resp = urllib.request.urlopen(req, timeout=2)
    except urllib.error.HTTPError as e:
        return json.loads(e.read())
    return json.loads(resp.read())


def _check():
    try:
        return _query()
    except Exception:
        return None


# Already running? Return version (and open file if requested).
result = _check()
if result:
    if len(sys.argv) > 1:
        filepath = os.path.abspath(sys.argv[1])
        _query(f'bpy.ops.wm.open_mainfile(filepath="{filepath}")')
    print(json.dumps(result))
    sys.exit(0)

# Launch Blender with env var so the addon auto-starts the server.
os.makedirs(OUTPUT_DIR, exist_ok=True)
env = os.environ.copy()
env["BLENDER_AGENT_OUTPUT"] = OUTPUT_DIR

cmd = [BLENDER]
if len(sys.argv) > 1:
    cmd.append(os.path.abspath(sys.argv[1]))
subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

# Poll until server is ready (usually <2s).
for _ in range(30):
    time.sleep(0.5)
    result = _check()
    if result:
        print(json.dumps(result))
        sys.exit(0)

print(json.dumps({"ok": False, "error": "timeout waiting for Blender to start"}))
sys.exit(1)
