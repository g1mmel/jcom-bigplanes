"""claude-design: independently reusable, photo-guided EO/IR visual component.

The visible fork, rounded optical housing, and unequal recessed windows are
guided by the public L3Harris MX-20 product photograph.  This is an original
visual approximation, not a reconstruction of sensor hardware or a claim that
every AC-130J installation uses this exact model.  The dimensions and two
exposed animation ranges are authored game presentation values.  Internal
stabilization, imaging, targeting, and real control behavior are not modeled.

Integration interface: ``add_sensor(model, cid, center)``.  The model supplies
the small GLB/Model API used by the family builder.  ``gltf_core``, NumPy and
SciPy are source dependencies; there are no aircraft meshes or textures here.

Canonical root: ``PIVOT_<cid>_component`` (the sole ``level 1`` tag).
Attachment datum: the supplied center; local +Y up and optics toward -Z.
The port instance is intentionally not rotated here: its installation pose
belongs to the aircraft assembly, outside this independent component.
Conservative rest bounds relative to center, in authored metres:
    X [-0.287, +0.287], Y [-0.306, +0.310], Z [-0.280, +0.280].
The actual mesh bounds and the two control bindings are returned to caller.
"""
from __future__ import annotations

import math
import numpy as np

from gltf_core import make_mesh, merge, normalize, tube


REFERENCES = {
    "product": "https://www.l3harris.com/all-capabilities/wescam-mx-20-air-surveillance-and-reconnaissance",
    "photo": "https://www.l3harris.com/sites/default/files/2026-04/wescam-mx-20-eo-ir-air-surveillance-reconnaissance.png",
    "brochure": "https://www.l3harris.com/sites/default/files/2020-07/ims_eo_brochure_wescam_MX-20-0102AB-Brochure.pdf",
    "w_identity": "https://www.robins.af.mil/News/Article-Display/Article/377994/mc-130w-dragon-spear-visits-robins/",
    "j_chin": "https://www.dvidshub.net/image/5621880/73rd-amu-air-commandos-perform-post-flight-inspection-ac-130j-ghostrider-gunship",
}

ASSET_ID = "JCNC_EOIR_MX20_FAMILY_VISUAL_r0003"


def _materials(model):
    """Own named materials so a component export needs no airframe material."""
    if hasattr(model, "_eoir_component_materials"):
        return model._eoir_component_materials
    g = model.glb
    specs = {
        "paint": ("EOIR_MATTE_NEUTRAL_GREY", [.43, .45, .45, 1], .08, .67),
        "paint_edge": ("EOIR_EDGE_GREY", [.34, .36, .36, 1], .12, .62),
        "paint_light": ("EOIR_RECESSED_FACE_GREY", [.48, .50, .49, 1], .08, .64),
        "rubber": ("EOIR_DARK_GASKET", [.018, .022, .023, 1], .01, .90),
        "dark": ("EOIR_OPTICAL_CAVITY", [.009, .013, .015, 1], .05, .74),
        "anodized": ("EOIR_ANODIZED_OPTICAL_BARREL", [.034, .044, .049, 1], .58, .31),
        "metal": ("EOIR_RESTRAINED_FASTENER_METAL", [.24, .27, .28, 1], .78, .30),
        "lens": ("EOIR_DARK_ANTIRELECTION_OPTICS", [.018, .042, .055, 1], .42, .13),
        "ir": ("EOIR_DARK_GREEN_WINDOW", [.025, .043, .031, 1], .27, .17),
        "seal": ("EOIR_RESTRAINED_WINDOW_SEAL", [.12, .063, .050, 1], .03, .83),
    }
    mats = {key: g.material(name, color, metal, rough, double=False)
            for key, (name, color, metal, rough) in specs.items()}
    for mid in mats.values():
        g.doc["materials"][mid]["extras"] = {
            "component_asset": ASSET_ID,
            "appearance": "photo-guided color/roughness; no photographic texture bake",
        }
    model._eoir_component_materials = mats
    return mats


