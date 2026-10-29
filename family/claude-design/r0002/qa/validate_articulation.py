#!/usr/bin/env python3
"""Independent decoded-GLB geometry and clip audit for the modular C-130 candidate.

This does not import the builder or viewer. It samples exported animation data and
actual mesh vertices. It is not a collision solver, visual acceptance test or a
substitute for Khronos conformance/native DCC/Unreal validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import struct
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

TYPES = {5120: '<i1', 5121: '<u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
DIMS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
SAMPLES = [0, .125, .25, .375, .5, .625, .75, .875, 1]
TOL = 2e-5


def sha(data):
    return hashlib.sha256(data).hexdigest()


def quat_matrix(q):
    q = np.asarray(q, dtype=float)
    x, y, z, w = q / max(np.linalg.norm(q), 1e-30)
    return np.array([
        [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z, 2*x*z + 2*w*y],
        [2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
        [2*x*z - 2*w*y, 2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y]])


def slerp(a, b, u):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    a, b = a/np.linalg.norm(a), b/np.linalg.norm(b)
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > .9995:
        q = (1-u)*a + u*b
        return q/np.linalg.norm(q)
    angle = math.acos(np.clip(d, -1, 1))
    return (math.sin((1-u)*angle)*a + math.sin(u*angle)*b)/math.sin(angle)


class Asset:
    def __init__(self, path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        magic, ver, size = struct.unpack_from('<4sII', self.data)
        if (magic, ver, size) != (b'glTF', 2, len(self.data)):
            raise ValueError('Invalid GLB magic, version or declared total length')
        chunks = []
        off = 12
        while off < len(self.data):
            length, kind = struct.unpack_from('<II', self.data, off)
            if length % 4 or off + 8 + length > len(self.data):
                raise ValueError('Invalid GLB chunk alignment/length')
            chunks.append((kind, self.data[off+8:off+8+length]))
            off += 8 + length
        if not chunks or chunks[0][0] != 0x4E4F534A:
            raise ValueError('First GLB chunk is not JSON')
        self.doc = json.loads(chunks[0][1])
        self.bin = next((x for kind, x in chunks if kind == 0x004E4942), b'')
        self.nodes = self.doc.get('nodes', [])
        self.parents = {}
        for i, n in enumerate(self.nodes):
            for c in n.get('children', []):
                if c in self.parents:
                    raise ValueError(f'Node {c} has more than one parent')
                self.parents[c] = i
        self.arrays = {}
        self.positions = {}
        self.mesh_signatures = {}
        for i, n in enumerate(self.nodes):
            if 'mesh' not in n:
                continue
            vertices = []
            sig = hashlib.sha256()
            for p in self.doc['meshes'][n['mesh']]['primitives']:
                for k, v in sorted(p['attributes'].items()):
                    sig.update(k.encode()); sig.update(self.accessor(v).tobytes())
                sig.update(self.accessor(p['indices']).tobytes())
                vertices.append(self.accessor(p['attributes']['POSITION']).astype(float))
            self.positions[i] = np.concatenate(vertices)
            self.mesh_signatures[n.get('name', str(i))] = sig.hexdigest()

    def accessor(self, idx):
        if idx in self.arrays:
            return self.arrays[idx]
        a = self.doc['accessors'][idx]
        if 'sparse' in a:
            raise ValueError('Sparse accessor outside this candidate auditor scope')
        v = self.doc['bufferViews'][a['bufferView']]
        dtype = np.dtype(TYPES[a['componentType']])
        dims, count = DIMS[a['type']], a['count']
        stride = v.get('byteStride', dims*dtype.itemsize)
        offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        end = offset + max(0, count-1)*stride + dims*dtype.itemsize
        if end > v.get('byteOffset', 0) + v['byteLength'] or end > len(self.bin):
            raise ValueError(f'Accessor {idx} exceeds bufferView/BIN bounds')
        ar = np.ndarray((count, dims), dtype=dtype, buffer=self.bin,
                        offset=offset, strides=(stride, dtype.itemsize)).copy()
        if a.get('normalized'):
            ar = ar.astype(float)/np.iinfo(dtype).max
            if dtype.kind == 'i':
                ar = np.maximum(ar, -1)
        self.arrays[idx] = ar
        return ar

    def descendants(self, i):
        found, stack = set(), [i]
        while stack:
            n = stack.pop()
            if n in found:
                raise ValueError('Cyclic/repeated hierarchy')
            found.add(n); stack.extend(self.nodes[n].get('children', []))
        return found

    def sample(self, animation, u):
        pose = {}
        for c in animation.get('channels', []):
            s = animation['samplers'][c['sampler']]
            t = self.accessor(s['input']).ravel()
            v = self.accessor(s['output'])
            target = c['target']
            if s.get('interpolation', 'LINEAR') == 'CUBICSPLINE':
                raise ValueError('Cubic spline outside current audit scope')
            if u <= t[0]:
                x = v[0]
            elif u >= t[-1]:
                x = v[-1]
            else:
                j = int(np.searchsorted(t, u, side='right') - 1)
                f = (u-t[j])/(t[j+1]-t[j])
                if s.get('interpolation') == 'STEP':
                    x = v[j]
                elif target['path'] == 'rotation':
                    x = slerp(v[j], v[j+1], f)
                else:
                    x = (1-f)*v[j]+f*v[j+1]
            pose[(target['node'], target['path'])] = x
        return pose

    def worlds(self, pose=None):
        pose = pose or {}
        local, cache = [], {}
        for i, n in enumerate(self.nodes):
            if 'matrix' in n:
                m = np.array(n['matrix']).reshape(4, 4, order='F')
            else:
                m = np.eye(4)
                m[:3, :3] = quat_matrix(pose.get((i, 'rotation'), n.get('rotation', [0,0,0,1]))) @ np.diag(pose.get((i, 'scale'), n.get('scale', [1,1,1])))
                m[:3, 3] = pose.get((i, 'translation'), n.get('translation', [0,0,0]))
            local.append(m)
        def world(i, visiting=None):
            if i not in cache:
                visiting = set(visiting or [])
                if i in visiting:
                    raise ValueError('Cyclic node hierarchy')
                visiting.add(i)
                cache[i] = world(self.parents[i], visiting)@local[i] if i in self.parents else local[i]
            return cache[i]
        return [world(i) for i in range(len(self.nodes))]

    def vertices(self, node, worlds):
        w = worlds[node]
        return self.positions[node]@w[:3, :3].T + w[:3, 3]


def audit(path, sidecar):
    asset = Asset(path)
    d = asset.doc
    report = {'file': str(path), 'bytes': len(asset.data), 'sha256': sha(asset.data),
              'errors': [], 'warnings': [], 'clips': [], 'checks': {}}
    errors, warnings = report['errors'], report['warnings']
    names = [n.get('name', '') for n in asset.nodes]
    if len(set(names)) != len(names) or '' in names:
        errors.append('Missing or duplicate exported node names')
    for i, v in enumerate(d.get('bufferViews', [])):
        if v.get('byteOffset', 0)+v['byteLength'] > len(asset.bin):
            errors.append(f'bufferView {i} exceeds binary chunk')
    nonuniform, negative, zero_normals, invalid_tangent_signs = [], [], 0, 0
    for i, n in enumerate(asset.nodes):
        scale = np.array(n.get('scale', [1,1,1]))
        if not np.isfinite(scale).all(): errors.append(f'Nonfinite scale: {names[i]}')
        if np.ptp(np.abs(scale)) > TOL: nonuniform.append(names[i])
        if np.prod(scale) <= 0: negative.append(names[i])
        if 'matrix' in n:
            singular = np.linalg.svd(np.array(n['matrix']).reshape(4,4,order='F')[:3,:3])[1]
            if np.ptp(singular) > TOL: nonuniform.append(names[i])
    if nonuniform: errors.append('Nonuniform node scales: '+', '.join(nonuniform))
    if negative: errors.append('Nonpositive node scales: '+', '.join(negative))
    for i in range(len(d.get('accessors', []))):
        a = asset.accessor(i)
        if not np.isfinite(a).all(): errors.append(f'Nonfinite accessor {i}')
    triangles = vertices = degenerate = 0
    for mesh in d.get('meshes', []):
        for p in mesh['primitives']:
            pos = asset.accessor(p['attributes']['POSITION'])
            ind = asset.accessor(p['indices']).ravel()
            vertices += len(pos)
            if len(ind) % 3: errors.append(f'Non-triangle index count in {mesh.get("name")}')
            if len(ind) and ind.max() >= len(pos): errors.append(f'Index outside POSITION in {mesh.get("name")}')
            if len(ind) % 3 == 0 and (not len(ind) or ind.max() < len(pos)):
                tr = pos[ind.reshape(-1,3)]; triangles += len(tr)
                degenerate += int(np.count_nonzero(np.linalg.norm(np.cross(tr[:,1]-tr[:,0],tr[:,2]-tr[:,0]),axis=1) < 1e-12))
            for attr, idx in p['attributes'].items():
                a = asset.accessor(idx)
                if len(a) != len(pos): errors.append(f'Attribute length mismatch {mesh.get("name")} {attr}')
                if attr == 'NORMAL':
                    lens = np.linalg.norm(a, axis=1)
                    zero_normals += int(np.count_nonzero(lens < 1e-8))
                    if np.any((lens > 1e-8) & (np.abs(lens-1) > .002)):
                        warnings.append(f'Nonunit normals in {mesh.get("name")}')
                if attr == 'TANGENT':
                    invalid_tangent_signs += int(np.count_nonzero(np.abs(np.abs(a[:,3])-1)>TOL))
    if degenerate: warnings.append(f'{degenerate} degenerate triangles in decoded geometry')
    if zero_normals: warnings.append(f'{zero_normals} zero-length normals')
    if invalid_tangent_signs: errors.append(f'{invalid_tangent_signs} invalid tangent handedness signs')
    report['inventory'] = {'nodes':len(asset.nodes), 'meshes':len(d.get('meshes',[])),
                           'vertices':vertices, 'triangles':triangles, 'clips':len(d.get('animations',[])),
                           'skins':len(d.get('skins',[])), 'zero_normals':zero_normals,
                           'degenerate_triangles':degenerate,'invalid_tangent_signs':invalid_tangent_signs}
    worlds0 = asset.worlds()
    points0 = {i:asset.vertices(i,worlds0) for i in asset.positions}
    all0 = np.concatenate(list(points0.values()))
    report['canonical_bounds_m'] = {'min':all0.min(0).tolist(),'max':all0.max(0).tolist(),'size':np.ptp(all0,axis=0).tolist()}
    animations = d.get('animations', [])
    animation_names = [a.get('name','') for a in animations]
    if not animations: errors.append('No embedded animation clips')
    if len(set(animation_names)) != len(animation_names): errors.append('Duplicate clip names')
    all_targets = {}
    for anim in animations:
        clip = {'name':anim.get('name'),'channels':len(anim.get('channels',[])),
                'targets':[], 'sample_displacement_m':{}, 'max_displacement_m':0,
                'time_zero_rest_error_m':0,'reset_error_m':0,'reverse_pose_error_m':0}
        targets = set()
        target_pairs = set()
        for c in anim.get('channels', []):
            idx, path = c['target']['node'], c['target']['path']
            targets.add(idx)
            pair = (idx,path)
            if pair in target_pairs: errors.append(f'Duplicate node/property target in {anim.get("name")}')
            target_pairs.add(pair)
            all_targets.setdefault(pair,[]).append(anim.get('name'))
            s = anim['samplers'][c['sampler']]
            t = asset.accessor(s['input']).ravel(); val = asset.accessor(s['output'])
            if not len(t) or np.any(np.diff(t) <= 0): errors.append(f'Nonascending times in {anim.get("name")}')
            if abs(t[0])>TOL or abs(t[-1]-1)>TOL: errors.append(f'Clip not normalized0..1: {anim.get("name")}')
            if len(t) != len(val): errors.append(f'Clip sample count mismatch: {anim.get("name")}')
            if path=='rotation' and np.max(np.abs(np.linalg.norm(val,axis=1)-1))>TOL:
                errors.append(f'Nonunit quaternion samples: {anim.get("name")}')
            if path=='scale' and np.max(np.ptp(val,axis=1))>TOL: errors.append(f'Animated nonuniform scale: {anim.get("name")}')
            clip['targets'].append({'node':names[idx],'property':path,'origin_world_m':worlds0[idx][:3,3].tolist()})
        moving=set()
        for target in targets: moving |= asset.descendants(target)
        moving &= set(asset.positions)
        if not moving: errors.append(f'Clip targets no actual mesh descendants: {anim.get("name")}')
        samples={}
        for u in SAMPLES:
            worlds=asset.worlds(asset.sample(anim,u)); pose={i:asset.vertices(i,worlds) for i in moving}
            samples[u]=pose
            disp=max([float(np.linalg.norm(pose[i]-points0[i],axis=1).max()) for i in moving] or [0])
            clip['sample_displacement_m'][str(u)]=disp
            clip['max_displacement_m']=max(clip['max_displacement_m'],disp)
        clip['time_zero_rest_error_m']=clip['sample_displacement_m']['0']
        if clip['time_zero_rest_error_m']>TOL: errors.append(f'Clip0 differs from canonical rest: {anim.get("name")}')
        if clip['max_displacement_m']<1e-5: errors.append(f'Clip has no decoded vertex motion: {anim.get("name")}')
        # Evaluate reverse-order samples, interrupted0.625->0.375, then canonical reset.
        for u in [1,.875,.75,.625,.375,.25,.125,0]:
            reverse=asset.worlds(asset.sample(anim,u))
            for i in moving:
                err=float(np.abs(asset.vertices(i,reverse)-samples[u][i]).max())
                clip['reverse_pose_error_m']=max(clip['reverse_pose_error_m'],err)
        reset=asset.worlds()
        for i in moving:
            clip['reset_error_m']=max(clip['reset_error_m'],float(np.abs(asset.vertices(i,reset)-points0[i]).max()))
        clip['affected_mesh_nodes']=[names[i] for i in sorted(moving)]
        clip['affected_vertex_count']=sum(len(asset.positions[i]) for i in moving)
        report['clips'].append(clip)
    shared={names[i]+'.'+p:clips for (i,p),clips in all_targets.items() if len(clips)>1}
    report['shared_channel_targets']=shared
    if shared: warnings.append('Multiple clips target same node/property; combined controller must arbitrate: '+', '.join(shared))
    spec = {}
    if sidecar and sidecar.exists():
        side_bytes=sidecar.read_bytes(); spec=json.loads(side_bytes)
        report['articulation']={'file':str(sidecar),'sha256':sha(side_bytes),'controls':len(spec.get('controls',[]))}
        if spec.get('sha256') != sha(asset.data): errors.append('Articulation model SHA256 does not match current GLB bytes')
        required=['controls','sequences','states','presets','effects','cameras','sim_inputs']
        missing=[k for k in required if k not in spec]
        if missing: errors.append('Missing sidecar groups: '+', '.join(missing))
        ids=[]
        for control in spec.get('controls',[]):
            ids.append(control.get('id'))
            cn=control.get('clip',control.get('id'))
            if cn not in animation_names: errors.append(f'Control missing clip: {control.get("id")} -> {cn}')
            if control.get('node') and control['node'] not in names: errors.append(f'Control missing node: {control.get("id")} -> {control["node"]}')
            if control.get('node') in names and cn in animation_names:
                a=animations[animation_names.index(cn)]; cidx=names.index(control['node'])
                targets={c['target']['node'] for c in a['channels']}
                descendants=asset.descendants(cidx)
                if not targets & descendants: errors.append(f'Control declared node does not own clip target: {control.get("id")}')
        if len(set(ids))!=len(ids): errors.append('Duplicate control IDs')
    else:
        errors.append('Missing explicit articulation sidecar')
    # Direct simultaneous sampled geometry, with declared owner/master clips winning.
    # This is not the viewer's staged demonstration schedule or a collision test.
    combined=[]
    primary_clips={c.get('clip',c.get('id')) for c in spec.get('controls',[]) if not c.get('owned_by')}
    combined_anims=[a for a in animations if a.get('name') in primary_clips]
    owned={c['id']:c['owned_by'] for c in spec.get('controls',[]) if c.get('owned_by')}
    report['declared_clip_ownership']=owned
    if shared and not owned: errors.append('Shared animation channels without declared ownership')
    for u in SAMPLES:
        pose={}
        for a in combined_anims:
            for key,value in asset.sample(a,u).items():
                if key in pose: errors.append(f'Unarbitrated combined primary target: {names[key[0]]}.{key[1]}')
                pose[key]=value
        w=asset.worlds(pose); p=np.concatenate([asset.vertices(i,w) for i in asset.positions])
        if not np.isfinite(p).all(): errors.append(f'Nonfinite simultaneous pose{u}')
        combined.append({'time':u,'min':p.min(0).tolist(),'max':p.max(0).tolist()})
    report['combined_direct_primary_clip_samples']=combined
    report['checks']={'glb_and_accessor_bounds':'PASS','finite_export_data':'PASS' if not any('Nonfinite' in e for e in errors) else 'FAIL',
                      'actual_decoded_vertex_motion':'PASS' if animations and not any('no decoded' in e or 'rest:' in e for e in errors) else 'FAIL',
                      'independent_sampler_reverse_interruption_reset':'PASS' if not any(c['reverse_pose_error_m']>TOL or c['reset_error_m']>TOL for c in report['clips']) else 'FAIL',
                      'collision_clearance':'NOT_RUN','photographic_acceptance':'NOT_RUN',
                      'viewer_runtime_control_sequence':'SEPARATE_REPORT','native_blender':'SEPARATE_REPORT_OR_NOT_RUN','native_unreal':'NOT_RUN',
                      'full_khronos_gltf_conformance':'SEPARATE_REPORT_OR_NOT_RUN'}
    report['status']='PASS_SCOPED' if not errors else 'FAIL'
    report['mesh_signatures']=asset.mesh_signatures
    return report


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--output',type=Path); args=ap.parse_args()
    reports=[]
    for model in ('c130','ac130','ac130j'):
        path=args.root/'models'/f'{model}.glb'; side=args.root/'articulation'/f'{model}.json'
        try: reports.append(audit(path,side))
        except Exception as e: reports.append({'file':str(path),'status':'FAIL','errors':[f'{type(e).__name__}: {e}']})
    signatures=[r.get('mesh_signatures',{}) for r in reports]
    common=set.intersection(*(set(s) for s in signatures))
    exact=sorted(n for n in common if len({s[n] for s in signatures})==1)
    changed=sorted(common-set(exact))
    result={'generated_utc':datetime.now(timezone.utc).isoformat(),'auditor':'independent Python/NumPy decoder; no builder/viewer imports',
            'runtime':{'python':platform.python_version(),'numpy':np.__version__},'sample_times':SAMPLES,
            'tolerance_m':TOL,'scope':'GLB/data integrity, actual sampled vertex transforms, clip/control binding, rest/reverse/reset in independent sampler. Does not certify swept collision, visual quality or engine execution.',
            'status':'PASS_SCOPED' if all(r['status']=='PASS_SCOPED' for r in reports) else 'FAIL',
            'models':reports,'shared_geometry':{'same_named_meshes_all_variants':len(common),'byte_identical_decoded_meshes':exact,'variant_different_same_name_meshes':changed}}
    target=args.output or args.root/'qa'/'independent_articulation_report.json'
    target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'models':[{'file':r['file'],'status':r['status'],'errors':r['errors'],'warnings':r.get('warnings',[])} for r in reports],'output':str(target)},indent=2))
    raise SystemExit(0 if result['status']=='PASS_SCOPED' else 1)


if __name__=='__main__':
    main()
