# GAU-23 family aircraft cannon — visual component

claude-design / cg46 · r0003 · `DRAFT_ARTICULATED_REVIEW`

The aircraft-style 30 mm component contains a single barrel, receiver, mount and articulated feed-guide detail, a flexible installation boot, and an empty-case collection bag. Its fire-cycle clip coordinates a brief muzzle flash, recoil, a visible empty case passing through the receiver opening toward the bag, and dissipating smoke. The separate yaw, pitch and recoil clips support visual inspection.

## Package contents

| File | Purpose |
| --- | --- |
| `model.glb` | Self-contained glTF 2.0 geometry, materials and named animation clips. |
| `articulation.json` | Exported controls, playback and visual-effect bindings. |
| `editable.blend` | Direct import of the delivered GLB, saved and reopened in Blender 4.5.15 LTS; named actions/NLA tracks and packed texture images are retained. |
| `source/` | Independent Python authoring source, component selection and pinned dependency versions. |
| `materials.json`, `textures/` | Exact PBR definitions, mesh/material/texture mappings and original embedded-image exports. |
| `inspector.html` | Portable inspector with the model and controls embedded. Its companion manifest and QA receipt describe that viewer artifact. |
| `manifest.json` | SHA-256 and size of every package file except the manifest itself, plus the delivered model/native-scene binding. |

## Rebuild and integration

From this component directory, install the pinned dependencies into a Python environment and run:

```bash
python -m pip install -r source/requirements.txt
python source/component_source.py
```

The entry point writes `model-rebuilt.glb` and `rebuild-receipt.json`; it leaves the delivered `model.glb` and controller unchanged. It needs no parent aircraft files or network access after dependency installation. The existing isolation review matched the rebuilt component's geometry, materials, hierarchy and clips. Whole-file bytes can differ because the assembled export retains additional unused material/metadata definitions.

The canonical component root is `PIVOT_gun30_component` and carries the `level 1` tag. Units are metres, with +Y up and barrel axis toward local −X. The native Blender import converts glTF `[x, y, z]` to Blender `[x, -z, y]`. Attach or reposition the component root; aircraft installation placement belongs to the containing aircraft asset. The empty `AIRFRAME_COMMON_SOURCE` node and unused family material names are retained metadata and carry no aircraft mesh or image dependency.

9 original analytic PNG images are embedded in the GLB and copied unchanged to `textures/`. The material inventory marks maps and materials that are retained but unused by this component. The editable Python source is the parametric authoring master; `editable.blend` is the reviewed native import of the delivered model.

## Provenance

The mesh geometry and visual animation were authored for this revision from public photographic references. No Sketchfab model, downloaded viewer geometry, third-party mesh or photographic texture was incorporated. The Sketchfab search did not produce an exact component with a readily available authorized original download suitable for this delivery. Reference pages guided visible form and configuration; they are not engineering drawings. Linked photographs and manufacturer materials are not bundled and retain their original terms.

- [USAF/DVIDS: AC-130J exterior 30 mm installation](https://www.dvidshub.net/image/6427944/ac-130j-crew-maintain-proficiency-combat-readiness)
- [USAF/DVIDS: AC-130W interior installation](https://www.dvidshub.net/image/6317363/ac-130w-supports-uae-us-maritime-surface-warfare-exercise)
- [USAF/DVIDS: AC-130W live-fire visual reference](https://www.dvidshub.net/image/3486265/live-fire-training-with-ac-130w)
- [USAF/DVIDS: AC-130J early firing reference](https://www.dvidshub.net/image/3146917/angry-annie-fires-first-rounds)

## Scope and limitations

The visible mount, feed guides and case path are authored approximations of an aircraft installation. Mechanical internals and ammunition feeding are not simulated. The case is an empty visual prop; no projectile, ballistic path, fire-control solution, damage or combat behavior is supplied. The flash, smoke, recoil distance, motion limits and clip timing are presentation choices, not measured operating data. Use the fire cycle on its own when inspecting coordinated firing; its recoil track overlaps the separate recoil demonstration clip.

Surface finish, dimensions and travel are visual approximations. Photographic equivalence and photorealistic acceptance have not been established. This is a game/visualization component, with no manufacturing or operational specification implied.

The delivered bytes passed the existing glTF format and scoped geometry/source-isolation checks, plus the native Blender import/save/reopen review. These checks do not establish continuous collision clearance, a particular aircraft tail/block fit, damage behavior, runtime performance or native Unreal acceptance. Those gates remain open. The manifest binds the existing review results to the delivered model and native scene; detailed receipts are in the full family revision's `qa/` directory.