def _lathe_y(name, center, profile, material, segments=64, capped=True):
    """Closed, bevel-profile body of revolution with outward winding."""
    c = np.asarray(center, float)
    angles = np.linspace(0, 2 * math.pi, segments, endpoint=False)
    verts = [c + [r * math.cos(a), y, r * math.sin(a)]
             for y, r in profile for a in angles]
    faces = []
    for k in range(len(profile) - 1):
        for j in range(segments):
            a = k * segments + j
            b = k * segments + (j + 1) % segments
            faces.extend([(a, a + segments, b + segments), (a, b + segments, b)])
    if capped:
        bottom = len(verts)
        verts.extend([c + [0, profile[0][0], 0], c + [0, profile[-1][0], 0]])
        off = (len(profile) - 1) * segments
        for j in range(segments):
            n = (j + 1) % segments
            faces.extend([(bottom, j, n), (bottom + 1, off + n, off + j)])
    return make_mesh(name, verts, faces, material)


def _shell_sector(name, center, r_outer, r_inner, top, material,
                  begin=58, end=302, segments=70):
    """Thick rear/side yoke with an actual front opening and shaped lower rim."""
    c = np.asarray(center, float)
    angles = np.linspace(math.radians(begin), math.radians(end), segments + 1)
    verts = []
    for a in angles:
        bottom = -.200 + .130 * (1 + math.cos(a)) / 2
        for radius, height in [(r_outer, bottom), (r_outer, top),
                               (r_inner, bottom), (r_inner, top)]:
            verts.append(c + [radius * math.sin(a), height, -radius * math.cos(a)])
    faces = []
    for j in range(segments):
        a, b = 4 * j, 4 * (j + 1)
        # Outer, inner, bottom rim, top rim.  The front remains genuinely open.
        faces.extend([(a, b, b + 1), (a, b + 1, a + 1),
                      (a + 2, a + 3, b + 3), (a + 2, b + 3, b + 2),
                      (a, a + 2, b + 2), (a, b + 2, b),
                      (a + 1, b + 1, b + 3), (a + 1, b + 3, a + 3)])
    faces.extend([(0, 1, 3), (0, 3, 2)])
    e = 4 * segments
    faces.extend([(e, e + 2, e + 3), (e, e + 3, e + 1)])
    # The angle convention starts at -Z; reverse the constructed strips so the
    # exterior, interior, rims, and end walls all face their exposed sides.
    return make_mesh(name, verts, np.asarray(faces)[:, [0, 2, 1]], material)


def _optical_globe(name, center, radius, front_z, material, sectors=64, rows=26):
    """Rounded housing terminated exactly at the open optical face plane."""
    c = np.asarray(center, float)
    alpha0 = math.acos(-front_z / radius)
    alphas = np.linspace(alpha0, math.pi, rows + 1)[:-1]
    verts = []
    for a in alphas:
        for b in np.linspace(0, 2 * math.pi, sectors, endpoint=False):
            verts.append(c + radius * np.array([math.sin(a) * math.cos(b),
                                                math.sin(a) * math.sin(b),
                                                -math.cos(a)]))
    faces = []
    for i in range(len(alphas) - 1):
        for j in range(sectors):
            a = i * sectors + j
            b = i * sectors + (j + 1) % sectors
            faces.extend([(a, b, b + sectors), (a, b + sectors, a + sectors)])
    pole = len(verts)
    verts.append(c + [0, 0, radius])
    off = (len(alphas) - 1) * sectors
    for j in range(sectors):
        faces.append((off + j, off + (j + 1) % sectors, pole))
    mesh = make_mesh(name, verts, faces, material)
    mesh.attrs["NORMAL"] = normalize(mesh.p - c)
    return mesh


def _face_disk(name, center, radius, material, segments=64):
    c = np.asarray(center, float)
    verts = [c] + [c + [radius * math.cos(a), radius * math.sin(a), 0]
                   for a in np.linspace(0, 2 * math.pi, segments, endpoint=False)]
    faces = [(0, (j + 1) % segments + 1, j + 1) for j in range(segments)]
    return make_mesh(name, verts, faces, material)


