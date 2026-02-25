"""
Blender Agent — run Python in Blender via HTTP POST.

Install as a Blender addon, enable it, press "Start" in the sidebar panel.
Then: curl localhost:5656 -d 'bpy.data.objects.keys()'

The POST body is Python code. It gets exec'd in Blender's main thread.
Response is JSON: {"ok": true, "result": "...", "output": "..."} or {"ok": false, "error": "..."}

- `output` = captured stdout (print statements)
- `result` = repr() of the last expression, if the code ends with one
"""

import bpy
import io
import ast
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from contextlib import redirect_stdout, redirect_stderr

_server_instance = None


def _exec_code(code):
    """Execute code in Blender context. Returns (result, stdout, error)."""
    namespace = {"bpy": bpy, "__builtins__": __builtins__}

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    # Try to split off the last expression so we can return its value.
    # e.g. "x = 1\nx + 2" -> exec "x = 1", then eval "x + 2" -> 3
    last_expr = None
    try:
        tree = ast.parse(code)
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last_expr = ast.Expression(tree.body.pop().value)
            ast.fix_missing_locations(last_expr)
            ast.fix_missing_locations(tree)
    except SyntaxError:
        pass  # let exec() raise it with a proper message

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(compile(tree, "<http>", "exec") if last_expr else code, namespace)
            result = eval(compile(last_expr, "<http>", "eval"), namespace) if last_expr else None
    except Exception as e:
        return None, stdout_buf.getvalue(), f"{type(e).__name__}: {e}"

    output = stdout_buf.getvalue()
    if stderr_buf.getvalue():
        output += stderr_buf.getvalue()

    # Try to make result JSON-friendly
    if result is not None:
        try:
            json.dumps(result)  # test serializability
        except (TypeError, ValueError):
            result = repr(result)

    return result, output, None


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        code = self.rfile.read(length).decode("utf-8") if length else ""

        if not code.strip():
            self._reply(400, {"ok": False, "error": "empty body"})
            return

        # We need to run in Blender's main thread.
        # Use an Event to block this HTTP thread until execution is done.
        event = threading.Event()
        response = {}

        def run_in_main():
            result, output, error = _exec_code(code)
            if error:
                response.update({"ok": False, "error": error, "output": output})
            else:
                r = {"ok": True, "output": output}
                if result is not None:
                    r["result"] = result
                response.update(r)
            event.set()
            return None  # don't re-register timer

        bpy.app.timers.register(run_in_main, first_interval=0.0)
        event.wait(timeout=30)

        if not event.is_set():
            self._reply(504, {"ok": False, "error": "timeout waiting for Blender main thread"})
            return

        self._reply(200 if response.get("ok") else 400, response)

    def do_GET(self):
        self._reply(200, {"ok": True, "message": "POST python code to eval in Blender"})

    def _reply(self, status, body):
        payload = json.dumps(body, default=repr, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print(f"[Blender Agent] {fmt % args}")


class Server:
    def __init__(self, port=5656):
        self.port = port
        self.httpd = None
        self.thread = None

    def start(self):
        self.httpd = HTTPServer(("0.0.0.0", self.port), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        print(f"[Blender Agent] listening on http://localhost:{self.port}")

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd = None
            self.thread = None
            print("[Blender Agent] stopped")


# ── Blender UI ──────────────────────────────────────────────

class BLENDERAGENT_OT_Start(bpy.types.Operator):
    bl_idname = "blenderagent.start"
    bl_label = "Start Blender Agent Server"

    def execute(self, context):
        global _server_instance
        if _server_instance:
            self.report({"WARNING"}, "Already running")
            return {"CANCELLED"}
        port = context.scene.blenderagent_port
        _server_instance = Server(port=port)
        _server_instance.start()
        self.report({"INFO"}, f"Listening on port {port}")
        return {"FINISHED"}


class BLENDERAGENT_OT_Stop(bpy.types.Operator):
    bl_idname = "blenderagent.stop"
    bl_label = "Stop Blender Agent Server"

    def execute(self, context):
        global _server_instance
        if _server_instance:
            _server_instance.stop()
            _server_instance = None
        self.report({"INFO"}, "Stopped")
        return {"FINISHED"}


class BLENDERAGENT_PT_Panel(bpy.types.Panel):
    bl_label = "Blender Agent"
    bl_idname = "BLENDERAGENT_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Agent"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "blenderagent_port")
        if _server_instance:
            layout.operator("blenderagent.stop", text="Stop", icon="PAUSE")
            layout.label(text=f"Listening on port {_server_instance.port}")
        else:
            layout.operator("blenderagent.start", text="Start", icon="PLAY")


classes = (BLENDERAGENT_OT_Start, BLENDERAGENT_OT_Stop, BLENDERAGENT_PT_Panel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.blenderagent_port = bpy.props.IntProperty(
        name="Port", default=5656, min=1024, max=65535
    )


def unregister():
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.blenderagent_port
