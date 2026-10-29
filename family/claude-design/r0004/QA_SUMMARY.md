# r0004 verification and acceptance scope

Author: **claude-design**. This summary separates format, runtime, native scene
and visual evidence. A pass in one category is not a pass in another.

## Frozen inputs

| Input | SHA-256 |
|---|---|
| `models/c130-family.glb` | `118f7674ca0b8582948e4b4228acf949e851f8a1aba7b3b121eeaaffb367cc4f` |
| `articulation/c130-family.json` | `e7a9e3f53330c44d15b7cfd56229739af1a04267589dab9801222ddbd70e4287` |
| `loadouts/catalog.json` | `243fd39c10655d34a3ca0439d5e71eab65ae5c2f938053c672ebbf59e8b78ee5` |

The model is 21,480,060 bytes with 768 nodes, 548 stored meshes, 44 clips and one
shared airframe instance. The catalogue contains 12 slots, 28 options and 8
presets. Counts of stored alternatives are distinct from counts visible in a
selected loadout. Source: [build-loadout-receipt.json](qa/build-loadout-receipt.json).

## Status by evidence type

| Check | Status | Evidence and practical scope |
|---|---|---|
| glTF format and resources | PASS | [gltf-validator-summary.json](qa/gltf-validator-summary.json), pinned Khronos validator 2.0.0-dev.3.10; master and all seven component GLBs each have 0 errors and 0 warnings |
| Actual master loadout runtime | PASS | [loadout-runtime-qa.json](viewer/loadout-runtime-qa.json), exact final master; Three.js 0.170.0 CPU scene and clip evaluation |
| Complete-family clean-source reproduction | PASS | [family-source-isolation.json](qa/family-source-isolation.json), current source snapshot and master; five GLBs rebuilt byte-identically with two declared original GLB inputs and no network attempts |
| Generic controller regressions | PASS | [controller-qa.json](viewer/controller-qa.json), staged cargo/gear and ownership behavior; independent of GLB appearance |
| Integrated ramp sampled motion | SCOPED RESULT | [ramp-motion-audit-final.json](qa/ramp-motion-audit-final.json), exact final master and specified pairs only |
| New-equipment reference and attachment fit | SCOPED REVIEW | [loadout-reference-fit-audit.md](qa/loadout-reference-fit-audit.md); final applicability amendment checks unchanged component/host geometry, placements and equipment clips; exact photographic fit remains unaccepted |
| Native Blender import, clips, save/reopen and final views | PASS | [native-loadout-review.json](qa/native-loadout-review.json), exact final hash; Blender 4.5.15 LTS, 44 clips, packed save/reopen and 13 views |
| Direct review of final native images | PASS_WITH_DECLARED_LIMITATIONS | [visual-review.json](qa/visual-review.json), all 13 exact-master images and native-report hash recorded; no blocking findings, draft faceting/surface finish retained |
| Final aircraft portable bytes and module closure | PASS | [portable-manifest.json](viewer/portable-manifest.json) and [portable-qa.json](viewer/portable-qa.json); exactly one embedded model restores the final-master bytes, and dependency closure passes |
| Four new isolated inspectors | PASS | Final component `inspector.manifest.json` files match their current component GLB and articulation; isolated module/CPU checks pass |
| Reused r0003 component byte identity | PASS | [REUSED_R0003_PROVENANCE.json](components/REUSED_R0003_PROVENANCE.json), 66 files; retained historical acceptance remains r0003 |
| Browser/WebGL rendering | NOT_RUN | No browser session or GPU image test was used for this revision |
| Native Unreal import, cook and runtime | NOT_RUN | No `.uasset`, Blueprint loadout consumer or engine acceptance report is included |
| Exact reference match / photorealism | NOT_ACCEPTED | Reference-guided visual equipment, with explicit approximation limits |
| Continuous collision / complete combined-motion clearance | NOT_ACCEPTED | Sampled, named ramp pairs cannot establish this broader property |

