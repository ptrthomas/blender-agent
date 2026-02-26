---
name: blender-3d
description: Manipulate Blender 3D scenes including creating objects, materials, cameras, lights, animations with keyframes, and rendering stills or video. Use when the user wants to create or modify 3D objects, set up materials, animate scenes, configure cameras or lighting, or render 3D output in Blender.
---

# Blender 3D — Scene Manipulation Skill

Drive Blender's 3D scene via HTTP POST to `localhost:5656`.
All code runs as Blender Python (`bpy`). Target: **Blender 5.0+**.

## Scene basics

```python
# List objects
bpy.data.objects.keys()

# Scene settings
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 250
scene.render.fps = 24
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
```

## Objects

### Create primitives
```python
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0), scale=(1, 1, 1))
bpy.ops.mesh.primitive_uv_sphere_add(location=(2, 0, 0), radius=1)
bpy.ops.mesh.primitive_cylinder_add(location=(-2, 0, 0), radius=0.5, depth=2)
bpy.ops.mesh.primitive_plane_add(location=(0, 0, -1), size=10)
bpy.ops.mesh.primitive_cone_add(location=(0, 2, 0))
bpy.ops.mesh.primitive_torus_add(location=(0, -2, 0))
```

### Transform objects
```python
obj = bpy.data.objects["Cube"]
obj.location = (1, 2, 3)
obj.rotation_euler = (0, 0, 0.785)     # radians
obj.scale = (2, 2, 2)
```

### Delete objects
```python
obj = bpy.data.objects["Cube"]
bpy.data.objects.remove(obj, do_unlink=True)
```

### Duplicate
```python
import bpy
src = bpy.data.objects["Cube"]
new = src.copy()
new.data = src.data.copy()
new.name = "Cube.Copy"
bpy.context.collection.objects.link(new)
```

## Materials

```python
# Create material
mat = bpy.data.materials.new(name="Red")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1, 0, 0, 1)  # RGBA red
bsdf.inputs["Metallic"].default_value = 0.5
bsdf.inputs["Roughness"].default_value = 0.3

# Assign to object
obj = bpy.data.objects["Cube"]
obj.data.materials.clear()
obj.data.materials.append(mat)
```

### Emission material (glowing)
```python
mat = bpy.data.materials.new(name="Glow")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Emission Color"].default_value = (0, 1, 0.5, 1)
bsdf.inputs["Emission Strength"].default_value = 5.0
```

## Camera

```python
cam = bpy.data.objects["Camera"]
cam.location = (7, -7, 5)
cam.rotation_euler = (1.1, 0, 0.8)

# Point camera at object
constraint = cam.constraints.new(type='TRACK_TO')
constraint.target = bpy.data.objects["Cube"]
constraint.track_axis = 'TRACK_NEGATIVE_Z'
constraint.up_axis = 'UP_Y'
```

## Lighting

```python
light = bpy.data.objects["Light"]
light.location = (4, -4, 6)
light.data.energy = 1000        # watts
light.data.color = (1, 1, 1)    # white

# Add new light
bpy.ops.object.light_add(type='AREA', location=(0, 0, 5))
area = bpy.context.active_object
area.data.energy = 500
area.data.size = 3
```

## Animation (keyframes)

```python
obj = bpy.data.objects["Cube"]

# Set keyframes
obj.location = (0, 0, 0)
obj.keyframe_insert(data_path="location", frame=1)

obj.location = (5, 0, 3)
obj.keyframe_insert(data_path="location", frame=30)

obj.rotation_euler = (0, 0, 6.283)  # full rotation
obj.keyframe_insert(data_path="rotation_euler", frame=60)

# Also works for scale, material properties, etc.
```

### Easing / interpolation
```python
# After setting keyframes, modify the F-curves
action = obj.animation_data.action
for fcurve in action.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'BEZIER'    # or 'LINEAR', 'CONSTANT'
        kp.easing = 'EASE_IN_OUT'      # or 'EASE_IN', 'EASE_OUT'
```

## Rendering

### Render still
```python
scene = bpy.context.scene
scene.render.filepath = "output/temp/render.png"
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_percentage = 100
scene.render.use_sequencer = False   # render 3D scene, not VSE
scene.frame_set(1)
bpy.ops.render.render(write_still=True)
```

### Render animation (image sequence)
```python
scene.render.filepath = "output/temp/frame_"
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(animation=True)
```

### Render animation (H.264 video)
```python
scene.render.filepath = "output/render.mp4"
# Blender 5.0: MUST set media_type to VIDEO before setting FFMPEG
scene.render.image_settings.media_type = 'VIDEO'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
scene.render.ffmpeg.audio_codec = 'NONE'
bpy.ops.render.render(animation=True)
```

### Render engine
```python
scene.render.engine = 'BLENDER_EEVEE'    # fast preview
# scene.render.engine = 'CYCLES'         # high quality (slow)
# scene.render.engine = 'BLENDER_WORKBENCH'  # solid/flat shading
```

## World / background

```python
world = bpy.data.worlds["World"]
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.05, 0.05, 0.1, 1)   # dark blue
bg.inputs["Strength"].default_value = 1.0
```

## Text objects (3D text, not VSE)

```python
bpy.ops.object.text_add(location=(0, 0, 0))
text_obj = bpy.context.active_object
text_obj.data.body = "Hello 3D!"
text_obj.data.size = 2
text_obj.data.extrude = 0.1      # depth
text_obj.data.align_x = 'CENTER'
```

## Collections

```python
# Create collection
col = bpy.data.collections.new("MyGroup")
bpy.context.scene.collection.children.link(col)

# Move object to collection
col.objects.link(obj)
bpy.context.scene.collection.objects.unlink(obj)
```
