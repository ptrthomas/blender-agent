---
name: blender-geometry-nodes
description: Create and manipulate Blender Geometry Nodes for procedural geometry, instancing, scatter, formations, and node-based modeling. Use when the user mentions geometry nodes, procedural geometry, instancing, scatter, formations, point clouds, node-based modeling, simulation zones, repeat zones, or music-driven animation in Blender.
---

# Blender Geometry Nodes — Procedural Geometry Skill

Python API reference for Blender 5.0+ Geometry Nodes. Send all code via:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
<python code>
PYEOF
```
See the main `blender` skill for communication details, visual feedback, and error recovery.
See `blender-3d` for materials, cameras, lighting, and rendering.

## Creating a node tree

```python
import bpy

# Create a new geometry node tree
tree = bpy.data.node_groups.new("MyGeoNodes", "GeometryNodeTree")

# Add group input/output nodes
group_in = tree.nodes.new("NodeGroupInput")
group_out = tree.nodes.new("NodeGroupOutput")
group_in.location = (-200, 0)
group_out.location = (200, 0)

# Add geometry sockets to the tree interface
tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

# Minimum viable tree: passthrough geometry
tree.links.new(group_out.inputs["Geometry"], group_in.outputs["Geometry"])
```

## Attaching to an object

```python
# Attach to an existing object
obj = bpy.data.objects["Cube"]
mod = obj.modifiers.new("GeometryNodes", "NODES")
mod.node_group = tree

# Empty mesh carrier pattern (for purely procedural scenes)
mesh = bpy.data.meshes.new("carrier")
obj = bpy.data.objects.new("Procedural", mesh)
bpy.context.collection.objects.link(obj)
mod = obj.modifiers.new("GeometryNodes", "NODES")
mod.node_group = tree
```

## Interface sockets (modifier inputs)

Add inputs that appear on the modifier panel:
```python
# Socket types for tree.interface.new_socket():
#   NodeSocketGeometry   NodeSocketFloat     NodeSocketInt
#   NodeSocketVector     NodeSocketColor     NodeSocketBool
#   NodeSocketObject     NodeSocketMaterial  NodeSocketCollection
#   NodeSocketString     NodeSocketImage

tree.interface.new_socket(name="Count", in_out='INPUT', socket_type='NodeSocketInt')
tree.interface.new_socket(name="Scale", in_out='INPUT', socket_type='NodeSocketFloat')
tree.interface.new_socket(name="Target", in_out='INPUT', socket_type='NodeSocketObject')
tree.interface.new_socket(name="Color", in_out='INPUT', socket_type='NodeSocketColor')
tree.interface.new_socket(name="Material", in_out='INPUT', socket_type='NodeSocketMaterial')
```

### Setting modifier input values

Each socket gets an auto-generated identifier like `Socket_2`, `Socket_3`, etc.
Always introspect to find the right identifier:
```python
# Find identifiers for all inputs
for item in tree.interface.items_tree:
    if item.in_out == 'INPUT':
        print(f"{item.name}: {item.identifier}")

# Set values via identifier
mod["Socket_2"] = 10        # int
mod["Socket_3"] = 2.5       # float
mod["Socket_4"] = target_obj # object reference

# IMPORTANT: force viewport refresh after changing values
obj.data.update()
```

## Adding and linking nodes

```python
# Add a node
grid = tree.nodes.new("GeometryNodeMeshGrid")
grid.location = (0, 200)

# Set default values via input sockets
grid.inputs["Size X"].default_value = 5.0
grid.inputs["Size Y"].default_value = 5.0
grid.inputs["Vertices X"].default_value = 20
grid.inputs["Vertices Y"].default_value = 20

# Link nodes: tree.links.new(to_socket, from_socket)
tree.links.new(group_out.inputs["Geometry"], grid.outputs["Mesh"])

# Discover socket names on any node
for inp in grid.inputs:
    print(f"  input: {inp.name} ({inp.type})")
for out in grid.outputs:
    print(f"  output: {out.name} ({out.type})")
