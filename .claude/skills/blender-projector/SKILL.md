---
name: blender-projector
description: Create spotlight projector effects in Blender using procedural shader patterns with volumetric fog. Use when the user wants disco ball effects, projected light patterns, gobos, grid/dot/radial projections, or volumetric spotlight effects in Blender.
---

# Blender Projector — Spotlight Pattern Projection Skill

Project procedural patterns (grid, dots, radial lines, concentric circles) from a Cycles
spotlight through volumetric fog. All parameters are keyframable via shader nodes.

**Requires Cycles** — EEVEE does not support light texture/node projection.

See `blender-3d` for cameras, materials, animation, and rendering.

Send all code via:
```bash
curl -s localhost:5656 --data-binary @- <<'PYEOF'
<python code>
PYEOF
```

## Core concept

A Cycles spotlight with `use_nodes = True` projects whatever color its Emission node
outputs. By building procedural patterns from math nodes (sine, modulo, atan2, distance),
every parameter — spacing, line width, color, count — is natively keyframable.

Volumetric fog (a cube with Volume Principled material) makes the light cone and beams
visible in mid-air. The beams interact naturally with all scene geometry (shadows, light
splash, occlusion) since they are real light.

## Foundation setup

### 1. Cycles renderer

```python
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 64          # increase for final render
scene.cycles.volume_bounces = 2
scene.render.use_sequencer = False  # IMPORTANT: disable or renders go black
```

### 2. Spotlight

Spot lights point along **-Z by default** (downward). Do NOT rotate by pi to point down.

```python
import bpy, math

bpy.ops.object.light_add(type='SPOT', location=(0, 0, 4.9))
spot = bpy.context.active_object
spot.name = "Projector"
# spot.rotation_euler = (0, 0, 0)  # default = pointing down, no rotation needed

spot.data.energy = 8000
spot.data.color = (1, 1, 1)                 # white (pattern provides color)
spot.data.spot_size = math.radians(90)       # cone angle
spot.data.spot_blend = 0.05                  # hard edge
spot.data.shadow_soft_size = 0.01            # sharp shadows for beam definition
spot.data.use_shadow = True
```

**Disco ball sweep**: tilt slightly off-vertical and rotate around Z:
```python
spot.rotation_euler = (math.radians(10), 0, 0)  # slight tilt
spot.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
spot.rotation_euler.z = math.pi * 2
spot.keyframe_insert(data_path="rotation_euler", index=2, frame=120)

# Make rotation linear
for fc in spot.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
```

### 3. Volumetric fog

A cube with Volume Principled material. The fog makes light cones and beams visible.

```python
ROOM_H = 5
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, ROOM_H / 2))
fog = bpy.context.active_object
fog.name = "FogVolume"
fog.scale = (20, 20, ROOM_H)

fog_mat = bpy.data.materials.new("FogMat")
fog_mat.use_nodes = True
nodes = fog_mat.node_tree.nodes
links = fog_mat.node_tree.links

for n in list(nodes):
    nodes.remove(n)

mat_out = nodes.new("ShaderNodeOutputMaterial")
vol = nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.06       # 0.03-0.1 typical range
vol.inputs["Anisotropy"].default_value = 0.7      # 0.5-0.9, higher = tighter beams
links.new(mat_out.inputs["Volume"], vol.outputs["Volume"])

fog.data.materials.clear()
fog.data.materials.append(fog_mat)
```

**Tuning fog:**
- `Density` 0.03 = subtle haze, 0.1 = thick fog
- `Anisotropy` 0.5 = diffuse glow, 0.9 = tight laser-like beams
- Both are keyframable for dramatic transitions

### 4. Dark world background

```python
world = bpy.data.worlds["World"]
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.01, 0.01, 0.02, 1)
bg.inputs["Strength"].default_value = 1.0
```

## Pattern node trees

All patterns follow the same structure:
1. `TexCoord(Normal)` -> `Mapping` -> `Separate XYZ`
2. Math nodes compute a mask (0 or 1)
3. `Mix(black, color, mask)` -> `Emission` -> `Light Output`

