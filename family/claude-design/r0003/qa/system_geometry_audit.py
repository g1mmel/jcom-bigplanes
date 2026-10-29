#!/usr/bin/env python3
"""claude-design: bounded independent audit of r0003 system deliverables.

Reads the exported bytes, not authoring arrays.  It checks all static geometry
in the five new GLBs and samples only the newly revised gun/sensor clips.  It
does not repeat the inherited flight-mechanism sweeps, certify continuous
collision clearance, establish photo acceptance, or run Unreal.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

DTYPE = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
DIMS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
FILES = ["models/ac130.glb", "models/ac130j.glb", "components/gau23-visual/model.glb",
         "components/m102-airborne-visual/model.glb", "components/eoir-visual/model.glb"]
SAMPLE_TIMES = [0, .025, .035, .06, .14, .24, .35, .5, .70, .82, .88, .94, 1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Export:
    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        magic, version, length = struct.unpack_from("<4sII", self.data)
        if magic != b"glTF" or version != 2 or length != len(self.data):
            raise ValueError("invalid GLB header")
        jl, jt = struct.unpack_from("<II", self.data, 12)
        if jt != 0x4E4F534A:
            raise ValueError("missing GLB JSON")
        self.doc = json.loads(self.data[20:20 + jl])
        bl, bt = struct.unpack_from("<II", self.data, 20 + jl)
        if bt != 0x004E4942:
            raise ValueError("missing GLB binary")
        self.buf = self.data[28 + jl:28 + jl + bl]
        self.nodes = self.doc["nodes"]
        self.names = {n.get("name", str(i)): i for i, n in enumerate(self.nodes)}
        self.parents = {}
        for i, node in enumerate(self.nodes):
            for child in node.get("children", []):
                if child in self.parents:
                    raise ValueError("node has more than one parent")
                self.parents[child] = i
        self.positions = {}
        for i, node in enumerate(self.nodes):
            if "mesh" in node:
                self.positions[i] = np.concatenate([self.accessor(pr["attributes"]["POSITION"]).astype(float)
                                                     for pr in self.doc["meshes"][node["mesh"]]["primitives"]])

    def accessor(self, idx):
        a = self.doc["accessors"][idx]
        v = self.doc["bufferViews"][a["bufferView"]]
        dtype = np.dtype(DTYPE[a["componentType"]])
        width = DIMS[a["type"]]
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        arr = np.ndarray((a["count"], width), dtype=dtype, buffer=self.buf, offset=start,
                         strides=(v.get("byteStride", width * dtype.itemsize), dtype.itemsize)).copy()
        if a.get("normalized"):
            arr = arr.astype(float) / np.iinfo(dtype).max
            if dtype.kind == "i":
                arr = np.maximum(arr, -1)
        return arr

    def image_bytes(self, i):
        img = self.doc["images"][i]
        if "uri" in img:
            raise ValueError("external image dependency: " + img["uri"])
        bv = self.doc["bufferViews"][img["bufferView"]]
        off = bv.get("byteOffset", 0)
        return self.buf[off:off + bv["byteLength"]]

    def descendants(self, idx):
        out, pending = set(), [idx]
        while pending:
            i = pending.pop()
            if i in out:
                raise ValueError("cycle in node tree")
            out.add(i)
            pending.extend(self.nodes[i].get("children", []))
        return out

    def world(self, override=None):
        override = override or {}
        matrices = {}

        def visit(i):
            if i in matrices:
                return matrices[i]
            node = self.nodes[i]
            if "matrix" in node:
                local = np.asarray(node["matrix"], float).reshape(4, 4, order="F")
            else:
                local = np.eye(4)
                tr = np.asarray(override.get((i, "translation"), node.get("translation", [0, 0, 0])), float)
                sc = np.asarray(override.get((i, "scale"), node.get("scale", [1, 1, 1])), float)
                x, y, z, w = override.get((i, "rotation"), node.get("rotation", [0, 0, 0, 1]))
                rotation = np.array([[1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
                                     [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
                                     [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)]])
                local[:3, :3] = rotation @ np.diag(sc)
                local[:3, 3] = tr
            matrices[i] = visit(self.parents[i]) @ local if i in self.parents else local
            return matrices[i]

        for i in range(len(self.nodes)):
            visit(i)
        return matrices


def sample(times, values, t, rotation=False):
    times = times.ravel()
    if t <= times[0]:
        return values[0]
    if t >= times[-1]:
        return values[-1]
    k = int(np.searchsorted(times, t) - 1)
    u = (t - times[k]) / (times[k + 1] - times[k])
    a, b = values[k].astype(float), values[k + 1].astype(float)
    if not rotation:
        return a * (1 - u) + b * u
    dot = float(a @ b)
    if dot < 0:
        b, dot = -b, -dot
    if dot > .9995:
        q = a * (1 - u) + b * u
        return q / np.linalg.norm(q)
    theta = math.acos(np.clip(dot, -1, 1))
    return (math.sin((1-u)*theta)*a + math.sin(u*theta)*b) / math.sin(theta)


def case_exit_probe(exp, cid):
    """Inspect the actual exported mouth with a small grid of segment rays.

    This establishes that the named visual receiver has an open mouth and
    that the 105 mm cover clears it.  A ray grid is deliberately not described
    as a whole-case, swept-body or continuous collision-clearance certificate.
    """
    large = cid == "gun105"
    cavity_name = cid + ("_CASE_EXIT_CAVITY" if large else "_DOWNWARD_CASE_EXIT_CAVITY")
    if cavity_name not in exp.names:
        return None
    root = exp.names["PIVOT_" + cid + "_component"]
    members = exp.descendants(root)
    cavity = exp.names[cavity_name]
    clip = next(a for a in exp.doc["animations"] if a["name"] == cid + "_fire_cycle")

    def pose(t):
        override = {}
        for channel in clip["channels"]:
            target = channel["target"]; sam = clip["samplers"][channel["sampler"]]
            override[(target["node"], target["path"])] = sample(
                exp.accessor(sam["input"]), exp.accessor(sam["output"]), t,
                target["path"] == "rotation")
        return exp.world(override)

    def hits(triangles, start, end):
        direction = end - start
        e1 = triangles[:, 1] - triangles[:, 0]
        e2 = triangles[:, 2] - triangles[:, 0]
        pvec = np.cross(np.broadcast_to(direction, e2.shape), e2)
        det = np.einsum("ij,ij->i", e1, pvec)
        good = np.abs(det) > 1e-11
        inv = np.zeros_like(det); inv[good] = 1 / det[good]
        tv = start - triangles[:, 0]
        u = np.einsum("ij,ij->i", tv, pvec) * inv
        qvec = np.cross(tv, e1)
        v = np.einsum("ij,j->i", qvec, direction) * inv
        along = np.einsum("ij,ij->i", e2, qvec) * inv
        return good & (u >= -1e-8) & (v >= -1e-8) & (u + v <= 1 + 1e-8) & (along > 1e-6) & (along < 1 - 1e-6)

    phases = [0., .23, .24] if large else [.24]
    rows = []
    for t in phases:
        world = pose(t)
        inv_root = np.linalg.inv(world[root])
        triangles, owners = [], []
        cavity_points = None
        for i in members.intersection(exp.positions):
            node = exp.nodes[i]
            name = node["name"]
            if name == cid + "_SPENT_CASE" or any(token in name for token in ["MUZZLE_FLASH", "MUZZLE_SMOKE"]):
                continue
            transform = inv_root @ world[i]
            for primitive in exp.doc["meshes"][node["mesh"]]["primitives"]:
                p = exp.accessor(primitive["attributes"]["POSITION"]).astype(float)
                p = p @ transform[:3, :3].T + transform[:3, 3]
                f = exp.accessor(primitive["indices"]).reshape(-1, 3).astype(np.int64)
                triangles.append(p[f]); owners.extend([name] * len(f))
                if i == cavity:
                    cavity_points = p
        triangles = np.concatenate(triangles)
        owners = np.asarray(owners)
        lo, hi = cavity_points.min(0), cavity_points.max(0)
        center = (lo + hi) / 2
        axis, sign = (0, 1) if large else (1, -1)
        transverse = [a for a in range(3) if a != axis]
        hit_names, clear = set(), 0
        for a in [.30, .50, .70]:
            for b in [.30, .50, .70]:
                start = center.copy()
                start[transverse[0]] = lo[transverse[0]] * (1-a) + hi[transverse[0]] * a
                start[transverse[1]] = lo[transverse[1]] * (1-b) + hi[transverse[1]] * b
                end = start.copy()
                end[axis] = (hi[axis] + .22) if sign > 0 else (lo[axis] - .30)
                mask = hits(triangles, start, end)
                if not mask.any():
                    clear += 1
                else:
                    hit_names.update(owners[mask].tolist())
        rows.append({"normalized_phase": t, "rays": 9, "clear_rays": clear,
                     "intersected_meshes": sorted(hit_names),
                     "cavity_bounds_component_local_m": [lo.tolist(), hi.tolist()]})
    expected = all(row["clear_rays"] == (0 if large and row["normalized_phase"] == 0 else 9) for row in rows)
    return {"component": cid, "status": "PASS" if expected else "FAIL", "observations": rows,
            "scope": "Nine rays start inside the exported cavity and cross its mouth into a short receiving corridor. Cases and effects are excluded so they cannot masquerade as an uncut wall. Not a full-body sweep, opening-truth verification, or operational cycle certification."}


def lower_30_skin_probe(exp, relative, root):
    """Close the observed lower-base regression using only three fixed meshes.

