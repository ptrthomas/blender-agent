---
name: blender-laser
description: Create laser beam effects in Blender using Python raycasting with reflection. Use when the user wants lasers, light beams, bouncing rays, or reflective beam effects in Blender scenes.
---

# Blender Laser Beams — Python Raycasting Skill

Build laser beams that raycast against scene geometry and reflect off surfaces using
a `frame_change_post` handler. See `blender-3d` for materials, cameras, and rendering.

Send all code via:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
<python code>
PYEOF
```

## Core concept

A Python handler runs every frame. For each laser beam object:
1. Get the beam's direction in world space (from a parent pivot's transform)
2. `scene.ray_cast()` from the origin along the direction — returns hit in **world space**
3. On hit: record the point, **reflect** the direction, offset origin to avoid self-hit
4. Repeat for N bounces
5. Rebuild the beam's mesh as a polyline from the collected points
6. A Geometry Nodes modifier converts the polyline to a visible tube

**Why Python over Geometry Nodes:** `scene.ray_cast()` works in world space — no
coordinate transforms needed. GN Raycast operates in the modifier's local space,
requiring a world→local transform chain that breaks reflection angles when the laser
source is rotated. Python is also far simpler to debug.

## Parameters

```python
BOUNCES = 3           # number of reflections
RAY_LENGTH = 50.0     # max segment length on miss (meters)
BEAM_RADIUS = 0.05    # tube cross-section radius
REFLECTION_LOSS = 0.2 # intensity reduction per bounce (0–1)
BASE_EMISSION = 8.0   # emission strength at full intensity
FIX_OFFSET = 0.01     # anti-self-intersection offset along normal
```

## Complete setup

### 1. Create beam objects

Each laser is a mesh object with custom properties. Parent them to a pivot for animation.

```python
import bpy
from mathutils import Vector

pivot = bpy.data.objects["LaserPivot"]  # animated empty at beam origin

LASER_DIRS = {
    "Laser_PosX": Vector((1, 0, 0)),
    "Laser_NegX": Vector((-1, 0, 0)),
    "Laser_PosY": Vector((0, 1, 0)),
    "Laser_NegY": Vector((0, -1, 0)),
}

for name, direction in LASER_DIRS.items():
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["beam_direction"] = list(direction)
    obj["is_laser_beam"] = True
```

### 2. Frame handler (the laser engine)

```python
import bpy
from mathutils import Vector

BOUNCES = 3
RAY_LENGTH = 50.0
REFLECTION_LOSS = 0.2

_updating = False

def update_lasers(scene, depsgraph=None):
    global _updating
    if _updating:
        return

    pivot = bpy.data.objects.get("LaserPivot")
    if not pivot:
        return

    _updating = True
    try:
        if depsgraph is None:
            depsgraph = bpy.context.evaluated_depsgraph_get()

        beam_objs = [o for o in bpy.data.objects if o.get("is_laser_beam")]

        # Hide beams so ray_cast doesn't hit them
        for obj in beam_objs:
            obj.hide_viewport = True
        depsgraph.update()

        pivot_eval = pivot.evaluated_get(depsgraph)
        pivot_matrix = pivot_eval.matrix_world
        origin = pivot_matrix.translation.copy()

        results = {}
        for obj in beam_objs:
            local_dir = Vector(obj["beam_direction"])
            world_dir = (pivot_matrix.to_3x3() @ local_dir).normalized()

            points = [origin.copy()]
            intensities = [1.0]
            ray_origin = origin.copy()
            ray_dir = world_dir.copy()
            intensity = 1.0

            for bounce in range(BOUNCES + 1):
                hit, pos, normal, idx, hit_obj, mx = scene.ray_cast(
                    depsgraph, ray_origin, ray_dir, distance=RAY_LENGTH
                )
                if hit:
                    points.append(pos.copy())
                    intensity *= (1.0 - REFLECTION_LOSS)
                    intensities.append(intensity)
                    # Reflect: R = D - 2(D·N)N
                    ray_dir = ray_dir - 2.0 * ray_dir.dot(normal) * normal
                    ray_dir.normalize()
                    ray_origin = pos + normal * 0.01  # offset to avoid self-hit
                else:
                    points.append(ray_origin + ray_dir * RAY_LENGTH)
                    intensities.append(intensity)
                    break

            results[obj.name] = (points, intensities)

        # Unhide and rebuild meshes
        for obj in beam_objs:
            obj.hide_viewport = False
            points, intensities = results[obj.name]
            mesh = obj.data
            mesh.clear_geometry()
            if len(points) < 2:
                continue
            verts = [tuple(p) for p in points]
            edges = [(i, i + 1) for i in range(len(points) - 1)]
            mesh.from_pydata(verts, edges, [])
            mesh.update()

            # Store intensity per vertex
            if "intensity" not in mesh.attributes:
                mesh.attributes.new("intensity", 'FLOAT', 'POINT')
            for i, val in enumerate(intensities):
                mesh.attributes["intensity"].data[i].value = val
    finally:
        _updating = False

