"""claude-design: fit the inherited lower cargo ramp to its actual aperture.

Source r0003 reconstruction leaves a 0.09--0.16 m open lateral seam and an
outboard corner flange. This is a local mesh-fit repair, not a real aircraft
engineering tolerance. The central ramp deck, rear upper door and all hinges,
clips and sequence timing are preserved. Run after assembling the graph.
"""
from __future__ import annotations
import copy,json,struct,hashlib
from pathlib import Path
import numpy as np

DT={5126:np.dtype('<f4'),5125:np.dtype('<u4'),5123:np.dtype('<u2'),5121:np.dtype('u1')}
DIM={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}

def _array(doc,buf,i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];n=DIM[a['type']];dt=DT[a['componentType']]
 return np.ndarray((a['count'],n),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*dt.itemsize),dt.itemsize)).copy()

def _put(doc,buf,i,a):
 acc=doc['accessors'][i];v=doc['bufferViews'][acc['bufferView']];n=DIM[acc['type']];dt=DT[acc['componentType']]
 view=np.ndarray((acc['count'],n),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+acc.get('byteOffset',0),strides=(v.get('byteStride',n*dt.itemsize),dt.itemsize));view[:]=a
 acc['min']=view.min(0).tolist();acc['max']=view.max(0).tolist()

def _worlds(doc):
 parents={j:i for i,q in enumerate(doc['nodes']) for j in q.get('children',[])};cache={}
 def w(i):
  if i in cache:return cache[i]
  q=doc['nodes'][i]
  if 'matrix' in q:m=np.array(q['matrix']).reshape(4,4,order='F')
  else:
   m=np.eye(4);x,y,z,qw=q.get('rotation',[0,0,0,1]);r=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*qw,2*x*z+2*y*qw],[2*x*y+2*z*qw,1-2*x*x-2*z*z,2*y*z-2*x*qw],[2*x*z-2*y*qw,2*y*z+2*x*qw,1-2*x*x-2*y*y]])
   m[:3,:3]=r@np.diag(q.get('scale',[1,1,1]));m[:3,3]=q.get('translation',[0,0,0])
  cache[i]=(w(parents[i])@m if i in parents else m);return cache[i]
 for i in range(len(doc['nodes'])):w(i)
 return cache

def _mesh(doc,buf,name,worlds):
 i=next(i for i,n in enumerate(doc['nodes']) if n['name']==name);node=doc['nodes'][i];pr=doc['meshes'][node['mesh']]['primitives'][0];p=_array(doc,buf,pr['attributes']['POSITION']).astype(float);f=_array(doc,buf,pr['indices']).astype(int).reshape(-1,3);w=worlds[i];return i,pr,p@w[:3,:3].T+w[:3,3],f

def _section(p,f,z):
 tris=p[f];d=tris[:,:,2]-z;tris=tris[(d.min(1)<0)&(d.max(1)>0)];out=[]
 for tri in tris:
  for a,b in zip(tri,np.roll(tri,-1,axis=0)):
   if(a[2]-z)*(b[2]-z)<0:out.append(a+(b-a)*(z-a[2])/(b[2]-a[2]))
 return np.array(out).reshape(-1,3)

def _edges(body,ramp,stations,upper=False):
 rows=[]
 for z in stations:
  a=_section(*body,z);a=a[(a[:,0]>(1.4 if upper else 1.5))&(a[:,0]<2.4)&(a[:,1]<(4.0 if upper else 3.0))]
  b=_section(*ramp,z);b=b[b[:,0]>1.45]
  if not len(a) or not len(b):continue
  target=a[np.argmin(a[:,1])];outer=b[b[:,0]>b[:,0].max()-1e-4];edge=outer[np.argmax(outer[:,1])]
  rows.append([float(z),*target[:2],*edge[:2]])
 return np.array(rows)

def _append_accessor(doc,buf,array,kind,index=False):
 a=np.asarray(array,dtype='<u4' if index else '<f4');n=1 if a.ndim==1 else a.shape[1]
 while len(buf)%4:buf.append(0)
 vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(buf),'byteLength':a.nbytes,'target':34963 if index else 34962});buf.extend(a.tobytes())
 ar=a.reshape(-1,n);rec={'bufferView':vi,'componentType':5125 if index else 5126,'count':len(a),'type':kind,'min':ar.min(0).tolist(),'max':ar.max(0).tolist()};doc['accessors'].append(rec);return len(doc['accessors'])-1

