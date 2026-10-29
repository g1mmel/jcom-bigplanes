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