# Register (idempotent)
bpy.app.handlers.frame_change_post[:] = [
    h for h in bpy.app.handlers.frame_change_post
    if not getattr(h, '__name__', '') == 'update_lasers'
]
bpy.app.handlers.frame_change_post.append(update_lasers)
```

### 3. Beam thickness (Geometry Nodes modifier)

The handler produces a polyline mesh. A simple GN modifier converts it to a tube:

```python
ng = bpy.data.node_groups.new("BeamThickness", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

nodes, links = ng.nodes, ng.links
gi = nodes.new("NodeGroupInput")
go = nodes.new("NodeGroupOutput")

m2c = nodes.new("GeometryNodeMeshToCurve")
circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
circle.mode = 'RADIUS'
circle.inputs["Radius"].default_value = 0.05  # beam thickness
circle.inputs["Resolution"].default_value = 6
c2m = nodes.new("GeometryNodeCurveToMesh")
set_mat = nodes.new("GeometryNodeSetMaterial")
set_mat.inputs["Material"].default_value = bpy.data.materials["LaserBeamMat"]

links.new(m2c.inputs["Mesh"], gi.outputs["Geometry"])
links.new(c2m.inputs["Curve"], m2c.outputs["Curve"])
links.new(c2m.inputs["Profile Curve"], circle.outputs["Curve"])
links.new(set_mat.inputs["Geometry"], c2m.outputs["Mesh"])
links.new(go.inputs["Geometry"], set_mat.outputs["Geometry"])

# Apply to all beam objects
for obj in bpy.data.objects:
    if obj.get("is_laser_beam"):
        mod = obj.modifiers.new("BeamThickness", 'NODES')
        mod.node_group = ng
```

### 4. Emission material with intensity falloff

```python
mat = bpy.data.materials.new("LaserBeamMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
for n in list(nodes):
    nodes.remove(n)

output = nodes.new("ShaderNodeOutputMaterial")
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Base Color"].default_value = (1, 0.05, 0.02, 1)
bsdf.inputs["Emission Color"].default_value = (1, 0.05, 0.02, 1)

# Read per-vertex intensity attribute
attr = nodes.new("ShaderNodeAttribute")
attr.attribute_type = 'GEOMETRY'
attr.attribute_name = "intensity"

multiply = nodes.new("ShaderNodeMath")
multiply.operation = 'MULTIPLY'
multiply.inputs[1].default_value = 8.0  # base emission strength

links.new(multiply.inputs[0], attr.outputs["Fac"])
links.new(bsdf.inputs["Emission Strength"], multiply.outputs[0])
links.new(output.inputs["Surface"], bsdf.outputs["BSDF"])
```

## Critical details

### Excluding beams from ray_cast

`scene.ray_cast()` hits ALL visible scene geometry. The beam meshes themselves will
block rays if visible. **Hide beam objects before raycasting, unhide after:**

```python
for obj in beam_objs:
    obj.hide_viewport = True
depsgraph.update()  # MUST update depsgraph after hiding
# ... ray_cast calls ...
for obj in beam_objs:
    obj.hide_viewport = False
```

### Recursion guard

The handler modifies mesh data, which can trigger `depsgraph_update_post`. Use a
`_updating` flag to prevent re-entry. Do NOT register on `depsgraph_update_post` —
only use `frame_change_post`.

### Evaluated depsgraph for animated pivots

Use `pivot.evaluated_get(depsgraph).matrix_world` to get the pivot's animated transform
at the current frame. The non-evaluated `pivot.matrix_world` may return stale data.

### Fix offset direction

Offset the ray origin along the **hit normal** (not the ray direction) to avoid
self-intersection: `ray_origin = hit_pos + hit_normal * 0.01`

### Reflection formula

```python
# Standard reflection: R = D - 2(D·N)N
ray_dir = ray_dir - 2.0 * ray_dir.dot(normal) * normal
ray_dir.normalize()
```

All vectors are in world space. No coordinate transforms needed.

## Volumetric atmosphere

For visible beams in dark scenes, wrap the scene in a volume cube:

```python
mat_vol = bpy.data.materials.new("VolumeMat")
mat_vol.use_nodes = True
tree = mat_vol.node_tree
# Remove Principled BSDF, add Volume Scatter → Material Output:Volume
vol_scatter.inputs["Density"].default_value = 0.02
vol_scatter.inputs["Anisotropy"].default_value = 0.3
# Noise texture → Map Range → Density for variation
```

Eevee 5.0 volumetric settings:
```python
eevee = bpy.context.scene.eevee
eevee.use_volumetric_shadows = True
eevee.volumetric_samples = 128
eevee.volumetric_tile_size = '4'  # string: '2', '4', '8', '16'
```

Note: Blender 5.0 removed `use_bloom`. For glow effects, use compositor glare node.

## Scene setup tips

- **Collider surfaces**: Any visible mesh in the scene will reflect lasers (via `scene.ray_cast`).
  To limit reflections to specific objects, put non-reflective objects in a collection
  and hide it from the viewport, or check `hit_obj` in the handler and skip unwanted hits.
- **Mirror materials**: Metallic=1.0, Roughness=0.05 for visual reflectivity
  (ray_cast ignores materials — reflection is purely geometric)
- **Pivot animation**: Parent all beam objects to an animated Empty. Rotate the Empty
  to sweep all beams together. The handler reads the pivot's world matrix each frame.
- **When stuck on visual issues**: Ask the user to validate the scene in Blender's
  viewport — they can see things the screenshot may miss.

