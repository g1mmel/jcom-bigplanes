#!/usr/bin/env python3
"""Independently prove that vertex indexing preserves decoded model meaning.

Compares actual old/new GLB bytes without importing the builder. Every vertex
attribute is expanded in original triangle-corner order before hashing. Node
hierarchy/rest transforms, animation data, materials, images and sidecar control
semantics must also match. This supports explicit transfer of sampled geometry
observations; it is not a new photographic or native-engine acceptance test.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from validate_articulation import Asset


def sha(data):
    return hashlib.sha256(data).hexdigest()


def geometry(asset):
    rows = []
    for mi, mesh in enumerate(asset.doc['meshes']):
        for pi, primitive in enumerate(mesh['primitives']):
            indices = asset.accessor(primitive['indices']).reshape(-1)
            attributes = {}
            for name, ai in sorted(primitive['attributes'].items()):
                array = asset.accessor(ai)
                accessor = asset.doc['accessors'][ai]
                expanded = array[indices]
                attributes[name] = {
                    'componentType': accessor['componentType'], 'type': accessor['type'],
                    'normalized': accessor.get('normalized', False),
                    'expanded_shape': list(expanded.shape), 'dtype': str(expanded.dtype),
                    'expanded_corner_sha256': sha(expanded.tobytes()),
                }
            rows.append({'mesh': mi, 'primitive': pi, 'name': mesh.get('name'),
                         'mode': primitive.get('mode', 4), 'material': primitive.get('material'),
                         'triangle_corners': len(indices), 'attributes': attributes,
                         'targets': primitive.get('targets', [])})
    return rows


def animations(asset):
    rows = []
    for clip in asset.doc.get('animations', []):
        samplers = []
        for sampler in clip['samplers']:
            entry = {'interpolation': sampler.get('interpolation', 'LINEAR')}
            for key in ('input', 'output'):
                array = asset.accessor(sampler[key])
                entry[key] = {'shape': list(array.shape), 'dtype': str(array.dtype),
                              'sha256': sha(array.tobytes())}
            samplers.append(entry)
        rows.append({'name': clip.get('name'), 'channels': clip['channels'],
                     'samplers': samplers, 'extras': clip.get('extras')})
    return rows


def images(asset):
    rows = []
    for item in asset.doc.get('images', []):
        if 'bufferView' not in item:
            raise ValueError('This proof requires embedded image bytes.')
        view = asset.doc['bufferViews'][item['bufferView']]
        start = view.get('byteOffset', 0)
        data = asset.bin[start:start+view['byteLength']]
        rows.append({'mimeType': item['mimeType'], 'bytes': len(data), 'sha256': sha(data)})
    return rows


def verify(root, baseline, mid):
    old = Asset(baseline/'models'/f'{mid}.glb')
    new = Asset(root/'models'/f'{mid}.glb')
    old_geo, new_geo = geometry(old), geometry(new)
    checks = {'expanded_corner_attributes_and_triangle_order': old_geo == new_geo,
              'nodes_hierarchy_names_rest_and_extras': old.doc['nodes'] == new.doc['nodes'],
              'decoded_animation_channels_and_values': animations(old) == animations(new),
              'embedded_image_bytes': images(old) == images(new)}
    for key in ['asset', 'scene', 'scenes', 'skins', 'materials', 'textures', 'samplers',
                'cameras', 'extensionsUsed', 'extensionsRequired', 'extensions']:
        checks[key] = old.doc.get(key) == new.doc.get(key)
    old_side = json.loads((baseline/'articulation'/f'{mid}.json').read_text())
    new_side = json.loads((root/'articulation'/f'{mid}.json').read_text())
    checks['old_sidecar_binds_old_bytes'] = old_side.pop('sha256') == sha(old.data)
    checks['new_sidecar_binds_new_bytes'] = new_side.pop('sha256') == sha(new.data)
    checks['sidecar_semantics_except_model_hash'] = old_side == new_side
    count = lambda a: sum(len(a.accessor(p['attributes']['POSITION'])) for m in a.doc['meshes'] for p in m['primitives'])
    return {'id': mid, 'before_sha256': sha(old.data), 'after_sha256': sha(new.data),
            'before_bytes': len(old.data), 'after_bytes': len(new.data),
            'before_vertex_records': count(old), 'after_vertex_records': count(new),
            'checks': checks, 'status': 'PASS_EXACT_EQUIVALENCE' if all(checks.values()) else 'FAIL',
            'expanded_corner_fingerprints': new_geo, 'images': images(new)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--baseline', type=Path, required=True,
                    help='Retained pre-index revision directory containing models/ and articulation/.')
    args = ap.parse_args()
    baseline = args.baseline
    models = [verify(args.root, baseline, mid) for mid in ('c130', 'ac130', 'ac130j')]
    result = {'generated_utc': datetime.now(timezone.utc).isoformat(),
              'auditor': 'Independent Python decoder; no builder imports',
              'method': 'Exact expanded triangle-corner attribute bytes and order, plus unchanged hierarchy, animation data, images, materials and control semantics.',
              'status': 'PASS_EXACT_EQUIVALENCE' if all(m['status'] == 'PASS_EXACT_EQUIVALENCE' for m in models) else 'FAIL',
              'scope': 'Representation equivalence only. It permits explicitly recorded transfer of observations on identical geometry and poses, not invention of a native or photographic test.',
              'baseline_location_during_verification': str(baseline),
              'models': models}
    (args.root/'qa/exact_indexing_equivalence.json').write_text(json.dumps(result, indent=2)+'\n')
    for model in models:
        print(model['id'], model['status'], model['before_bytes'], '->', model['after_bytes'],
              'failed', [k for k, v in model['checks'].items() if not v])
    raise SystemExit(0 if result['status'] == 'PASS_EXACT_EQUIVALENCE' else 1)


if __name__ == '__main__':
    main()
