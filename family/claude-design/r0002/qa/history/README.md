# Superseded QA evidence

Each historical report records the exact model hash it tested. A historical failure documents development evidence; it does not describe the current bytes automatically. Conversely, an earlier pass cannot validate a changed export. Current reports sit one directory above and must match the model hashes.

| Generation | C-130 hash prefix | Findings retained |
|---|---|---|
| First provisional export | `50050a58` | Empty leaf `children` arrays, invalid tangent handedness, cargo-ramp/cabin crossings and nose-cover/skin crossings. |
| Second export | `fdb8e542` | Format corrections passed; nose forward-hatch hinges, ramp corner and main-cover end contacts still required repair; gunship sensor pole degenerates remained. |
| Third export | `2208d13d` | Substantial contact reductions; final local lip/flange contacts and one float32-degenerate fuselage sliver identified. Numerical seam contact was distinguished from larger crossings. |
| Fourth export | `3c3b4125` | Format and independent clip sampling passed; sampled crossings above the scoped tolerance were cleared outside declared hinge regions. Native FLYING views then revealed incomplete gear-well closure, independently quantified by projection. |
| Fifth C-130-only fit | `5243faf1` | Improved nose coverage, but first-hit well depth exposed main receiver protrusion; restored inner skin interfered with retracted main wheels. Gear-only report isolates this regression. |
| Sixth C-130-only fit | `8ef71494` | Original nose panel replaces the added bridge; main fairing and receiver corrected. A targeted .95 sample found remaining nose-panel path contact. |
| Seventh / final geometry | `45f44c49` | All named pair-state checks passed the scoped tolerance. W/J geometry was propagated and verified; current indexed files preserve these expanded triangles and animation data exactly. |

The incident ledger tracks the attempted fixes and their actual exported-byte verification. `gear_closure_projected_coverage.json` addresses a separate visual endpoint condition that a zero triangle-crossing count cannot establish.

`pre_indexing.sampled_surface_crossings.json` is the executed final-geometry report. Current indexed hashes are linked through the independent exact-indexing proof one directory above. Full temporary pre-index GLB copies are retained outside this delivered revision; compact reports retain the exact hashes and fingerprints.
