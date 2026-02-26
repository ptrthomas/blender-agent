---
name: blender-3d
description: Manipulate Blender 3D scenes including creating objects, materials, cameras, lights, animations with keyframes, and rendering stills or video. Use when the user wants to create or modify 3D objects, set up materials, animate scenes, configure cameras or lighting, or render 3D output in Blender.
---

# Blender 3D — Scene Manipulation Skill

Python API reference for Blender 5.0+ 3D scenes. Send all code via:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
<python code>
PYEOF
```
See the main `blender` skill for full communication details, visual feedback, and error recovery.

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
scene.render.filepath = f"{SESSION}/render.png"
# If previously set to FFMPEG, must reset media_type before changing format
scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_percentage = 100
scene.render.use_sequencer = False   # render 3D scene, not VSE
scene.frame_set(1)
bpy.ops.render.render(write_still=True)
```

### Render animation (image sequence)
```python
scene.render.filepath = f"{SESSION}/frame_"
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(animation=True)
```

### Render animation (H.264 video)
```python
scene.render.filepath = f"{SESSION}/render.mp4"
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
# scene.render.engine = 'BLENDER_WORKBENCH'  # solid/flat shading (fastest)
```

### Fast iteration

Rendering is expensive — minimize render calls and use the cheapest method that answers your question:

- **Object placement/transforms** — screenshot the viewport, don't render
- **Composition/layout** — `resolution_percentage = 25` + `BLENDER_WORKBENCH`
- **Materials/lighting** — `resolution_percentage = 25` + `BLENDER_EEVEE`
- **Final output** — full resolution with the intended engine

Batch multiple changes before rendering. Don't render after every tweak.

## Drivers

Drivers let a property be computed from an expression referencing other properties.
Use them to link audio data, custom properties, or objects together without keyframing every target.

```python
# Add a driver to any animatable property
# Returns an FCurve-like object (FCurve for single value, list for vectors)
drv = light.data.driver_add("energy")

# Add a variable that reads from another object/property
var = drv.driver.variables.new()
var.name = "kick"
var.targets[0].id = source_obj               # object to read from
var.targets[0].data_path = '["kick"]'        # property path on that object

# Expression using the variable
drv.driver.expression = "kick * 2000"
```

### Common driver targets
```python
# Custom property on an object
var.targets[0].data_path = '["my_prop"]'

# Object transform
var.targets[0].data_path = 'location.z'

# Modifier input (geometry nodes)
var.targets[0].data_path = 'modifiers["GeometryNodes"]["Socket_2"]'

# Material node input
var.targets[0].id_type = 'MATERIAL'
var.targets[0].id = bpy.data.materials["MyMat"]
var.targets[0].data_path = 'node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value'
```

### Driving material properties
```python
mat = bpy.data.materials["GlowMat"]
bsdf = mat.node_tree.nodes["Principled BSDF"]

# Drive emission strength
drv = bsdf.inputs["Emission Strength"].driver_add("default_value")
var = drv.driver.variables.new()
var.name = "val"
var.targets[0].id = source_obj
var.targets[0].data_path = '["audio_level"]'
drv.driver.expression = "val * 10"
```

### Removing a driver
```python
light.data.driver_remove("energy")
bsdf.inputs["Emission Strength"].driver_remove("default_value")
```

### Baking drivers to keyframes

Drivers are computed on-the-fly and don't appear as editable F-curves. Bake them
to keyframes so the user can see and tweak the curves in the Graph Editor:
```python
def bake_driver(obj, data_path, frame_start, frame_end):
    """Evaluate a driven property per frame and bake to keyframes."""
    for frame in range(frame_start, frame_end + 1):
        bpy.context.scene.frame_set(frame)
        # Read the current (driver-evaluated) value
        val = obj.path_resolve(data_path)
        # Remove driver, set keyframe, re-add driver would lose it —
        # instead, bake to a custom property and keyframe that
        obj[f"_baked_{data_path}"] = val
        obj.keyframe_insert(data_path=f'["_baked_{data_path}"]', frame=frame)

# Or bake and replace the driver with direct keyframes:
def bake_and_replace_driver(target, data_path, frame_start, frame_end):
    """Replace a driver with baked keyframes for user editing."""
    scene = bpy.context.scene
    values = []
    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        values.append(target.path_resolve(data_path))
    # Remove the driver
    target.driver_remove(data_path)
    # Keyframe the actual values
    for i, frame in enumerate(range(frame_start, frame_end + 1)):
        exec(f"target.{data_path} = {values[i]}")
        target.keyframe_insert(data_path=data_path, frame=frame)
```

Offer to bake drivers when the user wants to hand-tweak animation curves.
Baked keyframes are editable in the Graph Editor; drivers are not.

