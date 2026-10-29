# Loadout reference and fit audit — r0004

**Result: scoped geometry corrections verified on the current master; photographic acceptance remains NOT_ACCEPTED.** The earlier floating/buried Fulton parts, unsupported fending-line route and partly buried JATO bottles were corrected during this review. The checks below use actual exported geometry and explicit artist-authored coordinates. They are visual/game-asset checks, not aircraft engineering or operational compatibility certification.

Audit owner: `c130_reference_audit`. Reviewed 29 October 2026. This audit changed this report only; source corrections were made by the master-asset owner.

## Exact audited inputs

| Input | SHA-256 |
| --- | --- |
| `models/c130-family.glb` | `de910de58de643328055f27246f2d8d7b86047cea6f35e4e46406144b71644fc` |
| `source/loadout_components.py` | `f7e3b034de893a0d1eb2f753a17ba85dc1815a1c6a310e3ad6de60905a60ea76` |
| `source/build_loadout_family.py` | `e616ff942e076f5d29b9acfbf472c98e47cd652413345d65033474a8be257591` |
| `loadouts/catalog.json` | `243fd39c10655d34a3ca0439d5e71eab65ae5c2f938053c672ebbf59e8b78ee5` |

Basis: metres; +X right, +Y up, nose −Z. Numbers below describe this asset's coordinates only.

## Fulton: correction and adopted fit

The previous assembly floated above the nose and its folded rods entered the fuselage. In the previous geometry, the housing underside was y2.78 above a local skin top near y2.498. A folded rod midpoint at x0.655 lay inside a roughly x±1.20 section, and its tip at x0.76 lay inside x±1.943. Those positions were unsuitable even for an illustrative mechanism.

The final export contains the following corrected datums. Mirror X for the left side.

| Element | Authored position / behavior |
| --- | --- |
| Central housing datum | `(0, 2.58, −14.85)` |
| Right arm pivot | `(0.90, 2.43, −14.55)` |
| Right folded arm tip | `(2.25, 2.38, −11.30)` |
| Rotation | Right +145° and left −145° around local Y; artist-authored |
| Right deployed arm tip | Approximately `(1.65827, 2.38, −17.98657)` |
| Nose fending-line endpoint | `(0.30, 2.58, −14.70)` |
| Nose cable attachment tube | `(0.12, 2.58, −14.73)` to the endpoint above; radius 0.035 |
| Leading-wingtip cable endpoint | `(19.70, 4.71105, −3.14578)` |

The central housing's lower face is y2.46, giving about 0.038 m overlap with the local nose skin at x0,z−14.85. That is intended visual attachment. Two braces join each hinge to inspected nose-surface points. The cable attachment tube begins inside the housing's x±0.14 and z[−15.01,−14.69] bounds, so its nose endpoint is visibly supported rather than floating. The wing endpoint is on the actual inherited leading-wingtip mesh, to displayed-coordinate precision.

**Folded/deployed sweep probe:** 30 angles from 0° to 145°, with 61 centerline samples per angle, against the actual fuselage, modified Talon nose and cockpit-glazing triangles. There were 1168 usable skin-section ray results. After deducting the 0.052 m rod radius, the smallest sampled **lateral X margin** was 0.08995 m, with zero negative results. The limiting sample was the folded arm near z−11.7875. This is a sampled lateral envelope test, not a continuous minimum-distance or complete triangle-collision proof. Hinge/brace contact is intentional.

**Arm-to-cable sweep:** 291 angular samples using finite three-dimensional line segments. The lowest centerline distance was 0.22913 m; subtracting rod and cable radii gives 0.16313 m surface-envelope separation. The earlier y2.80 hinge candidate intersected the corrected cable near 30°; the final y2.43 hinge removes that conflict. The guide-tip segment was also sampled at the same 291 angles; its smallest cable surface-envelope gap was 0.53337 m. These checks are not a substitute for the final shaded motion review.

## Fending lines and propellers

The earlier cable had a hard unsupported bend in the air and ended near the wing's trailing edge. The corrected line is a direct taut segment from its visible nose bracket to the actual leading-wingtip point. This follows the broad historical layout; it does not assert an exact MC-130E attachment design.

