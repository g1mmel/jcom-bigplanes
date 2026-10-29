#!/usr/bin/env python3
"""Diagnose gear-door closure on actual exported FLYING-pose triangles.

The rectangular regions are the surveyed apertures of candidate 3c3b4125,
not measured real-aircraft dimensions. This is a closure regression probe,
not photographic acceptance or an all-angle watertightness certificate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from validate_articulation import Asset
from probe_surface_crossings import triangles_for


REGIONS = [
    ("main_left_bottom", [0, 2], 1, -1, [-2.4, -1.25, -3.24, -.31], "left"),
    ("main_right_bottom", [0, 2], 1, -1, [1.25, 2.4, -3.24, -.31], "right"),
    ("nose_forward_bottom", [0, 2], 1, -1, [-.62, .62, -13.65, -10.95], "nose"),
    ("nose_aft_bottom", [0, 2], 1, -1, [-.81, .81, -11.92, -9.88], "nose"),
    ("main_left_side", [1, 2], 0, -1, [.91, 2.96, -3.24, -.31], "left"),
    ("main_right_side", [1, 2], 0, 1, [.91, 2.96, -3.24, -.31], "right"),
]


def projected_depth(triangles, points, axes, depth_axis, viewing_sign):
    """First projected intersection from the negative/positive depth side.

    Projected barycentric coordinates interpolate the actual triangle depth.
    Edge-on triangles have no area in this projection and are excluded.
    """
    depth = np.full(len(points), np.inf)
    lo, hi = points.min(0), points.max(0)
    t = triangles[:, :, axes]
    mask = np.all(t.max(1) >= lo, axis=1) & np.all(t.min(1) <= hi, axis=1)
    for tri, xy in zip(triangles[mask], t[mask]):
        a, b, c = xy
        v0, v1 = b-a, c-a
        det = v0[0]*v1[1]-v0[1]*v1[0]
        if abs(det) < 1e-14:
            continue
        ids = np.flatnonzero(np.all(points >= xy.min(0)-1e-9, axis=1)
                             & np.all(points <= xy.max(0)+1e-9, axis=1))
        if not len(ids):
            continue
        delta = points[ids]-a
        u = (delta[:, 0]*v1[1]-delta[:, 1]*v1[0])/det
        v = (v0[0]*delta[:, 1]-v0[1]*delta[:, 0])/det
        hit = (u >= -1e-8) & (v >= -1e-8) & (u+v <= 1+1e-8)
        ids, u, v = ids[hit], u[hit], v[hit]
        z = tri[0, depth_axis] + u*(tri[1, depth_axis]-tri[0, depth_axis]) + v*(tri[2, depth_axis]-tri[0, depth_axis])
        # Smaller signed depth is nearest the incoming ray.
        depth[ids] = np.minimum(depth[ids], -viewing_sign*z)
    return depth


def model_probe(root, mid):
    asset = Asset(root/'models'/f'{mid}.glb')
    sidecar = json.loads((root/'articulation'/f'{mid}.json').read_text())
    controls = {c['id']: c for c in sidecar['controls']}
    clips = {a['name']: a for a in asset.doc['animations']}
    pose = {}
    preset = sidecar['states']['FLYING']
    for cid, value in preset.items():
        control = controls[cid]
        owner = control.get('owned_by')
        if owner and preset.get(owner, 0) != 0:
            continue
        pose.update(asset.sample(clips[control['clip']], value))
    worlds = asset.worlds(pose)
    names = {n['name']: i for i, n in enumerate(asset.nodes)}
    pivots = {
        'left': ['PIVOT_gear_door_left'],
        'right': ['PIVOT_gear_door_right'],
        'nose': ['PIVOT_gear_door_nose', 'PIVOT_nose_forward_hatch_left', 'PIVOT_nose_forward_hatch_right'],
    }
    closure_names = {}
    for side, roots in pivots.items():
        ids = set()
        for name in roots:
            if name in names:
                ids.update(asset.descendants(names[name]))
        closure_names[side] = [asset.nodes[i]['name'] for i in sorted(ids) if 'mesh' in asset.nodes[i]]
    closures = {side: triangles_for(asset, items, worlds) for side, items in closure_names.items()}
    skin = triangles_for(asset, ['fuselage'], worlds)
    wells = {side: triangles_for(asset, ['GEAR_WELL_'+side.upper()], worlds) for side in pivots}
    rows = []
    for rid, axes, depth_axis, sign, region, side in REGIONS:
        points = np.array(np.meshgrid(np.linspace(region[0]+.015, region[1]-.015, 81),
                                      np.linspace(region[2]+.015, region[3]-.015, 161))).reshape(2, -1).T
        cover = projected_depth(closures[side], points, axes, depth_axis, sign)
        exterior = np.minimum(cover, projected_depth(skin, points, axes, depth_axis, sign))
        well = projected_depth(wells[side], points, axes, depth_axis, sign)
        well_first = np.isfinite(well) & (well < exterior-2e-5)
        missing = ~np.isfinite(exterior)
        misses = points[~np.isfinite(cover)]
        examples = misses[::max(1, len(misses)//12)][:12]
        exposed_ids = np.flatnonzero(well_first)
        exposed_ids = exposed_ids[::max(1, len(exposed_ids)//12)][:12]
        exposure_examples = []
        for i in exposed_ids:
            exposure_examples.append({
                'plane_point_m': points[i].tolist(),
                'well_depth_coordinate_m': float(-sign*well[i]),
                'nearest_exterior_depth_coordinate_m': float(-sign*exterior[i]) if np.isfinite(exterior[i]) else None,
            })
        # A second, even-sized cell-centre grid avoids overweighting an exact
        # symmetry seam such as X=0. Retain the original grid for comparisons.
        aa = region[0]+.015+(np.arange(80)+.5)*(region[1]-region[0]-.03)/80
        bb = region[2]+.015+(np.arange(160)+.5)*(region[3]-region[2]-.03)/160
        cell_points = np.array(np.meshgrid(aa, bb)).reshape(2, -1).T
        cell_cover = projected_depth(closures[side], cell_points, axes, depth_axis, sign)
        cell_skin = projected_depth(skin, cell_points, axes, depth_axis, sign)
        cell_well = projected_depth(wells[side], cell_points, axes, depth_axis, sign)
        cell_exterior = np.minimum(cell_cover, cell_skin)
        cell_exposed = np.isfinite(cell_well) & (cell_well < cell_exterior-2e-5)
        rows.append({
            'region': rid, 'plane_axes': ['XYZ'[a] for a in axes],
            'depth_axis': 'XYZ'[depth_axis], 'view_from_sign': sign,
            'surveyed_rectangle_m': region, 'border_exclusion_m': .015,
            'grid': [81, 161], 'samples': len(points),
            'closure_nodes': closure_names[side],
            'closure_only_coverage': float(np.isfinite(cover).mean()),
            'closure_plus_fixed_fuselage_coverage': float(np.isfinite(exterior).mean()),
            'well_surface_first_fraction': float(well_first.mean()),
            'missing_exterior_fraction': float(missing.mean()),
            'closure_uncovered_examples_m': examples.tolist(),
            'well_exposed_examples': exposure_examples,
            'cell_centre_grid': {'grid': [80, 160], 'samples': len(cell_points),
                                 'closure_only_coverage': float(np.isfinite(cell_cover).mean()),
                                 'well_surface_first_fraction': float(cell_exposed.mean()),
                                 'purpose': 'Avoid giving a zero-area symmetry seam the weight of one complete sample column.'},
        })
    return {'id': mid, 'sha256': hashlib.sha256(asset.data).hexdigest(),
            'bytes': len(asset.data), 'pose': 'FLYING', 'regions': rows,
            'status': 'DIAGNOSTIC_REQUIRES_NATIVE_VIEW_REVIEW'}


def attach_native_review(root, model, reviews):
    """Bind an explicit visual-review receipt to unchanged actual render bytes.

    This does not infer visual acceptance from a numeric coverage threshold.
    A changed model, native report or image invalidates the recorded review.
    """
    review = next((r for r in reviews.get('models', []) if r.get('id') == model['id']), None)
    if not review:
        return
    problems = []
    if review.get('model_sha256') != model['sha256']:
        problems.append('Visual review belongs to different model bytes.')
    report_path = root/review.get('native_report', '')
    if not report_path.is_file():
        problems.append('Native report is missing.')
    else:
        report_bytes = report_path.read_bytes()
        native = json.loads(report_bytes)
        if hashlib.sha256(report_bytes).hexdigest() != review.get('native_report_sha256'):
            problems.append('Native report bytes changed after visual review.')
        if native.get('input_sha256') != model['sha256']:
            problems.append('Native import used different model bytes.')
        native_renders = {r['path']: r for r in native.get('renders', [])}
        for item in review.get('images', []):
            image_path = root/item['path']
            if not image_path.is_file() or hashlib.sha256(image_path.read_bytes()).hexdigest() != item['sha256']:
                problems.append('Reviewed image missing or changed: '+item['path'])
            if native_renders.get(item['path'], {}).get('sha256') != item['sha256']:
                problems.append('Reviewed image is not bound by the native report: '+item['path'])
        if not review.get('images'):
            problems.append('No actual reviewed images recorded.')
    model['native_review'] = review
    model['native_review_binding_issues'] = problems
    if problems:
        model['status'] = 'PENDING_CURRENT_NATIVE_REVIEW'
    elif review.get('status') == 'PASS_SCOPED':
        model['status'] = 'PASS_SCOPED'
    elif review.get('status') == 'FAIL':
        model['status'] = 'FAIL'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--models', nargs='+', default=['c130'])
    ap.add_argument('--native-review', default='qa/gear_closure_native_review.json',
                    help='Explicit visual-review receipt, if present; no automatic visual pass is inferred.')
    args = ap.parse_args()
    result = {
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'method': 'Actual exported FLYING triangles, projected barycentric ray intersections; covers, fixed fuselage and dark well surfaces recorded separately.',
        'region_basis': 'Surveyed candidate 3c3b4125 aperture and well rectangles in model metres. These are regression regions, not real-aircraft measurements.',
        'limits': [
            'A filled projection alone does not establish a flush or watertight closure.',
            'First-hit classification includes named fuselage, closure and well meshes only; full-scene photographic visibility is not asserted.',
            'Ray intersections treat triangles as two-sided geometry; renderer-specific back-face culling is not simulated.',
            'Fractions describe specified finite grids, not exact continuous areas. The cell-centre comparison reduces sensitivity to exact symmetry seams.',
            'Side rectangles can include space beyond original curved skin; visible well surfaces there can indicate a protruding well box rather than only a hole.',
            'An aperture redesigned to be smaller may be covered by retained fixed skin; this is recorded separately from moving closure coverage.',
            'Native oblique belly and side views remain required.',
        ],
        'models': [model_probe(args.root, mid) for mid in args.models],
        'acceptance_scope': 'Draft closed-gear endpoint in the specified native views, supported by projection diagnostics; not production acceptance.',
        'full_swept_clearance': 'NOT_PROVEN',
        'photographic_acceptance': 'NOT_ACCEPTED',
        'native_unreal': 'NOT_RUN',
    }
    review_path = args.root/args.native_review
    if review_path.is_file():
        reviews = json.loads(review_path.read_text())
        for model in result['models']:
            attach_native_review(args.root, model, reviews)
    statuses = [model['status'] for model in result['models']]
    result['status'] = 'PASS_SCOPED' if statuses and all(s == 'PASS_SCOPED' for s in statuses) else ('FAIL' if 'FAIL' in statuses else 'PENDING_NATIVE_REVIEW')
    (args.root/'qa'/'gear_closure_projected_coverage.json').write_text(json.dumps(result, indent=2)+'\n')
    for model in result['models']:
        print(model['id'], model['sha256'])
        for row in model['regions']:
            print(row['region'], 'cover', round(row['closure_only_coverage'], 5),
                  'exterior', round(row['closure_plus_fixed_fuselage_coverage'], 5),
                  'well first', round(row['well_surface_first_fraction'], 5))


if __name__ == '__main__':
    main()
