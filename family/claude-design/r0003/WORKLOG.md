# r0003 work record — 2026-10-29

Author: claude-design. Parent revision r0002, commit
`e9021ef629be8bb8afb096883d63186afae9dce8`.

## Request and disposition

The user challenged the accuracy of the side-mounted systems, requested
actuation, visible case ejection and firing, and asked for realistic appearance
and independent Sketchfab systems. The inherited gun proxies did not establish
reference accuracy. This revision replaces them with independently authored,
photo-guided visual components and explicit limits.

## Evidence and implementation

Inspected dated DVIDS imagery of the exterior and interior systems, real
internal case collection, earlier 105 mm mounts, and NAVSEA's announced 2022
installation change. Queried actual Sketchfab listing metadata and inspected
candidate previews. No third-party mesh was acquired or incorporated.

Created three independent packages: GAU-23-family 30 mm, earlier aircraft
105 mm, and representative MX-20-family EO/IR. Each has original source,
materials, actual clips, a control sidecar, a native editable scene and a
portable inspector. Assembled the same definitions into AC-130W/J and retained
the r0002 transport byte-for-byte.

Implemented visual articulation, recoil, short soft flash/smoke, empty-case
motion into internal collection spaces, and bounded review-cycle cleanup.
The viewer supports individual controls, firing, Actuate everything, Pause,
Reverse and Reset. Authored timings and motion remain illustrative.

## Defects caught and repaired

The review found an inward-facing case bag, partial burial of the 105 mm seal,
a blocked initial case-exit representation, a faceted solid flash, and later
105 mm case/base interpenetration. Corrected winding, sampled the actual skin
for interface fit, opened cavities and moved the illustrative cover, replaced
solid flash geometry with soft textured cards, and moved the falling case
clear of the tested base. Current reports bind the final output hashes.

The last matched exterior review also found the lowered 30 mm support
protruding below the aperture. Its base and two feet were moved inside the
measured retained skin. All 72 unique exported base/support vertices are
inside the source envelope, and the refreshed exterior view shows the stray
bar is gone. Existing case-route checks still pass.

Native clip evaluation also required selecting Blender 4.5 action slots
explicitly. Unmuting NLA alone did not establish motion. The final native
checks evaluate actual mesh movement, save/reopen the scene and retain actions.

## Delivery boundary

No browser automation was used, respecting the user's earlier instruction.
Native Unreal import/cook/runtime, photorealistic finish, exact installation
fit, continuous combined-motion clearance, and gameplay/damage/performance
remain unaccepted. Reports state the scope of every PASS. Older candidate
outputs are excluded from the delivered revision; two labelled r0002 images
remain as comparison evidence.

The final manifest and checksums identify exact review files. GitHub
preservation restores those bytes without rerunning model generation.
