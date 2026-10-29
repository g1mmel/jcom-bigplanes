# r0004 — one C-130 with interchangeable loadouts

Author: **claude-design**. Parent: immutable r0003 source and reusable components.

## Changed

This revision replaces complete-aircraft switching with one common fuselage and
one `c130-family.glb`. A data-driven catalogue selects named equipment modules
inside that scene. It contains 12 slots, 28 choices and 8 presets. The full
mechanism inventory is 44 controls; each selection exposes only applicable
controls.

The forward 30 mm position swaps a closed transport skin/liner for its gun panel
and internal system. The aft port position swaps the working paratroop-door
module for the 105 mm panel and internal gun. Propulsion, flight station,
external tanks, radome, receiver, EO/IR sensors, independent tanker stations,
Fulton equipment and JATO are also selectable. Both tanker stations offer high
and low speed basket choices, with morphing hoses and fabric during the authored
deployment cycle.

The viewer loads the master once. Changes validate first, reset outgoing pose,
morphs and effects, then apply the selected module roots atomically. Saving and
reloading a loadout preserves the chosen slot values. Exact preset matches show
their reference-guided or historical labels; unmatched or conflicting choices
show **Custom JCNC** and the declared compatibility messages. The catalogue does
not claim universal real-aircraft compatibility.

Global Actuate everything, Pause, Reverse and Reset remain available. Surface,
wireframe, X-ray and equipment cameras operate on the selected configuration.
Mesh and triangle counts reflect visible equipment. Four new independent
component inspectors cover left/right hose-drogue systems, the Fulton yoke and
the JATO kit. The reusable gun and EO/IR component folders are copied from
r0003 byte-for-byte with a separate assembly provenance receipt.

## Rear ramp fit

The inherited closed lower ramp was too narrow around its lateral aperture.
The repair fits its lateral skirts to the existing fuselage profile, adds fixed
upper aperture jambs, makes a local aft underside correction and provides local
receiving pockets in the inner liner. The central cargo deck, upper moving leaf,
pivots and clips are retained. The comparison uses the actual inherited geometry
and the closed-aircraft photograph in the reference ledger.

At 68 sampled stations, the lower-ramp contour distance changed from
96.68–171.66 mm, median 126.67 mm, to 4.28–29.70 mm, median 8.93 mm. The upper
fixed jamb-to-leaf reveal is authored at 3 mm. These are asset measurements and
design choices, not calibrated aircraft tolerances.

The final corner pass addresses a triangular opening missed by the initial
side-seam stations. The outer lower lip now follows the actual upper leaf and
fixed jamb, and the jamb tips extend to finish the join. Sampled outer-lip
distance is 3.79–4.47 mm; the centerline remains 4.51 mm. The wider aperture survey
still reaches 22.36 mm on the preceding skirt. These are separate regional
measurements, not a claim that every closure seam is below 5 mm.

The integrated audit `qa/ramp-motion-audit-final.json` binds the repaired final
master. At nine sampled positions, it records zero strict crossings for tested
lower-ramp pairs and upper-door/cabin. All 846 aggregate upper-door/skin
crossings are inside the declared 50 mm hinge zone, with none outside. The
hinge-zone contacts are not certified intentional; continuous clearance is not
established. Earlier reports retain their different input hashes and do not
substitute for this final audit.

## Frozen model and evidence

The master is 21,480,060 bytes, 768 nodes, 548 stored meshes and 44 clips:

```text
SHA-256 118f7674ca0b8582948e4b4228acf949e851f8a1aba7b3b121eeaaffb367cc4f
```

`qa/gltf-validator-summary.json` records zero errors and zero warnings for this
master and all seven independent component GLBs. `viewer/loadout-runtime-qa.json`
passes every option and preset, actual transform and morph tracks, active
control filtering, same-scene geometry identity, pause/reverse/reset, loadout
round trips and outgoing firing/morph cleanup. The texture decoder is stubbed in
those CPU tests.
`qa/family-source-isolation.json` also passes: a fresh shallow temporary directory
containing the delivered source and two declared original GLBs reproduces the
master and all four new component GLBs byte-identically, with no network
attempts. This verifies source closure and reproduction, not visual accuracy.

Native Blender 4.5.15 LTS import, all 44 clip evaluations, packed save/reopen and
13 rendered views pass on the repaired final master. Direct inspection of all
13 views is `PASS_WITH_DECLARED_LIMITATIONS` in `qa/visual-review.json`, with no
blocking findings. The broad rear gap and triangular corner opening are closed;
small local corner faceting and inherited draft surface/normal detail remain
finishing work. This is functional visual-asset review, not photorealistic or
exact-aircraft acceptance.

Browser/WebGL appearance and native Unreal import/cook/runtime: **NOT_RUN**.
Portable byte-integrity and independent inspector reports bind their exact
embedded files; consult `QA_SUMMARY.md` and generated manifests for scope.

## Known approximation boundaries

The presets are equipment candidates supported by the dated sources in
`references/LOADOUT_RESEARCH.md`. A standard C-130 visual asset does not become an
exact aircraft variant merely by selecting equipment. The Combat Talon/Fulton
candidate lacks exact MC-130E avionics and interior fit. The historical JATO
study lacks LC-130 skis and its complete conversion. Eight bottle placement,
deployment shapes and burn/recoil effects remain authored visual work.

The Fulton yoke folds back along the nose sides and extends forward, following
the cited historical mechanism description; precise installation dimensions and
all endpoint details remain approximate. High and low speed basket selection is
supported by maintenance references, while exact dimensional profiles are not
accepted. The boom receiver is a supported equipment feature; its cover travel
is an inspection placeholder rather than an established real mechanism.

The generic GLB displays the default loadout by setting inactive module-root
scales to zero. The viewer restores `canonical_scale` before capturing rest and
uses visibility for selection. This encoding is equipment configuration, not
mechanical stowage. Unreal needs an explicit consumer of this contract.

No photorealism, manufacturing tolerance, continuous or combined-motion
clearance, flight/weapon simulation, universal carriage compatibility, or native
engine acceptance is asserted by this revision.