The **Mapping node** provides global keyframable control:
- `Location` X/Y = pan/offset the pattern
- `Scale` X/Y = density/spacing (higher = more repetitions)
- `Rotation` Z = spin the pattern

### Common preamble (used by all patterns)

```python
import bpy, math

spot = bpy.data.objects["Projector"]
light = spot.data
light.use_nodes = True

nodes = light.node_tree.nodes
links = light.node_tree.links

for n in list(nodes):
    nodes.remove(n)

# Output + Emission
output = nodes.new("ShaderNodeOutputLight")
emission = nodes.new("ShaderNodeEmission")
emission.inputs["Strength"].default_value = 12.0   # keyframable
links.new(output.inputs["Surface"], emission.outputs["Emission"])

# Texture coordinates + Mapping
tex_coord = nodes.new("ShaderNodeTexCoord")
mapping = nodes.new("ShaderNodeMapping")
links.new(mapping.inputs["Vector"], tex_coord.outputs["Normal"])

# Separate XYZ
sep = nodes.new("ShaderNodeSeparateXYZ")
links.new(sep.inputs["Vector"], mapping.outputs["Vector"])

# Color mix (shared by all patterns, connected at the end)
mix = nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.inputs["A"].default_value = (0, 0, 0, 1)        # background (black = no light)
mix.inputs["B"].default_value = (0, 1, 0.2, 1)      # beam color (keyframable)
links.new(emission.inputs["Color"], mix.outputs["Result"])
```

After the preamble, each pattern builds its mask and connects to `mix.inputs["Factor"]`.

### Pattern 1: Grid

Horizontal + vertical lines with independent visibility control.

```python
# (after preamble)
mapping.inputs["Scale"].default_value = (8, 8, 1)  # line density

# ── Vertical lines (from X) ──
mult_x = nodes.new("ShaderNodeMath")
mult_x.operation = 'MULTIPLY'
mult_x.inputs[1].default_value = 2 * math.pi
links.new(mult_x.inputs[0], sep.outputs["X"])

sine_x = nodes.new("ShaderNodeMath")
sine_x.operation = 'SINE'
links.new(sine_x.inputs[0], mult_x.outputs[0])

abs_x = nodes.new("ShaderNodeMath")
abs_x.operation = 'ABSOLUTE'
links.new(abs_x.inputs[0], sine_x.outputs[0])

gt_x = nodes.new("ShaderNodeMath")
gt_x.operation = 'GREATER_THAN'
gt_x.inputs[1].default_value = 0.97              # line width (higher = thinner)
links.new(gt_x.inputs[0], abs_x.outputs[0])

# Vertical visibility multiplier (keyframe between 0 and 1)
v_vis = nodes.new("ShaderNodeMath")
v_vis.operation = 'MULTIPLY'
v_vis.inputs[1].default_value = 1.0               # 1=visible, 0=hidden
v_vis.label = "V_Visibility"
links.new(v_vis.inputs[0], gt_x.outputs[0])

# ── Horizontal lines (from Y) ──
mult_y = nodes.new("ShaderNodeMath")
mult_y.operation = 'MULTIPLY'
mult_y.inputs[1].default_value = 2 * math.pi
links.new(mult_y.inputs[0], sep.outputs["Y"])

sine_y = nodes.new("ShaderNodeMath")
sine_y.operation = 'SINE'
links.new(sine_y.inputs[0], mult_y.outputs[0])

abs_y = nodes.new("ShaderNodeMath")
abs_y.operation = 'ABSOLUTE'
links.new(abs_y.inputs[0], sine_y.outputs[0])

gt_y = nodes.new("ShaderNodeMath")
gt_y.operation = 'GREATER_THAN'
gt_y.inputs[1].default_value = 0.97
links.new(gt_y.inputs[0], abs_y.outputs[0])

# Horizontal visibility multiplier
h_vis = nodes.new("ShaderNodeMath")
h_vis.operation = 'MULTIPLY'
h_vis.inputs[1].default_value = 1.0
h_vis.label = "H_Visibility"
links.new(h_vis.inputs[0], gt_y.outputs[0])

# Combine: Max(vertical, horizontal)
grid_max = nodes.new("ShaderNodeMath")
grid_max.operation = 'MAXIMUM'
links.new(grid_max.inputs[0], v_vis.outputs[0])
links.new(grid_max.inputs[1], h_vis.outputs[0])

links.new(mix.inputs["Factor"], grid_max.outputs[0])
```

