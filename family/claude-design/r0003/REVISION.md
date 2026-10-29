# C-130 family r0003 — gunship systems and visual firing

Author: claude-design · ChatGPT / GPT-6 Astra Pro · Crowd context code cg46.

Parent: `e9021ef629be8bb8afb096883d63186afae9dce8`, `family/claude-design/r0002`.

Status: **DRAFT_SYSTEMS_VISUAL_REVIEW**. This revision implements inspectable
game visuals and animation. It does not establish photographic acceptance,
real weapon operation, or native Unreal acceptance.

## What was corrected

The previous r0002 guns were expressly approximate tube/cradle proxies. Their
animation tests did not prove that their appearance or operation matched a
real installation. This revision replaces those provisional systems with
original, independently reusable models guided by the inspected DVIDS photos.

- **30 mm system:** one barrel, an actual vented muzzle sleeve, dark draped
  aperture seal, fitting ring and fasteners. The inboard receiver, curved feed
  guide representations, real downward case-exit cavity and open collection
  bag remain inside the aircraft. The support plate is below the bag.
- **105 mm system:** earlier aircraft-mounted tube/cradle, raised collars,
  inner spring-like details, yellow guard rails, actual recessed case exit,
  a reversible illustrative exit cover, and an internal receiving tray.
- **Mounting interface:** real circular openings cut through retained outer
  skin and cabin lining; the flexible seal, ring and fasteners conform to 72
  sampled positions around the inherited fuselage/door skin. The receiving
  space is the existing bounded cabin, not a sealed black box.
- **EO/IR:** separate fixed cap, yaw yoke and pitch housing; four actual
  recessed optical openings with differentiated materials and retaining rings.
- **Materials:** distinct dark coated metal, exposed metal, flexible seal,
  fabric, brass, painted rails and optics. Original analytic micro-roughness
  maps are packed in the gun exports. These are not photographic texture bakes.

## What the firing controls demonstrate

`Fire 30 mm burst` runs three authored visual cycles; `Fire 105 mm shot` runs
one. Each cycle drives actual recoil geometry, a short muzzle flash, a soft
smoke effect and a separately modeled **empty case**. Cases appear at an
internal exit and move into the cabin collection region. The 30 mm system
uses a bag. The larger case is represented in an illustrative internal tray.

Pause freezes the presentation. Reverse retraces the preview. Reset clears
cases/effects and restores the canonical pose. These are review controls,
not gameplay reload, ammunition, fire-control, targeting or ballistic logic.
The existing aircraft controls and global Actuate everything remain available.

The 105 mm exit-cover motion is a simplified visual device. Exact breech,
crew loading/catching motions and operating cadence are not reproduced or
accepted. All motion extents and timings are artist-authored presentation.

## Independent systems

Each `components/<id>/` directory contains a self-contained animated GLB,
adjacent articulation, independently editable Python source, an offline
inspector, native Blender source after review, texture exports and a manifest.

| Component ID | Purpose | Native clips |
|---|---|---:|
| `gau23-visual` | GAU-23-family representative aircraft 30 mm system | 4 |
| `m102-airborne-visual` | Earlier 105 mm aircraft installation, M102/M137A1 family reference | 4 |
| `eoir-visual` | MX-20-family representative optical gimbal | 2 |

The independent canonical systems have no aircraft mesh or texture dependency.
Installation-specific conforming seals belong to the aircraft assembly. The
two aircraft use the same authored system definitions, with a bag-material
override for the J. This is software asset modularity, not a claim that real
aircraft can be converted by swapping a few panels.

## Assumptions

1. The AC-130W and AC-130J review configurations use the **circa-2021 earlier
   gun installation**. NAVSEA announced a replacement 105 mm Gun Aircraft
   Unit in January 2022; that upgrade is a separate future configuration.
2. The retained source airframe and its inherited approximate envelope remain
   the authoring baseline. This task does not certify that silhouette or exact
   station coordinates. The ring fit is measured against our mesh, not real
   aircraft engineering drawings.
3. The EO/IR module represents an MX-20-family exterior. Exact J sensor type
   and slot/block fit remain unresolved; evidence mentions MX-20/MX-25.
4. Real photographs support internal case handling. The tray, collection path,
   decorative feed guides, shortened mechanism cycle, and operating travel are
   illustrative. No cases are depicted spraying into the air outside the plane.
5. No Sketchfab mesh was incorporated. The plausible M102 donor is a ground
   carriage model and its official download requires authentication. The closer
   aircraft-style 105 mm listing is display-only. See the acquisition ledger.

## Validation and limits

Current machine reports identify their exact input hashes. The QA summary
distinguishes glTF conformance, Three.js CPU animation, sampled physical case
geometry, standalone source rebuild and native Blender checks. A loader test
does not prove a visual match. An inboard-plane case check does not establish
all cabin collisions. Native Blender rendering does not establish browser or
Unreal behavior.

Photographic acceptance, continuous combined-motion clearance, precise
105 mm muzzle contour, inherited door-panel contour, exact sensor fit,
photorealistic finish, gameplay, damage, LOD/performance and native Unreal
remain open. The inherited original airframe's licensing provenance still
requires review. New independently authored systems contain no third-party
model geometry.

## Preservation

Original r0001 and r0002 assets are unchanged. The transport `c130.glb` in this
package is the byte-identical r0002 transport, SHA-256
`7bfc25e94d4b99900db6f25fa731bc867111dd5debb3a763aa7b619ee86b4146`.
The two gunships and the three standalone systems are the new r0003 outputs.
Exact final file hashes are in `manifest.json` and `SHA256SUMS.txt`.

## Reference anchors

- [30 mm exterior](https://www.dvidshub.net/image/6427944/ac-130j-crew-maintain-proficiency-combat-readiness)
- [W interior case ejection](https://www.dvidshub.net/image/3486265/live-fire-training-with-ac-130w)
- [Earlier J interior case ejection](https://www.dvidshub.net/image/3146917/angry-annie-fires-first-rounds)
- [105 mm recoil and earlier guard](https://www.dvidshub.net/image/3486262/live-fire-training-with-ac-130w)
- [105 mm cases handled inside](https://www.dvidshub.net/image/6427973/ac-130j-crew-maintain-proficiency-combat-readiness)
- [2022 installation change](https://www.navsea.navy.mil/Media/News/Article/2895381/nswc-dahlgren-engineers-deliver-upgraded-gun-aircraft-unit-for-the-warfighters/)

See `references/gunship-visual/reference-ledger.json` for the individual
photos, credits, dates, observations, permitted copies and limitations.
