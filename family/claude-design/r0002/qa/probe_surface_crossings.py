#!/usr/bin/env python3
"""Sample actual exported triangles at selected mechanism states.

Strict, non-coplanar edge/triangle crossings are evidence for review. No hit is
not a full collision-clearance certificate: containment, coplanar overlap,
endpoint-only contact and motion between samples are outside this probe.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from validate_articulation import Asset, SAMPLES


class BVH:
    def __init__(self, triangles, leaf_size=24):
        self.t = triangles
        self.lo = triangles.min(1)
        self.hi = triangles.max(1)
        self.center = (self.lo+self.hi)/2
        self.nodes=[]
        def build(ids):
            lo,hi=self.lo[ids].min(0),self.hi[ids].max(0)
            idx=len(self.nodes); self.nodes.append(None)
            if len(ids)<=leaf_size:
                self.nodes[idx]=(lo,hi,None,None,ids)
            else:
                ax=int(np.argmax(np.ptp(self.center[ids],axis=0)))
                order=ids[np.argsort(self.center[ids,ax])]; mid=len(order)//2
                left,right=build(order[:mid]),build(order[mid:])
                self.nodes[idx]=(lo,hi,left,right,None)
            return idx
        if len(triangles): build(np.arange(len(triangles)))

    def query(self,lo,hi):
        found=[]; stack=[0] if self.nodes else []
        while stack:
            nlo,nhi,left,right,ids=self.nodes[stack.pop()]
            if np.any(nlo>hi) or np.any(nhi<lo): continue
            if ids is not None:
                found.extend(ids[np.all(self.lo[ids]<=hi,axis=1)&np.all(self.hi[ids]>=lo,axis=1)])
            else: stack.extend((left,right))
        return np.array(found,dtype=int)


def segment_triangle(start,end,triangles):
    """Moller-Trumbore segment intersections strictly inside both primitives."""
    direction=end-start
    e1=triangles[:,1]-triangles[:,0]; e2=triangles[:,2]-triangles[:,0]
    h=np.cross(direction,e2); det=np.einsum('ij,ij->i',e1,h)
    valid=np.abs(det)>1e-12
    inv=np.divide(1.,det,out=np.zeros_like(det),where=valid)
    s=start-triangles[:,0]; u=np.einsum('ij,ij->i',s,h)*inv
    q=np.cross(s,e1); v=np.einsum('ij,j->i',q,direction)*inv
    t=np.einsum('ij,ij->i',e2,q)*inv
    eps=1e-7
    valid &= (u>eps)&(v>eps)&(u+v<1-eps)&(t>eps)&(t<1-eps)
    return valid,start+t[:,None]*direction


def crossings(a,bvh,pivot=None,axis=None,max_examples=12):
    count=0; hinge=0; numeric=0; substantive=0; examples=[]; b=bvh.t
    for ia,tri in enumerate(a):
        ids=bvh.query(tri.min(0),tri.max(0))
        if not len(ids): continue
        cand=b[ids]; matched=np.zeros(len(ids),dtype=bool); pts=np.zeros((len(ids),3))
        for j in range(3):
            hit,p=segment_triangle(tri[j],tri[(j+1)%3],cand)
            pts[hit&~matched]=p[hit&~matched]; matched|=hit
        # Reverse edge direction to catch the complementary intersection family.
        e1=tri[1]-tri[0]; e2=tri[2]-tri[0]
        for j in range(3):
            start=cand[:,j]; direction=cand[:,(j+1)%3]-start
            h=np.cross(direction,e2); det=h@e1
            valid=np.abs(det)>1e-12; inv=np.divide(1.,det,out=np.zeros_like(det),where=valid)
            s=start-tri[0]; u=np.einsum('ij,ij->i',s,h)*inv
            q=np.cross(s,e1); v=np.einsum('ij,ij->i',direction,q)*inv
            t=(q@e2)*inv; eps=1e-7
            hit=valid&(u>eps)&(v>eps)&(u+v<1-eps)&(t>eps)&(t<1-eps)
            pp=start+t[:,None]*direction
            pts[hit&~matched]=pp[hit&~matched]; matched|=hit
        for k in np.flatnonzero(matched):
            count+=1
            near=False
            if pivot is not None and axis is not None:
                delta=pts[k]-pivot
                distance=np.linalg.norm(delta-np.dot(delta,axis)*axis)
                near=bool(distance<=.05)
                if near: hinge+=1
            # A separate numerical diagnostic, not a solid penetration depth.
            # Keep every crossing, including those below export precision.
            other=cand[k]
            na=np.cross(tri[1]-tri[0],tri[2]-tri[0]);na/=np.linalg.norm(na)
            nb=np.cross(other[1]-other[0],other[2]-other[0]);nb/=np.linalg.norm(nb)
            da=(tri-other[0])@nb; db=(other-tri[0])@na
            straddle=float(min(abs(da.min()),abs(da.max()),abs(db.min()),abs(db.max())))
            numerical=bool(straddle<=2e-5)
            if numerical: numeric+=1
            if not near and not numerical: substantive+=1
            if len(examples)<max_examples:
                examples.append({'triangle_a':int(ia),'triangle_b':int(ids[k]),'point_m':pts[k].tolist(),
                                 'within_declared_50mm_hinge_zone':near,'min_triangle_plane_straddle_m':straddle,
                                 'straddle_within_20um_export_tolerance':numerical})
    return {'strict_crossing_triangle_pairs':count,'within_declared_hinge_contact_zone':hinge,
            'outside_declared_hinge_zone':count-hinge,'within_20um_plane_straddle_tolerance':numeric,
            'above_20um_outside_hinge_zone':substantive,'examples':examples}


def triangles_for(asset,names,worlds):
    result=[]
    name_map={n['name']:i for i,n in enumerate(asset.nodes)}
    for name in names:
        if name not in name_map: continue
        i=name_map[name]; n=asset.nodes[i]
        if 'mesh' not in n: continue
        for p in asset.doc['meshes'][n['mesh']]['primitives']:
            pos=asset.accessor(p['attributes']['POSITION']).astype(float)
            w=worlds[i]; pos=pos@w[:3,:3].T+w[:3,3]
            ind=asset.accessor(p['indices']).reshape(-1,3)
            result.append(pos[ind])
    return np.concatenate(result) if result else np.zeros((0,3,3))


def model_probe(root,id,only_controls=None):
    path=root/'models'/f'{id}.glb'; asset=Asset(path)
    spec=json.loads((root/'articulation'/f'{id}.json').read_text())
    controls={c['id']:c for c in spec['controls']}
    anims={a['name']:a for a in asset.doc['animations']}
    names={n['name']:i for i,n in enumerate(asset.nodes)}
    def actual_names(requested):
        expanded=[]
        for n in requested:
            if n in names:
                parent=asset.parents.get(names[n])
                parent_name=asset.nodes[parent].get('name','') if parent is not None else ''
                if parent_name.startswith(('PIVOT_gear_door_', 'PIVOT_nose_forward_hatch_')):
                    # Fitted closure patches/caps move with the same actual
                    # pivot and belong to this named closure's swept surface.
                    expanded.extend(asset.nodes[i]['name'] for i in sorted(asset.descendants(parent)) if 'mesh' in asset.nodes[i])
                else: expanded.append(n)
            elif n+'_RIM' in names and n+'_TIRE' in names:
                expanded.extend([n+'_RIM',n+'_TIRE'])
            else: expanded.append(n)
        return list(dict.fromkeys(expanded))
    pairs=[
      ('cargo_ramp','lower_ramp_vs_upper_door',['CARGO_LOWER_RAMP_PRESERVED','CARGO_RAMP_INTERIOR_PRESERVED'],['CARGO_UPPER_DOOR_PRESERVED'],False),
      ('cargo_ramp','lower_ramp_vs_cabin',['CARGO_LOWER_RAMP_PRESERVED','CARGO_RAMP_INTERIOR_PRESERVED'],['CARGO_CABIN_PRESERVED'],True),
      ('cargo_ramp','lower_ramp_vs_skin',['CARGO_LOWER_RAMP_PRESERVED','CARGO_RAMP_INTERIOR_PRESERVED'],['fuselage'],True),
      ('cargo_ramp','upper_door_vs_cabin',['CARGO_UPPER_DOOR_PRESERVED'],['CARGO_CABIN_PRESERVED'],True),
      ('cargo_ramp','upper_door_vs_skin',['CARGO_UPPER_DOOR_PRESERVED'],['fuselage'],True),
      ('gear_nose','nose_wheels_vs_well',['NOSE_WHEELS_PRESERVED'],['GEAR_WELL_NOSE'],True),
      ('gear_nose','nose_wheels_vs_cover',['NOSE_WHEELS_PRESERVED'],['NOSE_GEAR_COVER_PRESERVED'],False),
      ('gear_nose','nose_wheels_vs_skin',['NOSE_WHEELS_PRESERVED'],['fuselage'],True),
      ('gear_nose','nose_cover_vs_skin',['NOSE_GEAR_COVER_PRESERVED'],['fuselage'],True),
      ('gear_nose','nose_wheels_vs_forward_hatches',['NOSE_WHEELS_PRESERVED'],['NOSE_WELL_LEFT_SOURCE_HATCH','NOSE_WELL_RIGHT_SOURCE_HATCH'],False),
      ('gear_nose','nose_forward_hatches_vs_skin',['NOSE_WELL_LEFT_SOURCE_HATCH','NOSE_WELL_RIGHT_SOURCE_HATCH'],['fuselage'],True),
      ('gear_nose','nose_forward_hatches_vs_aft_cover',['NOSE_WELL_LEFT_SOURCE_HATCH','NOSE_WELL_RIGHT_SOURCE_HATCH'],['NOSE_GEAR_COVER_PRESERVED'],False),
    ]
    for side in ('left','right'):
        up=side.upper(); wheels=[f'WHEEL_{up}_1_PRESERVED',f'WHEEL_{up}_2_PRESERVED']
        pairs += [(f'gear_{side}',f'{side}_wheels_vs_well',wheels,[f'GEAR_WELL_{up}'],True),
                  (f'gear_{side}',f'{side}_wheels_vs_cover',wheels,[f'MAIN_GEAR_COVER_{up}_PRESERVED'],False),
                  (f'gear_{side}',f'{side}_wheels_vs_skin',wheels,['fuselage'],True),
                  (f'gear_{side}',f'{side}_cover_vs_skin',[f'MAIN_GEAR_COVER_{up}_PRESERVED'],['fuselage'],True)]
    rest=asset.worlds(); cache={}; rows=[]
    for control,pair,an,bn,fixed in pairs:
        if only_controls and control not in only_controls:
            continue
        an,bn=actual_names(an),actual_names(bn)
        if not all(n in names for n in an+bn):
            rows.append({'pair':pair,'status':'NOT_RUN_NODE_MISSING'}); continue
        co=controls[control]; pivot=rest[names[co['node']]][:3,3]
        axis=np.asarray(co['axis'],dtype=float);axis/=np.linalg.norm(axis)
        if co['kind']=='translation': pivot=axis=None
        if pair.startswith('upper_door'):
            upper=controls['cargo_upper_door'];pivot=rest[names[upper['node']]][:3,3]
        if pair.endswith('cover_vs_skin'):
            side=pair.split('_')[0]
            cover=controls[f'gear_door_{side}']
            pivot=rest[names[cover['node']]][:3,3]
            axis=np.asarray(cover['axis'],dtype=float);axis/=np.linalg.norm(axis)
        if 'forward_hatches' in pair:
            # Two different hinge axes; retain every crossing without one shared
            # geometric contact exclusion that could pardon the wrong side.
            pivot=axis=None
        rows_one=[]
        sample_times=sorted(set(SAMPLES+([.95] if control=='gear_nose' else [])))
        for u in sample_times:
            worlds=asset.worlds(asset.sample(anims[co['clip']],u))
            ta=triangles_for(asset,an,worlds)
            if fixed:
                key=tuple(bn)
                if key not in cache:cache[key]=BVH(triangles_for(asset,bn,rest))
                bvh=cache[key]
            else:bvh=BVH(triangles_for(asset,bn,worlds))
            check=crossings(ta,bvh,pivot,axis)
            rows_one.append({'time':u,**check})
        total=sum(r['outside_declared_hinge_zone'] for r in rows_one)
        substantive=sum(r['above_20um_outside_hinge_zone'] for r in rows_one)
        numeric=sum(r['within_20um_plane_straddle_tolerance'] for r in rows_one)
        rows.append({'pair':pair,'control':control,'parts_a':an,'parts_b':bn,
                     'status':'CROSSINGS_REQUIRE_REVIEW' if substantive else ('ONLY_CONTACTS_WITHIN_20UM_PLANE_TOLERANCE' if total else 'NO_STRICT_CROSSINGS_OUTSIDE_HINGE_ZONE_AT_SAMPLES'),
                     'sampled_outside_hinge_crossings':total,'sampled_above_20um_outside_hinge_crossings':substantive,
                     'sampled_within_20um_plane_tolerance':numeric,'samples':rows_one})
        print(f'{id}: {pair}: {total} raw / {substantive} above20um crossing pairs outside hinge zone',flush=True)
    return {'id':id,'file':f'models/{id}.glb','sha256':hashlib.sha256(asset.data).hexdigest(),'pairs':rows,
            'status':'REVIEW_REQUIRED' if any(r['status']=='CROSSINGS_REQUIRE_REVIEW' for r in rows) else 'NO_CROSSINGS_ABOVE_EXPORT_TOLERANCE_DETECTED_SCOPED'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--models',nargs='+',default=['c130'])
    ap.add_argument('--controls',nargs='+',help='Limit a targeted repair check to these control IDs.')
    ap.add_argument('--output',default='sampled_surface_crossings.json',help='Filename under qa; use a separate file for partial checks.')
    args=ap.parse_args()
    result={'generated_utc':datetime.now(timezone.utc).isoformat(),'method':'BVH broadphase and strict non-coplanar edge/triangle intersections on actual transformed exported triangles',
            'sample_times':SAMPLES,'extra_sample_times_by_control':{'gear_nose':[.95]},'intentional_contact_policy':'All crossings retained. A 50 mm radius around each relevant declared hinge axis is separately counted as an authored possible-contact region, not automatically proven intentional. Translation gear has no excluded hinge region.',
            'numeric_contact_policy':'A 20 micrometre minimum triangle-plane straddle tolerance identifies contacts below candidate export precision. Raw crossings and examples remain recorded; this is not solid-volume penetration depth or general clearance.',
            'limitations':['Not a continuous swept-volume or penetration-depth solver.','Coplanar overlap, vertex/edge-only contact and complete containment are not detected.','No-hit samples do not certify clearance between samples.','Preserved internal surfaces may overlap intentionally; any crossing requires native visual/geometry review.','Only named cargo/gear pairs tested; kit and all other surface pairs excluded.'],
            'control_filter':args.controls,'production_clearance':'NOT_ACCEPTED','models':[model_probe(args.root,x,args.controls) for x in args.models]}
    (args.root/'qa'/args.output).write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