The source envelope is read independently from the packaged original GLB;
no current authoring mesh arrays or prescribed plate coordinates are used.
Each unique exported support/base vertex is compared with the port skin at
the same aircraft-space Y,Z. This is a rest-vertex check, not a surface sweep.
"""
    if relative not in ("models/ac130.glb", "models/ac130j.glb"):
        return None
    source_relative = "source/inputs/c130-hercules-unified-r0001.glb"
    source = Export(root / source_relative)
    expected_source = "ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12"
    if sha(source.data) != expected_source:
        return {"status": "FAIL", "issue": "unexpected_source_skin_hash", "source": source_relative}
    basis = np.array([[-1., 0., 0.], [0., 0., 1.], [0., 1., 0.]])
    shift = np.array([0., .005873803637921924, 0.])
    source_world = source.world()
    source_names = ["Exterior_C130ExteriorSub_0", "LeftDoor_C130ExteriorSub_0"]
    skin = []
    for name in source_names:
        ni = source.names[name]
        transform = source_world[ni]
        for primitive in source.doc["meshes"][source.nodes[ni]["mesh"]]["primitives"]:
            p = source.accessor(primitive["attributes"]["POSITION"]).astype(float)
            p = (p @ transform[:3, :3].T + transform[:3, 3]) @ basis.T + shift
            faces = source.accessor(primitive["indices"]).reshape(-1, 3).astype(np.int64)
            skin.append(p[faces])
    skin = np.concatenate(skin)
    world = exp.world()
    target_names = ["gun30_INBOARD_BASE", "gun30_BASE_SUPPORT_0", "gun30_BASE_SUPPORT_1"]
    targets = []
    for name in target_names:
        if name not in exp.names:
            return {"status": "FAIL", "issue": "missing_lower_30_mesh", "mesh": name}
        ni = exp.names[name]
        p = exp.positions[ni]
        transform = world[ni]
        p = p @ transform[:3, :3].T + transform[:3, 3]
        targets.append((name, len(p), np.unique(p, axis=0)))
    all_points = np.concatenate([p for _, _, p in targets])
    lo, hi = all_points.min(0), all_points.max(0)
    # Restrict calculation to the local envelope around these exact vertices.
    skin = skin[(skin[:, :, 1].max(1) >= lo[1] - 1e-7) &
                (skin[:, :, 1].min(1) <= hi[1] + 1e-7) &
                (skin[:, :, 2].max(1) >= lo[2] - 1e-7) &
                (skin[:, :, 2].min(1) <= hi[2] + 1e-7) &
                (skin[:, :, 0].min(1) < 0)]
    a = skin[:, 0]
    e1, e2 = skin[:, 1] - a, skin[:, 2] - a
    det = e1[:, 1] * e2[:, 2] - e1[:, 2] * e2[:, 1]
    valid = np.abs(det) > 1e-10
    denominator = np.where(valid, det, 1.)
    observations = []
    tolerance = 1e-5
    for name, raw_count, points in targets:
        margins, misses, outside = [], [], []
        for p in points:
            y, z = p[1], p[2]
            u = ((y - a[:, 1]) * e2[:, 2] - (z - a[:, 2]) * e2[:, 1]) / denominator
            v = (e1[:, 1] * (z - a[:, 2]) - e1[:, 2] * (y - a[:, 1])) / denominator
            x = a[:, 0] + u * e1[:, 0] + v * e2[:, 0]
            mask = valid & (u >= -1e-7) & (v >= -1e-7) & (u + v <= 1 + 1e-7) & (x < 0)
            if not mask.any():
                misses.append(p.tolist())
                continue
            skin_x = float(x[mask].min())
            margin = float(p[0] - skin_x)
            row = {"vertex_aircraft_m": p.tolist(), "port_skin_x_m": skin_x, "inboard_margin_m": margin}
            margins.append(row)
            if margin < -tolerance:
                outside.append(row)
        observations.append({"mesh": name, "exported_vertex_records": raw_count, "unique_vertices_checked": len(points),
                             "skin_intersections": len(margins), "missing_skin_intersections": misses,
                             "outside_vertices": outside, "worst_vertex": min(margins, key=lambda x: x["inboard_margin_m"]) if margins else None,
                             "status": "PASS" if margins and not misses and not outside else "FAIL"})
    return {"status": "PASS" if all(x["status"] == "PASS" for x in observations) else "FAIL",
            "source": source_relative, "source_sha256": expected_source, "source_nodes": source_names,
            "source_coordinate_conversion": {"basis": basis.tolist(), "ground_shift_m": shift.tolist(), "source_node_world_transforms_applied": True},
            "pose": "exported canonical rest", "numerical_tolerance_m": tolerance,
            "method": "At each exported vertex Y,Z, project original exterior triangles along X and compare vertex X with the outermost negative-X intersection. Positive margin is inboard.",
            "observations": observations,
            "scope": "Only the fixed 30 mm inboard base and its two lower supports. No other airframe mechanism, animation sweep, triangle-interior clearance, real aircraft dimension or operational fit claim."}


def verify_file(path, relative, root):
    exp = Export(path)
    issues, mesh_rows = [], []
    total_tri, total_vertices = 0, 0
    for mesh in exp.doc.get("meshes", []):
        for pi, primitive in enumerate(mesh["primitives"]):
            name = mesh.get("name", "unnamed")
            attrs = {k: exp.accessor(v) for k, v in primitive["attributes"].items()}
            positions = attrs["POSITION"].astype(float)
            faces = exp.accessor(primitive["indices"]).reshape(-1, 3).astype(np.int64)
            row = {"mesh": name, "primitive": pi, "vertices": len(positions), "triangles": len(faces)}
            bad = []
            if int(faces.min()) < 0 or int(faces.max()) >= len(positions):
                bad.append("index_out_of_range")
            for attr, values in attrs.items():
                if not np.isfinite(values).all():
                    bad.append("nonfinite_" + attr)
            normals = attrs.get("NORMAL")
            if normals is None:
                bad.append("missing_normals")
            else:
                lengths = np.linalg.norm(normals.astype(float), axis=1)
                row["normal_length_min_max"] = [float(lengths.min()), float(lengths.max())]
                if np.any(lengths < 1e-8):
                    bad.append("zero_normals")
                if np.any(np.abs(lengths - 1) > .005):
                    bad.append("nonunit_normals")
            if "TANGENT" in attrs:
                tangents = attrs["TANGENT"]
                if np.any(np.abs(np.abs(tangents[:, 3]) - 1) > 1e-6):
                    bad.append("invalid_tangent_handedness")
            if not bad:
                fn = np.cross(positions[faces[:, 1]] - positions[faces[:, 0]],
                              positions[faces[:, 2]] - positions[faces[:, 0]])
                area = np.linalg.norm(fn, axis=1)
                degenerate = int((area <= 2e-12).sum())
                row["degenerate_triangles"] = degenerate
                if degenerate:
                    bad.append("degenerate_exported_triangles")
                if name.endswith("_INTERNAL_SPENT_CASE_BAG"):
                    centroids = positions[faces].mean(1)
                    mid = (positions.min(0) + positions.max(0)) / 2
                    radial = centroids - mid
                    radial[:, 1] = 0
                    # Side faces should point away from the empty bag cavity.
                    side = np.abs(fn[:, 1]) < np.linalg.norm(fn[:, [0, 2]], axis=1) * 2
                    dots = np.einsum("ij,ij->i", fn, radial)
                    inward = int(((dots < -1e-10) & side).sum())
                    row["bag_outward_winding_probe"] = {"side_triangles": int(side.sum()), "inward": inward}
                    if inward:
                        bad.append("spent_case_bag_has_inward_exterior_winding")
            row["issues"] = bad
            issues.extend({"mesh": name, "issue": value} for value in bad)
            mesh_rows.append(row)
            total_tri += len(faces)
            total_vertices += len(positions)

    images = []
    for i, img in enumerate(exp.doc.get("images", [])):
        try:
            data = exp.image_bytes(i)
            with Image.open(io.BytesIO(data)) as decoded:
                info = {"image": i, "bytes": len(data), "sha256": sha(data),
                        "size": list(decoded.size), "format": decoded.format, "mime_type": img.get("mimeType")}
                decoded.verify()
            images.append(info)
        except Exception as exc:
            issues.append({"issue": "image_dependency_or_decode", "detail": str(exc)})
    if any("uri" in b for b in exp.doc.get("buffers", [])):
        issues.append({"issue": "external_buffer_dependency"})

    refs = []
    for material in exp.doc.get("materials", []):
        def visit(value, key=""):
            if isinstance(value, dict):
                if key.endswith("Texture") and "index" in value:
                    ti = value["index"]
                    if not (0 <= ti < len(exp.doc.get("textures", []))):
                        issues.append({"issue": "invalid_texture_reference", "material": material.get("name")})
                    else:
                        texture = exp.doc["textures"][ti]
                        ii = texture.get("source")
                        if ii is None or not (0 <= ii < len(exp.doc.get("images", []))):
                            issues.append({"issue": "invalid_image_reference", "material": material.get("name")})
                        refs.append({"material": material.get("name"), "slot": key, "texture": ti, "image": ii})
                for k, v in value.items():
                    visit(v, k)
            elif isinstance(value, list):
                for v in value:
                    visit(v)
        visit(material)

    new_clips = [a for a in exp.doc.get("animations", []) if a.get("name", "").startswith(("gun30_", "gun105_", "eoir_"))]
    animation_rows = []
    rest = exp.world()
    for clip in new_clips:
        tracks, affected = [], set()
        errors = []
        for channel in clip["channels"]:
            target = channel["target"]
            sampler = clip["samplers"][channel["sampler"]]
            times = exp.accessor(sampler["input"]).ravel()
            values = exp.accessor(sampler["output"])
            node, prop = target["node"], target["path"]
            if not np.isfinite(times).all() or not np.isfinite(values).all() or not np.all(np.diff(times) > 0):
                errors.append("invalid_animation_values_or_times")
            if len(times) != len(values):
                errors.append("mismatched_sampler_lengths")
            if prop == "rotation" and np.any(np.abs(np.linalg.norm(values, axis=1) - 1) > .005):
                errors.append("nonunit_rotation_quaternion")
            tracks.append((node, prop, times, values))
            affected.update(exp.descendants(node))
        mesh_ids = affected.intersection(exp.positions)
        movement = 0.
        for t in SAMPLE_TIMES:
            override = {(i, prop): sample(times, values, t, prop == "rotation")
                        for i, prop, times, values in tracks}
            world = exp.world(override)
            for i in mesh_ids:
                p = exp.positions[i]
                a = p @ rest[i][:3, :3].T + rest[i][:3, 3]
                b = p @ world[i][:3, :3].T + world[i][:3, 3]
                movement = max(movement, float(np.linalg.norm(b - a, axis=1).max()))
        if not mesh_ids or movement < 1e-7:
            errors.append("clip_does_not_move_exported_geometry")
        cycle_return = None
        if clip["name"].endswith("_fire_cycle"):
            poses = []
            for t in [0, 1]:
                ov = {(i, prop): sample(times, values, t, prop == "rotation")
                      for i, prop, times, values in tracks}
                poses.append(exp.world(ov))
            cycle_return = max(float(np.max(np.abs(poses[0][i] - poses[1][i]))) for i in affected)
            if cycle_return > 1e-6:
                errors.append("cycle_end_does_not_return_to_start")
        animation_rows.append({"clip": clip["name"], "channels": len(tracks),
                               "affected_mesh_nodes": len(mesh_ids), "sample_count": len(SAMPLE_TIMES),
                               "max_world_vertex_displacement_m": movement,
                               "cycle_start_end_matrix_difference": cycle_return, "issues": errors})
        issues.extend({"clip": clip["name"], "issue": value} for value in errors)

    art_path = path.parent / "articulation.json" if relative.startswith("components/") else root / "articulation" / (path.stem + ".json")
    articulation = json.loads(art_path.read_text())
    if articulation.get("sha256") != sha(exp.data):
        issues.append({"issue": "articulation_hash_mismatch"})
    selected_controls = [c for c in articulation.get("controls", []) if c["id"].startswith(("gun30_", "gun105_", "eoir_"))]
    animation_names = {a["name"] for a in new_clips}
    for ctrl in selected_controls:
        if ctrl["clip"] not in animation_names or ctrl["node"] not in exp.names:
            issues.append({"issue": "unbound_control", "control": ctrl["id"]})
        if not ctrl.get("evidence", {}).get("sources"):
            issues.append({"issue": "missing_control_reference_metadata", "control": ctrl["id"]})
    roots = [n for n in exp.nodes if n.get("name", "").endswith("_component")]
    for node in roots:
        if "level 1" not in node.get("extras", {}).get("tags", []):
            issues.append({"issue": "missing_component_root_tag", "node": node["name"]})
        if not (node.get("extras", {}).get("reference") or node.get("extras", {}).get("references")):
            issues.append({"issue": "missing_component_reference_metadata", "node": node["name"]})
    for profile in articulation.get("firing_profiles", []):
        for field in ["muzzle_socket", "ejection_socket", "case_node", "case_transform", "flash_node", "smoke_node"]:
            if profile.get(field) not in exp.names:
                issues.append({"issue": "unbound_firing_profile", "field": field, "value": profile.get(field)})
        if profile.get("outside_case_ejection") is not False:
            issues.append({"issue": "unapproved_exterior_case_ejection_metadata"})

    exits = [probe for cid in ["gun30", "gun105"] if (probe := case_exit_probe(exp, cid)) is not None]
    for probe in exits:
        if probe["status"] != "PASS":
            issues.append({"issue": "focused_case_exit_ray_probe_failed", "component": probe["component"]})
    skin_probe = lower_30_skin_probe(exp, relative, root)
    if skin_probe and skin_probe["status"] != "PASS":
        issues.append({"issue": "lower_30_base_support_skin_probe_failed"})

    return {
        "file": relative, "bytes": len(exp.data), "sha256": sha(exp.data),
        "status": "FAIL" if issues else "PASS", "issues": issues,
        "vertices": total_vertices, "triangles": total_tri, "meshes": len(exp.doc["meshes"]),
        "clips_total": len(exp.doc.get("animations", [])), "revised_system_clips_checked": len(new_clips),
        "control_bindings_checked": len(selected_controls),
        "component_roots": [{"name": n["name"], "tags": n.get("extras", {}).get("tags", [])} for n in roots],
        "external_model_resource_uris": [], "embedded_images": images, "texture_references": refs,
        "mesh_checks": mesh_rows, "revised_system_animation_samples": animation_rows,
        "focused_case_exit_probes": exits,
        "focused_lower_30_skin_probe": skin_probe,
        "image_and_reference_scope": "Images decoded and texture references checked; reference metadata presence checked, not factual source truth or material realism.",
    }


def normalized_payload(exp):
    """Compare active mesh records/materials, component hierarchy, and clips."""
    def normalize_texture(value, key=""):
        if isinstance(value, dict):
            out = {k: normalize_texture(v, k) for k, v in value.items()}
            if key.endswith("Texture") and "index" in out:
                tex = exp.doc["textures"][out.pop("index")]
                out["resolved_image_sha256"] = sha(exp.image_bytes(tex["source"]))
                if "sampler" in tex:
                    out["sampler"] = exp.doc["samplers"][tex["sampler"]]
            return out
        if isinstance(value, list):
            return [normalize_texture(v) for v in value]
        return value

    meshes = {}
    for mesh in exp.doc["meshes"]:
        digest = hashlib.sha256()
        for primitive in mesh["primitives"]:
            indices = exp.accessor(primitive["indices"]).ravel().astype(np.int64)
            for key, accessor in sorted(primitive["attributes"].items()):
                a = np.ascontiguousarray(exp.accessor(accessor)[indices])
                digest.update(key.encode()); digest.update(str(a.shape).encode()); digest.update(a.tobytes())
            mat = normalize_texture(exp.doc["materials"][primitive["material"]])
            digest.update(json.dumps(mat, sort_keys=True, separators=(",", ":")).encode())
        meshes[mesh["name"]] = digest.hexdigest()
    roots = [i for i, n in enumerate(exp.nodes) if n.get("name", "").endswith("_component")]
    selected = set().union(*(exp.descendants(i) for i in roots))
    hierarchy = {}
    for i in selected:
        n = exp.nodes[i]; parent = exp.parents.get(i)
        hierarchy[n["name"]] = {"parent": exp.nodes[parent]["name"] if parent in selected else None,
                                 "translation": n.get("translation", [0, 0, 0]),
                                 "rotation": n.get("rotation", [0, 0, 0, 1]),
                                 "scale": n.get("scale", [1, 1, 1]), "matrix": n.get("matrix")}
    clips = {}
    for clip in exp.doc.get("animations", []):
        digest = hashlib.sha256()
        for channel in clip["channels"]:
            target = channel["target"]; s = clip["samplers"][channel["sampler"]]
            digest.update((exp.nodes[target["node"]]["name"] + ":" + target["path"]).encode())
            digest.update(exp.accessor(s["input"]).tobytes())
            digest.update(exp.accessor(s["output"]).tobytes())
            digest.update(s.get("interpolation", "LINEAR").encode())
        clips[clip["name"]] = digest.hexdigest()
    return {"expanded_triangle_attributes_and_materials": meshes,
            "component_hierarchy_and_rest_transforms": hierarchy, "animation_values_and_targets": clips}


def isolate_source(component, root):
    source = component / "source"
    source_files = sorted(p for p in source.iterdir() if p.is_file())
    with tempfile.TemporaryDirectory(prefix="claude-design-system-isolation-") as temporary:
        dest = Path(temporary) / component.name
        (dest / "source").mkdir(parents=True)
        for file in source_files:
            shutil.copy2(file, dest / "source" / file.name)
        # A fresh process has only the copied source and installed dependencies.
        # Audit hooks explicitly prohibit reads from the real project tree and
        # outbound socket creation; source is never allowed to open the parent
        # aircraft or fetch a dependency over the network during the rebuild.
        bootstrap = """
