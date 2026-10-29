# C-130 modular family — r0002

Author: **claude-design**. Continuation of the preserved `family/r0001` assets in `g1mmel/jcom-bigplanes`.

This revision provides three assembled aircraft from one reproducible family source, real embedded mechanism animations, editable Blender files, and an interactive review viewer. Its acceptance state is **DRAFT_ARTICULATED_REVIEW**. Read [REVISION.md](REVISION.md) and [manifest.json](manifest.json) for the exact completed checks and outstanding gates. Generated articulation sidecars retain their build-time pending labels; the manifest and matching QA reports record the completed revision checks.

## Open the models

- **[Portable C-130 family viewer](viewer/C130-family-portable.html)**: download the HTML and open it in a current desktop browser with WebGL2 and gzip `DecompressionStream` support. It embeds all three aircraft and the viewer runtime. Choose an aircraft, then **Actuate everything**. Pause, Reverse and Reset remain available throughout the demonstration.
- **[C-130H legacy transport GLB](models/c130.glb)** and [editable Blender file](editable/c130-r0002.blend).
- **[AC-130W Stinger II GLB](models/ac130.glb)** and [editable Blender file](editable/ac130-r0002.blend).
- **[AC-130J Ghostrider candidate GLB](models/ac130j.glb)** and [editable Blender file](editable/ac130j-r0002.blend).
- [Rendered model evidence](previews/) and [independent/native QA](qa/).

For the folder viewer, run `python -m http.server 8000` from this directory, then open `http://localhost:8000/viewer/`. The single HTML works without a server. A browser/WebGL visual smoke test is a separate gate; see the QA scope before interpreting programmatic Three.js tests as browser acceptance.

## How the family is organized

The shared authoring source retains the original fuselage, wings, empennage, cabin, source doors, wheels and usable propeller geometry. It extracts real control surfaces, bakes the coordinate correction, and uses explicit hinges and parent pivots. Configuration modules select transport infills or gunship apertures/equipment, legacy or J powerplants, and legacy or J cockpit inserts. The gunship port aft installation replaces the corresponding personnel-door module.

The three GLBs are complete standalone deliveries of those configurations. The current viewer selects complete assembled exports. It does not advertise arbitrary live interchange of unvalidated modules or a universal single-mesh aircraft. The component registry describes the supported reuse and configuration boundaries.

The final exports use exact indexing of complete vertex attribute records. This reduced their articulated export sizes by 42–44% while retaining every expanded triangle attribute, animation value, material, embedded image and hierarchy entry. [The independent equivalence report](qa/exact_indexing_equivalence.json) records the before/after hashes and checks. No performance gain is assumed from file size alone.

## Continue editing

Use the `.blend` files for native geometry/material/animation editing. They contain the actual imported GLB hierarchy, named NLA clips and packed maps; no linked external textures are required. Individual clips are intentionally separate. Enable the relevant NLA track for inspection, or use the portable viewer to exercise coordinated controls. Playing every Blender NLA track at once would bypass the controller's ownership and sequencing rules.

Use [source/build_family.py](source/build_family.py) and [source/gltf_core.py](source/gltf_core.py) for reproducible family authoring. The builder accepts only the preserved source GLB with SHA-256 `ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12`.

From the repository root:

```sh
python -m pip install -r family/claude-design/r0002/source/requirements.txt
python family/claude-design/r0002/source/build_family.py
```

If using a standalone revision download, supply the preserved source explicitly with `--input /path/to/c130-hercules-unified-r0001.glb`. Obtain that file from the pinned original commit shown in [RECOVERED_R0001.md](RECOVERED_R0001.md); do not substitute another similarly named model.

Read [UNREAL_HANDOFF.md](UNREAL_HANDOFF.md) before attempting an Unreal import. The package is not a tested `.uasset` or cooked Unreal product.

## Preservation and provenance

All original `r0001` files remain unchanged. Aircraft deliverables are added under `family/claude-design/r0002/`. A branch-scoped preservation workflow is the one supporting infrastructure addition; it restores checked bytes without rebuilding or rendering the aircraft. The inherited model license requires provenance review; this work does not grant new rights to the original geometry. Reference photographs are linked in the evidence ledger and are not redistributed as asset textures. The source branch's exclusion from Crowd migration is retained.
