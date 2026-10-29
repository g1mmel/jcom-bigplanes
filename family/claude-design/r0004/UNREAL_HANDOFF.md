# Unreal handoff — configurable C-130 r0004

Author: **claude-design**. **Native Unreal import, cook and runtime: NOT_RUN.**
This is a glTF/source delivery with a working JavaScript reference consumer. No
native `.uasset`, Blueprint or Unreal loadout implementation is supplied. The
following is the integration contract and proposed acceptance path.

## Keep one family assembly

Import `models/c130-family.glb` as the common aircraft assembly and retain the
stable module-root names used in `loadouts/catalog.json`. The catalogue defines
12 slots, 28 options, 8 presets and declared compatibility rules. An appropriate
game representation is one aircraft Actor with a shared body and independently
selectable module components. Preserve independent pivots for moving parts;
merging all meshes into one static mesh would remove required articulation and
configuration boundaries.

The glTF contains rigid-node animation and morph targets, with no skeletal skins.
Rigid clips operate propellers, surfaces, doors, gear, gimbals and visual effects.
Hose and basket deformation also uses morph weights. The target import pipeline
must explicitly preserve or translate both kinds of animation; a static-mesh
import alone is not the complete runtime asset.

Epic documents Interchange as a configurable import pipeline and describes glTF
scene import through Import Into Level. Those features provide an import entry
point, not evidence that this asset's full rigid hierarchy and morph animation
contract already works in the project's chosen engine version. Verify the exact
version and import settings used by the project:
[Importing assets using Interchange](https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-assets-using-interchange-in-unreal-engine).

## Default module scales and visibility

The master encodes the default transport-H selection by setting inactive
equipment roots to `[0,0,0]` scale. Each such root is identified by
`loadout_module_root: true` and carries `canonical_scale: [1,1,1]`. Active roots
start at canonical scale. This allows generic glTF viewers to show one coherent
default configuration without overlapping all alternatives.

Before recording animation rest state, restore every catalogue module root to
its canonical scale. Then apply the default selection through component
visibility/activation. Zero scale at these roots is configuration metadata, not a
stowed pose. Do not indiscriminately normalize descendant scales: actual
authored effect or mechanism tracks may use scale animation.

Use `viewer/loadouts.mjs` and `viewer/pose-driver.mjs` as the executable reference
for this distinction. If the importer discards glTF extras, retain the catalogue
root names and the canonical-scale map in an engine data asset. Preserve names
through import or produce an explicit name mapping; do not infer module identity
from arbitrary imported mesh order.

## Selection and mechanism behavior

The engine consumer should validate a complete selection before changing the
live aircraft. Require one known option for every slot, rejecting unknown slot,
option, family or revision identifiers. Resolve every module root and referenced
control before first use. Evaluate declared compatibility conditions separately
from syntactic validation: the supplied viewer permits creative choices and
labels unmatched or incompatible combinations **Custom JCNC**.

On a successful switch, stop outgoing animation/effect state, restore the old
pose and morph weights, apply all selected roots in one update, and refresh the
active controls. A control referenced by any catalogue option is optional and is
active only when selected options include it. A control not referenced by any
option remains common. A module shared by multiple selected options is enabled
once.

Implement global Actuate everything, Pause, Reverse and Reset using the active
controls and the ownership/staging rules in `articulation/c130-family.json` and
`viewer/controller.mjs`. Cargo staging opens the upper closure before lowering
the ramp, and reverses that order when closing. Gear staging respects covers and
wheel movement. A standalone animation clip does not itself reproduce every
controller sequence. Reset retains the selected loadout and restores transforms
and morph weights; returning to the default configuration is a separate action.

If the game adds collision, mass, hit reactions, effects or replicated state,
the same selection must govern those systems. Hidden rendering alone does not
remove collision or simulation cost. This delivery contains no validated flight
dynamics, live weapon logic, damage model or native collision/LOD policy.

## Units and coordinates

The source GLB uses metres, +X right, +Y up and nose along −Z. Epic's convention is
left handed with +Z up, +X forward and +Y right; the default length unit is
centimetres. Sources:
[Coordinate system and spaces](https://dev.epicgames.com/documentation/en-us/unreal-engine/coordinate-system-and-spaces-in-unreal-engine)
and [Units of measurement](https://dev.epicgames.com/documentation/en-us/unreal-engine/units-of-measurement-in-unreal-engine).

For a manual basis conversion, the intended position mapping from glTF to Unreal
is `[x, y, z]` metres → `[-z, x, y] × 100` centimetres. Convert the full transform
basis, mesh winding/normals and rotations consistently; do not transform
positions alone. Importers may already perform unit/handedness conversion, so
measure a known extent and inspect nose/up directions before applying an
additional conversion. The packed Blender scene uses Blender's own imported
basis; it is not a reason to apply the glTF position formula twice.

## Version-specific acceptance gate

1. Record engine version, importer, settings and input GLB/catalogue/sidecar
   hashes. Import into a clean test map and confirm scale, axes, materials and
   stable root-name mapping.
2. Confirm the default selection, restore all 37 canonical module roots, then
   switch every option. Only the chosen panel/door and equipment modules should
   remain active; common fuselage geometry should remain the same instance.
3. Exercise all 44 controls across applicable presets, checking rigid motion
   and actual hose/basket morph deformation. Verify cargo and gear staging,
   pause, reverse and reset, including interruptions.
4. Switch away during a gun visual cycle and hose deployment. Verify outgoing
   effects stop and old transform/morph state does not leak into the next use.
5. Inspect all eight presets and a conflicting custom selection. Check the
   Custom JCNC label, active controls and save/reload identity. Validate any
   native collision, visibility, replication and performance rules introduced
   by the game.
6. Cook/package the test project and repeat representative mechanisms and
   loadout switches in the packaged build. Store screenshots, logs and the exact
   accepted asset hashes as a distinct native acceptance report.

The CPU and Blender evidence in [QA_SUMMARY.md](QA_SUMMARY.md) is useful reference
material for comparison. It does not replace this gate. Sampled ramp checks also
leave hinge-zone contacts and unsampled/combined-motion clearance unresolved.

## Reusable components

The seven independent system folders in `components/` can be integrated or
inspected separately. Their local articulation files and original source define
their own pivots and control IDs. The three reused r0003 components retain
historical manifests; four new r0004 components have their own frozen receipts.
Use those local identities when promoting a component into a shared game asset
library. Aircraft module placement and per-component origin are separate
concerns and should be preserved in the target assembly.
