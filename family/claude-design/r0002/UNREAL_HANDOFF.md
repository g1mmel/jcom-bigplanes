# Unreal handoff — native validation not run

This revision has no connected Unreal Editor and no native Unreal acceptance result. The editable Blender and GLB artifacts are suitable inputs for integration work; they are not tested `.uasset` files.

## Asset contract

- GLB units are metres; +Y is up, nose is -Z and +X is starboard. Check the importer conversion and measured dimensions in centimetres. Do not apply the metre-to-centimetre factor twice.
- Mechanisms are separate rigid mesh nodes under named parent pivots. The GLBs contain node transform animations and **no skins**. Confirm how the target Interchange pipeline handles this hierarchy and animation. A static-mesh import result does not establish a working rig.
- The named clips are authoritative. Use either their converted animation or a faithful component/sequence implementation, with one driver per property. Do not simultaneously evaluate a fallback pivot driver and the original clip.
- Per-model `articulation/*.json` provides normalized controls, ownership, sequence semantics, authored durations and configuration presets. Gear 0 is down and 1 is retracted. Preserve this convention.
- `houseTint` is an independent material region. Retain the embedded normal maps and separate glass/rubber/metal materials. Inspect normal-map channel orientation after import.
- Game collision, damage states, detachable gameplay components, LODs, physical simulation and roster registration are not supplied as accepted systems.

## Required native evidence

1. Record engine version, import pipeline/options, source GLB hash, generated asset paths and import warnings.
2. Import all three exact exports. Verify approximately 40.41 m span and 29.79 m length against the revision's exact bounds and project dimension rows. Inspect port/starboard, ground contact, normals, materials, transparencies, hierarchy and local pivots.
3. Establish the target animation representation. If a rigid component hierarchy is retained, bind the exact clips to corresponding nodes. If converted to a skeleton, create and verify a deliberate rigid skinning/animation derivative from the editable source and record its new hashes.
4. Exercise every control at rest, intermediate samples and endpoint; reverse from an interrupted state, pause, then reset. Check ownership so master gear/cargo sequences and inspection controls never compete.
5. Inspect door, ramp, gear, nacelle/propeller and mission-module clearances. Compare the same states with `qa/viewer-poses-*.json` and the Blender evidence images.
6. Build collision and LOD/damage integration appropriate to the project, then run the packaged/cooked game. Measure actual performance with the expected scene population.
7. Save the native results, screenshots and exact cooked source revision before changing the gate from `NOT_RUN`.

## Official import references

Consult the documentation for the **actual installed engine version**. These official pages were checked during this revision:

- [Importing assets using Interchange](https://dev.epicgames.com/documentation/unreal-engine/importing-assets-using-interchange-in-unreal-engine): pipeline stacks, Import Into Level and Python integration. The documentation distinguishes editor imports from the example runtime Blueprint import, which has its own animation limitations.
- [Interchange import reference](https://dev.epicgames.com/documentation/unreal-engine/interchange-import-reference-in-unreal-engine): hierarchy/mesh options, animation tracks, materials and normal-map handling.

Neither page establishes that this particular rigid-node package has passed a target-engine import. This remains a native integration gate.
