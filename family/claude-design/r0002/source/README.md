# claude-design — C-130 modular source r0002

This is a continuation of the preserved r0001 C-130 family, not a substitute aircraft. The authoring master is shared; the three portable GLBs are separate, self-contained exports so they can be opened without a bespoke asset server.

## Immutable input and reproducible build

Input: `family/r0001/c130-hercules-unified-r0001.glb` from commit `65f83c26c0d03773fc1bc885728d7188a722960f` in `g1mmel/jcom-bigplanes`.

Required input SHA-256:

```
ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12
```

The input is opened read-only and the builder refuses a different hash. No r0001 file is overwritten. The original source's 24 mesh definitions, two embedded JPEG normal maps, UVs, vertex colours and source-part names remain recoverable. Extracted surface/panel boundaries interpolate those attributes. The imported source's redistribution licence remains an unresolved provenance gate.

From the repository root, with Python, NumPy and SciPy available:

```bash
python3 family/claude-design/r0002/source/build_family.py
```

For a separately recovered identical input, pass `--input /absolute/path/to/c130-hercules-unified-r0001.glb`. `--only c130`, `--only ac130`, or `--only ac130j` is for a scoped working export; use the full command to generate the complete component-reuse registry and all delivery files.

The default writer performs exact complete-record indexing within each primitive. It compares every exported float32 attribute byte, including normals, tangents, UVs, colours and signed zero; it keeps distinct seams and the original expanded triangle order. It uses 16-bit indices only when the unique-record count permits valid glTF indices. No triangles are simplified, no materials or nodes are merged, and no animation samples or textures are changed by this representation step. `source/exact-indexing-receipts.json` records per-primitive payload counts; [the independent equivalence report](../qa/exact_indexing_equivalence.json) establishes what was actually preserved and records the compared hashes. The previous representations were retained separately for the audit and are excluded from this delivery revision; `--preserve-vertex-records` reproduces them from the immutable r0001 input in an isolated working copy. File-size savings are not an FPS or loading-time claim.

The output contract is `models/{c130,ac130,ac130j}.glb` plus explicit `articulation/{id}.json` mappings. `source/variants.json` selects the three configurations. `articulation/component-registry.json` records actual exported geometry bytes and canonical world-transform hashes, shared components, and mutually exclusive modules. `source/build-receipts.json` records output hashes and counts. Root-level revision and QA documents govern acceptance; source generation alone does not establish acceptance.

## Shared geometry and replaceable modules

The shared authoring master retains the original exterior and detailed, bounded cargo cabin. It extracts original skin into independently moving flaps, ailerons, elevators and rudder. Original propellers, gear, wheels, covers, cargo leaves and personnel doors receive actual local pivots. All clipping retains the source attributes; small internal seam caps are explicitly inferred new geometry.

The transport uses the solid forward port skin and original operating port aft personnel door. Gunships replace those structural modules with a forward visual gun installation and an aft visual gun installation. The aft port door is omitted on gunships, so an actuating door does not pass through the gun. The starboard door remains operable. Gun apertures remove both outer skin and interior wall blockers and lead into bounded receiving recesses; they are not cylinders pasted over an intact fuselage.

`ac130` explicitly means the AC-130W Stinger II, circa 2021, based on the documented C-130H conversion. Its two guns and two EO/IR systems are visual assemblies. `ac130j` adds distinct J-style nacelle/lower-intake geometry, six swept propeller blades, and a digital cockpit/HUD insert. These are visible structural/powerplant/cockpit differences as well as mission equipment. Newly authored station positions, boots, gimbals, nacelle contours and cockpit layout remain photo-guided approximations; the exports are not accepted replicas of exact serial aircraft.

The gun assemblies have visual mount and reversible recoil channels. They contain no ballistic, targeting, guidance, ammunition, pressure, fuze or operational firing model. Literal `level 1` tags identify independent propeller and mission-system roots. No asset-local health or damage thresholds replace JCNC's shared gameplay catalogue.

## Frames, rest and motion

The r0001 world frame was X lateral, Y longitudinal/nose −Y and Z up; its named left parts were on positive X. The proper rotation `new = (-oldX, oldZ, oldY)` therefore preserves handedness while producing **+X right, +Y up, nose −Z**. The inherited approximate nonuniform envelope is baked into vertices so the exported node rig has unit scales. A 5.874 mm ground alignment is baked into the recovered source. `asset.extras.unit_dimensions` records the inherited approximate 29.79 m length, 40.41 m span and 11.84 m height with its provenance. This makes rig math consistent; it does not turn the inherited approximate envelope into photographic dimensional acceptance.

