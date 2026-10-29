# Independent QA: C-130 family r0002

The current models pass the recorded format, actual clip-motion and viewer-runtime gates. They are **working draft assets**, with explicit limits on geometry acceptance and engine validation. The final native Blender and scoped closure reviews also pass on these exact indexed bytes. No production acceptance is claimed.

## Exact current assets

| Asset | Bytes | Triangles | Embedded clips |
|---|---:|---:|---:|
| [C-130H legacy candidate](../models/c130.glb) | 13,876,572 | 159,558 | 27 |
| [AC-130W Stinger II candidate](../models/ac130.glb) | 14,240,532 | 167,487 | 36 |
| [AC-130J Ghostrider candidate](../models/ac130j.glb) | 14,006,440 | 163,519 | 36 |

SHA-256 values were computed from the actual local GLB bytes:

- **C-130H legacy candidate:** `7bfc25e94d4b99900db6f25fa731bc867111dd5debb3a763aa7b619ee86b4146`
- **AC-130W Stinger II candidate:** `7b50ca7a5eb910f471fff2d4d411e25a55a0047405bbecc55458e25090f45046`
- **AC-130J Ghostrider candidate:** `b3ab255efe8de3668dd0c07b4e215b485ca316c8a09ed0863771b8376be90a62`

The files contain rigid-node animation and zero skins. A source master generates three complete, self-contained GLBs. The independent decoder found **86 byte-identical decoded named meshes shared across all three**. Variant-aware fuselage/cabin apertures, mission panels and markings remain different where required. Portable exports duplicate common data; the source registry describes the common master and interchangeable modules.

## Gates and evidence

| Gate | Result on these bytes | Evidence |
|---|---|---|
| Official Khronos glTF/GLB validation | **PASS:** zero errors and zero warnings in all three. Informational unused-data messages are 50 / 49 / 24. | [Summary](gltf-validator-summary.json), full `c130`, `ac130` and `ac130j` validator reports in this directory. |
| Independent decoded geometry and articulation | **PASS_SCOPED:** finite data, valid indices, uniform positive node scales, unique node names, valid tangent handedness, no zero normals or degenerate triangles; every control binds to real clip targets and moves decoded vertices. | [Independent articulation report](independent_articulation_report.json). |
| Rest, reverse and reset in independent sampler | **PASS_SCOPED:** nine timeline samples, midpoint/interruption and reverse checks; observed reverse/reset error is zero. | The same independent report; this sampler result is distinct from runtime UI execution. |
| Actual Three.js viewer/controller | **PASS:** 27 / 36 / 36 controls exercised; owned master/child tracks arbitrate correctly; pause, interrupted reverse and reset pass with zero reset matrix drift. | [Actual model runtime report](../viewer/model-runtime-qa.json). |
| Sampled cargo/gear surface crossings | **Scoped no-hit result** above the declared tolerance outside declared hinge regions. 20 named pairs and 187 pair-state samples per model, 561 total. | [Current surface report](sampled_surface_crossings.json), with the original executed report preserved and explicit indexing-equivalence provenance. |
| Exact representation optimization | **PASS_EXACT_EQUIVALENCE:** every expanded triangle-corner attribute bit and corner order matches; hierarchy/rest/extras, animations, images, materials and sidecar semantics match. | [Independent exact-indexing proof](exact_indexing_equivalence.json). |
| Final native Blender import/playback/render/reopen | **PASS:** Blender 4.5.15 LTS imports and evaluates all 27 / 36 / 36 clips, saves/reopens the native files, and supplies 13 rendered previews per model (39 total). | [C-130 native report](c130-blender.json), [W native report](ac130-blender.json), [J native report](ac130j-blender.json); all identify the hashes above. |
| Final native gear-closure review | **PASS_SCOPED:** inspected closed-gear and service-cargo views; thin draft seams remain explicitly accepted within this scope. | [Closure projections](gear_closure_projected_coverage.json) and [explicit native review receipt](gear_closure_native_review.json); a different hash cannot reuse an earlier visual pass. |
| Native Unreal import, cook and gameplay runtime | **NOT_RUN.** | No substitute engine test is implied by Blender or Three.js results. |
| Photographic acceptance | **NOT_ACCEPTED.** | [Reference notes](../references/REFERENCE_NOTES.md) and [claim-level ledger](../references/REFERENCE_LEDGER.json). |
| Source licensing | **REVIEW_REQUIRED.** | Source lineage is retained; authorship/license provenance has not been cleared for production. |

