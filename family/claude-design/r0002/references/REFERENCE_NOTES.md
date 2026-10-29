# C-130 family r0002: reference decisions and gaps

Research date: 2026-10-29. Scope: visual game assets and authored articulation. This dossier does not establish aircraft engineering accuracy, operational weapon behavior, or production acceptance. `REFERENCE_LEDGER.json` records per-claim evidence, inspected-image hashes and limits. Reference photos were inspected from official public pages; the photos are not redistributed in this package.

## Concrete configurations

| Candidate | Reference identity | Evidence and consequence |
|---|---|---|
| `c130` | C-130H Hercules, legacy four-blade reference configuration | Use the preserved source as the common geometric baseline. The particular original source aircraft, author and license remain unverified. Modern eight-blade legacy upgrades also exist, so four blades must be an explicit configuration rather than a definition of every C-130H. |
| `ac130` | AC-130W Stinger II, late-service equipment identified in the March 2021 USAF factsheet | USAF describes a modified C-130H, T56-A15 propulsion, two EO/IR sensors, and 30 mm plus 105 mm installations. July 2018 official photos support the exterior arrangement. This is a named W candidate, not a generic blend of AC-130H/U/W features. |
| `ac130j` | AC-130J Ghostrider candidate, 2021–2023 exterior reference set | The J has different propulsion and cockpit equipment in addition to the mission installation. A six-blade substitution alone does not establish a faithful J model. Treat nacelle/intake, cockpit, sensor and installation geometry as separate J modules with their own acceptance gaps. |