The inherited outer legacy propeller has center `(10.56087, 3.94965, −6.26)`. Its actual blades, hub and separate tip patches produce a swept radial envelope of **2.20109 m**, over axial range z[−6.70119,−5.75947]. The corrected cable clears that entire conservative cylindrical envelope by at least **0.95610 m**, after deducting the cable's 0.014 m radius. This uses the measured exported legacy geometry rather than the initially assumed 2.05 m radius. Both outer propellers were checked (right 0.95612 m; left 0.95610 m). The inner propellers are farther from the cable at the corresponding axial range.

Source limitation: the USAF history describes lines between the outer wingtips and a point just aft of the sky anchor. Its printed page 31 diagram depicts an older A/B installation. It supports the family routing concept; the fitted coordinates, bracket appearance and 145° yoke travel remain authored approximations. Exact MC-130E stowed/deployed endpoint photographs remain NOT_DONE. See `references/LOADOUT_RESEARCH.md` and the inspected printed pages 31–32 views.

## JATO bottle and bracket fit

The side banks now form the vertically stacked arrangement visible in the inspected historical photograph. The final bottle centers are below; each carries the authored 18° downward-aft tilt. Brackets extend 0.34 m inward from the bottle center and intentionally join the skin.

| Bottle | Absolute X | Y | Z | Minimum right / left sampled lateral vertex gap |
| --- | ---: | ---: | ---: | ---: |
| 1 | 2.21874 | 1.65 | 3.75 | 0.05023 / 0.06314 m |
| 2 | 2.27890 | 2.00 | 3.69 | 0.04391 / 0.04768 m |
| 3 | 2.30262 | 2.35 | 3.63 | 0.03050 / 0.03828 m |
| 4 | 2.30550 | 2.70 | 3.57 | 0.02700 / 0.03067 m |

The check transformed actual bottle and clamp vertices through their exported node rotations and compared them with local skin sections. There were no negative sampled gaps on either side. The reported gaps are lateral section measurements, not full surface-to-surface distances. Mount brackets are excluded from separation checks because their intersection with the aircraft is intended.

The photograph supports historical shape and placement only. The chosen coordinates, tilt and plume timing are authored. This preset correctly calls itself a historical equipment study and explicitly says that LC-130 skis/full conversion are absent. Do not rename it a complete LC-130 preset.

## Tanker, receiver and reuse checks

No material attachment defect was found in the tanker pod's inspected source fit. The pylon runs from y3.63 to 4.40, overlapping the pod top near 3.69 and the nearby wing underside near 4.33–4.35. The source separates pod, hose, coupling, ribs and fabric. Hose end and coupling travel agree at the authored stowed and extended endpoints. Deployed fabric has an annular mouth rather than a solid disk.

The maintenance reference supports folded ribs/gathered fabric; the deployed reference supports an annular basket. The high/low-speed exchange photograph proves separate selectable basket types but does **not** establish the modeled 0.42/0.60 radii or 20/24 rib counts. Those differences are explicitly approximate in the catalog and remain NOT_ACCEPTED as exact types. Flight-stowed basket seating and complete flexible-hose dynamics also remain unverified.

The receiver is now above/aft of the cockpit glazing, consistent with the inspected contact-location photograph. The source labels its sliding cover travel illustrative. Exact hatch mechanics/endpoints remain NOT_DONE; this audit does not certify its complete swept clearance.

All four new independent exports—left/right hose-drogue pods, Fulton yoke and JATO kit—have root translation `(0,0,0)`, no external binary buffers, no aircraft subtree, and `parent_aircraft_dependency:false`. The aircraft keeps its fending lines as installation geometry outside the reusable nose-yoke subtree. These are appropriate dependency boundaries. An isolated component's default high-speed basket does not establish that its low-speed alternative is a measured real submodel.

Catalog semantics are coherent for the modeled options: receiver and tanker choices are independent; left/right tanker stations are independent; blank and gun panels are mutually exclusive choices within their slot. Unmatched/constraint-breaking combinations are labeled Custom JCNC rather than certified carriage. Final W/J labels now include **candidate**. Historical, candidate and equipment-study wording should be retained.

## Remaining gates and exact limits

