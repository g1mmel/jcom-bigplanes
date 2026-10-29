# Final cargo-ramp corner repair — claude-design / r0004

## Exact candidate and source

- Source: `source/ramp_repair.py`, SHA-256 `c00cd110ac5921a41b4280d9c61a4de2a3252547d9417bf4b3d7098f923427a6`.
- Tested derivative: `qa/ramp-corner-candidate.glb`, SHA-256 `18fa65edd7351baecc49a19db9d60324f20fa8786ec403b6429ed1f87273b0fe`, 21,465,392 bytes.
- Original frozen master: `de910de58de643328055f27246f2d8d7b86047cea6f35e4e46406144b71644fc`.

`repair_ramp_glb` now invokes `repair_ramp_corners_glb` after the initial lateral-skirt and receiving-pocket fit. The derivative exercises that final pass on the frozen master. Root delivery must repeat the geometry/runtime/native checks on the rebuilt master under its own final hash.

## Finding and local repair

The original corner scan found a 50.6 mm port and 48.6 mm starboard aperture-to-closure distance near Z6.336 m. The outer lower lip at absolute X1.49 m was 42.6 mm from the upper leaf. The earlier long lateral-seam measurement ended at Z6.2 m and did not certify this join.

The final pass subdivides only the aft portion of the existing lower mesh at the actual closing-contour bends, then fits its outer underside edge to the upper-leaf leading profile. Short tapered extensions finish the forward tips of the two existing fixed jambs. The hidden raised rim is beveled forward by up to 65 mm to clear those tips during the initial opening motion. The central lower geometry at absolute X≤1.04 m is unchanged, and the separate preserved cargo-deck mesh is byte-identical. No pivots, node transforms, hierarchy, clips or controls change.

The outer closing lip sampled from absolute X1.2–1.64 m now has a **3.79–4.47 mm** separation from the upper leaf or fixed jamb. The centerline remains at **4.51 mm**. These are authored game-asset reveals, not real-aircraft manufacturing tolerances.

The broader 201-station scan per side spans Z6.2454–6.40 m, including the preceding side-skirt transition. Its remaining maximum is **19.51 mm port / 22.36 mm starboard**. That broader maximum must not be reported as the new lip reveal, nor may the result be described as every seam below 5 mm. The native closeups show the previous black triangular opening filled by the fitted closing perimeter and aperture frame.

## Exact-hash evidence

`ramp-corner-fit-candidate.json` confirms unchanged cargo-deck attributes/indices, all 44 animation clips and their sampler data, node hierarchy and rest transforms. It records the independent aft-corner and lip measurements before and after the repair.

`ramp-corner-motion-candidate.json` evaluates the actual exported cargo sequence at nine normalized poses:

| Pair | Strict crossing pairs across samples | Outside declared hinge zone above numeric tolerance |
|---|---:|---:|
| Lower / skin and fixed jambs | 0 | 0 |
| Lower / cabin | 0 | 0 |
| Lower / upper | 0 | 0 |
| Upper / cabin | 0 | 0 |
| Upper / skin and fixed jambs | 846 | 0 |

All 846 upper contacts are inside the declared 50 mm hinge-contact zone. They are disclosed, not certified as intentional. Reset world-matrix error is zero. The test is a sampled strict triangle-crossing test; it does not prove continuous clearance, penetration depth, complete containment or coplanar overlap.

`ramp-corner-native.json` records Blender 4.5.15 LTS renders of the actual derivative with the unchanged original PARKED world transforms. Its model hash matches the fit and motion reports, and both PNG hashes were verified after visual inspection:

- `previews/ramp-corner-candidate-side.png`
- `previews/ramp-corner-candidate-belly.png`

Whole-aircraft photographic identity, surface finish and native Unreal acceptance remain outside this scoped repair.
