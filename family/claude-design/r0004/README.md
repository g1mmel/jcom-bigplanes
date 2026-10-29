# C-130 configurable family — r0004

Author: **claude-design**. This revision contains **one common C-130 airframe and
one master GLB**, with interchangeable panel and equipment modules. Loadouts
change those modules inside the existing scene. They do not load another complete
aircraft. The original source airframe is retained, and the rear ramp is fitted
to its existing aperture.

## Open the model

Open [C130-family-portable.html](viewer/C130-family-portable.html) for the complete
offline aircraft inspector. It embeds the master model, loadout catalogue,
articulation, revision notes and pinned viewer dependencies. A browser with
WebGL2 and gzip `DecompressionStream` support is required. The equivalent folder
viewer is [viewer/index.html](viewer/index.html); serve this revision directory
with `python -m http.server 8000` and open `http://localhost:8000/viewer/`.

Use **Loadouts** to select a named candidate or change individual equipment. The
viewer keeps one choice in every slot and updates only the selected modules and
their applicable controls. **Actuate everything**, **Pause**, **Reverse** and
**Reset** act on the current equipment. Reset returns mechanisms to rest while
keeping the loadout. **Return to default** also restores the initial loadout,
camera and surface mode. Save/load controls export or restore a small JSON
configuration. Camera buttons inspect drogues, Skyhook, JATO and the receiver;
surface, wireframe and X-ray views remain available.

The displayed geometry counts belong to the visible configuration. The master
inventory contains all stored alternatives, so its total is intentionally larger.
See [viewer/README.md](viewer/README.md) for runtime and verification details.

## Changeable equipment

The delivered catalogue contains **12 slots, 28 options and 8 named presets**.
The master has **44 mechanism controls** across all configurations; controls
irrelevant to the selected equipment are removed from the active control list.
The catalogue itself, [loadouts/catalog.json](loadouts/catalog.json), is the
authority for option IDs, node roots, control membership and compatibility notes.

| Slot | Available choices | What changes |
|---|---|---|
| Propulsion | Legacy four blade; J six blade; NP2000 style eight blade | Propellers and appropriate nacelle assemblies |
| Flight station | Analogue; digital/HUD | Cockpit equipment module |
| Forward port gun position | Closed transport panel; 30 mm visual installation | Outer skin and liner or gun aperture, mount and internal system |
| Aft port position | Working paratroop door; 105 mm visual installation | Door/panel opening and complete internal gun module |
| External tanks | None; both | Left and right tank assemblies |
| Nose | Standard; historical Talon style | Alternative radome module |
| Boom receiver | None; dorsal receptacle | Continuous skin or receiver module with illustrative inspection cover |
| EO/IR sensors | None; chin; chin and port | Gimbal modules and corresponding yaw/pitch controls |
| Left tanker station | None; high speed basket; low speed basket | Pod, deforming hose and selected basket |
| Right tanker station | None; high speed basket; low speed basket | Independent pod, hose and basket selection |
| Skyhook | None; Fulton equipment | Folding nose yoke and fending lines |
| JATO | None; eight bottle visual kit | External mounts, bottles and authored burn effect cycle |

The gun choices are **panel swaps**: the transport and gun configurations carry
their appropriate skin, liner, door or installation module. Opposite-side access
and common fuselage geometry remain shared. This covers the changeable equipment
authored in this revision; it is not an exhaustive catalogue of every C-130
conversion or every operator's installation.

## Presets and historical scope

| Preset ID | Displayed candidate | Scope |
|---|---|---|
| `transport_h` | C-130H transport | Default legacy propulsion/analogue transport equipment |
| `transport_j` | C-130J transport | J propulsion/digital flight station transport equipment |
| `gunship_w` | AC-130W style, circa 2021 | Dated gunship equipment candidate |
| `gunship_j` | AC-130J style, circa 2021 | Dated gunship equipment candidate |
| `tanker_j` | KC-130J style tanker | Two independent hose/drogue pod stations |
| `recovery_e` | Historical Combat Talon/Fulton | Recovery equipment study; exact MC-130E avionics and interior are incomplete |
| `legacy_jato` | Historical legacy JATO | Equipment study; LC-130 skis and its complete conversion are absent |
| `np2000_h` | C-130H NP2000 style upgrade | Legacy family with eight blade propeller alternative |

Names identify reference-guided or historical candidates, not certified exact
aircraft. The source ledger distinguishes supported features, authored geometry
and unresolved details. The dated gunship sources support the broad equipment
sets; the Fulton history supports a yoke that extends ahead of the nose and folds
back along its sides. JATO is treated as historical equipment. See
[LOADOUT_RESEARCH.md](references/LOADOUT_RESEARCH.md) and
[loadout-reference-ledger.json](references/loadout-reference-ledger.json) for
primary references, image credits and limits.
The scoped [equipment-fit audit](qa/loadout-reference-fit-audit.md) records
attachment checks and a final-master applicability amendment; it preserves the
original measured evidence and its limits.

