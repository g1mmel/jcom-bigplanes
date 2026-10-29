# Native systems review

`source/blender_systems_review.py` imports the actual exported GLB with Blender's native glTF importer. It does not rebuild or repair mesh geometry. The reports and pictures are scoped to the SHA-256 recorded in each report.

## What the script checks

- Native import of the full aircraft or independent component, with its original geometry, material images and named animation clips.
- Eight samples of each imported firing-cycle or EO/IR yaw/pitch clip. Every animated target must change, every sampled transform must stay finite, and sampled vertices from the actual descendant meshes must move.
- Saving and reopening an editable `.blend`, preserving named actions, NLA track inventory and packed material images.
- Exact conversion of requested controller snapshot world matrices after confirming the model, articulation, controller and pose-driver hashes.
- Unchanged GLB input bytes throughout the review and exact hashes for the `.blend` and every rendered PNG.

The native animation adapter restores the imported action and its Blender action slot from each named NLA track. This follows the glTF importer's own restore method; simply unmuting a stashed track did not evaluate correctly in this Blender version. The imported keys and curves remain unchanged.

Controller node names are matched exactly, with collision-checked aliases for the character sanitization used by Three.js `PropertyBinding.sanitizeNodeName`. The world-axis conversion is `[x,y,z] → [x,-z,y]`: source glTF uses +Y up and nose −Z, while Blender uses +Z up and nose +Y. Scene scale remains one metre per unit.

## Rendering

The selected evidence uses Blender 4.5.15 LTS, Cycles on CPU, 24 samples, denoising and 1000 × 740 PNG output. Cameras are orthographic inspection cameras. The 30 mm exterior camera is forward of the propeller so that the propeller does not obscure the gun. `qa/system-review-cameras.json` records camera positions, targets and framing.

Cutaway views hide explicitly named aircraft meshes only for the render. The original meshes stay intact in the native file. Every such image is labelled **CUTAWAY INSPECTION**. Interior inspection lights are also identified in the caption; they make the equipment readable and are not a claim about cabin lighting.

## Repeat the review

Run these commands from the revision directory, replacing `blender` with the installed Blender executable. Use the final exported files and freshly regenerated controller snapshots.

```bash
blender -b --factory-startup --python source/blender_systems_review.py -- \
  --root . --model ac130j --label r0003 \
  --camera-file qa/system-review-cameras.json --views gun105 gun30

blender -b --factory-startup --python source/blender_systems_review.py -- \
  --root . --model ac130j --label r0003 --reuse-editable \
  --camera-file qa/system-review-cameras.json --views internal30-cutaway \
  --snapshot-label GUN30_CYCLE_50

blender -b --factory-startup --python source/blender_systems_review.py -- \
  --root . --component components/gau23-visual/model.glb \
  --model gau23-visual --asset-id gau23-visual --label r0003 --views isolated
```

`--reuse-editable` is intended for extra pose renders from the same immutable asset. It rejects a native scene whose recorded GLB or review-script hash is stale. It avoids replacing the native file already referenced by another pose report. `--clip NAME --time 0.5` can instead render a normalized native action sample; this is an authored game-animation phase, not a real operational time.

`--compare-input /path/to/earlier.glb` renders an earlier source from the same camera contract at its canonical rest pose. It does not generate a substitute earlier model.

## Scope limits

These checks establish native import, editability, sampled animation evaluation and the appearance of the rendered poses. They do not certify continuous collision clearance, browser/GPU rendering, native Unreal import, photographic equivalence or real weapon operation. The independent runtime and geometry checks have separate reports. A photograph-guided visual model still contains authored dimensions, simplified internal equipment, and authored motion/FX; the reference ledger records what the photographs do and do not establish.

The final report index is `qa/system-review-summary.json`. Use that index to distinguish the selected deliverables from intermediate review files.