Validator informational messages are retained in the individual reports. The
master has 84 informational items covering unused objects, unused tangents or
weights, and non-power-of-two image dimensions; these are not errors or warnings.
Format validation does not establish mechanical fit, licence clearance or visual
authenticity.

## Runtime checks on the actual master

The runtime test loads one master with the delivered Three.js loader, restores
37 module roots to canonical scales and constructs the pose driver from those
rest transforms. It exercises every one of the 28 choices and all eight exact
presets. It checks that referenced roots and controls exist, that every slot has
exactly one selected option, and that the same scene and mesh geometry instances
survive configuration changes.

Every applicable mechanism uses actual exported clip tracks. The test covers
control membership, transform movement, hose morph deformation, pause, reverse,
interrupted reverse, reset, saved configuration round trips, rejection of
invalid input before mutation, and evaluation of the declared compatibility
rules. Outgoing gun-cycle state and hose morph state are reset before switching
equipment. The maximum local transform error after reset is zero in this test.

The default model has 27 active controls, while the two gunship presets have 39.
The 44-control count is the family inventory, not a claim that every preset
exposes all alternatives simultaneously. The report records each configuration's
visible mesh/triangle counts and selected control count.

These tests stub image decoding. They establish CPU scene/controller behavior,
not texture appearance, WebGL execution, GPU draw-call performance, display
quality, cinematic finish, physical clearance or native-engine import.

## Ramp fit and sampled crossings

[ramp-master-repair.json](qa/ramp-master-repair.json) measures the inherited
aperture and repaired ramp contour at 68 stations. Lateral edge distance before
repair was 96.68–171.66 mm, median 126.67 mm. After repair it is 4.28–29.70 mm,
median 8.93 mm. The larger remaining values include corner transitions. The
upper fixed jamb-to-leaf reveal is an authored 3 mm. This measurement is an XY
distance between the aperture edge and outer ramp contour at each sampled Z
station. It is not a real-aircraft tolerance or a watertightness measurement.

The final corner repair also has a dedicated measurement in the report's
`aft_corner_fit` section. It samples the aperture boundary at 201 stations per
side over Z = 6.2454–6.40 m, measuring nearest distance to lower-ramp, upper-leaf
or fixed-jamb triangles. A separate transverse-section sample measures the aft
closing lip. This test covers the transition missed by the original 68 side
stations.

| Corner measurement | Before local corner pass | After local corner pass |
|---|---:|---:|
| Port aperture-to-closure maximum in the surveyed region | 50.62 mm | 19.51 mm |
| Starboard aperture-to-closure maximum in the surveyed region | 48.64 mm | 22.36 mm |
| Outer lip at absolute X = 1.49 m, nearest upper-leaf surface | About 42.57 mm | About 4.46 mm |
| Sampled outer lip across absolute X = 1.2–1.64 m | Regionally variable | 3.79–4.47 mm |
| Centerline closing-lip sample | 4.51 mm | 4.51 mm |

The wider region's remaining maxima occur on the preceding skirt, around
Z = 6.27 m. The outer-lip sample must not be generalized into a sub-5 mm
whole-aperture claim. The central deck, node transforms and clips are preserved.

The final audit evaluates actual cargo-ramp animation at normalized times 0,
0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875 and 1. It uses a BVH broadphase and
strict noncoplanar edge/triangle intersection tests on the exact repaired master.

| Tested pair | Aggregate strict crossings across nine samples | Outside declared hinge zone |
|---|---:|---:|
| Lower ramp / inherited skin | 0 | 0 |
| Lower ramp / cabin | 0 | 0 |
| Lower ramp / upper door | 0 | 0 |
| Upper door / cabin | 0 | 0 |
| Upper door / inherited skin | 846 | 0 |

All upper-door/skin crossings lie inside the declared 50 mm hinge-contact zone.
The report exposes these contacts; it does not prove each is mechanically
intentional. World-matrix reset delta is zero. This scope excludes other
mechanisms, unsampled times, coplanar overlap, containment and continuous
collision. Earlier standalone and intermediate-master reports remain evidence
only for their recorded development hashes.

