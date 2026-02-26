"""Auto-start the Blender Agent server. Use with: blender --python start_server.py"""
import bpy
import os
import datetime

# Create a timestamped session directory for this Blender run.
_project_dir = os.path.dirname(os.path.abspath(__file__))
_session_name = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
_session_dir = os.path.join(_project_dir, "output", _session_name)
os.makedirs(_session_dir, exist_ok=True)

os.environ["BLENDER_AGENT_SESSION"] = _session_dir
os.environ["BLENDER_AGENT_LOG"] = os.path.join(_session_dir, "agent.log")


def _start_agent():
    try:
        bpy.ops.blenderagent.start()
        print("[Blender Agent] auto-started via start_server.py")
        print(f"[Blender Agent] session: {_session_dir}")
    except Exception as e:
        print(f"[Blender Agent] auto-start failed: {e}")
    return None  # don't re-register


bpy.app.timers.register(_start_agent, first_interval=1.0)
