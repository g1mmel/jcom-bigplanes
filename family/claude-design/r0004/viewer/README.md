# C-130 family loadout viewer — r0004

Author: claude-design. The viewer loads **one `c130-family.glb`**. Configuration
changes select named panel and equipment modules inside that same scene; they do
not download or replace complete aircraft models.

## Open and use

Open `C130-family-portable.html` in a browser that supports WebGL2 and gzip
`DecompressionStream`. The file contains the exact master GLB, articulation,
loadout catalogue, revision notes, and pinned Three.js 0.170.0 dependencies.

For the folder version, run `python -m http.server 8000` from the revision
directory and open `http://localhost:8000/viewer/`.

Choose a configuration in **Loadouts**, then change any individual equipment
dropdown. Exact presets retain their reference or historical designation.
Unmatched combinations display **Custom JCNC**. Compatibility messages explain
which combinations depart from the documented configuration; they do not prevent
creative game configurations or certify real aircraft carriage.

Changing a loadout resets the outgoing mechanisms, recoil, cases and effects
before installing the new selection. All choices change together within one
synchronous update. The list of mechanism controls and the displayed mesh and
triangle counts follow the selected equipment. Inventory counts in the runtime
API include all stored alternatives and are separately named.

- **Actuate everything** demonstrates the active mechanisms with the existing
  staging and ownership rules. **Pause**, **Reverse**, and **Reset** remain global.
- **Reset** resets mechanism poses and keeps the selected equipment.
- **Return to default** restores the default equipment preset, parked pose,
  surface view, and hero camera.
- **Save loadout** downloads a small JSON configuration. **Load file** restores
  its choices. Unknown families, revisions, slots and option IDs are rejected
  before a live model is changed.
- **Inspect equipment** selects the close-up cameras supplied by the current
  articulation or loadout catalogue. Surface, wireframe, and X-ray modes remain
  available. The gun buttons appear only when the relevant gun is fitted.

Visual firing/deployment times are authored presentation. None of these controls
is a flight model, real weapon operation, manufacturing data or carriage approval.

## Runtime contract

`loadouts/catalog.json` is authoritative for the available choices. Each slot has
mutually exclusive options, each option lists its `module_roots` and
`control_ids`, and presets select one option in every slot. A control referenced
by at least one option is optional; it is exposed only if the current selection
includes it. Unreferenced controls are common to the family. A root shared by
multiple selected options is shown exactly once.

`loadouts.mjs` validates the catalogue against actual model nodes and controls,
applies selections, evaluates declared compatibility conditions, matches exact
presets, and serializes configurations. `app.mjs` builds the interface directly
from that catalogue. `PoseDriver` evaluates the actual glTF clips.

### Default configuration in generic glTF importers

glTF has no standard node-visibility property. The exported master represents
inactive **module roots** at zero scale, so an ordinary importer displays the
default configuration without all mutually exclusive alternatives overlapping.
Those roots carry `loadout_module_root: true` and `canonical_scale: [1,1,1]`.
Zero scale here encodes the default equipment selection; it is not mechanical
stowage or part motion.

Before the pose driver records rest transforms, `normalizeModuleScales` restores
each catalogue module root to its canonical scale. Runtime loadout selection
then uses `node.visible`; animations retain their authored transforms. A target
engine must make the same distinction and implement its own configuration
consumer. Simply importing all zero-scale alternatives does not provide a
native Unreal loadout system.

## Rebuild and scoped verification

```sh
node --loader ./node-module-loader.mjs test-loadouts.mjs
node test-controller.mjs
python build-portable.py
node --experimental-vm-modules verify-portable.mjs
```

The actual-model test opens the master with Three.js, resolves every module and
clip, switches every option and preset in the same scene, checks active-control
selection and geometry identity, evaluates actual animation tracks, exercises
pause/reverse/reset, checks configuration round trips and invalid-input atomicity,
and verifies removal of outgoing firing state. Reports record the input hashes.
The generic controller test separately checks staged access and gear behavior.

`verify-portable.mjs` parses every embedded module, verifies dependency closure,
restores the exact compressed master bytes and compares the embedded catalogue
with the delivered file. `export-poses.mjs` can produce controller world-matrix
samples and `effective_visible` flags for a separate native renderer.

These are CPU scene/animation and byte-integrity checks. The texture decoder is
stubbed in the CPU loader tests. **Browser/WebGL appearance, photographic fit,
geometric clearance and native Unreal behavior are not established by them.**
See the revision's current reports for tests actually executed on its final
hashes. Historical r0003 QA outputs are not reused as r0004 evidence.
