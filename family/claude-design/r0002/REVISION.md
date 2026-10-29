# C-130 family r0002 — articulated review revision

**Status: DRAFT_ARTICULATED_REVIEW.** Author: claude-design. Source revision: `family/r0001` at commit `65f83c26c0d03773fc1bc885728d7188a722960f`.

This continuation preserves the existing work and adds functional rigid-part articulation and explicit family configurations. It does not promote the inherited aircraft to production acceptance. The final `manifest.json` and exact-hash QA reports identify what was actually tested.

## Aircraft configurations

| Export | Configuration | Distinguishing modules |
|---|---|---|
| `models/c130.glb` | C-130H legacy four-blade transport candidate | Original legacy propeller geometry, legacy cockpit insert, transport skin infills, cargo and personnel access |
| `models/ac130.glb` | AC-130W Stinger II, circa 2021 visual candidate | H-family propulsion, two EO/IR visual assemblies, port 30 mm/105 mm visual installations, actual receiving apertures, aft port door replaced by mission installation |
| `models/ac130j.glb` | AC-130J Ghostrider candidate | J-style nacelle/intake/exhaust modules, six swept propeller blades, digital cockpit/HUD insert, gunship aperture and sensor modules |

The W designation makes the previous generic legacy-gunship slot explicit. It does not rebind any existing AC-130U game roster entry. The original source's precise subvariant is still unverified. J installation shapes and the second EO/IR station remain approximations pending photographic acceptance.

## Implemented changes

- Corrected the scene basis to metres, +Y up, nose -Z, +X starboard using a proper rotation; inherited nonuniform parent normalization is baked into vertices rather than left on animated parents.
- Recentered legacy propeller pivots at their real hubs. Propellers, wheels, flight surfaces, access mechanisms, gear, and mission equipment have real embedded animation tracks.
- Extracted flap, aileron, elevator and rudder skins from the original geometry and added internal seam caps.
- Retained the detailed original cargo cabin and original ramp/door meshes. Access openings remove actual obstructing skin/interior triangles.
- Added forward crew stairs, staged upper cargo door/lower ramp motion, raised aft personnel-door motion, staged main/nose gear and bounded gear wells.
- Added explicit ownership so a gear master and its inspection cover control cannot both drive the same transform. Cargo and landing-gear sequences reverse in the proper order.
- Separated transport panels and mission-aperture modules, legacy/J powerplant and cockpit modules, and removable visual equipment. The complete assembly remains defined by one family source.
- Added a locally bundled Three.js 0.170.0 review viewer with per-control sliders, presets, wireframe/X-ray/surface modes, cameras, and Actuate everything/Pause/Reverse/Reset.
- Added native Blender import, sampled NLA evaluation, editable-file reopen checks, and renders of the actual exported geometry in controller-selected states.

## What the controls mean

All finite sliders use normalized one-way clip time from 0 to 1. Gear 0 is down and 1 is retracted. `PARKED` restores the canonical authored rest; `SERVICE` opens supported access mechanisms; `FLYING` closes access, retracts gear and runs propellers. These are presentation configurations, not flight dynamics or real aircraft operating procedures.

The global demonstration covers the exported inventory, runs compatible controls concurrently, and stages access closure before gear/propulsion. Pause freezes both motion and rotating phases. Reverse follows the authored sequence backward. Reset restores all canonical local transforms and clears accumulated rotating phases.

Gun mount movement, recoil and sensor movement are visual mechanisms with authored ranges. They do not model operational weapon performance, aiming, ammunition, firing logic or sensor capabilities.

## Verification scope

The package records independent glTF validation, decoded geometry/animation checks, actual Three.js loader/controller checks, native Blender checks, and sampled geometry probes. Every report must match the delivered model hash. A valid file, a moving node and a successful render are different checks.

Native Blender checks evaluate the imported animation tracks. Additional Blender evidence renders use exact Three.js world matrices, with an explicit coordinate conversion and measured matrix error. Those renders show what the controller produces; they do not by themselves prove every intermediate path clear.

**Native Unreal import, animation integration, cook and runtime tests have not been performed.** These GLBs use rigid node animation and contain no skinned skeletal rig. Engine-specific integration must preserve the hierarchy or deliberately convert it; successful static-mesh import alone does not validate animation.

## Outstanding acceptance work

1. Match the overall source shape, nacelles/intakes, window layout, cockpit, mission installations and surface finish against approved photographs. The retained source proportions and newly authored local travel are not measured production geometry.
2. Complete swept-clearance/contact review, especially upper cargo door/roof, personnel doors/cabin, gear cover/well transitions and equipment apertures. Sampled intersection probes have explicit limitations; inspect the final report for unresolved crossings.
3. Validate the actual target Unreal version, materials, units, hierarchy, animation ownership, collision, packaged runtime and performance. No `.uasset`, Unreal cook or native engine pass is claimed.
4. Resolve the inherited source author's license and provenance before production distribution. Reference evidence does not license the original mesh.
5. Complete game integration, damage states and performance/LOD acceptance. A named visual socket or `level 1` tag does not create a tested detachable gameplay system.

The master exports intentionally retain detail and embedded maps. Any later game LOD or compression should be a separately validated derivative, preserving articulation and appearance. [Reference decisions](references/REFERENCE_NOTES.md) and [the claim/evidence ledger](references/REFERENCE_LEDGER.json) distinguish inspected photographs from inferred geometry and travel.
