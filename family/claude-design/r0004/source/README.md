# r0004 authoring source and reproduction

Author: **claude-design**. The active entry point builds one configurable family
from the existing source airframe and inherited authored systems. Geometry,
motion and effects are reference-guided game visual approximations, not
construction or operating data.

## Build the family

Use Python 3.12 with the pinned dependencies in `requirements.txt` (NumPy 2.3.5,
SciPy 1.17.0 and Pillow 12.3.0). Run from the r0004 directory:

```sh
python -m pip install -r source/requirements.txt
python source/build_loadout_family.py
```

The required original input files are included in `source/inputs/`:

| Input | Identity |
|---|---|
| `r0003-ac130j.glb` | SHA-256 `e7075a4097d1842de0b0353cb27e5e294ee3506ee5d0ecdb47e8eeea22e94e93` |
| `r0003-ac130j-articulation.json` | Parent articulation corresponding to that GLB |
| `c130-hercules-unified-r0001.glb` | SHA-256 `ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12` |

Keep these immutable inputs with the source. The original r0001 asset supplies
preserved transport geometry; the r0003 parent supplies the shared airframe and
previously authored gun/sensor systems. The r0004 builder adds module boundaries,
new equipment and the source-aperture ramp repair. It writes the family GLB,
articulation, loadout catalogue, new component exports and build receipts.

| Source | Responsibility |
|---|---|
| `build_loadout_family.py` | Current r0004 family build entry point |
| `family_glb.py` | Import existing GLB data, replace/reparent modules, prune and export independent subsets |
| `loadout_components.py` | New hose/drogue, Fulton and JATO visual systems and their motion |
| `ramp_repair.py` | Fit the inherited ramp to its aperture and write the measured repair receipt |
| `build_family.py`, `gltf_core.py` | Inherited geometry, assembly, animation and binary export utilities |
| `gun_components.py`, `eoir_component.py` | Inherited reusable visual systems |
| `blender_loadout_review.py` | Current native master import, clip checks, exact viewer-pose review, packed save/reopen and renders |
| `blender_systems_review.py` | Shared native review helpers |
| `package_components_r4.py` | Isolated source rebuild, native review and packaging of the four new independent components |
| `package_revision.py` | r0004 frozen-evidence validation and final file inventory |
| `create_transfer.py` | r0004 exact-byte transport archive/chunk creation |
| `restore_delivery.py` | Restore/verify the reviewed transport bytes without regenerating models |

`build_systems_revision.py`, `component_source.py`, `variants.json` and other
inherited helpers retain their historical purpose. They are not the r0004
aircraft build entry point. Original reusable component source remains inside
each component folder. The obsolete r0003 build-all receipt is not current
evidence for this revision.

## Rebuild runtime evidence and inspectors

The viewer vendors Three.js 0.170.0 and its loader dependencies. The actual-model
tests use Node.js; the recorded validator environment uses Node 24.22.1. From
`viewer/`:

```sh
node --loader ./node-module-loader.mjs test-loadouts.mjs
node test-controller.mjs
node --loader ./node-module-loader.mjs export-poses.mjs c130-family
python build-component-inspectors.py
python build-portable.py
node --experimental-vm-modules verify-portable.mjs
```

The family portable build embeds `REVISION.md`; finalize that document before
freezing the portable HTML hash. Independent inspectors embed their own component
GLBs and do not load the aircraft. Rebuild them after any relevant component,
articulation or runtime change. Their manifests record exact restored hashes and
isolated CPU verification.

The Khronos wrapper and pinned package metadata are in `qa/validate_gltf.mjs` and
`qa/package.json`. Regenerate its reports for the current exported master and all seven
component files. `qa/ramp-motion-audit.py` records the explicitly tested ramp
pairs; preserve its input hash and scope when interpreting the result.

`python qa/check-family-source.py`, run from r0004, rebuilds the complete family
in a shallow clean temporary directory using only the delivered source and its
two declared original GLB inputs. It guards network access and prebuilt model
reads, compares the rebuilt master and four new component GLBs byte-for-byte,
and records input/source identity in `qa/family-source-isolation.json`. Check the
receipt's current status and hash before treating the source reproduction as
accepted.

## Native review

Blender 4.5.15 LTS is the native review environment. Export viewer poses before
running the current native review. From r0004, with `blender` available:

```sh
blender --background --python source/blender_loadout_review.py -- --root "$PWD"
```

The script checks that pose snapshots bind the same GLB, catalogue, articulation,
controller and pose driver before applying matrices, effective visibility and
morph influences. It evaluates imported clips, saves/reopens the packed native
scene and renders selected configurations. The snapshots include deployed
tanker and Fulton states, JATO at the authored 25% cycle state, gun visual cycles
and service access. This is Blender evidence; it does not imply browser or
native Unreal acceptance.

Each component's README describes its independent rebuild and native source
package. The four new component packages are produced by
`package_components_r4.py --master-sha256 <frozen-master-sha256> --blender <blender-path>`.
The master hash guards the assembly's delivery identity; the component rebuilds
themselves use their local source without loading the aircraft. Use
`--package-only` only after inspector-only changes, when the existing source and
native evidence still match the component inputs. The r0003 gun/sensor folders are preserved exactly, including their
original manifests. `components/REUSED_R0003_PROVENANCE.json` records the reuse
without changing those original component identities.

## Freeze, package and recover

After all affected reports, native scenes, docs and portable files match the
current inputs, run the r0004 `package_revision.py` entry point. It validates
frozen evidence before creating the revision manifest and checksum list. Use
`create_transfer.py --output <directory>` to create the exact-byte transport
package. Follow the generated transfer instructions with `restore_delivery.py`
to verify or restore it; restoring a delivery does not invoke the model builder.

Rebuilding changes the evidence identity. Do not retain a PASS receipt from an
older model merely because the filename is unchanged. Preserve previous
revisions, regenerate affected reports and portable files, then create a new
manifest. Exclude Python caches, Blender backup files and temporary output from
the deliverable. Acceptance boundaries are in [QA_SUMMARY.md](../QA_SUMMARY.md)
and [UNREAL_HANDOFF.md](../UNREAL_HANDOFF.md).
