# r0003 QA summary

claude-design / cg46 · recorded 2026-10-29T05:51:50.304530+00:00.

**DRAFT_SYSTEMS_VISUAL_REVIEW.** Current reports support the bounded checks below. They do not establish exact photographic fit, photorealism, real weapon operation, continuous clearance, or Unreal acceptance. Original r0001/r0002 are preserved; the transport below is unchanged r0002 geometry.

## Frozen model inputs

| Export | Controls / clips | SHA-256 |
|---|---:|---|
| C-130H (unchanged r0002) | 27 | `7bfc25e94d4b99900db6f25fa731bc867111dd5debb3a763aa7b619ee86b4146` |
| AC-130W candidate | 38 | `d9664ac13bea159f02519e44db028ce1fcba21094135c6ef5382b8033677ef74` |
| AC-130J candidate | 38 | `e7075a4097d1842de0b0353cb27e5e294ee3506ee5d0ecdb47e8eeea22e94e93` |
| Independent 30 mm | 4 | `2850c4d215d90f96839d724733a44d9b1a237360385a2672c76ea1830709e053` |
| Independent 105 mm | 4 | `597e8897d855229c0e98ebcaf652518fc050ff7b5221e90201251ff38cd2d026` |
| Independent EO/IR | 2 | `6ceb0589b84eb83a6bbde926e709ab46f62f7e3b794ea7c4ed29c4ae92e5843f` |

## Current evidence

| Gate | Result and scope | Evidence |
|---|---|---|
| Khronos glTF validation | **PASS:** five new r0003 GLBs, zero errors and zero warnings. Informational messages remain. The unchanged transport was not rerun in this format-validation pass. | [Format summary](gltf-validator-summary.json) |
| Exported geometry / independent sources | **PASS:** mesh/index/normal and embedded image/link checks, revised system bindings and 13 actual motion samples per revised clip; focused exit ray grids; independent source rebuilds. See the report's exact scope. | [System geometry report](system_geometry_report.json) |
| Actual Three.js scenes and controllers | **PASS:** all six assets, **113 controls**, no unresolved bindings, finite combined transforms, master/inspection ownership, Pause and interrupted Reverse. **Maximum Reset matrix error: 0** for each asset. Image decoding is stubbed; this is CPU scene/animation validation. | [Runtime report](../viewer/model-runtime-qa.json) |
| Physical spent cases | **PASS:** actual separate case meshes move; reset hides them. Visible vertices stay inboard of the mount plane over **3 yaw × 3 pitch × 65 firing phases**. Hidden epsilon-scale phases are omitted. This does not test all cabin contacts. | [Firing / case report](../viewer/firing-model-qa.json) |
| Repaired case-route obstruction | **PASS:** at rest aim, **129 firing phases**, no sampled AABB overlaps between the visible cases and the named base/support/exit-cover meshes. The repaired 105 mm path has minimum sampled gaps **0.073851 m to its base** and **0.122016 m to its cover**. These are game-mesh measurements. Other geometry, aim combinations and continuous travel are outside this probe. | [Obstruction report](../viewer/case-obstruction-qa.json) |
| Portable delivery | **PASS:** one portable with **six assets**, plus **three component-only inspectors**. All imports are embedded; gzip restores exact GLBs; GLB/sidecar and HTML hashes agree. Final revision/reference notes are embedded exactly. | [Portable receipt](../viewer/final-portable-receipt.json), [main portable QA](../viewer/portable-qa.json) |
| Native Blender refresh | **PASS, scoped:** five current assets import, save and reopen with named actions/NLA and packed images retained. **16** firing/sensor clips pass eight native samples each. **10 current-mesh images plus 2 labelled r0002 comparisons** use 1000 × 740, 24-sample Cycles CPU renders. Three controller-snapshot views pass exact source-hash and world-matrix checks. This does not grant photographic, full-clearance, browser or Unreal acceptance. | [Native index](system-review-summary.json), [review usage](system-review-usage.md) |
| Browser / WebGL rendering | **NOT_RUN.** No browser was used. | Explicit gate |
| Native Unreal import / cook / runtime | **NOT_RUN.** No connected Unreal project validation. | [Unreal handoff](../UNREAL_HANDOFF.md) |

## Acceptance still open

Exact aircraft/subvariant fit, gun/sensor installations, inherited airframe and door-panel contour, detailed muzzle/breech/crew behavior, photorealistic finish, full combined-motion clearance, gameplay/damage, LOD and runtime performance remain unaccepted. The inherited source airframe's licensing provenance remains unresolved. The new systems are original authored visual approximations; no Sketchfab mesh was incorporated.

The incident ledger preserves the corrected bag winding, ring occlusion, solid-looking flash, and sampled 105 mm case/base obstruction. Passing a loader or sampled probe does not close those broader acceptance gates. See [QA scope](QA_SCOPE.md) and [incident ledger](INCIDENT_LEDGER.json).

## Input refresh

Lower 30 mm bracket trim: the W/J/30 mm reports and snapshots were refreshed against their new hashes. Unchanged transport, 105 mm and EO/IR evidence was retained only after model/sidecar hash identity checks. No additional test scope was introduced. Refreshed 2026-10-29T05:55:10.740435+00:00.