**Keyframable parameters:**
- `mapping.inputs["Scale"]` — line density (X and Y independent)
- `mapping.inputs["Location"]` — pan/scroll the grid
- `mapping.inputs["Rotation"]` — rotate the grid
- `gt_x.inputs[1]` / `gt_y.inputs[1]` — line width (0.9 = thick, 0.99 = hair-thin)
- `v_vis.inputs[1]` — vertical line visibility (0 or 1)
- `h_vis.inputs[1]` — horizontal line visibility (0 or 1)
- `mix.inputs["B"]` — beam color (RGBA)
- `emission.inputs["Strength"]` — overall brightness

### Pattern 2: Dots

Circular dots on a regular grid. Dot density controlled by Mapping scale.

```python
# (after preamble)
mapping.inputs["Scale"].default_value = (8, 8, 1)  # dot density

# Fractional position within each cell
frac_x = nodes.new("ShaderNodeMath")
frac_x.operation = 'FRACT'
links.new(frac_x.inputs[0], sep.outputs["X"])

sub_x = nodes.new("ShaderNodeMath")
sub_x.operation = 'SUBTRACT'
sub_x.inputs[1].default_value = 0.5               # center in cell
links.new(sub_x.inputs[0], frac_x.outputs[0])

sq_x = nodes.new("ShaderNodeMath")
sq_x.operation = 'POWER'
sq_x.inputs[1].default_value = 2.0
links.new(sq_x.inputs[0], sub_x.outputs[0])

frac_y = nodes.new("ShaderNodeMath")
frac_y.operation = 'FRACT'
links.new(frac_y.inputs[0], sep.outputs["Y"])

sub_y = nodes.new("ShaderNodeMath")
sub_y.operation = 'SUBTRACT'
sub_y.inputs[1].default_value = 0.5
links.new(sub_y.inputs[0], frac_y.outputs[0])

sq_y = nodes.new("ShaderNodeMath")
sq_y.operation = 'POWER'
sq_y.inputs[1].default_value = 2.0
links.new(sq_y.inputs[0], sub_y.outputs[0])

# Distance from cell center
add_sq = nodes.new("ShaderNodeMath")
add_sq.operation = 'ADD'
links.new(add_sq.inputs[0], sq_x.outputs[0])
links.new(add_sq.inputs[1], sq_y.outputs[0])

dist = nodes.new("ShaderNodeMath")
dist.operation = 'SQRT'
links.new(dist.inputs[0], add_sq.outputs[0])

# Dot mask: distance < radius
dot_mask = nodes.new("ShaderNodeMath")
dot_mask.operation = 'LESS_THAN'
dot_mask.inputs[1].default_value = 0.15            # dot radius (0.01-0.45)
dot_mask.label = "Dot_Radius"
links.new(dot_mask.inputs[0], dist.outputs[0])

links.new(mix.inputs["Factor"], dot_mask.outputs[0])
```

**Keyframable parameters:**
- `mapping.inputs["Scale"]` — dot density (higher = more dots)
- `mapping.inputs["Location"]` — pan/scroll
- `mapping.inputs["Rotation"]` — rotate the dot grid
- `dot_mask.inputs[1]` — dot radius (0.01 = tiny, 0.45 = nearly touching)
- `mix.inputs["B"]` — dot color
- `emission.inputs["Strength"]` — brightness

### Pattern 3: Radial lines (spokes)

Lines radiating from center, like a starburst or laser fan.

