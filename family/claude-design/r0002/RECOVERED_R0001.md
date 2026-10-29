# Preserved r0001 outputs

Original review head: `65f83c26c0d03773fc1bc885728d7188a722960f`, October 27, 2026. Original generation run: [40579808570](https://github.com/g1mmel/jcom-bigplanes/actions/runs/40579808570), source commit `675a878881395416b5577edcbe47a6acd041d532`.

The original workflow generated and structurally checked the models and rendered previews. Its final push failed because the remote branch had advanced. The current workflow already contains fetch/rebase handling, so that historical failure was not treated as evidence of a still-unfixed push defect.

| Preserved file | Exact bytes | SHA-256 |
|---|---:|---|
| [C-130 Hercules GLB](https://raw.githubusercontent.com/g1mmel/jcom-bigplanes/65f83c26c0d03773fc1bc885728d7188a722960f/family/r0001/c130-hercules-unified-r0001.glb) | 9,823,080 | `ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12` |
| [AC-130 Hercules GLB](https://raw.githubusercontent.com/g1mmel/jcom-bigplanes/65f83c26c0d03773fc1bc885728d7188a722960f/family/r0001/ac130-hercules-unified-r0001.glb) | 9,826,580 | `101c7032fa67481bcefe4e32423f11fb2bb676eb0605fbf529df9694ebee7723` |
| [AC-130J candidate GLB](https://raw.githubusercontent.com/g1mmel/jcom-bigplanes/65f83c26c0d03773fc1bc885728d7188a722960f/family/r0001/ac130j-ghostrider-unified-r0001.glb) | 9,862,284 | `38f596b9f6ffcfa7d77bf77da97bc3c17c321664e62b27875861c2cecb33af6b` |

[Original manifest](https://github.com/g1mmel/jcom-bigplanes/blob/65f83c26c0d03773fc1bc885728d7188a722960f/family/r0001/manifest.json) · [All 13 original previews](https://github.com/g1mmel/jcom-bigplanes/tree/65f83c26c0d03773fc1bc885728d7188a722960f/family/r0001/previews).

During the recovery audit, all three hosted GLBs were downloaded and independently rehashed to the values above. Their binary contents contained zero animation clips and zero skins. All derived from the same 24-mesh source; the gunships added mission kit nodes. Legacy pivots and the scene basis required correction before meaningful motion.

The original manifest remains `DRAFT_UNVALIDATED` / `DRAFT_NOT_PHOTO_ACCEPTED`. No photographic, native Blender/Unreal or rig-motion acceptance is retroactively granted to r0001. All r0002 validation belongs only to its own exact file hashes. The original bytes remain unchanged and available for recovery.