## What the geometry checks establish

The surface probe tests the actual exported triangles of cargo doors/ramp, surrounding cabin/skin, landing-gear wheels, covers, forward nose leaves and receiving wells. It samples 0, .125, .25, .375, .5, .625, .75, .875 and 1. The seven nose-gear pairs also sample .95 because an earlier authored closure sequence showed a concrete staging defect there. Every fitted child mesh under a checked closure pivot belongs to the checked assembly.

The current result retains one numerical nose seam per aircraft. It also retains **818 / 782 / 782** upper-cargo-door/fuselage triangle-pair contacts within the builder-declared 50 mm hinge attachment region. The interface is not silently erased from the report. The 20 micrometre triangle-plane straddle threshold distinguishes numerical contact; it is not a solid penetration-depth measurement.

A zero count outside those regions is not an all-path clearance certificate. Complete containment, coplanar overlaps, boundary-only contacts, intervals between samples and unenumerated part pairs remain outside this test. Full swept clearance is **NOT_PROVEN**.

The later indexing change removed duplicate complete vertex records and used valid smaller indices where possible. It saved **31,916,500 bytes** across the family while preserving all expanded corner attributes, triangle order and animation semantics exactly. Format and independent clip checks were rerun on the current indexed files. The expensive triangle observations were explicitly transferred through the independent equivalence proof; their original tested hashes and original report are retained. This is recorded as a transfer, not a new execution.

## Closure and native-view limits

Development checks caught an incomplete closed-gear endpoint even after its sampled crossing count had cleared. The earlier nose cover did not span its opening, and a main-well box protruded beyond the preserved outer skin. Those failures are retained in [the incident ledger](INCIDENT_LEDGER.json) and historical reports.

The corrected design retains the original outer main fairing, fits the wheel receiving volume, and uses the preserved original nose belly panel instead of the discarded added bridge. Closure projections now show small inner/perimeter seams rather than the previous large exposed wells. The final native review accepts those seams for the draft presentation only. The closure probe checks the exact model, native report and reviewed image hashes before retaining a scoped visual pass. All 39 PNG hashes match the final native reports; one damaged J service-hero PNG was repaired from the unchanged native/model state with explicit provenance in `preview-repair-receipt.json`. It cannot certify a watertight airframe, calibrated door linkage or photographic accuracy.

## Reference and configuration limits

The reference ledger records 55 sources, including 47 actually inspected images and 17 claim records. Official military/manufacturer sources and actual photographs support the selected legacy C-130H, late-service AC-130W and C-130J-derived Ghostrider configurations. The ledger separates direct observation, inference, authored assumptions and remaining gaps. Reference images were inspected locally and are not redistributed in this package.

Major variant changes include powerplant/nacelle/propeller, cockpit and mission modules in addition to panels. The J configuration is not established merely by fitting gunship panels to a legacy four-blade aircraft. Exact station dimensions, surface proportions, all sensor placements, camouflage/markings and full open/closed mechanism trajectories remain unaccepted. Flap motion and several guided linkages are authored visual approximations; no aerodynamic limits, operational timing, physics, weapon firing or targeting behavior is claimed.

The original r0001 assets remain the preserved baseline. This revision continues that work with source lineage and actual articulated meshes. It does not turn the original structural pass, these scoped checks, or the presence of previews into production certification.

Reproduction commands and precise tool limits are in [QA_SCOPE.md](QA_SCOPE.md).
