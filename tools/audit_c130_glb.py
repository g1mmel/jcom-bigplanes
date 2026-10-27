#!/usr/bin/env python3
"""Inspect the three original Hercules GLBs without changing them.

Standard-library only. Read-only, bounded glTF/GLB structural, node and
geometry audit. Reports are evidence, not photo or airworthiness acceptance.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

FILES = ("c130-hercules.glb", "ac130-hercules.glb", "ac130j-ghostrider.glb")
CATEGORIES = (
    ("refuel_receiver", r"uarrsi|receptacle|receiver|probe|refuel.?door|refuel.?cover"),
    ("tanker_delivery", r"drogue|hose|refuel.?pod|tanker|fuel.?boom"),
    ("armament", r"gun|cannon|howitzer|weapon|pylon|munition|missile|flare|chaff"),
    ("sensor", r"sensor|turret|radar|antenna|camera|eo.?ir|flir|radome"),
    ("fuselage", r"fuselage|hull|body|nose|cockpit|windshield|window|glazing|cabin"),
    ("wing", r"wing|aileron|flap|slat"),
    ("tail", r"tail|rudder|stabiliz|elevator|fin"),
    ("propeller", r"prop|blade|spinner|hub"),
    ("engine", r"engine|nacelle|intake|exhaust"),
    ("landing_gear", r"wheel|gear|tyre|tire|strut|sponson"),
    ("cargo", r"cargo|ramp|paratroop|door|floor|seat|roller"),
)
TYPE_FMT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
TYPE_N = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load_glb(path: Path):
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        raise ValueError(f"{path}: invalid GLB magic")
    version, declared = struct.unpack_from("<II", raw, 4)
    if version != 2 or declared != len(raw):
        raise ValueError(f"{path}: GLB header mismatch")
    chunks = []
    pos = 12
    while pos < len(raw):
        length, kind = struct.unpack_from("<II", raw, pos)
        pos += 8
        if pos + length > len(raw):
            raise ValueError(f"{path}: truncated chunk")
        chunks.append((kind, memoryview(raw)[pos:pos + length]))
        pos += length
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise ValueError(f"{path}: JSON chunk absent")
    doc = json.loads(bytes(chunks[0][1]).rstrip(b"\x00 \t\r\n"))
    bins = [data for kind, data in chunks if kind == 0x004E4942]
    return raw, doc, bins[0] if bins else memoryview(b"")


def matrix_mult(a, b):
    # glTF column-major matrices.
    return [sum(a[k * 4 + r] * b[c * 4 + k] for k in range(4))
            for c in range(4) for r in range(4)]


IDENTITY = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]


def node_matrix(node):
    if "matrix" in node:
        return list(map(float, node["matrix"]))
    x, y, z, w = node.get("rotation", [0., 0., 0., 1.])
    sx, sy, sz = node.get("scale", [1., 1., 1.])
    tx, ty, tz = node.get("translation", [0., 0., 0.])
    rot = [
        1-2*(y*y+z*z), 2*(x*y+z*w), 2*(x*z-y*w), 0.,
        2*(x*y-z*w), 1-2*(x*x+z*z), 2*(y*z+x*w), 0.,
        2*(x*z+y*w), 2*(y*z-x*w), 1-2*(x*x+y*y), 0.,
        tx, ty, tz, 1.,
    ]
    for col, scale in enumerate((sx, sy, sz)):
        for row in range(3):
            rot[col * 4 + row] *= scale
    return rot


def transform(m, p):
    x, y, z = p
    return (
        m[0]*x + m[4]*y + m[8]*z + m[12],
        m[1]*x + m[5]*y + m[9]*z + m[13],
        m[2]*x + m[6]*y + m[10]*z + m[14],
    )


def world_nodes(doc):
    nodes = doc.get("nodes", [])
    children = {j for n in nodes for j in n.get("children", [])}
    scene = doc.get("scenes", [{}])[doc.get("scene", 0)] if doc.get("scenes") else {}
    roots = scene.get("nodes") or [i for i in range(len(nodes)) if i not in children]
    out = {}
    def visit(i, parent, ancestors):
        if i in ancestors:
            raise ValueError(f"node hierarchy cycle at {i}")
        mat = matrix_mult(parent, node_matrix(nodes[i]))
        out[i] = mat
        for child in nodes[i].get("children", []):
            visit(child, mat, ancestors | {i})
    for root in roots:
        visit(root, IDENTITY, set())
    for i in range(len(nodes)):
        if i not in out:
            visit(i, IDENTITY, set())
    return out


def positions(doc, binary, accessor_id):
    accessor = doc["accessors"][accessor_id]
    if accessor["type"] != "VEC3" or accessor["componentType"] != 5126:
        raise ValueError(f"Unsupported POSITION accessor {accessor_id}")
    view = doc["bufferViews"][accessor["bufferView"]]
    if view.get("buffer", 0) != 0:
        raise ValueError("External buffer not supported")
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", 12)
    count = accessor["count"]
    for i in range(count):
        offset = start + i * stride
        if offset + 12 > len(binary):
            raise ValueError("POSITION exceeds BIN chunk")
        yield struct.unpack_from("<fff", binary, offset)


def classify(name):
    for label, pattern in CATEGORIES:
        if re.search(pattern, name, re.I):
            return label
    return "unclassified"


def audit_one(path: Path):
    raw, doc, binary = load_glb(path)
    meshes = doc.get("meshes", [])
    nodes = doc.get("nodes", [])
    mats = world_nodes(doc)
    category_counts = Counter()
    category_triangles = Counter()
    top = []
    total_vertices = total_triangles = 0
    overall_min = [float("inf")] * 3
    overall_max = [float("-inf")] * 3
    exact_geom = []
    warnings = []
    for i, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        mesh_id = node["mesh"]
        mesh = meshes[mesh_id]
        name = node.get("name") or mesh.get("name") or f"mesh_{mesh_id}"
        category = classify(name)
        category_counts[category] += 1
        triangles = vertices = 0
        for primitive in mesh.get("primitives", []):
            attrs = primitive.get("attributes", {})
            if "POSITION" not in attrs:
                continue
            a = doc["accessors"][attrs["POSITION"]]
            vertices += a["count"]
            count = doc["accessors"][primitive["indices"]]["count"] if "indices" in primitive else a["count"]
            mode = primitive.get("mode", 4)
            triangles += count // 3 if mode == 4 else max(0, count - 2) if mode in (5, 6) else 0
            try:
                for p in positions(doc, binary, attrs["POSITION"]):
                    q = transform(mats[i], p)
                    for j in range(3):
                        overall_min[j] = min(overall_min[j], q[j])
                        overall_max[j] = max(overall_max[j], q[j])
            except ValueError as exc:
                warnings.append(f"{name}: {exc}")
            view = doc["bufferViews"][a["bufferView"]]
            start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
            stride = view.get("byteStride", 12)
            if stride == 12 and start + a["count"] * 12 <= len(binary):
                digest = hashlib.sha256(binary[start:start + a["count"] * 12]).hexdigest()[:20]
                exact_geom.append({"node": name, "position_sha256_prefix": digest, "count": a["count"]})
        total_vertices += vertices
        total_triangles += triangles
        category_triangles[category] += triangles
        top.append({"node": name, "category": category, "mesh": mesh_id,
                    "vertices": vertices, "triangles": triangles})
    top.sort(key=lambda x: x["triangles"], reverse=True)
    bounds = {"min": [round(x, 4) for x in overall_min],
              "max": [round(x, 4) for x in overall_max],
              "dimensions": [round(b-a, 4) for a, b in zip(overall_min, overall_max)]}
    return {
        "filename": path.name, "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "asset": doc.get("asset", {}),
        "scene_count": len(doc.get("scenes", [])),
        "node_count": len(nodes), "mesh_count": len(meshes),
        "material_count": len(doc.get("materials", [])),
        "texture_count": len(doc.get("textures", [])),
        "animation_count": len(doc.get("animations", [])),
        "skin_count": len(doc.get("skins", [])),
        "total_node_vertices": total_vertices,
        "total_node_triangles": total_triangles,
        "bounds": bounds,
        "category_mesh_nodes": dict(category_counts),
        "category_triangles": dict(category_triangles),
        "top_meshes": top[:100],
        "node_names": [n.get("name", "") for n in nodes[:500]],
        "exact_position_signatures": exact_geom[:300],
        "warnings": warnings[:100],
    }


def main():
    root = Path(__file__).resolve().parents[1]
    reports = [audit_one(root / name) for name in FILES]
    out = root / "audit"
    out.mkdir(exist_ok=True)
    (out / "c130-originals.json").write_text(json.dumps(reports, indent=2) + "\n")
    for r in reports:
        print("=== " + r["filename"] + " ===")
        print("sha256:", r["sha256"])
        print("asset:", json.dumps(r["asset"])[:400])
        print("nodes/meshes/materials/animations:", r["node_count"], r["mesh_count"], r["material_count"], r["animation_count"])
        print("triangles/vertices:", r["total_node_triangles"], r["total_node_vertices"])
        print("world dimensions:", r["bounds"]["dimensions"])
        print("categories:", r["category_mesh_nodes"])
        print("largest mesh nodes:", json.dumps(r["top_meshes"][:30]))
        print("warnings:", r["warnings"][:10])
    print("AUDIT COMPLETE — read-only; no acceptance implied.")


if __name__ == "__main__":
    main()