import os,pathlib,runpy,socket,sys
source=pathlib.Path(sys.argv[1]).resolve(); forbidden=pathlib.Path(sys.argv[2]).resolve()
def audit(event,args):
    if event in ('socket.__new__','socket.connect','socket.getaddrinfo'):
        raise PermissionError('network disabled during isolated source rebuild')
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        path=pathlib.Path(os.fsdecode(args[0])).resolve()
        if path==forbidden or forbidden in path.parents:
            raise PermissionError('parent project unavailable during isolated source rebuild')
sys.addaudithook(audit)
sys.path.insert(0,str(source));sys.argv=[str(source/'component_source.py')]
runpy.run_path(str(source/'component_source.py'),run_name='__main__')
"""
        command = [sys.executable, "-I", "-c", bootstrap, str(dest / "source"), str(root.parent.parent.parent)]
        process = subprocess.run(command, cwd=dest, text=True, capture_output=True, timeout=90,
                                 env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        row = {"component": component.name, "source_files": [{"file": f.name, "sha256": sha(f.read_bytes())} for f in source_files],
               "network_disabled": True, "parent_project_reads_forbidden": True,
               "python": sys.version.split()[0], "returncode": process.returncode,
               "stdout": process.stdout, "stderr": process.stderr,
               "status": "FAIL" if process.returncode else "PASS"}
        if process.returncode:
            return row
        rebuilt = Export(dest / "model-rebuilt.glb")
        delivered = Export(component / "model.glb")
        left, right = normalized_payload(delivered), normalized_payload(rebuilt)
        comparison = {}
        for key in left:
            missing = sorted(set(left[key]) - set(right[key]))
            extra = sorted(set(right[key]) - set(left[key]))
            changed = sorted(name for name in set(left[key]).intersection(right[key]) if left[key][name] != right[key][name])
            comparison[key] = {"equal": not (missing or extra or changed), "records": len(left[key]),
                               "missing": missing, "extra": extra, "changed": changed}
        row.update(delivered_sha256=sha(delivered.data), rebuilt_sha256=sha(rebuilt.data),
                   rebuilt_bytes=len(rebuilt.data), byte_identical=delivered.data == rebuilt.data,
                   semantic_comparison=comparison,
                   expected_byte_difference="Assembly-built exports retain unused family material records and metadata; semantic payload is compared independently.")
        if not all(x["equal"] for x in comparison.values()):
            row["status"] = "FAIL"
        return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--skip-isolation", action="store_true")
    parser.add_argument("--files", nargs="+", choices=FILES,
                        help="Refresh selected files and retain hash-matched results for other frozen GLBs; source isolation still covers all three components.")
    args = parser.parse_args()
    root = args.root.resolve()
    report = {"author": "claude-design", "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Exported static geometry, buffer/index/normal validity, embedded images and texture links, revised system control/tag/reference bindings, 13 actual vertex motion samples per revised gun/sensor clip, small focused case-exit ray grids, exported lower-30-base/support vertices against the retained source skin, and aircraft-independent source rebuilds.",
              "not_tested": ["photographic or photorealistic acceptance", "continuous collision clearance", "all combined motion paths", "inherited flight mechanism sweeps", "real weapon or sensor behavior", "native Unreal import/cook/runtime", "performance or gameplay"],
              "animation_sample_times": SAMPLE_TIMES, "files": [], "source_isolation": []}
    selected = args.files or FILES
    previous = json.loads((root / "qa/system_geometry_report.json").read_text()) if args.files else None
    report["refresh"] = {"refreshed_files": selected, "reused_hash_matched_files": [x for x in FILES if x not in selected]}
    for relative in FILES:
        if relative in selected:
            row = verify_file(root / relative, relative, root)
        else:
            row = next(x for x in previous["files"] if x["file"] == relative)
            if sha((root / relative).read_bytes()) != row["sha256"]:
                raise ValueError("Cannot reuse geometry result for changed file: " + relative)
        report["files"].append(row)
        print("claude-design", relative, row["status"], "issues", len(row["issues"]),
              "refreshed" if relative in selected else "reused unchanged", flush=True)
    if not args.skip_isolation:
        for component in [root / "components" / x for x in ["gau23-visual", "m102-airborne-visual", "eoir-visual"]]:
            row = isolate_source(component, root)
            report["source_isolation"].append(row)
            print("claude-design isolation", component.name, row["status"], flush=True)
    report["inputs_unchanged_during_audit"] = all(sha((root / row["file"]).read_bytes()) == row["sha256"] for row in report["files"])
    report["status"] = "PASS" if (all(row["status"] == "PASS" for row in report["files"] + report["source_isolation"]) and report["inputs_unchanged_during_audit"]) else "FAIL"
    (root / "qa" / "system_geometry_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("claude-design geometry audit", report["status"])
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