Sources: [USAF AC-130W factsheet](https://www.hurlburt.af.mil/About-Us/Fact-Sheets/Fact-Sheets/Article/2559094/ac-130w-stinger-ii/), [USAF C-130 factsheet](https://www.amc.af.mil/About-Us/Fact-Sheets/Display/Article/2848932/c-130-hercules/), [USAF AC-130J factsheet](https://www.af.mil/About-Us/Fact-Sheets/Display/Article/467756/ac-130j-ghostrider/).

## Shared model architecture

One source-controlled family master is appropriate. Share verified fuselage, wing, empennage and compatible mechanism geometry, then select explicit configuration modules. Separate cargo/plain panels from actual mission apertures and surrounding installation surfaces. Keep the engine/nacelle/propeller assembly and cockpit equipment configurable independently. Preserve the original revision as a recoverable baseline.

Every assembled export still needs complete geometry, correctly bound nodes, materials and animations. Shared ancestry does not make three variants interchangeable. No panel should hide an intact underlying fuselage wall when opened. Interior bays may be simplified for this candidate, but must have bounded depth and meaningful receiving space.

## Observed visual landmarks supplied to the builder

| Component | Actually inspected evidence | Supported observation | Limit |
|---|---|---|---|
| W chin EO/IR | [DVIDS 4610557](https://www.dvidshub.net/image/4610557/16th-expeditionary-special-operations-squadron-provides-air-support), [4610565](https://www.dvidshub.net/image/4610565/16th-expeditionary-special-operations-squadron-provides-air-support) | Rounded sensor housing beneath the forward radome; individual optical windows are visible. | No exact dimensions, pivot axis or travel range. |
| W second EO/IR | DVIDS 4610565 and [4610532](https://www.dvidshub.net/image/4610532/16th-expeditionary-special-operations-squadron-provides-air-support) | Lower port belly, immediately ahead of main-gear sponson, behind the forward entry stairs. | Relative landmarks; no measured aircraft station. |
| W forward gun station | DVIDS 4610565 and 4610532 | Port installation behind forward crew entry and ahead of wing/main-gear sponson. | Exact aperture profile, mounting geometry and train envelope are not established. |
| W aft gun station | DVIDS 4610532 | Large circular installation on port side aft of the main-gear sponson, near the aft personnel-door station. | A single oblique still cannot establish full assembly depth or movement. |
| J aft installation | [DVIDS 7918482](https://www.dvidshub.net/image/7918482/centcom-ghostriders) | Large aft port installation with a flexible-looking dark surround; visible external barrel and nearby cargo ramp. | Visual shape only. No internal or operating mechanics inferred. |
| J forward installation and propulsion | [DVIDS 6616476](https://www.dvidshub.net/image/6616476/ac-130j-ghostrider-hurlburt-field-supports-joint-mission-fairchild-afb) | Forward port protruding installation; six swept propeller blades; intake below propeller-spinner area. | Perspective and parked covers prevent exact nacelle/intake sizing. |
| H/W cockpit | [DVIDS 4610577](https://www.dvidshub.net/image/4610577/16th-expeditionary-special-operations-squadron-provides-air-support) | Analogue flight-engineer instrument panel in the W reference aircraft. | Does not establish every instrument or a particular H avionics upgrade. |
| J cockpit | [DVIDS 7918484](https://www.dvidshub.net/image/7918484/centcom-ghostriders), [7918479](https://www.dvidshub.net/image/7918479/centcom-ghostriders) | Digital display panels and HUD visible. | Close-up illustrative fit only; no instrument functionality acceptance. |

The J second EO/IR location is still a reference gap in the inspected set. The factsheet establishes two sensors, but an exact mesh placement derived from the W arrangement must remain `inferred`. Do not mistake small defensive sensor windows for the two large EO/IR turrets.

## Motion endpoints and implementation guidance

| Mechanism | Inspected endpoint references | Visual interpretation | Unresolved portion |
|---|---|---|---|
| Lower cargo ramp | [C-130J ground-open 7368321](https://www.dvidshub.net/image/7368321/c-130j-transition-track-guardsmen-prepare-change), [flight-open 7536231](https://www.dvidshub.net/image/7536231/dyess-c-130j-flight), [AC-130J closed 6616471](https://www.dvidshub.net/image/6616471/ac-130j-ghostrider-hurlburt-field-supports-joint-mission-fairchild-afb), [AC-130J open rear 7918477](https://www.dvidshub.net/image/7918477/centcom-ghostriders) | Distinct lower panel hinged at the aft cargo-floor threshold; lowers into a loading platform. Ground and flight states differ. | Hinge coordinates, angular endpoints, actuator linkage, timing and full swept clearance are authored. Family photographs support arrangement, not source-mesh fit. |
| Upper cargo door | The same open rear views plus [9092109](https://www.dvidshub.net/image/9092109/d-day-c-130-media-flight) | Retracts/raises inward beneath aft ceiling; does not open as a second outward clamshell. | Exact guided path and interface with roof/cargo structure remain provisional. |
| Forward crew entry | [W 4610490](https://www.dvidshub.net/image/4610490/16th-expeditionary-special-operations-squadron-provides-air-support), W 4610565 | Port forward entry lowers outward/down into stairs. The opening must reveal actual cabin depth. | Closed contour comes from source geometry; exact ladder links and door angle not measured. |
| Aft personnel/paratroop door | [AC-130J 7135325](https://www.dvidshub.net/image/7135325/balikatan-22-ac-130j-ghostrider-static-display) | Interior view shows door raised overhead into the cabin, with visible upward-lift instruction. | One open-side view; full track path, closed fit and movement sequence require further evidence. Port gunship installation can replace/conflict with this door and must be configured explicitly. |
| Main landing gear | [DVIDS 229267–229272 series](https://www.dvidshub.net/image/229270/c-130-landing-gear-inspection), W 4610565 | Upright tandem tyres/struts move into side wells; hanging covers are visible in down/maintenance states. Official photographs plus original manual text support vertical translation. | Exact travel, door coupling and full clearance not proven by static photographs. |
| Nose landing gear | W 4610565 down state; original USN/USCG manual descriptions available via mirrors | Nose gear folds forward into fuselage; extends down and aft. | No actual motion video or complete stowed-state close-up inspected. Travel and cover timing remain authored. |
| Wing flaps | J 6616471 rear view and [7556670](https://www.dvidshub.net/image/7556670/hurlburt-field-aircraft) port-aft view; W 4610532 | Lowered trailing-edge flap panels and distinct outboard aileron region. | Fowler travel and pivot trajectories are not calibrated. A pure hinge implementation is a simplified authored approximation. |
| Ailerons, elevators, rudder | General external geometry references | Separate moving surfaces are appropriate game components. | No measured travel limits or endpoint series in this dossier. Declared motion is an authored presentation. |
| Propellers and sensor gimbals | W 4610565; J 6616476; W 4610557 | Visible blade counts and broad housing shape. | Motion rates, phase, blade-pitch behavior and sensor angular limits are authored. |

Primary source documents establish overall gear architecture, not game animation timing. The USN and USCG manual copies encountered are hosted on unofficial mirrors and are recorded as corroborating leads rather than official-host photo validation. Do not promote the clip to `REFERENCE_VALIDATED` on their basis alone.

The [mirrored USCG flight-manual text](https://pdfcoffee.com/uscg-lockheed-c-130-flight-manual-2-pdf-free.html) describes retracted landing gear as enclosed by mechanically operated flush doors. This corroborates the required visible closed endpoint: a large uncovered dark well in the FLYING state is a model defect, not a supported configuration choice. The exact closing path, door linkage and surface fit remain authored approximations; a complete stowed-gear close-up and motion sequence have not been independently inspected in this dossier.

## Acceptance remains separate

Reference inspection is not model acceptance. This set is adequate to guide a useful candidate and to reject several incorrect mechanisms, but it does not provide calibrated drawings or every required closed/open/path view. Exact skin continuity, openings, moving-node origins, pose sweeps, shared component signatures and export data require independent checks against the generated bytes. Native Blender and Unreal gates must report what actually ran. Source licensing, photographic acceptance, all-path collision clearance, native Unreal import/cook/runtime and production use remain separate unresolved gates unless evidenced elsewhere in this revision.

Unsuitable retrieved images are marked in the ledger: infographic composites, dark night-vision images, blurred aircraft backgrounds, removed-engine maintenance views and operator close-ups were not treated as calibrated exterior evidence.