## Native scene and image review

[native-loadout-review.json](qa/native-loadout-review.json) binds the final GLB and
viewer-pose snapshot hashes. Blender 4.5.15 LTS evaluates all 44 imported clips at
eight samples per action, then applies exact controller matrices, effective
visibility and flexible morph weights for the selected renders. Packed native
save/reopen passes. This is separate from the CPU viewer tests.

[visual-review.json](qa/visual-review.json) records direct inspection of all 13
final shaded images, their hashes and the native-report identity. The views
cover transport H/J, gunship and both gun panels, tanker stowed/deployed, Fulton
folded/deployed, JATO active, cargo open, and closed rear side/belly details. The
broad lower-ramp gap and triangular corner opening are resolved in those views;
selected equipment appears with the correct transport or emplacement panels.

The image review has no blocking findings and is accepted with declared limits.
Small local ramp-corner faceting and inherited surface/normal detail remain draft
finishing work. It does not accept exact aircraft fidelity, photorealism,
continuous clearance, every possible equipment combination, or browser/Unreal
behavior. Receiver-cover mechanics, precise basket geometry, Fulton endpoint
details and JATO installation fidelity remain approximate.

## Complete-family source reproduction

[family-source-isolation.json](qa/family-source-isolation.json) records a clean
rebuild with the delivered source copied into a fresh shallow temporary
directory. The guard permits prebuilt GLB reads only for the two declared
original inputs and blocks network access. The resulting master and four new
component GLBs all match their delivered SHA-256 values byte-for-byte. No network
attempts occurred. The receipt records source-file hashes, input hashes, test
script identity and the exact rebuilt model set.

This establishes reproduction and source dependency closure for those five
models. The retained gun/sensor components have their separate r0003 source
history. Source reproduction does not establish photographic fidelity, motion
clearance or an accepted browser/Unreal implementation.

## Independent components and portability

Each new component inspector embeds only its own GLB, articulation and pinned
runtime dependencies. Its builder extracts the embedded data into an isolated
temporary directory, verifies the restored bytes and hashes, parses embedded
modules, checks import closure and blocks external network requests. It then
loads the actual component, evaluates available clips, and checks global
coverage, pause/reverse/reset and morph recovery. Both hose inspectors also
check high/low basket selection. These checks still do not render a browser.

The aircraft portable verifier checks that exactly one family model is embedded,
that decompression restores the final master bytes, that its catalogue agrees
with the delivered JSON and that embedded module imports close without missing
dependencies. This is byte and module evidence, not browser appearance evidence.

The reused `gau23-visual`, `m102-airborne-visual` and `eoir-visual` folders retain
the exact prior component files, including original native scenes, source,
inspectors and manifests. Their copied manifests identify r0003 on purpose.
The r0004 format validator also checks the three unchanged component GLBs.
Assembly-level byte-identity and format verification do not expand their prior
native, source-isolation or geometry acceptance to the new full aircraft.

## Unresolved visual and integration work

The receiver is a visual receptacle with illustrative cover travel; the precise
real cover mechanism has not been established. Pod and basket proportions,
Fulton endpoint details, JATO attachments and visual effects remain authored
approximations. The historical recovery preset lacks exact MC-130E avionics and
interior. The JATO study does not include LC-130 skis. See the primary-source
[research notes](references/LOADOUT_RESEARCH.md) and
[ledger](references/loadout-reference-ledger.json) for the evidence boundary.

Unreal acceptance requires a version-specific import and runtime implementation,
including the zero-scale default-module contract, rigid-node clips, morph
weights, collision activation and unit/axis conversion. No such native result is
inferred from glTF validity or Blender import. The proposed integration and
acceptance steps are in [UNREAL_HANDOFF.md](UNREAL_HANDOFF.md).
