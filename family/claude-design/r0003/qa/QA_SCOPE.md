# r0003 QA scope and limits

claude-design / cg46 · recorded 2026-10-29T05:51:50.304530+00:00.

## Inputs and freshness

The authoritative input list is the six frozen SHA-256 values in [QA_SUMMARY.md](QA_SUMMARY.md). Every machine report identifies the actual model hashes it inspected. A reused filename, an earlier preview, or a prior revision's PASS does not validate new bytes. The all-six portable and three independent inspectors embed the final geometry and final revision/reference notes; exact HTML/model hashes are in [the portable receipt](../viewer/final-portable-receipt.json).

## What the current passes establish

- **Format and exported geometry:** five new GLBs pass Khronos validation with zero errors/warnings. The separate system geometry audit checks its declared geometry, resources, revised control bindings, motion samples and independent source rebuilds. These checks do not establish photographic shape accuracy.
- **Controller execution:** the actual Three.js loader and exported tracks exercise **113 controls** over six assets, concurrent compatible mechanisms, ownership, pauses, interrupted reversal and canonical reset. Every asset returns with **zero matrix drift**. Test image decoding is stubbed; material appearance and WebGL rendering are not tested here.
- **Firing and cases:** actual empty-case meshes move and are hidden at reset. An inboard-plane check samples transformed case vertices over **3 × 3 aim poses and 65 cycle phases**. It proves only that these sampled visible vertices stay on the inboard side of the mount datum.
- **Named obstruction pairs:** at **rest aim and 129 cycle phases**, transformed case vertices and named base/support/exit-cover vertices form disjoint bounding boxes. This proves no intersections between those named objects at those sampled times. Earlier overlapping boxes were followed by convex-mesh face-plane containment, which confirmed a case/base penetration; the repaired candidate has zero sampled box overlaps. Collection-bag contact, every other cabin object, other aim combinations and continuous between-sample clearance are not certified.
- **Portable files:** the embedded import graph parses and is closed; browser-standard gzip decoding reconstructs exact model bytes; sidecar/model/HTML hashes and final notes match. The component-only files embed no aircraft. This verifies data/dependency closure, not a browser session.

## Native and visual gates

**Native Blender final refresh is PASS for its exact-hash scope.** Eight completed current-source reports cover five assets, sixteen firing/sensor clips with eight native samples each, five saved/reopened native scenes, and ten current-mesh renders. Two separately labelled images compare the preserved r0002 model from identical cameras. The three firing/case render poses use verified actual Three.js world-matrix snapshots. Component native delivery copies are byte-identical to the scenes that were reopened. See [the native index](system-review-summary.json) for all model, native-file, report and render hashes. These are bounded native checks, not a full collision or photographic acceptance.

**Browser rendering and native Unreal import/cook/runtime are NOT_RUN.** Native Blender, even after a completed refresh, cannot substitute for either gate.

No current report grants exact photographic or photorealistic acceptance. Reference-guided geometry, differentiated materials and soft flash cards improve presentation without establishing such acceptance. Gun/breech/crew/case timing and travel remain illustrative, with no targeting, ballistics or operating certification. Continuous collision clearance, gameplay/damage, performance and inherited source licensing remain open.

This summary was written from existing reports; no new test campaign was performed for this documentation update.

## Input refresh

Lower 30 mm bracket trim: the W/J/30 mm reports and snapshots were refreshed against their new hashes. Unchanged transport, 105 mm and EO/IR evidence was retained only after model/sidecar hash identity checks. No additional test scope was introduced. Refreshed 2026-10-29T05:55:10.740435+00:00.