## Volumetric fog / smoke

### EEVEE volumetric settings
```python
scene = bpy.context.scene
scene.eevee.use_volumetric_shadows = True
scene.eevee.volumetric_samples = 64
scene.eevee.volumetric_tile_size = '8'   # STRING enum: '1','2','4','8','16'
scene.eevee.volumetric_start = 0.1
scene.eevee.volumetric_end = 60.0
```

**Gotcha**: `volumetric_tile_size` is a string enum, not an int. Use `'8'` not `8`.

### Fog volume cube
```python
# Create a cube that fills the scene
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 4))
fog = bpy.context.active_object
fog.name = "FogVolume"
fog.scale = (20, 20, 10)

# Volume material — connects to Volume output, NOT Surface
fog_mat = bpy.data.materials.new("FogMat")
fog_mat.use_nodes = True
nodes = fog_mat.node_tree.nodes
links = fog_mat.node_tree.links

for n in list(nodes):
    nodes.remove(n)

mat_out = nodes.new("ShaderNodeOutputMaterial")
vol = nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.03       # thin haze
vol.inputs["Anisotropy"].default_value = 0.6      # forward scattering (makes beams visible)
links.new(mat_out.inputs["Volume"], vol.outputs["Volume"])

# Noise texture for smoke-like variation
noise = nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 2.0
noise.inputs["Detail"].default_value = 8.0

multiply = nodes.new("ShaderNodeMath")
multiply.operation = 'MULTIPLY'
multiply.inputs[1].default_value = 0.05
links.new(multiply.inputs[0], noise.outputs["Fac"])
links.new(vol.inputs["Density"], multiply.outputs[0])

fog.data.materials.append(fog_mat)
```

## Spot lights

```python
bpy.ops.object.light_add(type='SPOT', location=(5, -5, 3))
spot = bpy.context.active_object
spot.data.energy = 5000
spot.data.color = (1.0, 0.05, 0.02)       # red
spot.data.spot_size = 0.14                 # cone angle in radians (~8°)
spot.data.spot_blend = 0.05                # 0 = hard edge, 1 = fully soft
spot.data.shadow_soft_size = 0.01          # sharp shadows

# Aim at a target
track = spot.constraints.new(type='TRACK_TO')
track.target = bpy.data.objects["Target"]
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'
```

Spot lights create visible beams through volumetric fog (see Volumetric section above).

## Compositor (bloom / post-processing)

In Blender 5.0, bloom is NOT an EEVEE setting (`use_bloom` was removed).
The compositor API changed completely:
- `scene.node_tree` removed — use `scene.compositing_node_group`
- `CompositorNodeComposite` removed — use `NodeGroupOutput` + tree interface socket
- `scene.use_nodes` deprecated (always True) — removed in 6.0
- Glare node: all old properties removed — everything is via input sockets

### Bloom setup
```python
scene = bpy.context.scene

# Create compositor node tree (standalone data block)
tree = bpy.data.node_groups.new("BloomCompositor", "CompositorNodeTree")
scene.compositing_node_group = tree

# REQUIRED: create output socket on tree interface
tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")

# Add nodes
rlayers = tree.nodes.new(type="CompositorNodeRLayers")
glare = tree.nodes.new(type="CompositorNodeGlare")
group_output = tree.nodes.new(type="NodeGroupOutput")

# Configure bloom via input sockets (NOT node properties)
glare.inputs["Type"].default_value = "Bloom"       # "Bloom", "Streaks", "Ghosts", "Fog Glow", "Simple Star", "Sun Beams"
glare.inputs["Quality"].default_value = "High"      # "Low", "Medium", "High"
glare.inputs["Threshold"].default_value = 0.5        # brightness cutoff
glare.inputs["Smoothness"].default_value = 0.2       # threshold smoothness (0-1)
glare.inputs["Size"].default_value = 0.6             # bloom radius (0-1)
glare.inputs["Strength"].default_value = 0.8          # effect intensity (0-1)
glare.inputs["Saturation"].default_value = 1.0        # color saturation (0-1)
# Optional: glare.inputs["Tint"].default_value = (1, 1, 1, 1)

# Link: Render Layers -> Glare -> Output
tree.links.new(glare.inputs["Image"], rlayers.outputs["Image"])
tree.links.new(group_output.inputs["Image"], glare.outputs["Image"])
```

### Glare node outputs
```python
glare.outputs["Image"]       # combined result (original + glare)
glare.outputs["Glare"]       # glare effect only (for custom compositing)
glare.outputs["Highlights"]  # extracted highlights only
```

### Removing compositor
```python
if scene.compositing_node_group:
    bpy.data.node_groups.remove(scene.compositing_node_group)
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
