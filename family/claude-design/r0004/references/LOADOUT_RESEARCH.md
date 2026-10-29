# C-130 family loadout evidence

Reviewed 29 October 2026. Scope: public references for a non-operational JCNC game asset. The reference photographs were downloaded and visually inspected. This research has **not** compared the new model to those photographs, and does not certify full photographic fidelity.

## Decision for the master asset

Use one master C-130 family asset with replaceable panels and attached mission systems. A loadout should resolve the complete visible configuration: closed skin infill or aperture/frame/seal, installed component, associated cabin geometry and any variant-dependent fairing. A weapon visibility toggle alone will leave the wrong skin, an empty hole, or duplicate geometry.

Real variants contain substantial structural, propulsion, avionics and interior differences. The shared game asset can represent those differences through coherent presets and dependent modules; it should not describe every game combination as a real quick conversion. The AC-130W reference specifically identifies a highly modified C-130H. NAVAIR documents a genuine modular kit precedent in Harvest HAWK, including a replacement paratroop-door package and replacement of a refueling pylon. [S01–S05]

| Configuration | Evidence-backed visual package | Compatibility decision |
| --- | --- | --- |
| C-130H cargo baseline | Legacy airframe and selected-era propulsion, cargo ramp and upper closure | Use closed infill panels when mission apertures are absent. |
| AC-130W, circa 2020/2021 | H-derived configuration; 30mm/105mm installations and two EO/IR systems | Preserve W identity. Do not silently replace it with J nacelles, flight deck, or pressure-boot geometry. [S02] |
| AC-130J | J-based propulsion/flight-deck identity and selected-era mission package | Treat as a separate preset of the family asset. W and J system appearance needs its own photographic comparison. [S01, S03] |
| KC-130J / MC-130J tanker | Underwing pods, hoses and drogue assemblies | Use independent left/right stations. On a documented 2012 Harvest HAWK fit, the left weapon pylon replaces the left refueling pylon. [S04, S05] |
| MC-130J receiver and tanker | Dorsal UARRSI receiving interface plus underwing tanker pods and EO/IR | Receiving and dispensing fuel are separate capabilities that can coexist. A global receiver-versus-tanker exclusion would be wrong. [S06] |
| Historical MC-130E / HC-130H Fulton | Special nose/yoke fit, protective fending lines and recovery kit | Keep it historical. Nose shape and cabin/ramp equipment are part of the fit, not just a pair of prongs. [S07–S09] |
| Historical LC-130H JATO | Ski configuration, side bottle banks and legacy four-blade appearance in the 2003 photograph | Use an era-tagged historical kit. Later LC-130H NP2000 eight-blade upgrades mean propeller count alone cannot distinguish every H from every J. [S10, S11] |

## Ramp: closed skin continuity, with seams

The inspected underside photograph, **DVIDS-383774**, shows the closed rear assembly following the upswept aft belly. Panel boundaries remain visible. It does not show a broad daylight opening or a detached horizontal slab below the aircraft. For the model, a closed ramp should mate with the surrounding lower fuselage contour; a large gap or projecting slab is not explained by normal panel seams.

**DVIDS-3858825** is an interior intermediate closure frame: the lower ramp is rising, the upper closure is descending into the opening, and daylight remains between them. It establishes separate moving pieces but is not proof of fully closed exterior geometry. Neither photograph provides millimeter flushness, seal compression or exact hinge tolerances.

Local files: `loadout-photos/c130h-closed-underbelly.jpg` and `loadout-photos/ramp-closing.jpg`.

## Tanker pod, hose and drogue

**DVIDS-7758343** is the strongest inspected maintenance reference. The hose comes out of a circular opening at the pod's aft end. It is dark with pale bands. The basket on the ground has elongated ribs, a central coupling and gathered pale fabric. This is a hose-unreeled maintenance pose, not the fully stowed flight endpoint.

**DVIDS-8289439** shows a basket during helicopter refueling: a pale annular funnel around the coupling, radial ribs, and the hose approaching it. It supports the deployed visual form; perspective does not establish exact basket diameter or a universal hose curve. The photographed hose shape is only one moment in flight.

**DVIDS-8942759** explicitly documents exchanging a low-speed drogue for a high-speed drogue. That supports separate basket choices in Loadouts. Crew obscure the profiles, so **the precise geometric distinction between those two basket types remains NOT_DONE**. Do not invent a measured size or rib-angle difference from this image.

Author the pod, hose and basket as separate components/states. A deployed basket should have an open annular mouth and ribs; the folded form should collapse toward the central coupling. Exact stow position, hose travel and basket deformation remain authored until matched to clear endpoint references.

## Boom receiver

The MC-130J fact sheet lists UARRSI, tanker pods and EO/IR together. The receiver should therefore be independent of tanker station occupancy. [S06]

The inspected close AC-130J photograph **DVIDS-9074140** shows contact at the dorsal centerline, just above/aft of the cockpit glazing, with pale guide markings. The tanker boom hides the aperture edges. It is useful for location, not a verified door mechanism. The Hurlburt AC-130U maintenance caption confirms that an aerial-refueling door operates, but its image was not accessible. [S12]

**Open/closed receiver-door endpoints and sliding-versus-hinged motion remain NOT_DONE.** A game animation can be tagged illustrative; do not name its chosen motion as operationally verified. This 2025 J image also does not establish an exact circa-2021 W hatch fit.

## Fulton Skyhook geometry

