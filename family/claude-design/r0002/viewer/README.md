# C-130 family review viewer

Author: claude-design. Revision: r0002.

The viewer loads the **actual current GLBs** from `../models/` and drives their embedded node-animation clips through the corresponding files in `../articulation/`. It does not construct substitute aircraft geometry.

## Open

The generated `C130-family-portable.html` embeds all three models, their mechanism data, and the pinned Three.js runtime. Open that file directly. No network connection or local server is required.

For the normal folder version, run this command **from the revision directory**:

```sh
python -m http.server 8000
```

Then open `http://localhost:8000/viewer/`. Opening `index.html` through `file://` can be blocked by browser module and fetch policies; use the portable file for direct opening.

## Controls

- **ASSET** selects the current C-130, legacy AC-130, or AC-130J candidate export.
- **PARKED / SERVICE / FLYING** select authored presentation presets. FLYING is a mechanism configuration, not a flight-dynamics simulation.
- **WIREFRAME / X-RAY / SURFACE** inspect mesh topology, internal geometry, and preserved materials. Triangle counts are computed from the loaded meshes.
- **Actuate everything** covers every exported control. Compatible mechanisms run concurrently; cargo/personnel access and standalone gear doors close before propulsion and gear retraction.
- **Pause** freezes finite motion and continuous propeller phases. **Reverse** follows the demonstration in reverse order. **Reset** restores canonical rest and clears continuous phases.
- Individual mechanism sliders use normalized 0–1 clip time. Gear master clips contain their own staged door motion; standalone door controls are deferred while a gear master owns those transforms.
- Hero, side, front, top, doors, and ramp cameras retain ordinary orbit/pan/zoom navigation.

## Rebuild the portable file

After updating both models and articulation:

```sh
python viewer/build-portable.py
```

This writes `viewer/C130-family-portable.html` and its exact model hashes in `viewer/portable-manifest.json`.

## Verification boundary

`node viewer/test-controller.mjs` tests scheduling, full control coverage, pause, reverse, reset, and interlocks. The separate actual-model test loads exported GLBs and checks their clip bindings and transformed geometry. These tests do not substitute for visually observed browser rendering, collision-free motion, photographic acceptance, or native Unreal import/cook/runtime validation. Consult the revision QA reports for completed and unrun gates.

Three.js **0.170.0** is bundled locally under its MIT license. Official npm tarball SHA-512 integrity was checked at download; `vendor/PROVENANCE.json` records the source and local file hashes. No CDN is used at runtime.