- Final shaded motion inspection of this exact export is performed by the master owner; it was not completed by this audit. No browser, native Unreal or full continuous triangle-collision acceptance is claimed here.
- Exact Fulton endpoint references, exact receiver-door travel and exact high/low drogue type geometry remain missing, as recorded in the reference ledger.
- The checks are scoped to the reported new equipment fit. Ramp fit, gun internals, all-system concurrent motion and full aircraft photographic matching are separate reports.
- A source or master change invalidates the numeric conclusions until the affected probes are rerun.

## Inspected public reference basis

- [USAF/Air University Press, The Praetorian STARShip](https://www.govinfo.gov/content/pkg/GOVPUB-D301-PURL-LPS20515/pdf/GOVPUB-D301-PURL-LPS20515.pdf), printed pp. 31–33: historical foldback principle and fending-line layout; older A/B diagram distinguished from exact E fit.
- [DVIDS 7758343](https://www.dvidshub.net/image/7758343/airmen-inspect-mc-130j-commando-ii-refueling-pod): pod outlet, hose and folded basket.
- [DVIDS 8289439](https://www.dvidshub.net/image/8289439/joint-haar-extends-search-and-rescue-capabilities): deployed annular drogue.
- [DVIDS 8942759](https://www.dvidshub.net/image/8942759/marine-aerial-refueler-transport-squadron-153-trains-australia): low/high-speed drogue exchange, obscured shape comparison.
- [DVIDS 7304591](https://www.dvidshub.net/image/7304591/chaplain-ice): historical LC-130/JATO appearance; courtesy Dr. Todd Valentic.
- [DVIDS 9074140](https://www.dvidshub.net/image/9074140/91st-ars-refuels-1st-sow-ac-130js): dorsal receiver location, hatch obscured by boom.


## Final-master applicability amendment — cargo-ramp corner repair

The measurements and original input table above retain their originally tested master, `de910de58de643328055f27246f2d8d7b86047cea6f35e4e46406144b71644fc`. In particular, earlier wording about the current master describes that original audit run. They have not been relabeled as newly executed geometry tests.

The delivered master is now **`118f7674ca0b8582948e4b4228acf949e851f8a1aba7b3b121eeaaffb367cc4f`**, 21,480,060 bytes. Its four new independent component GLBs are byte-identical to the versions covered by their current component manifests, inspectors, source-isolation and native results, and the original aggregate receipt. Every component-manifest file, corresponding editable and packaged ZIP hash was also checked; those artifacts were not rebuilt.

| Unchanged component | SHA-256 |
| --- | --- |
| hose-drogue-left | `92315788d86a747a049efb1b7ba5cae65b7c03af6ca934bc509cc7476d40b7eb` |
| hose-drogue-right | `1e51bfbb25b613e6d3615dcdb49a6c1a6cf857e7cc18bdf567b23b70d086f3dd` |
| fulton-yoke | `047d1d3b2510ddadafd93de142d33e93d50865b1819ef497436f005660839e53` |
| jato-kit | `a18d1c0a0102728a2d2f4fa07cd6f70f76bcfe2d275628386bba3b68b5f5a44c` |

The equipment-fit host comparison used the recorded corner-only derivative `qa/ramp-corner-candidate.glb`, SHA-256 `18fa65edd7351baecc49a19db9d60324f20fa8786ec403b6429ed1f87273b0fe`. Its fit report identifies `de910de58de643328055f27246f2d8d7b86047cea6f35e4e46406144b71644fc` as its input and records preservation of the clips and node transforms. The final master was compared directly to that derivative:

- **46 meshes match exactly** by expanded indexed attributes and morph-target arrays, including the common fuselage, Talon nose, cockpit glazing, all propeller alternatives and Fulton/fending installation geometry. No floating-point tolerance was used.
- **12 named host/equipment placement chains match exactly**, including ancestors and rest TRS/matrices.
- The left/right tanker deployment, Fulton deployment, JATO visual cycle and receiver-cover clip target/interpolation/input/output data match exactly.

These unchanged inputs preserve the applicability of the scoped equipment-fit findings above to the final master. The amendment does not certify the repaired ramp, rerun component geometry/native tests, or grant photographic acceptance. Ramp fit and final-master runtime/native checks remain governed by their own current-hash reports. Full machine-readable comparison digests and the preserved original tested identities are in `qa/component-source-isolation.json` under `master_identity_amendments`; the earlier shallow-import `source_snapshot_amendments` remains intact.
