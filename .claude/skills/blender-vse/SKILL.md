---
name: blender-vse
description: Drive Blender's Video Sequence Editor to create and edit video timelines, add strips (text, color, movie, image, sound, effects), transitions, keyframe animations, and render video output. Use when the user mentions video editing, VSE, sequences, timelines, subtitles, text overlays, or video rendering in Blender.
---

# Blender VSE — Video Sequence Editor Skill

Python API reference for Blender 5.0+ Video Sequence Editor. Send all code via:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
<python code>
PYEOF
```
See the main `blender` skill for full communication details, visual feedback, and error recovery.

## Setup

Before using VSE, ensure the sequence editor exists:
```python
scene = bpy.context.scene
if not scene.sequence_editor:
    scene.sequence_editor_create()
se = scene.sequence_editor
```

Configure timeline:
```python
scene.frame_start = 1
scene.frame_end = 250       # 250 frames
scene.render.fps = 24       # or 30, 60
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
```

## Creating strips

All strip creation is via `scene.sequence_editor.strips.*`:

### Text strip
```python
strip = se.strips.new_effect(name="Title", type="TEXT", channel=1, frame_start=1, length=120)
strip.text = "Hello World"
strip.font_size = 80
strip.location = (0.5, 0.5)        # normalized 0-1, (0.5, 0.5) = center
strip.color = (1, 1, 1, 1)         # RGBA white
strip.use_shadow = True
strip.shadow_color = (0, 0, 0, 1)
strip.use_bold = True
strip.alignment_x = 'CENTER'       # 'LEFT', 'CENTER', 'RIGHT'
strip.wrap_width = 0.8             # text wrap width (0-1)
```

### Color strip (solid background)
```python
strip = se.strips.new_effect(name="BG", type="COLOR", channel=1, frame_start=1, length=120)
strip.color = (0.1, 0.1, 0.1)     # dark gray RGB
```

### Movie strip (video file)
```python
strip = se.strips.new_movie(name="Clip", filepath="/path/to/video.mp4", channel=1, frame_start=1)
# fit_method: 'ORIGINAL', 'FIT', 'FILL', 'STRETCH'
```

### Image strip
```python
strip = se.strips.new_image(name="Photo", filepath="/path/to/image.png", channel=1, frame_start=1)
strip.frame_final_duration = 48    # hold for 48 frames (2 sec at 24fps)
```

### Sound strip
```python
strip = se.strips.new_sound(name="Audio", filepath="/path/to/audio.mp3", channel=2, frame_start=1)
strip.volume = 0.8
```

### Scene strip (render 3D scene into VSE)
```python
strip = se.strips.new_scene(name="3D", scene=bpy.data.scenes["Scene"], channel=1, frame_start=1)
```

### Adjustment layer
```python
strip = se.strips.new_effect(name="Adjust", type="ADJUSTMENT", channel=5, frame_start=1, length=120)
```

## Effect strips (require input strips)

### 1-input effects (SPEED, GLOW, GAUSSIAN_BLUR)
```python
blur = se.strips.new_effect(name="Blur", type="GAUSSIAN_BLUR", channel=3, frame_start=1, length=60, input1=some_strip)
blur.size_x = 10
blur.size_y = 10
```

### 2-input effects (ALPHA_OVER, CROSS, WIPE, ADD, SUBTRACT, MULTIPLY, GAMMA_CROSS, ALPHA_UNDER, COLORMIX)
```python
transition = se.strips.new_effect(name="Fade", type="CROSS", channel=3, frame_start=50, length=20, input1=strip_a, input2=strip_b)
```

## Strip properties (common to all visual strips)

### Transform (position, scale, rotation)
Every visual strip has a `.transform` property:
```python
strip.transform.offset_x = 100      # pixels from center
strip.transform.offset_y = -50
strip.transform.scale_x = 1.5
strip.transform.scale_y = 1.5
strip.transform.rotation = 0.785    # radians (~45 degrees)
```

Note: TRANSFORM is NOT a valid effect type in Blender 5.0. Use `strip.transform` directly.

### Crop
```python
strip.crop.min_x = 100   # crop from left
strip.crop.max_x = 100   # crop from right
strip.crop.min_y = 50    # crop from bottom
strip.crop.max_y = 50    # crop from top
```

### Blending
```python
strip.blend_alpha = 1.0             # opacity 0-1
strip.blend_type = 'ALPHA_OVER'     # or 'ADD', 'SUBTRACT', 'MULTIPLY', 'REPLACE', etc.
strip.mute = False
strip.lock = False
```

### Timing
```python
strip.frame_start                  # start position on timeline
strip.frame_final_start            # visual start (after soft trim)
strip.frame_final_end              # visual end
strip.frame_final_duration         # visual duration
strip.frame_offset_start           # soft trim from start
strip.frame_offset_end             # soft trim from end
```

## Text strip — full property reference

```python
# Content
strip.text = "Your text here"
strip.font_size = 60.0
strip.font = None                  # or bpy.data.fonts.load("/path/to/font.ttf")
strip.use_bold = False
strip.use_italic = False
strip.wrap_width = 1.0             # 0-1, fraction of frame width

# Position (normalized 0-1 coordinates)
strip.location = (0.5, 0.5)       # center of screen
strip.alignment_x = 'CENTER'      # 'LEFT', 'CENTER', 'RIGHT'
strip.anchor_x = 'CENTER'
strip.anchor_y = 'CENTER'

# Color
strip.color = (1, 1, 1, 1)        # RGBA

