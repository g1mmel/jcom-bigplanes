# C-130 family and independent systems review viewer

Author: claude-design. Revision: r0003.

The viewer loads the actual GLB exports and drives their embedded node animation clips using each model's adjacent articulation data. The separate gun and sensor entries load independent component files; they do not require an aircraft to exist in the scene.

## Open

`C130-family-portable.html` embeds the three aircraft, three independent visual systems, their controls, and the pinned Three.js runtime. Open it directly in a browser supporting WebGL2 and gzip `DecompressionStream`. No network request or local server is required to load the embedded models. Model checksums are verified on browsers that expose the Web Crypto API.

The folder viewer loads aircraft from `../models/` and components from `../components/<id>/model.glb`. From the revision directory, run `python -m http.server 8000`, then open `http://localhost:8000/viewer/`. The folder version uses normal module and fetch requests; the portable version supports opening a downloaded HTML file directly.

## Firing and internal cases

- **Fire 30 mm burst** plays three authored visual cycles. **Fire 105 mm shot** plays one cycle. These are presentation timings, not measured operating rates.
- A cycle drives the actual exported recoil, spent-case, and muzzle-effect tracks. Case movement belongs inside the aircraft. The 30 mm system has a collection bag; the 105 mm system has an internal collection area.
- **30 mm close-up / 105 mm close-up** show the exterior installations. **30 mm cases / 105 mm cases** move inside and use X-RAY to expose the cabin while keeping the systems opaque.
- The normalised firing-cycle sliders inspect a particular moment. Manual recoil inspection and a firing cycle cannot own the same transform simultaneously.
- **Pause** freezes firing and other motion. **Reverse** reverses the firing presentation from its current phase, including an interrupted burst. **Reset** clears every firing instance and restores the canonical rest state.
- The 30 mm and 105 mm presentation can run together. Moving an unrelated sensor control does not freeze active case movement. Selecting manual recoil cancels only that system's firing cycle.

## Other controls

**ASSET** includes C-130H, circa-2021 AC-130W, AC-130J, independent 30 mm, independent 105 mm, and independent EO/IR entries. The independent components are visual approximations with evidence and limits recorded in their packages.

**PARKED / SERVICE / FLYING** retain the aircraft presets. FLYING configures mechanisms; it does not simulate flight dynamics. **WIREFRAME / X-RAY / SURFACE** inspect topology, interiors, and materials. The wireframe depth-tests its lines against the surface. X-RAY keeps gun and sensor components opaque for inspection.

**Actuate everything** covers every declared control, including the firing cycles. Compatible mechanisms run concurrently. Cargo/personnel access and standalone gear doors close before propulsion and gear retraction. Dedicated inspection controls and master clips arbitrate ownership. Individual sliders use normalized 0–1 clip time.

Hero, side, front, top, doors, ramp, and system close-up cameras retain orbit, pan, and zoom. Component hero views fit their actual exported bounds.

## Rebuild

After updating models and articulation:

```sh
python viewer/build-portable.py
```

For a component-only portable file with no embedded aircraft:

```sh
python viewer/build-portable.py --component gau23-visual
```

The component IDs are `gau23-visual`, `m102-airborne-visual`, and `eoir-visual`. `--output /absolute/path/output.html` selects a destination. `--aircraft-only` builds a three-aircraft bundle for diagnosis.

## Verification boundary

The scheduling tests are:

```sh
node viewer/test-controller.mjs
node viewer/test-firing.mjs
```

Actual GLB scene, clip, and transform validation uses:

```sh
node --loader ./viewer/node-module-loader.mjs viewer/test-models.mjs
node --experimental-vm-modules viewer/verify-portable.mjs
```

The Node loader tests deliberately stub image decoding. They verify animation/scene bindings and matrix movement, not texture appearance, GPU rendering, swept clearance, photographs, or native Unreal. The portable test checks embedded dependency closure and exact decompressed model hashes. Browser rendering remains NOT_RUN unless a separate observed browser report says otherwise.

Three.js 0.170.0 is bundled under the MIT license. `vendor/PROVENANCE.json` records its source and local hashes. No CDN is used at runtime.