```python
# (after preamble)
# Mapping scale not needed for radial (beam count is explicit)

# Angle from center: atan2(Y, X)
atan2 = nodes.new("ShaderNodeMath")
atan2.operation = 'ARCTAN2'
links.new(atan2.inputs[0], sep.outputs["Y"])       # Y first
links.new(atan2.inputs[1], sep.outputs["X"])       # X second

# Scale by beam count
NUM_BEAMS = 16
mult_beams = nodes.new("ShaderNodeMath")
mult_beams.operation = 'MULTIPLY'
mult_beams.inputs[1].default_value = NUM_BEAMS     # keyframable beam count
mult_beams.label = "Beam_Count"
links.new(mult_beams.inputs[0], atan2.outputs[0])

# sin(angle * count) -> abs -> threshold
sine = nodes.new("ShaderNodeMath")
sine.operation = 'SINE'
links.new(sine.inputs[0], mult_beams.outputs[0])

abs_node = nodes.new("ShaderNodeMath")
abs_node.operation = 'ABSOLUTE'
links.new(abs_node.inputs[0], sine.outputs[0])

gt = nodes.new("ShaderNodeMath")
gt.operation = 'GREATER_THAN'
gt.inputs[1].default_value = 0.97                  # beam width threshold
gt.label = "Beam_Width"
links.new(gt.inputs[0], abs_node.outputs[0])

links.new(mix.inputs["Factor"], gt.outputs[0])
```

**Keyframable parameters:**
- `mult_beams.inputs[1]` — number of beams (integer values: 8, 12, 16, 24...)
- `gt.inputs[1]` — beam width (0.9 = wide, 0.99 = hair-thin)
- `mapping.inputs["Rotation"].default_value[2]` — spin the whole pattern (Z rotation)
- `mapping.inputs["Location"]` — offset the center point
- `mix.inputs["B"]` — beam color
- `emission.inputs["Strength"]` — brightness

**Spinning animation** (keyframe the Mapping rotation Z):
```python
mapping.inputs["Rotation"].default_value = (0, 0, 0)
mapping.inputs["Rotation"].keyframe_insert("default_value", index=2, frame=1)
mapping.inputs["Rotation"].default_value = (0, 0, math.pi * 2)
mapping.inputs["Rotation"].keyframe_insert("default_value", index=2, frame=120)

# Linear interpolation for constant speed
for fc in light.node_tree.animation_data.action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
```

### Pattern 4: Concentric circles (rings)

Rings expanding outward from center.

```python
# (after preamble)

# Distance from center: sqrt(x^2 + y^2)
pow_x = nodes.new("ShaderNodeMath")
pow_x.operation = 'POWER'
pow_x.inputs[1].default_value = 2.0
links.new(pow_x.inputs[0], sep.outputs["X"])

pow_y = nodes.new("ShaderNodeMath")
pow_y.operation = 'POWER'
pow_y.inputs[1].default_value = 2.0
links.new(pow_y.inputs[0], sep.outputs["Y"])

add = nodes.new("ShaderNodeMath")
add.operation = 'ADD'
links.new(add.inputs[0], pow_x.outputs[0])
links.new(add.inputs[1], pow_y.outputs[0])

dist = nodes.new("ShaderNodeMath")
dist.operation = 'SQRT'
links.new(dist.inputs[0], add.outputs[0])

# Scale distance for ring spacing
ring_freq = nodes.new("ShaderNodeMath")
ring_freq.operation = 'MULTIPLY'
ring_freq.inputs[1].default_value = 8.0            # ring count/density
ring_freq.label = "Ring_Frequency"
links.new(ring_freq.inputs[0], dist.outputs[0])

# sin(dist * freq * 2pi) for periodic rings
mult_2pi = nodes.new("ShaderNodeMath")
mult_2pi.operation = 'MULTIPLY'
mult_2pi.inputs[1].default_value = 2 * math.pi
links.new(mult_2pi.inputs[0], ring_freq.outputs[0])

sine = nodes.new("ShaderNodeMath")
sine.operation = 'SINE'
links.new(sine.inputs[0], mult_2pi.outputs[0])

abs_node = nodes.new("ShaderNodeMath")
abs_node.operation = 'ABSOLUTE'
links.new(abs_node.inputs[0], sine.outputs[0])

gt = nodes.new("ShaderNodeMath")
gt.operation = 'GREATER_THAN'
gt.inputs[1].default_value = 0.95                  # ring width
gt.label = "Ring_Width"
links.new(gt.inputs[0], abs_node.outputs[0])

links.new(mix.inputs["Factor"], gt.outputs[0])
```

