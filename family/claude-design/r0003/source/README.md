# r0003 authoring source

Author: claude-design. These scripts are the editable source masters for the
photo-guided game visual systems. All dimensions, movement and timing are
authored approximations. They are not engineering or operating data.

## Rebuild the revised gunships and independent systems

Use Python 3.12 and the exact dependencies in `requirements.txt`:

```sh
python -m pip install -r source/requirements.txt
python source/build_systems_revision.py --only all
```

Run those commands from the revision directory. The packaged original input
is `source/inputs/c130-hercules-unified-r0001.glb`, SHA-256
`ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12`.
The generator verifies that hash. It can also locate the unchanged input in
the full repository. The r0002 transport is retained as exact delivered bytes;
this script rebuilds only the two revised gunships and three independent systems.

| Source | Responsibility |
|---|---|
| `build_systems_revision.py` | Revision entry point and standalone source copies |
| `build_family.py` | Inherited aircraft decomposition, assembly and clip/sidecar output |
| `gun_components.py` | Original gun geometry, materials and visual cycles |
| `eoir_component.py` | Representative EO/IR gimbal, optics and yaw/pitch clips |
| `gltf_core.py` | Mesh operations, transforms, exact indexing and GLB writing |
| `variants.json` | Named visual configuration assumptions |
| `component_source.py` | Aircraft-independent component rebuild |
| `blender_systems_review.py` | Native import, action evaluation, save/reopen and renders |
| `package_revision.py` | Verify frozen evidence and create the manifest |
| `create_transfer.py` | Compress exact files into a checksum-verified archive |
| `restore_delivery.py` | Restore exact reviewed bytes; no model generation |

Each component carries the minimal independent Python source and its own
requirements. Run `python source/component_source.py` inside that component
directory to rebuild it without an aircraft asset or network access. The
source-isolation audit compares geometry, materials, hierarchy and animation
payloads; export metadata can differ without changing those payloads.

## Verification

The viewer directory contains the pinned Three.js runtime and actual-model
tests. The QA directory contains the Khronos validator wrapper and dependency
pin, plus the independent geometry audit. `qa/QA_SCOPE.md` defines the checks.
Blender 4.5.15 LTS produced the native evidence.

The current GLBs, articulation JSON and portable HTML form a frozen review set.
Rebuilding changes evidence identity; regenerate affected reports and portable
artifacts before publishing a new revision. Preserve each review snapshot.

Browser rendering and native Unreal import/cook/runtime were not run.
Photorealistic finish, exact reference fit and continuous combined-motion
clearance are not accepted.