Unmatched combinations display **Custom JCNC**. Declared incompatibilities are
shown explicitly while creative combinations remain selectable. These warnings
express this asset's documented preset rules, not a complete aircraft engineering
compatibility model. Tanker equipment and a boom receiver are not universally
exclusive: the [USAF MC-130J description](https://www.193sow.ang.af.mil/About-Us/Fact-Sheets/Display/Article/1062881/mc-130j-commando-ii/)
describes both roles on that type.

## Rear closure correction

The inherited lower ramp had an excessive lateral gap against its fuselage
opening. The closed-aircraft reference supports a continuous upswept lower contour
with visible panel seams:
[DVIDS, Red Flag 11-3](https://www.dvidshub.net/image/383774/red-flag-11-3).
The repair reshapes the ramp's lateral skirts against the actual source opening,
adds fixed receiving jambs around the unchanged upper moving leaf, and relieves
local inner-liner areas swept by the closures. The inherited pivots and animation
clips are retained.

At 68 measured model stations, median lateral edge distance changed from
**126.67 mm to 8.93 mm**. The revised range is **4.28–29.70 mm**, including retained
corner transitions. These are model-space contour measurements, not measured
aircraft manufacturing tolerances. The source report is
[ramp-master-repair.json](qa/ramp-master-repair.json).

A final close-up also exposed a triangular gap and step at the join between the
lower lip and upper closure, beyond the initial side-seam survey. The outer
closing lip is now fitted to the actual upper-leaf contour, with extended fixed
jamb tips. Sampled outer-lip distance to the upper leaf or jamb is
**3.79–4.47 mm**; the unchanged centerline sample is 4.51 mm. A separate, broader
aperture-to-closure survey still reaches **22.36 mm** on the preceding skirt. These
measurements describe different regions; they do not establish a uniform
sub-5 mm seam or perfect flushness over the complete closure.

The repaired final-master motion audit sampled nine positions. It found no
strict crossings for the tested lower-ramp pairs or upper-door/cabin pair. It
recorded 846 upper-door/skin triangle-pair crossings across the samples, all
inside the declared 50 mm hinge zone, with none outside. That zone is reported
rather than accepted as proven intentional contact. Continuous collision
clearance, coplanar/containment cases and watertightness are not established. See
[ramp-motion-audit-final.json](qa/ramp-motion-audit-final.json) and
[QA_SUMMARY.md](QA_SUMMARY.md). The final
[native-image review](qa/visual-review.json) confirms that the broad gap and
triangular opening are closed in the rendered side/belly views, while retaining
visible seams and the declared finishing limitations.

## Reusable systems

Independent component folders contain their own GLB, articulation, editable
source, native scene, inspector and provenance. They can be inspected without
loading the aircraft:

| Component | Independent inspector | Revision relationship |
|---|---|---|
| Left hose/drogue pod | [Open](components/hose-drogue-left/inspector.html) | New r0004 component |
| Right hose/drogue pod | [Open](components/hose-drogue-right/inspector.html) | New r0004 component |
| Fulton yoke | [Open](components/fulton-yoke/inspector.html) | New r0004 component |
| JATO kit | [Open](components/jato-kit/inspector.html) | New r0004 component |
| 30 mm visual gun | [Open](components/gau23-visual/inspector.html) | Exact reusable r0003 component |
| 105 mm visual gun | [Open](components/m102-airborne-visual/inspector.html) | Exact reusable r0003 component |
| EO/IR visual sensor | [Open](components/eoir-visual/inspector.html) | Exact reusable r0003 component |

The three inherited components retain their original r0003 manifests and
historical native/source QA scope. Their exact model bytes are also included in
the r0004 format validation. [REUSED_R0003_PROVENANCE.json](components/REUSED_R0003_PROVENANCE.json)
records byte identity for all 66 copied files. Their retained reports do not
establish new native acceptance for this r0004 aircraft assembly.

## Delivery and acceptance

The frozen master is `models/c130-family.glb`, **21,480,060 bytes**, with 768 nodes,
548 stored meshes and 44 clips. Its SHA-256 is:

```text
118f7674ca0b8582948e4b4228acf949e851f8a1aba7b3b121eeaaffb367cc4f
```

[build-loadout-receipt.json](qa/build-loadout-receipt.json) records the inventory.
The [clean-source reproduction check](qa/family-source-isolation.json) rebuilds
the master and four new component GLBs byte-identically in a fresh temporary
directory using the delivered source and two declared original GLB inputs, with
no network attempts.
The final master and all seven component GLBs pass the pinned Khronos validator
with zero errors and zero warnings. The final-master CPU runtime tests pass all
28 options and 8 presets, including active controls, same-scene geometry identity,
pause/reverse/reset, morph reset and configuration round trips. These tests do
not exercise browser rendering. Native Blender import, all 44 clip evaluations,
packed save/reopen and 13 rendered views pass on this final master. Direct review
of those 13 images is **PASS_WITH_DECLARED_LIMITATIONS**, with no blocking findings.
Small local ramp-corner faceting and inherited draft surface/normal detail remain
finishing work. Browser/WebGL appearance and native Unreal import/cook/runtime
are **NOT_RUN**.
The current acceptance boundaries and report identities are in
[QA_SUMMARY.md](QA_SUMMARY.md).

The geometry, motion and effects are authored game visual approximations.
High/low basket identity is supported by references, but precise basket profiles
remain approximate. The receiver's cover motion is illustrative, not a verified
mechanism. Exact MC-130E conversion, LC-130 skis, calibrated clearances, flight
dynamics and native Unreal runtime assets are outside this delivery. Materials
and markings are inherited or authored visual treatments, not a photorealistic
acceptance claim.

Start with [source/README.md](source/README.md) to rebuild, and
[UNREAL_HANDOFF.md](UNREAL_HANDOFF.md) for the engine integration contract.
[REVISION.md](REVISION.md) records what changed and what remains unresolved.