def _plane_points(p,f,axis,station):
 """Closed triangle/plane intersections, including vertices on the plane."""
 ts=p[f];pieces=[]
 for j in range(3):
  a=ts[:,j];b=ts[:,(j+1)%3];den=b[:,axis]-a[:,axis]
  t=np.divide(station-a[:,axis],den,out=np.full(len(a),np.inf),where=np.abs(den)>1e-12)
  ok=(t>=-1e-8)&(t<=1+1e-8)
  pieces.append(a[ok]+np.clip(t[ok],0,1)[:,None]*(b[ok]-a[ok]))
  pieces.append(a[np.abs(a[:,axis]-station)<1e-8])
 return np.concatenate(pieces) if pieces else np.empty((0,3))

def _closest_triangle_point(point,triangles):
 a,b,c=triangles[:,0],triangles[:,1],triangles[:,2];ab=b-a;ac=c-a;n=np.cross(ab,ac);nn=np.sum(n*n,1)
 q=point-n*np.divide(np.sum((point-a)*n,1),nn,out=np.zeros(len(n)),where=nn>1e-20)[:,None]
 d00=np.sum(ab*ab,1);d01=np.sum(ab*ac,1);d11=np.sum(ac*ac,1);d20=np.sum((q-a)*ab,1);d21=np.sum((q-a)*ac,1);den=d00*d11-d01*d01
 u=np.divide(d11*d20-d01*d21,den,out=np.zeros(len(n)),where=np.abs(den)>1e-20);v=np.divide(d00*d21-d01*d20,den,out=np.zeros(len(n)),where=np.abs(den)>1e-20)
 good=(u>=0)&(v>=0)&(u+v<=1)&(nn>1e-20);dist=np.linalg.norm(q-point,axis=1);dist[~good]=np.inf;candidate=q.copy()
 for aa,bb in [(a,b),(b,c),(c,a)]:
  edge=bb-aa;t=np.clip(np.sum((point-aa)*edge,1)/np.maximum(np.sum(edge*edge,1),1e-30),0,1);pt=aa+t[:,None]*edge;dd=np.linalg.norm(pt-point,axis=1);sel=dd<dist;dist[sel]=dd[sel];candidate[sel]=pt[sel]
 i=int(np.argmin(dist));return float(dist[i]),candidate[i]

def measure_ramp_corners(doc,buf):
 """Aft-join metric, deliberately separate from the long lateral seam metric."""
 worlds=_worlds(doc);names=['fuselage','CARGO_LOWER_RAMP_PRESERVED','CARGO_UPPER_DOOR_PRESERVED','CARGO_UPPER_APERTURE_JAMB_PORT','CARGO_UPPER_APERTURE_JAMB_STARBOARD'];parts={n:_mesh(doc,buf,n,worlds)[2:] for n in names};triangles={n:p[f] for n,(p,f) in parts.items()}
 report={'method':'201 aperture-boundary stations per side over Z6.2454..6.40; exact nearest point to triangles of lower ramp, upper leaf and fixed jambs. Aft lip sampled independently in transverse sections. Asset fit, not real aircraft tolerances.','sides':{},'aft_lip_samples':[]}
 for side,sgn in [('port',-1),('starboard',1)]:
  rows=[]
  for z in np.linspace(6.2454,6.40,201):
   q=_plane_points(*parts['fuselage'],2,z);q=q[(q[:,0]*sgn>1.4)&(q[:,0]*sgn<2)&(q[:,1]<2.6)];p=q[np.argmin(q[:,1])]
   choices=[(distance,name,near) for name in names[1:] for distance,near in [_closest_triangle_point(p,triangles[name])]];distance,name,near=min(choices,key=lambda r:r[0]);rows.append({'station_z_m':float(z),'distance_m':distance,'aperture_point_m':p.tolist(),'nearest_closure':name,'nearest_point_m':near.tolist()})
  report['sides'][side]={'samples':len(rows),'maximum':max(rows,key=lambda r:r['distance_m']),'median_distance_m':float(np.median([r['distance_m']for r in rows])),'over_20mm_samples':sum(r['distance_m']>.02 for r in rows)}
  for ax in [0.,.5,1.,1.2,1.3,1.4,1.45,1.49,1.52,1.55,1.6,1.64]:
   q=_plane_points(*parts['CARGO_LOWER_RAMP_PRESERVED'],0,sgn*ax);q=q[(q[:,2]>6)&(q[:,2]<6.6)]
   if not len(q):continue
   p=q[np.argmax(q[:,2])];choices=[(distance,name,near)for name in names[2:]for distance,near in [_closest_triangle_point(p,triangles[name])]];distance,name,near=min(choices,key=lambda r:r[0]);report['aft_lip_samples'].append({'side':side,'abs_x_m':ax,'distance_m':distance,'lower_lip_m':p.tolist(),'nearest_closure':name,'nearest_point_m':near.tolist()})
 return report