The USAF history *The Praetorian STARShip* describes the Combat Talon yoke as a permanent retractable installation which folds back along the fuselage. The nose radome was redesigned for it, producing the characteristic drooped historical nose. Protective fending lines run from the outer wingtips toward a point near the nose sky-anchor assembly. Cabin recovery equipment can be removed. [S08]

The deployed V spreads **left and right ahead of the nose in plan view**, rather than vertically like antlers. The folded state should therefore sweep rearward along the sides of the nose/fuselage. The publication's illustrations on printed pages 31–32 depict the **earlier C-130A/B fixed tubular installation**: they establish family layout, not an exact MC-130E nose mount or truss design. The nearby text, rather than those older trusses, establishes Talon foldback behavior.

Saved page views:

- `fulton-history-printed31-family-diagram.png`: older A/B external plan/front/side layout, explicitly marked as family context.
- `fulton-history-printed32-foldback-evidence.png`: older A/B internal diagram plus the relevant Combat Talon retractable/foldback description.
- `fulton-history-printed424-nose-removal.png`: USAF-credited retirement photograph with nose equipment being removed; not an endpoint pair.

**Exact MC-130E deployed/stowed photographic endpoints, pivot placement and hinge travel remain NOT_DONE.** Several public archive image hosts returned errors. An inspected balloon display photograph was rejected as yoke geometry evidence because it contains no installed aircraft yoke. Do not let the existence of that photograph imply that endpoint validation is complete.

## JATO and skis

The inspected **DVIDS-7304591** photograph shows a historical LC-130 with four-blade propellers, ski landing gear and a bank of JATO bottles along the fuselage aft of the main gear fairing. Flames and stirred snow establish the visual effect, not a calibrated thrust model.

A 2022 Air Force/109th report describes later engine and NP2000 upgrades and the end of JATO production in 1991. Its 2003 photograph should not become an undocumented modern fleet preset. [S10, S11]

Model separate brackets, loaded bottles and spent/removed appearances. Flame/smoke animation, bottle-state timing and reset are authored game behavior. No operational performance or real launch procedure is claimed.

## What remains to accept

The documentary/visual references are ready for authoring. The following are still distinct acceptance tasks:

1. Compare the implemented closed ramp and all installed/blank panel states against the references and the actual shared airframe.
2. Verify that individual station choices remove every conflicting panel, interior part and attachment, including left/right tanker-pylon occupancy.
3. Acquire exact Fulton deployed/stowed endpoints, receiver-door endpoints, and clear high/low-speed basket profiles before claiming those motions or shapes are photographically matched.
4. Keep a coherent variant/era preset separate from a custom game mixture. This is asset data behavior, not a claim about real aircraft interchangeability.

## Primary sources

The machine-readable ledger carries complete image URLs, dates, credits, SHA-256 hashes, observations and limitations. Images are public DVIDS previews unless stated as page renders from the USAF history. The JATO photograph has a specific courtesy credit to Dr. Todd Valentic which must be retained.

- **S01:** [Air Mobility Command — C-130 Hercules](https://www.amc.af.mil/About-Us/Fact-Sheets/Display/Article/2848932/c-130-hercules/). Some dimension conversions on the fact sheet appear erroneous; do not use them as a precision ruler.
- **S02:** [USAF/DVIDS — AC-130W Stinger II, 17 December 2020](https://www.dvidshub.net/news/385195/jtf-quartz-weapon-system-ac-130w-stinger-ii).
- **S03:** [USAF — AC-130J Ghostrider](https://www.af.mil/About-Us/Fact-Sheets/Display/Article/467756/ac-130j-ghostrider/).
- **S04:** [NAVAIR — C/KC-130 Hercules/Super Hercules](https://www.navair.navy.mil/product/CKC-130-Hercules-Super-Hercules).
- **S05:** [NAVAIR — historical Harvest HAWK installation, 23 February 2012](https://www.navair.navy.mil/node/18671).
- **S06:** [193rd SOW — MC-130J Commando II](https://www.193sow.ang.af.mil/About-Us/Fact-Sheets/Display/Article/1062881/mc-130j-commando-ii/).
- **S07:** [Hurlburt Field — MC-130E Combat Talon I](https://www.hurlburt.af.mil/About-Us/Fact-Sheets/Fact-Sheets/Article/495225/mc-130e-combat-talon-i/).
- **S08:** [Jerry L. Thigpen, Air University Press — The Praetorian STARShip, 2001](https://www.govinfo.gov/content/pkg/GOVPUB-D301-PURL-LPS20515/pdf/GOVPUB-D301-PURL-LPS20515.pdf), printed pages 31–33 and 424; PDF pages 60–62 and 447.
- **S09:** [Air Force Test Center — historical Fulton recovery milestone](https://www.aftc.af.mil/About-Us/History/On-This-Day-in-Test-History/Article-Display-Test-History/Article/2555277/may-3-1966-fulton-recovery-system-also-passed-an-important-milestone-when-the-f/).
- **S10:** [109th Airlift Wing/DVIDS — new engine testing, 20 October 2022](https://www.dvidshub.net/news/431703/109th-airlift-wing-aircrew-tests-new-engine).
- **S11:** [USAF — LC-130 modernization, 2022](https://www.af.mil/News/Article-Display/Article/2969577/empowered-airmen-from-109th-aw-modernize-lc-130-for-future-fight/).
- **S12:** [Hurlburt Field — 4th AMU Night MX gallery, 23 October 2013](https://www.hurlburt.af.mil/News/Photos/igpage/48/igsort/Title/?igsearch=force+support), caption-only evidence of AC-130U receiver-door operation.
