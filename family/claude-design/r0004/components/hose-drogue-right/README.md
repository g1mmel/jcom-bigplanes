# Hose Drogue Right — r0004

Author: **claude-design**. Independent reusable visual component, tagged `level 1`.

The high-speed basket is active at rest; the low-speed alternative is present with its configuration scale zero. Change the basket selector in the independent inspector to preview either variant. Hose and woven fabric use actual morph targets; coupling and rib pivots use transform tracks.

## Files and use

- `model.glb`: compact standalone geometry, materials, embedded resources and real animation channels.
- `articulation.json`: named controls and presentation durations.
- `inspector.html`: self-contained component inspector; open in a WebGL2 browser. It includes Actuate everything, pause, reverse, reset, individual controls and surface/wireframe/X-ray views.
- `editable.blend`: actual GLB imported into Blender 4.5.15 LTS, with editable meshes, named pivots, materials and imported object/shape-key actions. Saved and reopened during validation.
- `source/`: complete local Python source and configuration for a fresh rebuild; no aircraft GLB or external project is required.
- `source-isolation.json`, `native-blender.json`, `inspector.manifest.json`: separate source, native and inspector evidence.
- `materials.json` and `textures/`: material bindings and any exact embedded image payloads.
- `manifest.json`: file hashes, datum and acceptance scope.

## Datum and timeline

Local mounting datum at [0,0,0]; +X right, +Y up, forward -Z; metres.

glTF basis is +X right, +Y up, forward -Z, in metres. Blender performs its standard glTF basis conversion to +Z up. The imported normalized animation occupies NLA frames 1–25 at 24 fps; runtime presentation duration comes from `articulation.json`. Scrub the timeline to evaluate the preserved native animation. The saved file starts in the canonical rest state.

## Rebuild independently

Use Python 3.12 with the versions in `source/requirements.txt` installed. From this component folder:

```sh
python source/build_component.py --output-dir rebuilt
```

The command creates `rebuilt/model.glb`, `rebuilt/articulation.json` and `rebuilt/rebuild-receipt.json`. The builder creates a fresh empty authoring model and extracts only this component subtree. It has a network audit guard and rejects attempts to read prebuilt GLB, glTF or Blender assets. Shared utility source is included to resolve imports; the aircraft build entry point is not called.

To recreate the native editable file from the delivered model, use Blender 4.5 LTS:

```sh
blender --background --factory-startup --python source/make_editable.py -- --component-dir .
```

## Verification and limits

Isolated rebuilding passed with no prebuilt model input and no network calls. Every expanded geometry attribute, morph target, node hierarchy/rest transform, material/image binding and animation input/output was compared with the delivered component. Maximum absolute numeric difference: **5.99480369e-15**; tolerance: **0.00001**, relative tolerance zero. The result is semantic equivalence; metadata and local origin baking can produce different GLB bytes.

Blender import, seven-sample native object and shape-key animation evaluation, actual local morph vertex movement, reset and save/reopen passed. These are visible game representations informed by public references. Exact dimensions, travel, flexible material behavior and effect timing are artist authored. Browser/WebGL rendering, continuous physical clearance, photographic acceptance and native Unreal acceptance are not established by these component checks. See each evidence file for its exact scope.