def _apertured_face(name, center, radius, windows, material):
    """Triangulate the thin optical face and verify all four opening borders.

    Dense boundary sampling supplies the desired Delaunay constraints.  Check
    the resulting boundary edge set explicitly so a changed aperture layout
    cannot silently create a filled window or a missing connecting surface.
    """
    from scipy.spatial import Delaunay
    points, expected = [], set()
    circles = [(0., 0., radius, 64)] + [(dx, dy, rad, 48) for _, dx, dy, rad, _ in windows]
    for x, y, r, segments in circles:
        off = len(points)
        points.extend([x + r * math.cos(a), y + r * math.sin(a)]
                      for a in np.linspace(0, 2 * math.pi, segments, endpoint=False))
        expected.update(tuple(sorted((off + j, off + (j + 1) % segments)))
                        for j in range(segments))
    p = np.asarray(points)
    faces = Delaunay(p).simplices
    centroids = p[faces].mean(1)
    keep = np.ones(len(faces), bool)
    for _, dx, dy, r, _ in windows:
        keep &= np.linalg.norm(centroids - [dx, dy], axis=1) > r * math.cos(math.pi / 48)
    faces = faces[keep]
    edges = {}
    for tri in faces:
        for a, b in zip(tri, np.roll(tri, -1)):
            key = tuple(sorted((int(a), int(b))))
            edges[key] = edges.get(key, 0) + 1
    actual = {edge for edge, count in edges.items() if count == 1}
    if actual != expected or any(count > 2 for count in edges.values()):
        raise ValueError("EOIR face triangulation does not preserve the exact aperture boundaries")
    # scipy supplies counterclockwise +Z faces; the optical front faces -Z.
    verts = np.column_stack((p, np.zeros(len(p)))) + np.asarray(center)
    return make_mesh(name, verts, faces[:, [0, 2, 1]], material)


def _face_ring(name, center, outer, inner, material, depth=.004, segments=48):
    """Sloped window bezel, its opening stays clear through the face panel."""
    c = np.asarray(center, float)
    verts = []
    for r, z in [(outer, -.001), (inner, depth)]:
        for a in np.linspace(0, 2 * math.pi, segments, endpoint=False):
            verts.append(c + [r * math.cos(a), r * math.sin(a), z])
    faces = []
    for j in range(segments):
        k = (j + 1) % segments
        faces.extend([(j, j + segments, k + segments), (j, k + segments, k)])
    return make_mesh(name, verts, faces, material)


def _recess_wall(name, center, radius, depth, material, segments=48):
    mesh = tube(name, center, np.asarray(center) + [0, 0, depth],
                radius, material, segments=segments, cap=False)
    mesh.faces = mesh.faces[:, [0, 2, 1]]
    mesh.attrs["NORMAL"] *= -1
    return mesh


def _convex_lens(name, center, radius, material, rings=5, sectors=48):
    """A shallow dark optical surface; curvature is solely visual."""
    c = np.asarray(center, float)
    verts = [c + [0, 0, -.0025]]
    for r in np.linspace(radius / rings, radius, rings):
        z = -.0025 * (1 - (r / radius) ** 2)
        for a in np.linspace(0, 2 * math.pi, sectors, endpoint=False):
            verts.append(c + [r * math.cos(a), r * math.sin(a), z])
    faces = [(0, 1 + (j + 1) % sectors, 1 + j) for j in range(sectors)]
    for k in range(rings - 1):
        a0, a1 = 1 + k * sectors, 1 + (k + 1) * sectors
        for j in range(sectors):
            n = (j + 1) % sectors
            faces.extend([(a0 + j, a0 + n, a1 + n), (a0 + j, a1 + n, a1 + j)])
    return make_mesh(name, verts, faces, material)