```

## Node type reference

### Mesh primitives

| Node | Type string | Key inputs |
|------|-------------|------------|
| Grid | `GeometryNodeMeshGrid` | Size X/Y, Vertices X/Y |
| Cube | `GeometryNodeMeshCube` | Size, Vertices X/Y/Z |
| Line | `GeometryNodeMeshLine` | Count, Start/End Location |
| Circle | `GeometryNodeMeshCircle` | Vertices, Radius |
| UV Sphere | `GeometryNodeMeshUVSphere` | Segments, Rings, Radius |
| Cone | `GeometryNodeMeshCone` | Vertices, Radius Top/Bottom, Depth |
| Points | `GeometryNodePoints` | Count, Position, Radius |

### Instancing

| Node | Type string | Key inputs |
|------|-------------|------------|
| Instance on Points | `GeometryNodeInstanceOnPoints` | Points, Instance, Scale, Rotation |
| Realize Instances | `GeometryNodeRealizeInstances` | Geometry |
| Object Info | `GeometryNodeObjectInfo` | Object, As Instance |
| Collection Info | `GeometryNodeCollectionInfo` | Collection, Separate Children |

### Transform and position

| Node | Type string | Key inputs |
|------|-------------|------------|
| Transform Geometry | `GeometryNodeTransformGeometry` | Geometry, Translation, Rotation, Scale |
| Set Position | `GeometryNodeSetPosition` | Geometry, Position, Offset |
| Position | `GeometryNodeInputPosition` | *(field output)* |
| Index | `GeometryNodeInputIndex` | *(field output)* |
| Normal | `GeometryNodeInputNormal` | *(field output)* |

### Math and fields

| Node | Type string | Notes |
|------|-------------|-------|
| Math | `ShaderNodeMath` | `node.operation`: ADD, SUBTRACT, MULTIPLY, DIVIDE, SINE, COSINE, MODULO, POWER, SQRT, etc. |
| Vector Math | `ShaderNodeVectorMath` | `node.operation`: ADD, SUBTRACT, SCALE, LENGTH, NORMALIZE, CROSS_PRODUCT, DOT_PRODUCT, etc. |
| Combine XYZ | `ShaderNodeCombineXYZ` | X, Y, Z → Vector |
| Separate XYZ | `ShaderNodeSeparateXYZ` | Vector → X, Y, Z |
| Map Range | `ShaderNodeMapRange` | Value, From Min/Max, To Min/Max |
| Random Value | `FunctionNodeRandomValue` | `node.data_type`: FLOAT, INT, FLOAT_VECTOR, BOOLEAN |
| Compare | `FunctionNodeCompare` | `node.data_type` + `node.operation` |

### Geometry operations

| Node | Type string | Key inputs |
|------|-------------|------------|
| Join Geometry | `GeometryNodeJoinGeometry` | Geometry (multi-input) |
| Set Material | `GeometryNodeSetMaterial` | Geometry, Material |
| Mesh to Points | `GeometryNodeMeshToPoints` | Mesh, Position, Radius |
| Distribute Points on Faces | `GeometryNodeDistributePointsOnFaces` | Mesh, Density/Distance Min |
| Store Named Attribute | `GeometryNodeStoreNamedAttribute` | Geometry, Name, Value |
| Delete Geometry | `GeometryNodeDeleteGeometry` | Geometry, Selection |
| Merge by Distance | `GeometryNodeMergeByDistance` | Geometry, Distance |

### Curves

| Node | Type string | Key inputs |
|------|-------------|------------|
| Curve Line | `GeometryNodeCurvePrimitiveLine` | Start, End |
| Curve Circle | `GeometryNodeCurvePrimitiveCircle` | Resolution, Radius |
| Curve to Mesh | `GeometryNodeCurveToMesh` | Curve, Profile Curve |
| Resample Curve | `GeometryNodeResampleCurve` | Curve, Count |
| Set Curve Radius | `GeometryNodeSetCurveRadius` | Curve, Radius |
| Fillet Curve | `GeometryNodeFilletCurve` | Curve, Radius, Count |

## Example: grid with instanced cubes

```python
import bpy

# Clean slate
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# Create the instance object (a small cube)
bpy.ops.mesh.primitive_cube_add(size=0.3)
instance_obj = bpy.context.active_object
instance_obj.name = "InstanceCube"

