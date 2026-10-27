#!/usr/bin/env python3
"""Spatial node inventory for the original C-130 GLBs; no writes to source files."""
import json
import math
from pathlib import Path

from audit_c130_glb import FILES, load_glb, positions, transform, world_nodes


def main():
    root = Path(__file__).resolve().parents[1]
    for filename in FILES:
        raw, doc, binary = load_glb(root / filename)
        world = world_nodes(doc)
        print("\n=== DETAILED", filename, "===")
        print("MATERIALS:", [(i, m.get("name"), m.get("alphaMode"), m.get("doubleSided")) for i, m in enumerate(doc.get("materials", []))])
        print("TEXTURES:", len(doc.get("textures", [])), "IMAGES:", len(doc.get("images", [])))
        print("ROOTS:", doc.get("scenes", []))
        print("EXTENSIONS:", doc.get("extensionsUsed", []))
        for i, n in enumerate(doc.get("nodes", [])):
            if "mesh" not in n:
                continue
            mesh = doc["meshes"][n["mesh"]]
            lo = [math.inf] * 3
            hi = [-math.inf] * 3
            mats = set()
            for prim in mesh.get("primitives", []):
                mats.add(prim.get("material", -1))
                if "POSITION" not in prim.get("attributes", {}):
                    continue
                for pos in positions(doc, binary, prim["attributes"]["POSITION"]):
                    p = transform(world[i], pos)
                    for k in range(3):
                        lo[k] = min(lo[k], p[k])
                        hi[k] = max(hi[k], p[k])
            if not math.isfinite(lo[0]):
                continue
            center = [(a+b)/2 for a, b in zip(lo, hi)]
            size = [b-a for a, b in zip(lo, hi)]
            print("NODE", i, json.dumps(n.get("name","")),
                  "MESH", n["mesh"],
                  "CENTER", [round(x,2) for x in center],
                  "SIZE", [round(x,2) for x in size],
                  "MATS", sorted(mats))


if __name__ == "__main__":
    main()
