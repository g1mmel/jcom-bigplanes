# Unreal handoff — r0003 systems

claude-design / cg46. **Native Unreal import, cook and runtime: NOT_RUN.**

The exports are glTF 2.0 rigid-node hierarchies with animation clips and
self-contained materials. They are not native `.uasset` files and contain
no skeletal skins. Import using a tested route that preserves hierarchy and
rigid transform tracks, or bake the independent rigid parts to the target
project's supported skeletal/Blueprint arrangement. Do not treat static-mesh
import alone as animation acceptance.

## Frames and bindings

- glTF: metres, +Y up, +X right, aircraft nose −Z.
- Blender imported scene: metres, +Z up, +X right, aircraft nose +Y.
- Intended UE mapping from glTF: `UE centimetres = (-Z, X, Y) * 100`.
  Check the port gun and a moving asymmetric part after import.
- Component gun visual axis is −X. Sensor optics default to −Z. Install the
  systems using the assembly transform; do not rotate internal clip tracks
  independently. The port optical instance has an explicit +90° Y placement.

Use adjacent articulation files as the binding inventory. Firing controls
own their recoil track; the manual recoil inspection must not write that
transform simultaneously. All gun effects originate at named muzzle sockets.
Spent-case roots have a distinct literal `level 1` identity and stay inside
the aircraft in the review animation.

## Effects and case lifecycle

The portable viewer plays normalized authored clips, including flash/smoke
geometry and an actual case mesh. For UE, replace or bind the visual FX to
the project's Niagara/material convention while keeping muzzle attachment
and deterministic presentation events. Material/effect changes need native
inspection: core glTF alpha cards are not a complete Niagara implementation.

The case is hidden at rest, appears at an internal exit, moves to its
receiving space and is consumed after the preview. Reset restores one
hidden representation. There is no ammunition inventory, gameplay reload,
ballistics, aiming, targeting or damage consumer in this package.

## Acceptance remaining in the project

1. Import/reopen in the actual target UE version; verify scale and axes.
2. Verify each rigid hierarchy, clip, material, embedded/exported map and socket.
3. Inspect individual and combined motion, including reverse/interruption,
   cases, mounted systems and neighboring skin in the native renderer.
4. Implement project collision, LOD, damage, event/state replication and
   gameplay bindings through the authoritative shared catalog.
5. Cook and run the actual packaged project, then record performance and
   visual acceptance against the corresponding artifact hashes.

Exact real mechanism travel, full photographic matching, the inherited
airframe's license, and photorealistic finish remain unresolved separately.