def add_sensor(model, cid, center):
    """Add one complete visual sensor and bind existing yaw/pitch control IDs."""
    c = np.asarray(center, float)
    if c.shape != (3,) or not np.isfinite(c).all():
        raise ValueError("sensor center must be three finite coordinates")
    mats = _materials(model)
    g = model.glb
    root = model.pivot(cid + "_component", c, parent=model.kit, extras={
        "tags": ["level 1"],
        "component_asset": ASSET_ID,
        "component_instance": cid,
        "component_type": "visual_eoir_sensor",
        "geometry_status": "PHOTO_GUIDED_VISUAL_APPROXIMATION",
        "source": "Original claude-design geometry; no Sketchfab meshes ingested",
        "references": REFERENCES,
        "bounds_scope": "authored rest geometry; animation clearance is a separate gate",
        "units": "metres",
        "local_basis": "+X right, +Y up, optical face -Z",
        "installation_model": "MX-20-family visual form; exact J slot/block remains unresolved",
        "operational_sensor_model": False,
    })
    yaw = model.pivot(cid + "_yaw", c, parent=root, extras={
        "part_role": "external_yaw_yoke", "component_asset": ASSET_ID})
    globe_c = c + [0, -.055, 0]
    pitch = model.pivot(cid + "_pitch", globe_c, parent=yaw, extras={
        "part_role": "external_optical_gimbal", "component_asset": ASSET_ID})
    recorded = []

    def attach(mesh, pivot, role):
        mesh.extras = {**(mesh.extras or {}), "component_asset": ASSET_ID,
                       "component_instance": cid, "part_role": role,
                       "geometry_status": "PHOTO_GUIDED_VISUAL_APPROXIMATION"}
        recorded.append(mesh.p.copy())
        return model.attach(mesh, pivot)

    # The attachment cap is fixed; the yoke moves below its dark bearing seam.
    attach(_lathe_y(cid + "_FIXED_ATTACHMENT_CAP", c,
                    [(.240, .154), (.247, .176), (.300, .176), (.310, .165)],
                    mats["paint"], segments=56), root, "fixed_attachment_cap")
    attach(_lathe_y(cid + "_AZIMUTH_BEARING_SEAM", c,
                    [(.231, .168), (.242, .168)], mats["rubber"], segments=56),
           root, "fixed_yaw_bearing_seam")
    attach(_lathe_y(cid + "_YAW_TOP_BAND", c,
                    [(.144, .273), (.151, .279), (.230, .279), (.240, .267),
                     (.240, .247), (.144, .247), (.144, .273)],
                    mats["paint"], segments=64, capped=False), yaw, "yaw_upper_shell")
    attach(_shell_sector(cid + "_OPEN_FRONT_YOKE", c, .277, .262, .148,
                          mats["paint"]), yaw, "open_front_yoke")

    cheeks = []
    fasteners = []
    for sign, side in [(-1, "LEFT"), (1, "RIGHT")]:
        attach(tube(cid + "_" + side + "_TRUNNION_GASKET",
                    globe_c + [sign * .253, 0, 0], globe_c + [sign * .277, 0, 0],
                    .088, mats["rubber"], segments=40), yaw, "stationary_pivot_gasket")
        attach(tube(cid + "_" + side + "_PITCH_CAP",
                    globe_c + [sign * .277, 0, 0], globe_c + [sign * .285, 0, 0],
                    .074, mats["paint_edge"], segments=40), pitch, "pitch_cap")
        for a in np.linspace(0, 2 * math.pi, 6, endpoint=False):
            off = np.array([sign * .286, .057 * math.cos(a), .057 * math.sin(a)])
            fasteners.append(tube(cid + "_" + side + "_PIVOT_FASTENER",
                                  globe_c + off, globe_c + off + [sign * .001, 0, 0],
                                  .0037, mats["metal"], segments=8))
        # Small side panel hardware follows the outer yoke rather than floating
        # over the optical housing.
        for yy in [.190, .107, .022]:
            cheeks.append(tube(cid + "_" + side + "_YOKE_FASTENER",
                               c + [sign * .277, yy, .030],
                               c + [sign * .280, yy, .030],
                               .0043, mats["metal"], segments=8))
    attach(merge(fasteners, cid + "_PITCH_FASTENERS"), pitch, "pitch_fasteners")
    attach(merge(cheeks, cid + "_YOKE_FASTENERS"), yaw, "yoke_fasteners")

    radius, front_z = .250, -.150
    attach(_optical_globe(cid + "_ROUNDED_OPTICAL_HOUSING", globe_c,
                           radius, front_z, mats["paint"]), pitch, "optical_housing")
    face_c = globe_c + [0, 0, front_z]
    face_radius = math.sqrt(radius * radius - front_z * front_z)
    # Unequal windows follow the visible family form.  Their internal optical
    # function and exact sensor assignment are deliberately not asserted.
    windows = [
        ("LARGE_UPPER", .073, .075, .091, "lens"),
        ("LARGE_LOWER", -.077, -.073, .088, "ir"),
        ("SMALL_UPPER", -.104, .085, .043, "lens"),
        ("SMALL_LOWER", .104, -.098, .043, "lens"),
    ]
    face = _apertured_face(cid + "_APERTURED_OPTICAL_FACE", face_c, face_radius,
                           windows, mats["paint_light"])
    for label, dx, dy, rad, kind in windows:
        wc = face_c + [dx, dy, 0]
        seg = 48
        attach(_face_ring(cid + "_" + label + "_PAINT_BEZEL", wc,
                           rad + .006, rad, mats["paint_edge"], segments=seg),
               pitch, "window_bevel")
        attach(_face_ring(cid + "_" + label + "_SEAL", wc + [0, 0, .002],
                           rad, rad - .002, mats["seal"], depth=.002, segments=seg),
               pitch, "window_seal")
        attach(_recess_wall(cid + "_" + label + "_RECESSED_WALL", wc,
                             rad - .0015, .043, mats["dark"], segments=seg),
               pitch, "visible_window_recess")
        attach(_face_disk(cid + "_" + label + "_BLACK_BACKING", wc + [0, 0, .044],
                           rad - .0015, mats["dark"], segments=seg),
               pitch, "optical_cavity_backing")
        if kind == "ir":
            attach(_convex_lens(cid + "_" + label + "_DARK_WINDOW", wc + [0, 0, .018],
                                rad - .004, mats["ir"]), pitch, "dark_optical_window")
        else:
            attach(_face_ring(cid + "_" + label + "_OPTICAL_BARREL", wc + [0, 0, .024],
                               rad * .86, rad * .56, mats["anodized"], depth=.006,
                               segments=seg), pitch, "recessed_optical_barrel")
            attach(_face_ring(cid + "_" + label + "_LENS_RETAINER", wc + [0, 0, .031],
                               rad * .57, rad * .53, mats["metal"], depth=.001,
                               segments=seg), pitch, "lens_retainer")
            attach(_convex_lens(cid + "_" + label + "_OPTICS", wc + [0, 0, .033],
                                rad * .53, mats["lens"]), pitch, "recessed_dark_optics")
    face.name = cid + "_APERTURED_OPTICAL_FACE"
    attach(face, pitch, "face_with_four_actual_openings")
    attach(_face_ring(cid + "_FACE_PERIMETER_SEAM", face_c,
                       face_radius, face_radius - .002, mats["paint_edge"],
                       depth=.001, segments=64), pitch, "face_perimeter_seam")

    face_screws, screw_recesses = [], []
    for i, a in enumerate(np.deg2rad([0, 90, 130, 180, 270, 310])):
        p = face_c + [.189 * math.cos(a), .189 * math.sin(a), -.0005]
        screw_recesses.append(_face_disk(cid + f"_FACE_SCREW_RECESS_{i}", p,
                                         .0055, mats["rubber"], segments=12))
        face_screws.append(tube(cid + f"_FACE_SCREW_{i}", p + [0, 0, -.0003],
                                p + [0, 0, -.0013], .0031, mats["metal"], segments=8))
    attach(merge(screw_recesses, cid + "_FACE_SCREW_RECESSES"), pitch, "fastener_recesses")
    attach(merge(face_screws, cid + "_FACE_FASTENERS"), pitch, "face_fasteners")

    ev = {
        "status": "PHOTO_GUIDED_EXTERNAL_FORM_ARTIST_AUTHORED_TRAVEL",
        "sources": [REFERENCES["product"], REFERENCES["photo"], REFERENCES["j_chin"]],
        "limitations": "External form only. Exact variant, lens assignments, scale, and travel remain artist approximations. Internal stabilization and real sensor functions are not reproduced.",
    }
    model.control(cid + "_yaw", cid.replace("_", " ").title() + " azimuth", yaw,
                  [0, 1, 0], 90, duration=3.6, group="Mission sensors", ev=ev)
    model.control(cid + "_pitch", cid.replace("_", " ").title() + " elevation", pitch,
                  [1, 0, 0], 45, duration=3.0, group="Mission sensors", ev=ev)
    pts = np.concatenate(recorded)
    bounds = [(pts.min(0) - c).tolist(), (pts.max(0) - c).tolist()]
    g.doc["nodes"][root]["extras"]["rest_bounds_local_m"] = bounds
    if hasattr(model, "log"):
        model.log.append({
            "component": cid, "asset": ASSET_ID, "root": g.doc["nodes"][root]["name"],
            "status": "PHOTO_GUIDED_VISUAL_APPROXIMATION_NOT_PHOTOGRAPHICALLY_ACCEPTED",
            "references": REFERENCES, "third_party_meshes": False,
            "notes": "Independent fixed cap/yaw yoke/pitch housing. Four recessed optical windows. Appearance uses own PBR colors and roughness, not a photographic material bake.",
        })
    return {"root": root, "root_name": g.doc["nodes"][root]["name"],
            "yaw": yaw, "pitch": pitch, "asset_id": ASSET_ID,
            "rest_bounds_local_m": bounds, "controls": [cid + "_yaw", cid + "_pitch"]}
