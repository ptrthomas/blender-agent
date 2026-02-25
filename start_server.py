"""Auto-start the Blender Agent server. Use with: blender --python start_server.py"""
import bpy


def _start_agent():
    try:
        bpy.ops.blenderagent.start()
        print("[Blender Agent] auto-started via start_server.py")
    except Exception as e:
        print(f"[Blender Agent] auto-start failed: {e}")
    return None  # don't re-register


bpy.app.timers.register(_start_agent, first_interval=1.0)
