# C-130 family r0003

claude-design · **DRAFT_SYSTEMS_VISUAL_REVIEW**

Extract the family archive into an empty folder, then open
`viewer/C130-family-portable.html` locally. It embeds all three aircraft,
the three independent systems and the pinned viewer libraries. Use the asset
dropdown, Fire 30 mm burst / Fire 105 mm shot, individual controls, and
Actuate everything / Pause / Reverse / Reset. Use X-RAY and internal cameras
to inspect the actual empty cases inside the cabin. Each component also has
its own `inspector.html`, which embeds no aircraft.

The portable viewer requires a browser with WebGL2 and DecompressionStream
support. Programmatic loading and bundle integrity were tested; browser
rendering is explicitly NOT_RUN in this revision.

| Directory | Contents |
|---|---|
| `models` | Two revised gunships and unchanged r0002 C-130H transport |
| `components` | Independent 30 mm, 105 mm and representative EO/IR packages |
| `articulation` | Per-aircraft clip/control, state, effect and camera bindings |
| `editable` | Native Blender imports with retained actions and packed maps |
| `source` | Reproducible original-source family and component generators |
| `viewer` | Local Three.js libraries, review controls and portable inspector |
| `previews` | Actual native-model renders and labelled prior-revision comparisons |
| `references` | Inspected military photo evidence and Sketchfab acquisition audit |
| `qa` | Hash-bound format, geometry, runtime, native and source-isolation evidence |

Read `REVISION.md` for the changes and assumptions. `UNREAL_HANDOFF.md` records
the native-engine work that remains. No production acceptance is implied by
the presence of an export or a PASS in a scoped report.

Keep accepted revisions unchanged. Make follow-up work as a new candidate
revision and leave a dated note identifying source/output hashes, changed
systems, tested scope, unresolved issues and next action.
