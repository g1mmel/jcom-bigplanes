# MX-20-family representative EO/IR visual component

claude-design / cg46 · r0003 · `DRAFT_ARTICULATED_REVIEW`

This representative sensor has a matte gray housing, its own top cap, an open fork/yoke, recessed unequal optical windows, dark optical barrels, seals and fastener details. Separate yaw and pitch hierarchies articulate the housing and optical assembly. It is an independent visual component; aircraft pylons, installation transforms and aircraft geometry are outside the package.

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

The canonical component root is `PIVOT_eoir_component` and carries the `level 1` tag. Units are metres, with +Y up and optical face toward local −Z. The native Blender import converts glTF `[x, y, z]` to Blender `[x, -z, y]`. Attach or reposition the component root; aircraft installation placement belongs to the containing aircraft asset. The empty `AIRFRAME_COMMON_SOURCE` node and unused family material names are retained metadata and carry no aircraft mesh or image dependency.

This component uses PBR material factors without image maps. The `textures/` directory explains that intentional absence. The editable Python source is the parametric authoring master; `editable.blend` is the reviewed native import of the delivered model.

## Provenance

The mesh geometry and visual animation were authored for this revision from public photographic references. No Sketchfab model, downloaded viewer geometry, third-party mesh or photographic texture was incorporated. The Sketchfab search did not produce an exact component with a readily available authorized original download suitable for this delivery. Reference pages guided visible form and configuration; they are not engineering drawings. Linked photographs and manufacturer materials are not bundled and retain their original terms.

- [L3Harris: WESCAM MX-20 manufacturer product page](https://www.l3harris.com/all-capabilities/wescam-mx-20-air-surveillance-and-reconnaissance)
- [L3Harris: manufacturer product photograph used for visible form](https://www.l3harris.com/sites/default/files/2026-04/wescam-mx-20-eo-ir-air-surveillance-reconnaissance.png)
- [L3Harris: public MX-20 family brochure](https://www.l3harris.com/sites/default/files/2020-07/ims_eo_brochure_wescam_MX-20-0102AB-Brochure.pdf)
- [USAF: MC-130W Dragon Spear sensor identification](https://www.robins.af.mil/News/Article-Display/Article/377994/mc-130w-dragon-spear-visits-robins/)
- [USAF/DVIDS: 2019 AC-130J chin installation photograph](https://www.dvidshub.net/image/5621880/73rd-amu-air-commandos-perform-post-flight-inspection-ac-130j-ghostrider-gunship)

## Scope and limitations

The visible form is guided by public MX-20 family imagery. Exact aperture assignments, window sizes, surface finishes, motion limits and internal gimbal construction are not established. The AC-130W source identifies two MX-20 sensors, but the exact sensor type fitted to each AC-130J slot remains configuration-dependent; this package does not establish a particular J tail/block fit. It contains no sensor image generation, tracking, laser, targeting or other operational sensor simulation. The manufacturer product photograph is a later family-form reference, not proof of a specific 2021 installation.

Surface finish, dimensions and travel are visual approximations. Photographic equivalence and photorealistic acceptance have not been established. This is a game/visualization component, with no manufacturing or operational specification implied.

The delivered bytes passed the existing glTF format and scoped geometry/source-isolation checks, plus the native Blender import/save/reopen review. These checks do not establish continuous collision clearance, a particular aircraft tail/block fit, damage behavior, runtime performance or native Unreal acceptance. Those gates remain open. The manifest binds the existing review results to the delivered model and native scene; detailed receipts are in the full family revision's `qa/` directory.
