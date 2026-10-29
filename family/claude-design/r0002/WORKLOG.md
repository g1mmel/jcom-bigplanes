# claude-design C-130 family r0002 — work checkpoint

Author: claude-design (ChatGPT, GPT-6 Astra Pro)
Observed UTC: 2026-10-29 02:15:00 UTC
Parent repository: g1mmel/jcom-bigplanes
Parent revision: family/r0001 at 65f83c26c0d03773fc1bc885728d7188a722960f
Working branch: claude-design/c130-modular-r0002-20261028

## Authorized request
The owner said "do it" after the proposed plan to preserve r0001, correct scale/basis and mechanism pivots, implement smooth controls and motion, separate legacy/J configurations, replace mission proxies with modular installations, and validate each generated variant.

## Scope and preservation
- Continue the original C-130 geometry; do not replace it with a generic aircraft.
- Three configurations: C-130 legacy; AC-130W Stinger II (2021 reference configuration, selected to make the previous generic legacy gunship explicit); AC-130J Ghostrider candidate.
- Write only family/claude-design/r0002/ in this proposal. Preserve all r0001 and original source bytes.
- Do not claim cg11 chat identity. cg11 is source lineage, not this continuation's verified registration.
- Preserve the source README's exclusion from Crowd asset migration.
- This checkpoint records intent, not delivered or accepted assets.

## Intended outputs
Editable/reproducible source, three animated GLBs, explicit per-model articulation, shared component/variant data, local and portable viewer, original-output previews, reference ledger, independent checks, native-engine handoff and revision notes.

## Verification boundary
Prior hosted r0001 files were downloaded and rehashed successfully. Their animations were absent; shared parts and placeholder equipment need work. Native Unreal is not connected and acceptance cannot be claimed. Investigating local Blender availability. Photographic acceptance and source licensing remain open until supported.

## Next action
Correct the shared geometry basis and pivots; implement actual controls and clips; assemble variant-specific modules; inspect exports and restore the exact committed bytes.

## claude-design milestone: authoring and review tools
- Confirmed the immutable source branch still points to 65f83c26c0d03773fc1bc885728d7188a722960f.
- Recovered the architecture, repository and unit standards directly from their authorized GitHub repositories after the Pages hub returned HTTP 403. Follow units OD-01 (-Z forward), OD-05 (one-way clips; gear0 down/1 retracted), OD-06 (uncompressed PNG/JPEG masters), OD-08 (actuator metadata) and OD-16 (Unreal metre/cm conversion).
- Installed official Blender 4.5.15 LTS in task scratch, verified its published archive SHA-256, and successfully imported the preserved original model natively. This does not yet validate the new revision.
- Recovered the source's detailed bounded cargo interior and separate door/ramp/wheel parts for reuse.
- Authored a local-vendor Three.js viewer, deterministic mechanism controller and native Blender review script. Viewer model-specific checks await the new exports; browser/WebGL rendering is not claimed.
- Selected AC-130W Stinger II circa2021 for the generic legacy-gunship slot. This is a new explicit review configuration, not a change to any AC-130U roster binding.


## claude-design milestone: exact-byte delivery route
- The GitHub connector rejected a complete model-sized blob request at the transport layer. No asset was replaced by that attempt.
- Added a branch-scoped preservation workflow and hash-checking restore script. This is the one infrastructure addition outside r0002; it exists only to transfer and preserve the already-generated files. It does not execute the model builder or renderer.
- The restore process checks every transport chunk, the complete archive and the delivered file manifest, preserves a workflow artifact before the final push, and fetches/rebases before a non-forced push.
- Independent review caught and repaired invalid empty node children, tangent handedness, local ramp/cabin pockets, and a nose-hatch hinge fitted to the curved source edge. Current reports and final hashes supersede historical intermediate failures.


## claude-design milestone: final articulated review package
- Frozen final assembled candidates: C-130H legacy transport, AC-130W Stinger II circa 2021, and AC-130J Ghostrider. The original r0001 and original source files remain unchanged.
- Final GLB SHA-256 values: c130 `7bfc25e94d4b99900db6f25fa731bc867111dd5debb3a763aa7b619ee86b4146`; ac130 `7b50ca7a5eb910f471fff2d4d411e25a55a0047405bbecc55458e25090f45046`; ac130j `b3ab255efe8de3668dd0c07b4e215b485ca316c8a09ed0863771b8376be90a62`.
- Exact full-record indexing reduced the articulated exports by 42–44%. Independent comparison confirmed all expanded triangle attributes/order, hierarchy, animation values, embedded maps and materials were preserved. Prior representations are retained separately for audit, excluded from the delivery revision.
- Final Khronos validation reports zero errors and warnings for all three. Actual Three.js loader/controller tests exercise 27/36/36 controls, pause, interrupted reverse and exact reset.
- Blender 4.5.15 LTS imported every final GLB, evaluated every actual imported clip at seven samples, saved packed editable files and reopened them successfully. Thirty-nine final native renders show parked, service, flying and mid-demonstration states.
- Root and independent QA inspected final flying undersides and cargo views. Large exposed main-well rectangles are gone; nose/main closures and retained cabin/ramp pass scoped draft review. Perimeter seams, declared hinge-interface contacts and unmeasured travel remain limitations.
- A final image-integrity pass caught one truncated J service-hero PNG after its original render. That single image was regenerated in an isolated revision from unchanged model/controller inputs, visually inspected and recorded in qa/preview-repair-receipt.json. Every delivered preview decodes and matches its native report hash.
- Acceptance stays DRAFT_ARTICULATED_REVIEW. Browser/WebGL, native Unreal import/cook/runtime, exact photographic fit, full continuous clearance, source licensing and gameplay/LOD/performance acceptance remain open.
- The exact-byte transport archive contains the frozen reviewed outputs and evidence. Its restoration process verifies every chunk, the archive, manifest and individual file checksums; it never regenerates aircraft geometry or renders.
