#!/usr/bin/env python3
"""claude-design: targeted cargo closure sweep of the actual exported glTF clips.
Strict triangle crossings only; coplanar/contained contact and between-sample
motion are outside this audit. All observed contacts are retained in the report.
"""
from pathlib import Path
import sys,copy,json,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
from ramp_repair import _read,_array,_worlds,_mesh

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



def sample(doc,buf,t):
 d=copy.deepcopy(doc);a=next(a for a in d['animations'] if a['name']=='cargo_ramp')
 for c in a['channels']:
  s=a['samplers'][c['sampler']];times=_array(d,buf,s['input']).ravel();v=_array(d,buf,s['output']);j=min(max(int(np.searchsorted(times,t)-1),0),len(times)-2);f=float(np.clip((t-times[j])/(times[j+1]-times[j]),0,1));x=v[j]*(1-f)+v[j+1]*f
  if c['target']['path']=='rotation':
   u=v[j].astype(float);w=v[j+1].astype(float);dp=np.dot(u,w)
   if dp<0:w=-w;dp=-dp
   if dp<.9995:angle=math.acos(np.clip(dp,-1,1));x=(np.sin((1-f)*angle)*u+np.sin(f*angle)*w)/np.sin(angle)
   x/=np.linalg.norm(x)
  d['nodes'][c['target']['node']][c['target']['path']]=x.tolist()
 return d

def tris(d,b,names):
 worlds=_worlds(d);pieces=[]
 for n in names:
  _,_,p,f=_mesh(d,b,n,worlds);pieces.append(p[f])
 return np.concatenate(pieces)

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--output',default=str(ROOT/'qa/ramp-motion-audit.json'));a=p.parse_args();d,b,sha=_read(a.input)
 lower=['CARGO_LOWER_RAMP_PRESERVED','CARGO_RAMP_INTERIOR_PRESERVED']+[n['name'] for n in d['nodes'] if n['name'].startswith('CARGO_LOWER_RAMP_FLANGE_CAP_')];upper=['CARGO_UPPER_DOOR_PRESERVED'];skin=['fuselage']+[n['name'] for n in d['nodes'] if n['name'].startswith('CARGO_UPPER_APERTURE_JAMB_')];pairs=[('lower_vs_skin',lower,skin,'PIVOT_cargo_ramp'),('lower_vs_cabin',lower,['CARGO_CABIN_PRESERVED'],'PIVOT_cargo_ramp'),('upper_vs_skin',upper,skin,'PIVOT_cargo_upper_door'),('upper_vs_cabin',upper,['CARGO_CABIN_PRESERVED'],'PIVOT_cargo_upper_door'),('lower_vs_upper',lower,upper,'PIVOT_cargo_ramp')];rows=[];ws=_worlds(d)
 for label,an,bn,pivotname in pairs:
  ni=next(i for i,n in enumerate(d['nodes']) if n['name']==pivotname);pivot=ws[ni][:3,3];axis=np.array([1.,0,0]);samples=[];fixed='lower_vs_upper'!=label;tree=BVH(tris(d,b,bn)) if fixed else None
  for t in [0,.125,.25,.375,.5,.625,.75,.875,1]:
   pose=sample(d,b,t);bt=tree if fixed else BVH(tris(pose,b,bn));r=crossings(tris(pose,b,an),bt,pivot,axis,max_examples=4);samples.append({'time':t,**r})
  row={'pair':label,'samples':samples,'strict_crossing_count':sum(s['strict_crossing_triangle_pairs'] for s in samples),'outside_hinge_above_20um':sum(s['above_20um_outside_hinge_zone'] for s in samples)};rows.append(row);print(label,row['strict_crossing_count'],row['outside_hinge_above_20um'],flush=True)
 reset=sample(d,b,0);delta=max(float(np.max(np.abs(_worlds(reset)[i]-ws[i]))) for i in range(len(d['nodes'])))
 out={'author':'claude-design','input':a.input,'sha256':sha,'method':'Actual exported cargo_ramp animation evaluated at nine normalized samples; BVH broadphase and strict noncoplanar edge/triangle intersections. Original hinge/contact policy retained.','scope':'Lower ramp and interior / upper door / inherited skin and cabin, including fitted flange caps. No other pairs.','reset_world_matrix_delta':delta,'pairs':rows,'status':'SCOPED_CONTACT_REVIEW' if any(x['outside_hinge_above_20um'] for x in rows) else 'NO_SUBSTANTIVE_CROSSINGS_IN_SCOPED_SAMPLES','limitations':['No continuous swept volume, solid penetration-depth, coplanar overlap or complete containment proof.','50 mm hinge-zone contacts are reported, not certified as intentional.','Authored timing/geometry remain artist approximations.']};Path(a.output).write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
