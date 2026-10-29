# Cargo ramp fit repair — claude-design / r0004

## Finding

The r0003 closed model had a broad open lateral seam. At 68 sampled longitudinal stations, the XY distance from the source fuselage aperture edge to the lower ramp outer contour was 96.7–171.7 mm, median 126.7 mm. This is an inherited geometry-fit defect, not evidence that the real ramp should hang below an open gap. The inspected [closed C-130H underbelly photograph](https://www.dvidshub.net/image/383774/red-flag-11-3) shows a continuous closed contour with visible panel boundaries. It does not provide calibrated manufacturing tolerances.

## Repair

`source/ramp_repair.py` supplies `repair_ramp(model)` and `repair_ramp_glb(doc, bytearray_buf)`.

- Fit the lower ramp's outer skirt to the actual aperture. Constrain the inherited corner flanges inside that boundary. The central cargo-deck mesh is preserved.
- Bring the aft underside closing lip toward the measured leading contour of the upper door. This local adjustment repairs the roughly 70 mm exterior mismatch while keeping the cargo floor.
- Keep the moving upper leaf and its width unchanged. Add two fixed conforming aperture jambs to close its progressively wider source side gap. The authored leaf-to-jamb reveal is 3 mm.
- Relieve only local inside-liner side-rib/hinge pockets that obstructed the repaired closing rim. The outer fuselage skin remains intact and the interior remains bounded by it.
- Preserve hinge pivots, source clip data, staging, opening and reset. Exact complete-record indexing reduces storage without changing triangle attributes.

All new local fit dimensions are authored game-asset clearances, not real aircraft drawings or tolerances.

## Scoped evidence

The lower seam measurement after repair is recorded in `ramp-fit.json`; the range includes the retained corner/step transition. This is a substantial fit correction, not a watertightness certificate.

Nine actual exported cargo-ramp clip samples passed the strict triangle crossing probe for lower-vs-skin, lower-vs-cabin, lower-vs-upper and upper-vs-cabin. Upper-vs-skin retains 818 aggregate crossings within the declared 50 mm hinge zone; there are zero substantive crossings outside it. These hinge-zone contacts are reported, not certified as intentional. Reset world-matrix drift was 0.

`ramp-motion-audit.json` identifies the tested intermediate GLB. `ramp-exact-index-equivalence.json` proves that the final indexed GLB preserves every nondegenerate expanded triangle attribute and triangle order, and unchanged animation metadata; 58 float32-collapsed fragments are removed. `ramp-native-review.json` links the native imported-clip render states to the same geometry. The integrated family master must be tested under its own final hash.

## Remaining limits

Original whole-airframe silhouette, cabin layout and rendering finish remain draft. The probe does not establish continuous clearance, penetration depth, coplanar overlap, complete containment or all combinations with unrelated mechanisms. Native Unreal acceptance is not claimed. The source's upper hinge contacts remain declared. The final closure is better fitted; it is not accepted as an exact aircraft seal or production rig.

## Final aft-corner follow-up

The subsequent exact-master closeup identified a residual triangular opening beyond the lateral metric's Z6.2 m endpoint. That local join has now been repaired and tested separately. See `ramp-corner-REVIEW.md`, `ramp-corner-fit-candidate.json`, `ramp-corner-motion-candidate.json` and `ramp-corner-native.json` for its exact candidate hash, unchanged rig/deck evidence, independent corner measurements and native closeups. The earlier intermediate reports above remain historical evidence for the initial lateral repair.