def repair_ramp_corners_glb(doc,buf):
 """Finish the local outer closing lip and fixed jamb tips; leave rig/deck intact."""
 from gltf_core import make_mesh,Mesh,plane_split,merge
 if doc['asset'].get('extras',{}).get('ramp_corner_repair_r0004'):raise ValueError('Corner repair already applied')
 worlds=_worlds(doc);_,_,bp,bf=_mesh(doc,buf,'fuselage',worlds);i,pr,p,f=_mesh(doc,buf,'CARGO_LOWER_RAMP_PRESERVED',worlds);_,_,up,uf=_mesh(doc,buf,'CARGO_UPPER_DOOR_PRESERVED',worlds)
 before=measure_ramp_corners(doc,buf);oldattrs={k:_array(doc,buf,a).astype(float) for k,a in pr['attributes'].items()};oldattrs['POSITION']=p
 # The inherited aft skin spans the curved closing contour with very broad
 # triangles. Add only local cross-stations before fitting that contour, so
 # interpolation cannot turn a corner correction into a new raised ridge.
 work=Mesh('CARGO_LOWER_RAMP_PRESERVED',oldattrs,f,pr.get('material',0));aft,front=plane_split(work,[0,0,1],6.05)
 for x in [1.04,1.10,1.14,1.20,1.25,1.30,1.3437,1.40,1.45,1.49,1.49731,1.52,1.55,1.58,1.60,1.625,1.64,1.65,1.675,1.70,1.73]:
  for s in [-1,1]:a,b=plane_split(aft,[1,0,0],s*x);aft=merge([a,b],aft.name)
 work=merge([front,aft],work.name);p=work.p.copy();f=work.faces;oldattrs=work.attrs;original=p.copy();changes=[];profiles={}
 for side,sgn in [('PORT',-1),('STARBOARD',1)]:
  ax=np.abs(p[:,0]);side_mask=p[:,0]*sgn>0
  xs=np.unique(np.r_[np.linspace(1.04,1.756,241),ax[side_mask&(p[:,2]>6.16)&(ax>1.04)]])
  old=[]
  for x in xs:
   section=_plane_points(original,f,0,sgn*x);section=section[(section[:,2]>6.16)&(section[:,2]<6.5)&(section[:,1]<2.28)]
   if not len(section):continue
   far=section[section[:,2]>section[:,2].max()-1e-7];q=far[np.argmin(far[:,1])];old.append([x,q[1],q[2]])
  old=np.asarray(old);xmax=float(np.max(up[:,0]*sgn));ux=np.unique(np.r_[np.linspace(0,xmax,181),np.abs(up[(up[:,0]*sgn>0)&(up[:,2]<6.45),0])]);lead=[]
  for x in ux:
   section=_plane_points(up,uf,0,sgn*x);section=section[section[:,2]<6.5]
   if len(section):q=section[np.argmin(section[:,1])];lead.append([x,q[1],q[2]])
  lead=np.asarray(lead);section=_plane_points(bp,bf,2,6.30);section=section[(section[:,0]*sgn>1.4)&(section[:,0]*sgn<2)&(section[:,1]<2.6)];a=section[np.argmin(section[:,1])];outer_x=abs(a[0])-.008;outer_y=a[1]-.004
  endpoint=np.array([xmax,lead[-1,1]-.002,lead[-1,2]-.004]);target=old.copy();core=old[:,0]<=xmax;target[core,1]=np.interp(old[core,0],lead[:,0],lead[:,1])-.002;target[core,2]=np.interp(old[core,0],lead[:,0],lead[:,2])-.004
  corner=(old[:,0]>xmax)&(old[:,0]<outer_x);u=(old[corner,0]-xmax)/(outer_x-xmax);target[corner,1]=endpoint[1]*(1-u)+outer_y*u;target[corner,2]=endpoint[2]*(1-u)+6.30*u
  # The preceding long lateral skirt is already fitted. Blend the two target
  # endpoints back into its measured boundary without extending into the floor.
  outside=old[:,0]>=outer_x;fade=np.clip((1.754-old[outside,0])/(1.754-outer_x),0,1);target[outside,1]=old[outside,1]+(outer_y-np.interp(outer_x,old[:,0],old[:,1]))*fade;target[outside,2]=old[outside,2]+(6.30-np.interp(outer_x,old[:,0],old[:,2]))*fade
  rear=np.interp(ax,old[:,0],old[:,2]);weight=np.clip((p[:,2]-(rear-.24))/.24,0,1);weight=weight*weight*(3-2*weight);width=np.clip((ax-1.04)/.10,0,1);width=width*width*(3-2*width);baseweight=weight*width*side_mask*(p[:,2]>6.05)
  height=p[:,1]-np.interp(ax,old[:,0],old[:,1]);depth=np.clip((.045-height)/.025,0,1);weight=baseweight*depth
  dy=np.interp(ax,old[:,0],target[:,1]-old[:,1]);dz=np.interp(ax,old[:,0],target[:,2]-old[:,2]);p[:,1]+=dy*weight;p[:,2]+=dz*weight
  # Raised hidden rim pieces otherwise sweep aft through the short fixed
  # corner before the ramp drops. Bevel that receiving edge forward; retain
  # the fitted exterior skin and the entirely separate original cargo deck.
  inner=np.clip((height-.025)/.07,0,1);inner=inner*inner*(3-2*inner);bevel=np.clip((ax-1.22)/.15,0,1);bevel=bevel*bevel*(3-2*bevel)
  p[:,2]-=.065*baseweight*inner*bevel
  profiles[side]={'sign':sgn,'lead':lead,'target':target,'outer_x':outer_x,'outer_y':outer_y,'endpoint':endpoint}
 w=worlds[i];local=(p-w[:3,3])@np.linalg.inv(w[:3,:3]).T;attrs=oldattrs.copy();attrs['POSITION']=local
 fn=np.cross(local[f[:,1]]-local[f[:,0]],local[f[:,2]]-local[f[:,0]]);groupkey=np.c_[np.round(original,6),np.round(oldattrs['NORMAL'],2)];_,groups=np.unique(groupkey,axis=0,return_inverse=True);gn=np.zeros((groups.max()+1,3))
 for k in range(3):np.add.at(gn,groups[f[:,k]],fn)
 normal=gn[groups];ln=np.linalg.norm(normal,axis=1);good=ln>1e-12;normal[good]/=ln[good,None];normal[~good]=oldattrs['NORMAL'][~good];attrs['NORMAL']=normal
 if 'TANGENT'in attrs:
  tan=attrs['TANGENT'];tan[:,:3]-=np.sum(tan[:,:3]*normal,1)[:,None]*normal;tan[:,:3]/=np.maximum(np.linalg.norm(tan[:,:3],axis=1)[:,None],1e-12)
 exportp=local.astype('<f4').astype(float);area=np.linalg.norm(np.cross(exportp[f[:,1]]-exportp[f[:,0]],exportp[f[:,2]]-exportp[f[:,0]]),axis=1);f=f[area>2e-12]
 arrays={k:np.ascontiguousarray(v,dtype='<f4') for k,v in attrs.items()};keys=sorted(arrays);packed=np.concatenate([arrays[k].view(np.uint8).reshape(len(local),-1) for k in keys],axis=1);records=np.ascontiguousarray(packed).view(np.dtype((np.void,packed.shape[1]))).ravel();_,first,remap=np.unique(records,return_index=True,return_inverse=True);attrs={k:v[first]for k,v in arrays.items()};f=remap[f]
 for key,value in attrs.items():pr['attributes'][key]=_append_accessor(doc,buf,value,{2:'VEC2',3:'VEC3',4:'VEC4'}[value.shape[1]])
 pr['indices']=_append_accessor(doc,buf,f.ravel(),'SCALAR',True)
 moved=np.linalg.norm(p-original,axis=1);changes.append({'node':'CARGO_LOWER_RAMP_PRESERVED','moved_vertices':int((moved>1e-7).sum()),'maximum_displacement_m':float(moved.max()),'central_abs_x_le_1_04_max_displacement_m':float(moved[np.abs(original[:,0])<=1.04].max())})
 # Short tapered fixed corner gussets join the actual skin to the closing
 # perimeter. They are part of the bounded aperture frame, never moving leaves.
 for side,profile in profiles.items():
  sgn=profile['sign'];mir=np.array([sgn,1,1]);cv=_edges((bp*mir,bf),(up*mir,uf),np.linspace(6.36,10.07,110),upper=True);vs=[];fs=[];target=profile['target'];lead=profile['lead'];corner=target[(target[:,0]>=lead[-1,0])&(target[:,0]<=profile['outer_x'])];order=np.argsort(corner[:,2]);corner=corner[order]
  for zz in np.linspace(6.30,6.36,25)[:-1]:
   q=_plane_points(bp,bf,2,zz);q=q[(q[:,0]*sgn>1.4)&(q[:,0]*sgn<2)&(q[:,1]<2.6)];a=q[np.argmin(q[:,1])]
   inner_z=zz-.003;x=np.interp(inner_z,corner[:,2],corner[:,0])+.003;y=np.interp(inner_z,corner[:,2],corner[:,1])+.002
   if zz>=lead[-1,2]:x=lead[-1,0]+.003;y=lead[-1,1]+(zz-lead[-1,2])*(cv[0,4]-lead[-1,1])/(6.36-lead[-1,2])
   b=np.array([sgn*x,y,zz]);blend=np.clip((zz-6.30)/.005,0,1);b=a+(b-a)*blend;vs.extend([a,b,a+[0,.018,0],b+[0,.018,0]])
  for zz,tx,ty,ox,oy in cv:
   a=np.array([sgn*tx,ty,zz]);b=np.array([sgn*(ox+.003),oy,zz]);vs.extend([a,b,a+[0,.018,0],b+[0,.018,0]])
  for k in range(len(vs)//4-1):
   a=4*k;b=a+4
   for q in [(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)]:fs.extend([(q[0],q[1],q[2]),(q[0],q[2],q[3])])
  for q in [(0,1,3,2),(len(vs)-4,len(vs)-2,len(vs)-1,len(vs)-3)]:fs.extend([(q[0],q[1],q[2]),(q[0],q[2],q[3])])
  name='CARGO_UPPER_APERTURE_JAMB_'+side;ni,prim,oldp,oldf=_mesh(doc,buf,name,worlds);mesh=make_mesh(name,vs,fs,prim['material']);ff=mesh.faces;pp=mesh.p.astype('<f4').astype(float);area=np.linalg.norm(np.cross(pp[ff[:,1]]-pp[ff[:,0]],pp[ff[:,2]]-pp[ff[:,0]]),axis=1);ff=ff[area>2e-12]
  for key,value in mesh.attrs.items():prim['attributes'][key]=_append_accessor(doc,buf,value,{2:'VEC2',3:'VEC3',4:'VEC4'}[value.shape[1]])
  prim['indices']=_append_accessor(doc,buf,ff.ravel(),'SCALAR',True);changes.append({'node':name,'forward_extension_m':.06,'original_aft_frame_profile_preserved':True})
 report={'author':'claude-design','method':'Local outer lower-lip profile fitted to actual upper-leaf leading skin and inherited aperture; short fixed jamb tips finish the triangular corner. Central deck, node hierarchy/TRS and all clips remain untouched.','before':before,'after':measure_ramp_corners(doc,buf),'changes':changes,'geometry_changed_nodes':[x['node']for x in changes],'limitations':'Artist-authored local reveals; rest/native appearance and current-export sampled contact review required.'}
 doc['asset'].setdefault('extras',{})['ramp_corner_repair_r0004']=report;doc['buffers'][0]['byteLength']=len(buf);return report

def repair_ramp_glb(doc,buf):
 """Mutate document and mutable BIN buffer; return scoped fit evidence."""
 from gltf_core import Mesh,plane_split,merge,extract,boxplanes,make_mesh
 if not isinstance(buf,bytearray):raise TypeError('buf must be bytearray')
 if doc['asset'].get('extras',{}).get('ramp_repair_r0004'):raise ValueError('Ramp repair already applied')
 worlds=_worlds(doc);_,_,bp,bf=_mesh(doc,buf,'fuselage',worlds);_,_,rp,rf=_mesh(doc,buf,'CARGO_LOWER_RAMP_PRESERVED',worlds);_,_,up,uf=_mesh(doc,buf,'CARGO_UPPER_DOOR_PRESERVED',worlds)
 stations=np.unique(np.r_[np.linspace(2.76,6.30,180),2.8,3.1514,3.1516,3.5696,3.5698,5.131,5.151,5.84,6.245,6.27,6.3])
 curve=_edges((bp,bf),(rp,rf),stations);upper_curve=_edges((bp,bf),(up,uf),np.linspace(6.36,10.07,110),upper=True);mirror=np.array([-1,1,1]);upper_port_curve=_edges((bp*mirror,bf),(up*mirror,uf),np.linspace(6.36,10.07,110),upper=True)
 changes=[]
 for i,n in enumerate(doc['nodes']):
  name=n['name'];is_upper=name=='CARGO_UPPER_DOOR_PRESERVED'
  if not(name=='CARGO_LOWER_RAMP_PRESERVED' or name.startswith('CARGO_LOWER_RAMP_FLANGE_CAP_')):continue
  i,pr,p,f=_mesh(doc,buf,name,worlds);attrs={k:_array(doc,buf,ai).astype(float) for k,ai in pr['attributes'].items()};attrs['POSITION']=p
  work=Mesh(name,attrs,f,pr.get('material',0))
  # Source perimeter spans large triangles across several aperture bends.
  # Subdivide on actual source station changes before applying the fit field.
  cuts=([6.3908,6.789,7.0087,7.6184,8.4312,9.086,10.0547] if is_upper else [2.779,3.1514,3.1516,3.5696,3.5698,3.7165,4.2,4.8,5.1316,5.1320,5.15,5.24,5.84,6.2453,6.30])
  for zz in cuts:
   a,b=plane_split(work,[0,0,1],zz);work=merge([a,b],name)
  p=work.p.copy();original=p.copy();f=work.faces;ax=np.abs(p[:,0]);cv=upper_curve if is_upper else curve;z=cv[:,0];old=cv[:,3:5];target=cv[:,1:3].copy()
  if is_upper:target[:,0]-=.003
  else:target[:,1]-=.004
  delta=target-old;edge=np.interp(p[:,2],z,old[:,0]);inner=1.10 if is_upper else 1.46;t=np.clip((ax-inner)/np.maximum(edge-inner,.02),0,1);t=t*t*(3-2*t)
  if not is_upper:
   end=np.minimum(np.clip((p[:,2]-2.735)/.025,0,1),np.clip((6.365-p[:,2])/.065,0,1));t*=end
  dx=np.interp(p[:,2],z,delta[:,0]);dy=np.interp(p[:,2],z,delta[:,1])
  if is_upper:
   pc=upper_port_curve;pd=pc[:,1:3]-pc[:,3:5];pd[:,0]-=.003;side=p[:,0]<0;dx[side]=np.interp(p[side,2],pc[:,0],pd[:,0]);dy[side]=np.interp(p[side,2],pc[:,0],pd[:,1])
  p[:,0]+=np.sign(p[:,0])*dx*t;p[:,1]+=dy*t
  if not is_upper:
   allowed=np.interp(p[:,2],curve[:,0],curve[:,1])-.008;inzone=(p[:,2]>2.78)&(p[:,2]<6.30);p[inzone,0]=np.sign(p[inzone,0])*np.minimum(np.abs(p[inzone,0]),allowed[inzone])
  # Match the exterior aft edge to the measured upper-door leading contour.
  # The original lower edge stops 44--58 mm short; preserve the actual cargo
  # deck and blend only the underside/closing lip over the last 0.35 m.
  if not is_upper:
   lx=np.array([0.,.5501,1.03425,1.52033]);ly=np.array([1.74349,1.76168,1.82523,1.99169]);lz=np.array([6.38093,6.37496,6.35403,6.29932])
   ux=np.array([0.,.5903,1.0043,1.3437,1.4973]);uy=np.array([1.801316,1.8204,1.8765,1.966,2.0269]);uz=np.array([6.4251,6.4196,6.4014,6.3739,6.3556])
   oldz=np.interp(ax,lx,lz);fade=np.clip((original[:,2]-(oldz-.35))/.35,0,1);fade=fade*fade*(3-2*fade)
   depth=.9819+.354*(original[:,2]-2.7427)-original[:,1];weight=np.clip((depth-.10)/.20,0,1);width=np.clip((1.57-ax)/.12,0,1);fitting=fade*weight*width
   p[:,1]+=(np.interp(ax,ux,uy)-np.interp(ax,lx,ly)-.002)*fitting
   p[:,2]+=(np.interp(ax,ux,uz)-oldz-.004)*fitting
   allowed=np.interp(p[:,2],curve[:,0],curve[:,1])-.008;inzone=(p[:,2]>2.78)&(p[:,2]<6.31);allowed[np.abs(p[:,2]-3.5697)<.0003]=1.746;p[inzone,0]=np.sign(p[inzone,0])*np.minimum(np.abs(p[inzone,0]),allowed[inzone])
  w=worlds[i];local=(p-w[:3,3])@np.linalg.inv(w[:3,:3]).T;work.attrs['POSITION']=local
  normal=np.zeros_like(local);fn=np.cross(local[f[:,1]]-local[f[:,0]],local[f[:,2]]-local[f[:,0]])
  groupkey=np.c_[np.round(original,6),np.round(work.attrs.get('NORMAL',normal),2)];_,groups=np.unique(groupkey,axis=0,return_inverse=True);gn=np.zeros((groups.max()+1,3))
  for k in range(3):np.add.at(gn,groups[f[:,k]],fn)
  normal=gn[groups]
  length=np.linalg.norm(normal,axis=1);good=length>1e-12;normal[good]/=length[good,None]
  if 'NORMAL'in work.attrs:normal[~good]=work.attrs['NORMAL'][~good];work.attrs['NORMAL']=normal
  if 'TANGENT'in work.attrs:
   tan=work.attrs['TANGENT'];tan[:,:3]-=np.sum(tan[:,:3]*normal,axis=1)[:,None]*normal;ln=np.linalg.norm(tan[:,:3],axis=1);tan[:,:3]/=np.maximum(ln[:,None],1e-12);work.attrs['TANGENT']=tan
  exportp=local.astype('<f4').astype(float);area=np.linalg.norm(np.cross(exportp[f[:,1]]-exportp[f[:,0]],exportp[f[:,2]]-exportp[f[:,0]]),axis=1);f=f[area>2e-12]
  arrays={k:np.ascontiguousarray(v,dtype='<f4') for k,v in work.attrs.items()};keys=sorted(arrays);packed=np.concatenate([arrays[k].view(np.uint8).reshape(len(local),-1) for k in keys],axis=1);records=np.ascontiguousarray(packed).view(np.dtype((np.void,packed.shape[1]))).ravel();_,first,remap=np.unique(records,return_index=True,return_inverse=True);work.attrs={k:v[first] for k,v in arrays.items()};f=remap[f]
  for key,arr in work.attrs.items():pr['attributes'][key]=_append_accessor(doc,buf,arr,{2:'VEC2',3:'VEC3',4:'VEC4'}[arr.shape[1]])
  pr['indices']=_append_accessor(doc,buf,f.flatten(),'SCALAR',index=True)
  n.setdefault('extras',{})['ramp_fit_repair']='r0004 aperture-matched lateral skirt; central floor and pivot unchanged'
  moved=np.linalg.norm(p-original,axis=1);changes.append({'node':name,'vertices':len(p),'changed_vertices':int((moved>1e-7).sum()),'max_vertex_displacement_m':float(moved.max()),'central_geometry_abs_x_le_'+str(inner)+'_max_displacement_m':float(moved[ax<=inner].max()) if np.any(ax<=inner) else 0.})
 # Preserve moving upper-door width; form a fixed conforming aperture jamb
 # between the inherited narrower leaf and the source skin. This fits the
 # opening while keeping the original inside-folding clearance.
 fixed=[]
 frame_mat=copy.deepcopy(doc['materials'][1]);frame_mat.pop('normalTexture',None);frame_mat['name']='CARGO_APERTURE_MATCHED_PAINT';frame_material=len(doc['materials']);doc['materials'].append(frame_mat)
 for side,sgn,cv in [('STARBOARD',1,upper_curve),('PORT',-1,upper_port_curve)]:
  vs=[];fs=[]
  for zz,tx,ty,ox,oy in cv:
   a=np.array([sgn*tx,ty,zz]);b=np.array([sgn*(ox+.003),oy,zz]);vs.extend([a,b,a+[0,.018,0],b+[0,.018,0]])
  for k in range(len(cv)-1):
   a=4*k;b=a+4
   for q in [(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)]:fs.extend([(q[0],q[1],q[2]),(q[0],q[2],q[3])])
  for q in [(0,1,3,2),(4*(len(cv)-1),4*(len(cv)-1)+2,4*(len(cv)-1)+3,4*(len(cv)-1)+1)]:fs.extend([(q[0],q[1],q[2]),(q[0],q[2],q[3])])
  name='CARGO_UPPER_APERTURE_JAMB_'+side;mm=make_mesh(name,vs,fs,frame_material)
  prim={'attributes':{k:_append_accessor(doc,buf,v,{2:'VEC2',3:'VEC3',4:'VEC4'}[v.shape[1]]) for k,v in mm.attrs.items()},'indices':_append_accessor(doc,buf,mm.faces.flatten(),'SCALAR',True),'material':mm.material};mi=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':[prim]});ni=len(doc['nodes']);doc['nodes'].append({'name':name,'mesh':mi,'extras':{'part_id':'cargo_upper_aperture_frame','geometry_status':'ARTIST_AUTHORED_SOURCE_SURFACE_FIT','opening':'cargo_ramp','fixed':True}});doc['nodes'][0].setdefault('children',[]).append(ni);fixed.append(name)
 # The original cabin liner intrudes into the repaired rim's receiving space.
 # Relieve only measured side-rib/hinge pockets; the outer skin and central
 # floor remain intact, so these are bounded receiving recesses.
 ci,cp,cp0,cf=_mesh(doc,buf,'CARGO_CABIN_PRESERVED',worlds);ca={k:_array(doc,buf,ai).astype(float) for k,ai in cp['attributes'].items()};ca['POSITION']=cp0;cm=Mesh('CARGO_CABIN_PRESERVED',ca,cf,cp.get('material',0));pockets=[]
 for sgn in [-1,1]:
  for ax0,ax1,y0,y1,z0,z1 in [(1.64,1.79,1.82,2.39,5.16,6.34),(1.59,1.79,.93,1.37,2.72,3.62)]:
   lo=[min(sgn*ax0,sgn*ax1),y0,z0];hi=[max(sgn*ax0,sgn*ax1),y1,z1];removed,cm=extract(cm,boxplanes(lo,hi),'RAMP_RIM_RECEIVING_POCKET');pockets.append({'lo':lo,'hi':hi,'removed_triangle_fragments':len(removed.faces)})
 cw=worlds[ci];cm.attrs['POSITION']=(cm.p-cw[:3,3])@np.linalg.inv(cw[:3,:3]).T
 pp=cm.p.astype('<f4').astype(float);ff=cm.faces;area=np.linalg.norm(np.cross(pp[ff[:,1]]-pp[ff[:,0]],pp[ff[:,2]]-pp[ff[:,0]]),axis=1);cabin_degenerate_faces=int((area<=2e-12).sum());cm.faces=ff[area>2e-12]
 ca={k:np.ascontiguousarray(v,dtype='<f4') for k,v in cm.attrs.items()};keys=sorted(ca);packed=np.concatenate([ca[k].view(np.uint8).reshape(len(cm.p),-1) for k in keys],axis=1);records=np.ascontiguousarray(packed).view(np.dtype((np.void,packed.shape[1]))).ravel();_,first,remap=np.unique(records,return_index=True,return_inverse=True);cm.attrs={k:v[first] for k,v in ca.items()};cm.faces=remap[cm.faces]
 for key,arr in cm.attrs.items():cp['attributes'][key]=_append_accessor(doc,buf,arr,{2:'VEC2',3:'VEC3',4:'VEC4'}[arr.shape[1]])
 cp['indices']=_append_accessor(doc,buf,cm.faces.flatten(),'SCALAR',True);doc['nodes'][ci].setdefault('extras',{})['ramp_receiving_recesses']=pockets
 corner_report=repair_ramp_corners_glb(doc,buf)
 worlds=_worlds(doc);_,_,rp2,rf2=_mesh(doc,buf,'CARGO_LOWER_RAMP_PRESERVED',worlds);_,_,up2,uf2=_mesh(doc,buf,'CARGO_UPPER_DOOR_PRESERVED',worlds)
 probe=np.linspace(2.85,6.2,68);before=_edges((bp,bf),(rp,rf),probe);after=_edges((bp,bf),(rp2,rf2),probe)
 distances=lambda ar:np.linalg.norm(ar[:,1:3]-ar[:,3:5],axis=1)
 stats=lambda ar:{'min':float(distances(ar).min()),'median':float(np.median(distances(ar))),'max':float(distances(ar).max())}
 report={'author':'claude-design','revision':'r0004','method':'Measured source fuselage aperture side profile; local lateral-skirt deformation; unchanged central floor, rig and clips. Three/four-millimetre reveal is artist-authored.','reference':'https://www.dvidshub.net/image/383774/red-flag-11-3','sampled_stations':len(after),'before_edge_distance_m':stats(before),'after_edge_distance_m':stats(after),'upper_before_edge_distance_m':stats(_edges((bp,bf),(up,uf),np.linspace(6.5,10,36),True)),'upper_after_effective_frame_to_leaf_gap_m':.003,'upper_moving_leaf_changed':False,'fixed_aperture_jamb_nodes':fixed,'inner_liner_receiving_pockets':pockets,'float32_collapsed_cabin_faces_removed':cabin_degenerate_faces,'changes':changes,'notes':['Native final-render and sampled-motion review are required on the integrated export.','Edge-distance measurement is the XY distance between lateral source aperture edge and ramp outermost contour at each sampled Z station; not a manufacturing tolerance.','Only local source geometry fit is established; photographic aircraft identity and continuous collision clearance remain unaccepted.']}
 report['aft_corner_fit']=corner_report
 doc['buffers'][0]['byteLength']=len(buf);doc['asset'].setdefault('extras',{})['ramp_repair_r0004']=report
 return report

def repair_ramp(model):
 report=repair_ramp_glb(model.glb.doc,model.glb.buf)
 if hasattr(model.glb,'names'):model.glb.names={n['name']:i for i,n in enumerate(model.glb.doc['nodes'])}
 if hasattr(model,'log'):model.log.append(report)
 return report

def _read(path):
 b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),bytearray(b[28+n:]),hashlib.sha256(b).hexdigest()
def _write(path,doc,buf):
 doc['buffers'][0]['byteLength']=len(buf);s=json.dumps(doc,separators=(',',':')).encode();s+=b' '*((-len(s))%4);bb=bytes(buf);bb+=b'\0'*((-len(bb))%4);Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(s)+len(bb))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(bb),0x004e4942)+bb)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');p.add_argument('--report');a=p.parse_args();doc,buf,sha=_read(a.input);report=repair_ramp_glb(doc,buf);report['input_sha256']=sha;_write(a.output,doc,buf);report['output_sha256']=hashlib.sha256(Path(a.output).read_bytes()).hexdigest()
 if a.report:Path(a.report).write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