**Keyframable parameters:**
- `ring_freq.inputs[1]` — number of rings (higher = more rings, tighter spacing)
- `gt.inputs[1]` — ring thickness (0.85 = thick, 0.99 = hair-thin)
- `mapping.inputs["Scale"]` — stretch into ellipses (non-uniform X/Y)
- `mapping.inputs["Location"]` — offset center point
- `mix.inputs["B"]` — ring color
- `emission.inputs["Strength"]` — brightness

**Expanding animation** (rings move outward by animating Mapping location or ring_freq):
```python
# Animate ring frequency decreasing = rings expand outward
ring_freq.inputs[1].default_value = 12.0
ring_freq.inputs[1].keyframe_insert("default_value", frame=1)
ring_freq.inputs[1].default_value = 4.0
ring_freq.inputs[1].keyframe_insert("default_value", frame=120)
```

## Combining patterns

Patterns can be combined on a single light by merging masks before the color mix.
Use `Maximum` (union) or `Multiply` (intersection) to combine two pattern masks:

```python
# Example: radial lines + concentric circles = spiderweb
# Build both masks separately, then:
combine = nodes.new("ShaderNodeMath")
combine.operation = 'MAXIMUM'       # MAXIMUM = union, MINIMUM = intersection
links.new(combine.inputs[0], radial_mask.outputs[0])
links.new(combine.inputs[1], circles_mask.outputs[0])
links.new(mix.inputs["Factor"], combine.outputs[0])
```

## Multiple projectors

Each spotlight is independent. Create multiple spots with different patterns, colors,
positions, and animations:

```python
# Second projector with different color and pattern
bpy.ops.object.light_add(type='SPOT', location=(2, 0, 4.9))
spot2 = bpy.context.active_object
spot2.name = "Projector_Red"
spot2.data.energy = 8000
spot2.data.spot_size = math.radians(70)
# Build pattern nodes on spot2.data.node_tree (same technique)
# Set mix.inputs["B"] = (1, 0.05, 0.02, 1) for red beams
```

## Keyframing pattern parameters

All node socket values are keyframable. Access them through the node tree:

```python
light = bpy.data.objects["Projector"].data
nodes = light.node_tree.nodes

# Find node by label or name
ring_freq = next(n for n in nodes if n.label == "Ring_Frequency")

# Keyframe a value
ring_freq.inputs[1].default_value = 12.0
ring_freq.inputs[1].keyframe_insert("default_value", frame=1)
ring_freq.inputs[1].default_value = 6.0
ring_freq.inputs[1].keyframe_insert("default_value", frame=60)

# Keyframe color change
mix = next(n for n in nodes if n.type == 'MIX' and n.data_type == 'RGBA')
mix.inputs["B"].default_value = (0, 1, 0.2, 1)    # green
mix.inputs["B"].keyframe_insert("default_value", frame=1)
mix.inputs["B"].default_value = (1, 0.05, 0.02, 1) # red
mix.inputs["B"].keyframe_insert("default_value", frame=60)

# Linear interpolation on node tree animation
action = light.node_tree.animation_data.action
for fc in action.fcurves:
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'
```

## Rendering tips

- **Cycles only** — EEVEE does not support spotlight node tree projection
- Use `resolution_percentage = 25-50` while iterating, full res for final
- `cycles.samples = 64` is enough for previews; 256+ for clean final renders
- Volumetric fog adds significant render time — lower `Density` for faster iteration
- `spot_size` (cone angle) controls how far beams spread — wider = more room coverage
- `spot_blend` near 0 = hard cone edge (good for projection), near 1 = soft fade
- `shadow_soft_size` near 0 = sharp beam edges, larger = soft/diffuse beams

## Scene setup tips

- **Floor and walls** with diffuse materials show the projected pattern clearly
- **Objects in the scene** naturally occlude and interact with beams (shadows, light splash)
- **Dark room** with dark world background makes beams most visible
- **Bloom** via compositor Glare node (see `blender-3d` skill) adds glow to bright beams
- **Multiple fog densities**: use separate fog cubes with different densities for
  localized haze effects