# Create material
mat = bpy.data.materials.new("CubeMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.2, 0.5, 1.0, 1.0)
instance_obj.data.materials.append(mat)

# Build geometry node tree
tree = bpy.data.node_groups.new("ScatterCubes", "GeometryNodeTree")

group_in = tree.nodes.new("NodeGroupInput")
group_out = tree.nodes.new("NodeGroupOutput")
group_in.location = (-400, 0)
group_out.location = (400, 0)

tree.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

# Grid node
grid = tree.nodes.new("GeometryNodeMeshGrid")
grid.location = (-200, 0)
grid.inputs["Size X"].default_value = 5.0
grid.inputs["Size Y"].default_value = 5.0
grid.inputs["Vertices X"].default_value = 10
grid.inputs["Vertices Y"].default_value = 10

# Object info (the cube to instance)
obj_info = tree.nodes.new("GeometryNodeObjectInfo")
obj_info.location = (-200, -200)
obj_info.inputs["As Instance"].default_value = True

# Instance on Points
instance = tree.nodes.new("GeometryNodeInstanceOnPoints")
instance.location = (100, 0)

# Links
tree.links.new(instance.inputs["Points"], grid.outputs["Mesh"])
tree.links.new(instance.inputs["Instance"], obj_info.outputs["Geometry"])
tree.links.new(group_out.inputs["Geometry"], instance.outputs["Instances"])

# Create carrier object and attach
mesh = bpy.data.meshes.new("carrier")
carrier = bpy.data.objects.new("GeoNodes", mesh)
bpy.context.collection.objects.link(carrier)
mod = carrier.modifiers.new("GeometryNodes", "NODES")
mod.node_group = tree

# Set Object and Material references directly on the nodes
obj_info.inputs["Object"].default_value = instance_obj

"done"
```

Note: Object, Material, and Collection references on nodes like Object Info, Set Material,
and Collection Info are set via `node.inputs["Name"].default_value = reference`. These
also appear on the modifier panel in the UI.

## Keyframing geometry node inputs

Animate modifier inputs using the object's `keyframe_insert`:
```python
obj = bpy.data.objects["GeoNodes"]
mod = obj.modifiers["GeometryNodes"]

# Animate a float input (e.g. Socket_2)
mod["Socket_2"] = 0.0
obj.keyframe_insert(data_path='modifiers["GeometryNodes"]["Socket_2"]', frame=1)

mod["Socket_2"] = 10.0
obj.keyframe_insert(data_path='modifiers["GeometryNodes"]["Socket_2"]', frame=60)
```

### Vector socket keyframing
```python
# Vector sockets are arrays — keyframe each component
mod["Socket_3"] = [0.0, 0.0, 0.0]
for i in range(3):
    obj.keyframe_insert(
        data_path=f'modifiers["GeometryNodes"]["Socket_3"]',
        frame=1, index=i
    )

mod["Socket_3"] = [5.0, 0.0, 2.0]
for i in range(3):
    obj.keyframe_insert(
        data_path=f'modifiers["GeometryNodes"]["Socket_3"]',
        frame=60, index=i
    )
```

### Easing via F-curves
```python
action = obj.animation_data.action
for fc in action.fcurves:
    if 'modifiers["GeometryNodes"]' in fc.data_path:
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'
```

## Simulation zones

Simulation zones let geometry persist and evolve across frames (physics, trails, etc.).

```python
# IMPORTANT: create output node first, then input, then pair
sim_out = tree.nodes.new("GeometryNodeSimulationOutput")
sim_in = tree.nodes.new("GeometryNodeSimulationInput")
sim_in.pair_with_output(sim_out)

sim_in.location = (-100, 0)
sim_out.location = (200, 0)

# Default state already includes a Geometry socket.
# Add extra state items for persistent data:
sim_out.state_items.new('FLOAT', "Age")
sim_out.state_items.new('VECTOR', "Velocity")

# Access delta time inside the zone
# Use GeometryNodeSimulationInput's "Delta Time" output
# tree.links.new(some_node.inputs["Value"], sim_in.outputs["Delta Time"])

# Wire geometry through the zone
tree.links.new(sim_in.inputs["Geometry"], group_in.outputs["Geometry"])
tree.links.new(group_out.inputs["Geometry"], sim_out.outputs["Geometry"])

# Inside the zone: link sim_in outputs → processing → sim_out inputs
# The zone's internal geometry flows: sim_in.outputs["Geometry"] → ... → sim_out.inputs["Geometry"]
```

**State item types**: `'FLOAT'`, `'INT'`, `'BOOLEAN'`, `'VECTOR'`, `'ROTATION'`, `'RGBA'`, `'GEOMETRY'`

## Repeat zones

Repeat zones run a sub-graph multiple times per frame (iterative refinement, L-systems, etc.).

```python
# IMPORTANT: create output first, then input, then pair
repeat_out = tree.nodes.new("GeometryNodeRepeatOutput")
repeat_in = tree.nodes.new("GeometryNodeRepeatInput")
repeat_in.pair_with_output(repeat_out)

repeat_in.location = (-100, 0)
repeat_out.location = (200, 0)

# Set iteration count
repeat_in.inputs["Iterations"].default_value = 8

# Default state includes Geometry. Add extra items:
repeat_out.repeat_items.new('FLOAT', "Accumulated")
repeat_out.repeat_items.new('INT', "Counter")

# Wire geometry through the zone (same pattern as simulation)
tree.links.new(repeat_in.inputs["Geometry"], some_geo_output)
tree.links.new(next_node.inputs["Geometry"], repeat_out.outputs["Geometry"])

# Inside: repeat_in.outputs → processing → repeat_out.inputs
```

## Music-driven animation

Blender's `sound_bake` operator requires a Graph Editor context and is unreliable via script.
Use Python's stdlib `wave` + `struct` to read audio data directly:

```python
import wave, struct, math

def audio_rms_per_frame(wav_path, fps, frame_count):
    """Read a WAV file and return RMS amplitude per frame."""
    wf = wave.open(wav_path, 'rb')
    sr = wf.getframerate()
    nch = wf.getnchannels()
    sw = wf.getsampwidth()
    samples_per_frame = sr // fps
    fmt = {1: 'b', 2: 'h', 4: 'i'}[sw]
    max_val = float(2 ** (8 * sw - 1))
    rms_values = []
    for _ in range(frame_count):
        raw = wf.readframes(samples_per_frame)
        if not raw:
            rms_values.append(0.0)
            continue
        count = len(raw) // sw
        samples = struct.unpack(f'<{count}{fmt}', raw)
        # Average channels if stereo
        mono = [samples[i] for i in range(0, count, nch)]
        rms = math.sqrt(sum(s * s for s in mono) / max(len(mono), 1)) / max_val
        rms_values.append(rms)
    wf.close()
    return rms_values

# Bake to keyframes on a custom property
import bpy
obj = bpy.data.objects["GeoNodes"]
scene = bpy.context.scene

rms = audio_rms_per_frame("/path/to/audio.wav", scene.render.fps, scene.frame_end)
for frame, val in enumerate(rms, start=1):
    obj["audio_level"] = val
    obj.keyframe_insert(data_path='["audio_level"]', frame=frame)
```

### Drive modifier input from custom property

```python
mod = obj.modifiers["GeometryNodes"]

# Add a driver to a geometry nodes input
drv = obj.driver_add(f'modifiers["GeometryNodes"]["Socket_2"]')
var = drv.driver.variables.new()
var.name = "audio"
var.targets[0].id = obj
var.targets[0].data_path = '["audio_level"]'
drv.driver.expression = "audio * 5.0"  # scale to taste
```

## Fast iteration tips

- **Screenshot the viewport** before rendering — check object placement for free
- **Low instance counts** during iteration (e.g. 5x5 grid, not 100x100)
- **`resolution_percentage = 25`** + `BLENDER_EEVEE` for quick visual checks
- **Batch changes**, then render once — don't render after every tweak
- See `blender-3d` skill for full rendering and materials reference

## Known issues (Blender 5.0.1)

- **`mod["Socket_N"]` may need `obj.data.update()`** after setting values to refresh the viewport
- **Socket identifiers renumber** when the tree interface changes — always introspect `tree.interface.items_tree` rather than hardcoding identifiers
- **`sound_bake` needs Graph Editor context** — use the WAV reader approach above instead
- **Render can crash** with threading issues — use `resolution_percentage = 25` for test renders