All physical clips are normalized 0 = canonical rest and 1 = deployed/retracted endpoint. Finite channels use sampled smooth easing; continuous wheel/propeller clips have intermediate quaternion keys so a 360° turn cannot collapse to an identity interpolation. Metadata and glTF clips come from the same control definitions. Sidecars declare exact node names, local axes, units, roles, evidence, owners, conflicts and states.

PARKED has gear down, source main covers hanging open, access closed and propulsion stopped. SERVICE opens access while propulsion remains stopped. FLYING retracts gear and runs the propeller presentation. Gear masters open covers, move the wheels, then close the covers; standalone cover controls are blocked while their gear master owns the tracks. Nose gear folds forward and main tandems translate vertically. Travel distances and cover-linkage timing are artist authored, not operational specifications.

Cargo rest is reconstructed from the source's baked leaf transforms. The upper leaf opens inward before the lower ramp lowers; reversal raises the ramp before closing the upper leaf. The separate upper-door inspection channel is owned by that sequence while the ramp operates. Forward crew access unfolds downward with visible treads. Side personnel doors rise and tilt inward into the cabin overhead; that recovery path is an authored fit, not a certified linkage.

## Recorded corrections and limitations

The first actual exported geometry sweep found small cabin-rib intersections with the outer ramp side rails near the closing endpoint. The builder relieves only the measured paired internal pockets at absolute X 1.47–1.66 m, Y 1.85–2.37 m, Z 5.20–6.32 m. It keeps the rest of the cabin and exterior shell. A second localized closing-corner contact is addressed by trimming/capping only the outer ramp flanges past absolute X 1.89 m in the recorded Y/Z pocket. Forward nose hatch hinges are fitted to the actual extracted curved skin edge. The added forward well closes with those original skin leaves. The preserved aft nose-cover panel moves forward into the original source hole, then lifts into its closed endpoint; its linkage and small final tilt are authored visual fits. No invented bridge panel spans the parked wheels. Main-gear wells retain the original outer sponsons, remove only inner skin intersecting the actual wheel sweep, and use receivers fitted inside the curved source envelope and above the closed covers. Their 1.25 m presentation stroke fits this inherited source; it is not a real-aircraft travel specification. Native underside review and a separate endpoint-coverage probe are required, because absence of intersections alone cannot establish that a bay is closed. Current-byte QA must be rerun after any edit.

A first glTF conformance run identified empty leaf `children` arrays and fractional tangent handedness introduced by attribute clipping. Export omits empty leaf children, forces tangent W to ±1 and normalizes tangent XYZ. Attribute keys are sorted for deterministic output. Generated sensor spheres omit degenerate pole faces. Before writing indices, export checks the actual float32 local positions and removes only collapsed or negligible clipping slivers, recording a removal count in the affected mesh node's extras. These are concrete format/geometry corrections, not proof of native Unreal integration.

Rubber, rims, propeller blades and hub/tip areas have separate review materials while preserving all original triangles and UVs. The finish is neutral review shading, not a finished photorealistic paint/marking package. The `houseTint` patch is a separate material on conforming original skin.

Remaining gates include exact silhouette/station photographic acceptance, licensing clearance, complete continuous collision testing, native Unreal import/cook/runtime and authoritative damage/gameplay integration. Evidence of successful native Blender reopening or viewer controls, when present in adjacent QA reports, applies only to the hashes named in those reports.

## Reference principles used

- [AC-130W official fact sheet](https://www.hurlburt.af.mil/About-Us/Fact-Sheets/Fact-Sheets/Article/2559094/ac-130w-stinger-ii/): exact legacy gunship identity and C-130H lineage.
- [AC-130W forward/port photograph](https://www.dvidshub.net/image/4610565/16th-expeditionary-special-operations-squadron-provides-air-support): four-blade propellers, crew stairway and two visible sensor locations.
- [Crew doorway photograph](https://www.dvidshub.net/image/4610490/16th-expeditionary-special-operations-squadron-provides-air-support): lower-sill, downward entry stairway principle.
- [Gear maintenance photograph](https://www.dvidshub.net/image/229270/c-130-landing-gear-inspection): vertically retracting main-gear configuration and well/cover context.
- DVIDS image identifiers 7368321, 7918477 and 7135325: cargo opening and raised personnel-door principles; 6616476 and 7918484: J propulsion and digital cockpit visual distinctions. Exact viewed-image records belong in the revision reference ledger.

All photos remain evidence, not redistribution permission. This source package makes no Crowd migration claim and does not identify itself as the previous chat owner.
