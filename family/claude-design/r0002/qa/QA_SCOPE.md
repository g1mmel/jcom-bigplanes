# Independent QA scope

The generated candidate must be assessed by the exact hash in each current report. First-export failures are preserved in `history/`; they do not describe later corrected bytes automatically.

## Reproduce the current checks

From this revision's directory:

```sh
npm ci --prefix qa --ignore-scripts --no-audit --no-fund
node qa/validate_gltf.mjs .
python qa/validate_articulation.py --root .
python qa/probe_surface_crossings.py --root . --models c130 ac130 ac130j
python qa/probe_gear_closure.py --root . --models c130 ac130 ac130j
```

The first command uses the pinned official Khronos validator dependency and lockfile. Python requires NumPy. No validator result requires publishing the model or uploading it to a web service.

The final writer also replaced duplicate complete vertex records with exact indices. `exact_indexing_equivalence.json` independently compares every expanded triangle-corner attribute byte and its order, hierarchy/rest/extras, animation channels and values, embedded images, materials and control semantics. All comparisons match. It records the old and current model hashes. The completed triangle observations are explicitly carried through that proof in `sampled_surface_crossings.json`; the original executed report remains at `history/pre_indexing.sampled_surface_crossings.json`. This avoids presenting a carried observation as a new execution. Running the ordinary surface-probe command above recomputes the same scoped observations directly from the current representation.

Full temporary pre-index binaries are retained outside the delivered revision. If they are available, the optional equivalence proof can be reproduced with `python qa/verify_exact_indexing.py --root . --baseline /path/to/retained-baseline`. The compact proof, historical observations and fingerprints remain in the deliverable.

The closure probe remains pending until an explicit native visual-review receipt exists at `qa/gear_closure_native_review.json`. It verifies that receipt against the actual model, native report and reviewed PNG bytes. Only an unchanged, explicitly reviewed draft endpoint can retain `PASS_SCOPED`. A projection fraction alone cannot promote the asset to visual acceptance, and altered bytes invalidate an earlier receipt.

## What the reports mean

| Report | What actually runs | What it cannot establish |
|---|---|---|
| `gltf-validator-summary.json` and each `*.gltf-validator.json` | Official Khronos glTF 2.0 schema, GLB container, references, accessor/binary data, animation data and embedded resource validation. Full message output, exact model hashes and tool version are recorded. | Photo resemblance, licensing, mechanical path clearance, or engine acceptance. Informational unused data is separated from errors/warnings. |
| `independent_articulation_report.json` | An independent Python decoder, without builder or viewer imports, reads the actual exported vertices. Checks unique node names, finite/accessor/index data, node scales, tangent handedness, clip/control binding, normalized timeline/quaternions and model-sidecar hashes. Samples 0,.125,.25,.375,.5,.625,.75,.875,1; evaluates reverse/interruption/reset; compares canonical rest and primary combined poses; records shared decoded mesh signatures. | Native execution or complete collision tests. Its deterministic reset check belongs to this sampler; actual viewer pause/reverse/reset is separately tested by the viewer agent. |
| `sampled_surface_crossings.json` | Actual posed triangle pairs for named cargo and landing-gear components use BVH broadphase followed by strict edge/triangle intersection. All crossings are retained. A declared 50 mm hinge-axis contact region is counted separately. A 20 micrometre triangle-plane straddle threshold separately identifies numerical seam contacts below export precision. | Continuous swept volume, solid penetration depth, complete containment, coplanar overlap, boundary-only contacts, or mechanisms/kit geometry outside the enumerated pairs. A zero count is a scoped no-hit observation, not a clearance certificate. |
| `gear_closure_projected_coverage.json` | The actual FLYING pose is sampled from exported clips with ownership respected. Projected rays compare moving covers, fixed fuselage and dark well surfaces over explicitly stated aperture/side rectangles, retaining first-hit well exposure separately from simple footprint coverage. | Exact real-aircraft apertures, flush fit, watertight topology or all-angle visual acceptance. The surveyed rectangles belong to the draft model. Native oblique belly and side views decide whether the closed endpoint is visually adequate. |
| `exact_indexing_equivalence.json` | Before/after GLBs are independently expanded into complete triangle-corner records; every attribute bit and corner order matches. Hierarchy/rest, animation data, materials, images and sidecar control semantics also match. | It validates a representation change. It does not add a new native-engine, photographic or continuous-clearance test. |
| Viewer and native reports, if supplied elsewhere in this package | Their own runtime and exact hashes define the gate. | A report in one runtime does not substitute for another. |

## Contacts and acceptance

Closure perimeter seams, ramp hinge contact and gear attachment interfaces can be intentional. The triangle probe does not automatically pardon a collision merely because it is near such a feature. It records the location, state and number of crossed triangle pairs for review. Native views and specific geometry investigation must distinguish a sealing seam from penetration through a receiving wall.

The builder explicitly identifies the upper cargo-door attachment within 50 mm of its hinge axis as a designed contact interface preserving the original leaf attachment. The report retains these contacts. This is a declared modeling interface supported by native inspection when available, not an independently proved real-aircraft mechanism. Numerical seam diagnostics also retain their raw intersections; a tiny triangle-plane straddle is not a claim about solid penetration depth.

The final triangle report enumerates 20 part pairs per aircraft. Each uses the nine ordinary samples. The seven nose-gear pairs additionally sample 0.95 because an earlier closure sequence showed a concrete staging defect there. This totals 187 pair-state evaluations per aircraft, 561 across the family. Fitted patches and caps under a gear-cover or forward-hatch pivot are included with that closure; adding a child mesh cannot silently omit it from the existing pair. Other asset pairs remain outside this scope.

The first export exposed cargo-ramp side-edge interference with original cabin side ribs and late nose-cover interference with fuselage skin. The builder was given exact sample times, part identities and intersection coordinates. The current report must be regenerated after a repair; a source-code edit alone does not close an incident.

The fourth export then showed why surface crossing and closure are separate checks: its named sampled pairs had no crossings above the stated threshold outside hinge regions, but native FLYING renders still showed exposed gear wells. The nose covers did not span their opening, and the main well sides remained visible despite almost complete bottom projection coverage. That failure is retained in the incident ledger and historical projection report. A later correction must pass both actual triangle-motion checks and closed-endpoint native review.

The deliverable remains a draft candidate unless all separate acceptance gates are evidenced. Source license provenance, photographic acceptance, native Unreal import/cook/runtime, complete mechanism clearance and operational certification are not established by these checks. Animation timings and limits are authored game values. No physics, damage, weapon firing or targeting simulation is implied by a working rigid-node animation.