# Shadow
strip.use_shadow = True
strip.shadow_color = (0, 0, 0, 1) # RGBA
strip.shadow_offset = 0.04
strip.shadow_angle = 1.134        # radians
strip.shadow_blur = 0.0

# Outline
strip.use_outline = True
strip.outline_color = (0, 0, 0, 1)
strip.outline_width = 0.05

# Box (background rectangle)
strip.use_box = True
strip.box_color = (0, 0, 0, 0.5)  # semi-transparent black
strip.box_margin = 0.01
strip.box_roundness = 0.0
```

## Keyframing strip properties

Animate any strip property over time:
```python
# Fade in text opacity
strip.blend_alpha = 0.0
strip.keyframe_insert(data_path="blend_alpha", frame=1)
strip.blend_alpha = 1.0
strip.keyframe_insert(data_path="blend_alpha", frame=24)

# Animate position
strip.location = (0.5, 0.0)
strip.keyframe_insert(data_path="location", frame=1)
strip.location = (0.5, 0.5)
strip.keyframe_insert(data_path="location", frame=30)

# Animate transform
strip.transform.scale_x = 1.0
strip.transform.keyframe_insert(data_path="scale_x", frame=1)
strip.transform.scale_x = 2.0
strip.transform.keyframe_insert(data_path="scale_x", frame=60)
```

## Managing strips

```python
# List all strips
[(s.name, s.type, s.channel) for s in se.strips]

# Access by name
strip = se.strips["Title"]

# Remove
se.strips.remove(strip)

# Channels (128 available, 1-128)
se.channels[1].name = "Video"
se.channels[2].name = "Audio"
se.channels[1].mute = False
se.channels[1].lock = False
```

## Rendering

### Render single frame (PNG)
```python
scene.render.filepath = f"{SESSION}/frame.png"
# If previously set to FFMPEG, must reset media_type before changing format
scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_percentage = 100
scene.frame_set(30)
bpy.ops.render.render(write_still=True)
```

### Render animation (video)
```python
scene.render.filepath = f"{SESSION}/render.mp4"
# Blender 5.0: MUST set media_type to VIDEO before setting FFMPEG
scene.render.image_settings.media_type = 'VIDEO'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
scene.render.ffmpeg.audio_codec = 'AAC'
bpy.ops.render.render(animation=True)
```

### Use VSE output (not 3D viewport)
To render VSE output instead of 3D scene, set the sequencer as the render source. If a sequence editor with strips exists, Blender renders from VSE by default. To force it, ensure:
```python
scene.render.use_sequencer = True
```

### Fast iteration

Rendering full video is slow. Use the cheapest check that answers your question:

- **Strip layout/timing** — screenshot the VSE timeline, don't render
- **Single frame check** — render one frame at `resolution_percentage = 25` instead of the full animation
- **Final output** — full resolution animation

Batch changes before rendering. Don't render after every strip adjustment.

## Workflow: subtitle overlay

```python
scene = bpy.context.scene
se = scene.sequence_editor_create() if not scene.sequence_editor else scene.sequence_editor

# Background video
video = se.strips.new_movie(name="Main", filepath="/path/to/video.mp4", channel=1, frame_start=1)

# Subtitles (channel 2, above video)
fps = scene.render.fps
subs = [
    (0, 3, "Welcome to the video"),
    (3, 6, "Let me show you something"),
    (6, 10, "Thanks for watching!"),
]
for i, (start_sec, end_sec, text) in enumerate(subs):
    s = se.strips.new_effect(
        name=f"Sub_{i}", type="TEXT", channel=2,
        frame_start=int(start_sec * fps) + 1,
        length=int((end_sec - start_sec) * fps)
    )
    s.text = text
    s.font_size = 48
    s.location = (0.5, 0.1)          # bottom center
    s.alignment_x = 'CENTER'
    s.color = (1, 1, 1, 1)
    s.use_shadow = True
    s.use_box = True
    s.box_color = (0, 0, 0, 0.6)
    s.box_margin = 0.01
```

## Switching to Video Editing workspace

The Video Editing workspace can be loaded from Blender's built-in template:
```python
template_path = "/Applications/Blender.app/Contents/Resources/5.0/scripts/startup/bl_app_templates_system/Video_Editing/startup.blend"
bpy.ops.workspace.append_activate(idname="Video Editing", filepath=template_path)
bpy.context.window.workspace = bpy.data.workspaces["Video Editing"]
```

**Important**: The template's sequencer areas don't auto-link to the current scene's strips.
In Blender 5.0, each workspace has its own `sequencer_scene` (separate from `window.scene`).
Must be set with a timer delay after the workspace switch:
```python
template_path = "/Applications/Blender.app/Contents/Resources/5.0/scripts/startup/bl_app_templates_system/Video_Editing/startup.blend"
bpy.ops.workspace.append_activate(idname="Video Editing", filepath=template_path)
bpy.context.window.workspace = bpy.data.workspaces["Video Editing"]

# Delayed — workspace needs a frame to initialize before sequencer_scene can be set
def fix_scene():
    bpy.context.workspace.sequencer_scene = bpy.data.scenes["Scene"]
    bpy.context.scene.frame_set(40)  # set to desired frame
    return None
bpy.app.timers.register(fix_scene, first_interval=0.3)
```

## Known issues (Blender 5.0.1)

- **Strip modifiers crash**: `strip.modifiers.new()` segfaults. Avoid until patched.
- **TRANSFORM effect type removed**: use `strip.transform` property instead.
- **Rendering can crash** with threading issues — use lower resolution_percentage for test renders.
