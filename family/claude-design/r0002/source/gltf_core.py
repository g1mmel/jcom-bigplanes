"""claude-design: small deterministic glTF geometry/animation authoring utilities.

No original asset is modified. All source attributes are retained on extracted
skin patches; clipping interpolates UVs, colours and smooth normals.
"""
from __future__ import annotations
import copy, hashlib, json, math, struct
from dataclasses import dataclass
from pathlib import Path
import numpy as np

DTYPE={5126:np.dtype('<f4'),5125:np.dtype('<u4'),5123:np.dtype('<u2'),5122:np.dtype('<i2'),5121:np.dtype('u1'),5120:np.dtype('i1')}
DIMS={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
BASIS=np.array([[-1.,0.,0.],[0.,0.,1.],[0.,1.,0.]])

def normalize(v):
    n=np.linalg.norm(v,axis=-1,keepdims=True)
    return v/np.maximum(n,1e-12)

def quat(axis,angle):
    a=normalize(np.asarray(axis,dtype=float));r=math.radians(angle)*.5
    return [*(a*math.sin(r)),math.cos(r)]

def rot(axis,angle):
    x,y,z=normalize(np.asarray(axis,dtype=float));a=math.radians(angle);c=math.cos(a);s=math.sin(a);t=1-c
    return np.array([[t*x*x+c,t*x*y-s*z,t*x*z+s*y],[t*x*y+s*z,t*y*y+c,t*y*z-s*x],[t*x*z-s*y,t*y*z+s*x,t*z*z+c]])

@dataclass
class Mesh:
    name:str
    attrs:dict
    faces:np.ndarray
    material:int=0
    extras:dict|None=None

    @property
    def p(self):return self.attrs['POSITION']
    def clone(self,name=None):return Mesh(name or self.name,{k:v.copy() for k,v in self.attrs.items()},self.faces.copy(),self.material,copy.deepcopy(self.extras or {}))
    def bounds(self):return self.p.min(0),self.p.max(0)
    def center(self):
        a,b=self.bounds();return (a+b)*.5
    def move(self,delta):self.attrs['POSITION']+=np.asarray(delta);return self
    def transform(self,m,t=(0,0,0)):
        self.attrs['POSITION']=self.p@np.asarray(m).T+np.asarray(t)
        if 'NORMAL' in self.attrs:self.attrs['NORMAL']=normalize(self.attrs['NORMAL']@np.linalg.inv(m))
        if 'TANGENT' in self.attrs:self.attrs['TANGENT'][:,:3]=normalize(self.attrs['TANGENT'][:,:3]@np.asarray(m).T)
        if np.linalg.det(m)<0:self.faces=self.faces[:,[0,2,1]]
        return self
    def rotate(self,pivot,axis,angle):
        p=np.asarray(pivot);r=rot(axis,angle);return self.transform(r,p-r@p)
    def subset(self,mask,name=None):
        f=self.faces[mask]
        if not len(f):return Mesh(name or self.name,{k:np.zeros((0,v.shape[1])) for k,v in self.attrs.items()},np.zeros((0,3),dtype=np.int64),self.material,self.extras)
        ids,inv=np.unique(f.ravel(),return_inverse=True)
        return Mesh(name or self.name,{k:v[ids].copy() for k,v in self.attrs.items()},inv.reshape(-1,3),self.material,copy.deepcopy(self.extras or {}))

def merge(meshes,name='merged'):
    meshes=[m for m in meshes if len(m.faces)]
    if not meshes:return Mesh(name,{'POSITION':np.zeros((0,3)),'NORMAL':np.zeros((0,3))},np.zeros((0,3),dtype=int))
    keys=set.intersection(*(set(m.attrs) for m in meshes));offset=0;fs=[]
    for m in meshes:fs.append(m.faces+offset);offset+=len(m.p)
    return Mesh(name,{k:np.concatenate([m.attrs[k] for m in meshes]) for k in keys},np.concatenate(fs),meshes[0].material,copy.deepcopy(meshes[0].extras or {}))

def plane_split(mesh,n,d):
    """Return positive and negative half-space triangle patches, preserving attrs."""
    n=np.asarray(n,dtype=float);ds=mesh.p@n-float(d);f=mesh.faces;vals=ds[f]
    inside=np.all(vals>=-1e-8,axis=1);outside=np.all(vals<=1e-8,axis=1)&~inside;cross=~(inside|outside)
    outputs=[]
    for sign,whole in ((1,inside),(-1,outside)):
        chunks=[mesh.subset(whole)];attrs={k:[] for k in mesh.attrs};faces=[];offset=0
        for fi in f[cross]:
            poly=[{k:v[i].copy() for k,v in mesh.attrs.items()} for i in fi]
            out=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                da=(a['POSITION']@n-d)*sign;db=(b['POSITION']@n-d)*sign
                if da>=-1e-8:out.append(a)
                if (da>1e-8 and db< -1e-8) or (da< -1e-8 and db>1e-8):
                    t=da/(da-db);out.append({k:a[k]+t*(b[k]-a[k]) for k in a})
            if len(out)<3:continue
            for v in out:
                for k in attrs:attrs[k].append(v[k])
            for j in range(1,len(out)-1):faces.append((offset,offset+j,offset+j+1))
            offset+=len(out)
        if faces:
            aa={k:np.asarray(v) for k,v in attrs.items()}
            if 'NORMAL' in aa:aa['NORMAL']=normalize(aa['NORMAL'])
            if 'TANGENT' in aa:aa['TANGENT'][:,:3]=normalize(aa['TANGENT'][:,:3])
            chunks.append(Mesh(mesh.name,aa,np.asarray(faces),mesh.material,copy.deepcopy(mesh.extras or {})))
        outputs.append(merge(chunks,mesh.name))
    return outputs

def extract(mesh,planes,name):
    """Extract convex intersection; outside is preserved without overlap."""
    selected=mesh;outside=[]
    for n,d in planes:
        selected,reject=plane_split(selected,n,d);outside.append(reject)
        if not len(selected.faces):break
    selected.name=name;return selected,merge(outside,mesh.name)

def boxplanes(lo,hi):
    return [([1,0,0],lo[0]),([-1,0,0],-hi[0]),([0,1,0],lo[1]),([0,-1,0],-hi[1]),([0,0,1],lo[2]),([0,0,-1],-hi[2])]

def make_mesh(name,verts,faces,material=0,extras=None):
    p=np.asarray(verts,dtype=float);f=np.asarray(faces,dtype=np.int64)
    if not len(f):return Mesh(name,{'POSITION':p,'NORMAL':np.zeros_like(p)},f,material,extras)
    normal=np.zeros_like(p);fn=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
    for j in range(3):np.add.at(normal,f[:,j],fn)
    return Mesh(name,{'POSITION':p,'NORMAL':normalize(normal)},f,material,extras)

def box(name,lo,hi,material=0,omit=None):
    x0,y0,z0=lo;x1,y1,z1=hi
    verts=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    quads={'front':(0,3,2,1),'back':(4,5,6,7),'bottom':(0,1,5,4),'top':(3,7,6,2),'left':(0,4,7,3),'right':(1,2,6,5)}
    faces=[]
    for key,q in quads.items():
        if key not in (omit or []):faces.extend([(q[0],q[1],q[2]),(q[0],q[2],q[3])])
    return make_mesh(name,verts,faces,material)

def tube(name,start,end,radius,material=0,segments=24,cap=True,radius_end=None):
    a=np.asarray(start,dtype=float);b=np.asarray(end,dtype=float);axis=normalize(b-a);u=normalize(np.cross(axis,[0,1,0] if abs(axis[1])<.9 else [1,0,0]));v=np.cross(axis,u)
    verts=[];faces=[]
    for center,r in [(a,radius),(b,radius if radius_end is None else radius_end)]:
        verts.extend(center+r*(math.cos(t)*u+math.sin(t)*v) for t in np.linspace(0,2*math.pi,segments,endpoint=False))
    for i in range(segments):j=(i+1)%segments;faces.extend([(i,j,segments+j),(i,segments+j,segments+i)])
    if cap:
        for j in range(1,segments-1):faces.extend([(0,j+1,j),(segments,segments+j,segments+j+1)])
    return make_mesh(name,verts,faces,material)

def sphere(name,center,radii,material=0,stacks=12,sectors=24):
    center=np.asarray(center,dtype=float);radii=np.asarray(radii if isinstance(radii,(list,tuple,np.ndarray)) else [radii]*3)
    vs=[];fs=[]
    for i in range(stacks+1):
        a=math.pi*i/stacks
        for j in range(sectors):
            b=2*math.pi*j/sectors;vs.append(center+radii*np.array([math.sin(a)*math.cos(b),math.cos(a),math.sin(a)*math.sin(b)]))
    for i in range(stacks):
        for j in range(sectors):
            k=i*sectors+j;l=i*sectors+(j+1)%sectors;fs.extend([(k,k+sectors,l+sectors),(k,l+sectors,l)])
    return make_mesh(name,vs,fs,material)

def load_source(path,canonical=False):
    data=Path(path).read_bytes();jl,jt=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+jl]);bl,bt=struct.unpack_from('<II',data,20+jl);buf=data[28+jl:28+jl+bl]
    def accessor(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dt=DTYPE[a['componentType']];n=DIMS[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0)
        ar=np.ndarray((a['count'],n),dtype=dt,buffer=buf,offset=off,strides=(v.get('byteStride',n*dt.itemsize),dt.itemsize)).copy()
        if a.get('normalized'):
            ar=ar.astype(float)/np.iinfo(dt).max
        return ar
    parent=doc['nodes'][24];pm=np.eye(4);pm[:3,:3]=np.diag(parent['scale']);pm[:3,3]=parent['translation'];bm=np.eye(4);bm[:3,:3]=BASIS
    meshes=[]
    for i,n in enumerate(doc['nodes'][:24]):
        src=doc['meshes'][n['mesh']];pr=src['primitives'][0];attrs={k:accessor(a).astype(float) for k,a in pr['attributes'].items()}
        if 'COLOR_0' in attrs and attrs['COLOR_0'].max()>1:attrs['COLOR_0']/=255
        m=Mesh(n['name'],attrs,accessor(pr['indices']).astype(np.int64).reshape(-1,3),pr.get('material',0),{'source_node':i,'source_name':n['name'],'source_geometry':'PRESERVED_ORIGINAL'})
        local=np.array(n.get('matrix',np.eye(4).flatten(order='F'))).reshape(4,4,order='F')
        if canonical and i in (6,11,15,22):
            base=np.eye(4);base[:3,:3]=rot([1,0,0],90)
            delta=local@np.linalg.inv(base);angle=math.degrees(math.atan2(delta[2,1],delta[1,1]));pivot=np.linalg.lstsq(np.eye(3)-delta[:3,:3],delta[:3,3],rcond=1e-6)[0]
            m.extras.update({'reconstructed_source_open_angle':angle,'reconstructed_source_pivot':(bm@pm@np.r_[pivot,1.])[:3].tolist(),'reconstructed_source_axis':(BASIS@np.array([1.,0.,0.])).tolist(),'rest_reconstruction':'SOURCE_UNIFORM_ORIENTATION_MATRIX_INFERRED'})
            local=base
        world=bm@pm@local;m.transform(world[:3,:3],world[:3,3]);meshes.append(m)
    images=[]
    for im in doc.get('images',[]):
        v=doc['bufferViews'][im['bufferView']];o=v.get('byteOffset',0);images.append((buf[o:o+v['byteLength']],im['mimeType']))
    return meshes,images,hashlib.sha256(data).hexdigest()

class GLB:
    def __init__(self,name):
        self.doc={'asset':{'version':'2.0','generator':'claude-design JCNC C130 modular r0002'},'scene':0,'scenes':[{'name':name,'nodes':[0]}],'nodes':[{'name':'C130_FAMILY_ROOT','children':[],'extras':{'units':'metres','basis':'+X right,+Y up,nose -Z','revision':'r0002','author':'claude-design','acceptance':'DRAFT_NATIVE_ENGINE_NOT_RUN'}}],'meshes':[],'materials':[],'buffers':[{'byteLength':0}],'bufferViews':[],'accessors':[],'animations':[]};self.buf=bytearray();self.names={'C130_FAMILY_ROOT':0}
    def blob(self,data,target=None):
        while len(self.buf)%4:self.buf.append(0)
        o=len(self.buf);self.buf.extend(data);v={'buffer':0,'byteOffset':o,'byteLength':len(data)}
        if target:v['target']=target
        self.doc['bufferViews'].append(v);return len(self.doc['bufferViews'])-1
    def acc(self,a,atype=None,index=False,target=True):
        a=np.asarray(a);a=a.astype('<u4' if index else '<f4');v=self.blob(a.tobytes(),(34963 if index else 34962) if target else None);n=1 if a.ndim==1 else a.shape[1];typ=atype or {1:'SCALAR',2:'VEC2',3:'VEC3',4:'VEC4'}[n]
        rec={'bufferView':v,'componentType':5125 if index else 5126,'count':len(a),'type':typ};aa=a.reshape(len(a),n);rec.update(min=aa.min(0).tolist(),max=aa.max(0).tolist());self.doc['accessors'].append(rec);return len(self.doc['accessors'])-1
    def material(self,name,color,metal=0.,rough=.7,normal=None,double=True,emissive=None):
        m={'name':name,'pbrMetallicRoughness':{'baseColorFactor':list(color),'metallicFactor':metal,'roughnessFactor':rough},'doubleSided':double}
        if normal is not None:m['normalTexture']={'index':normal,'scale':.35}
        if len(color)>3 and color[3]<1:m['alphaMode']='BLEND'
        if emissive:m['emissiveFactor']=list(emissive)
        self.doc['materials'].append(m);return len(self.doc['materials'])-1
    def image(self,data,mime):
        self.doc.setdefault('images',[]).append({'bufferView':self.blob(data),'mimeType':mime});i=len(self.doc['images'])-1
        self.doc.setdefault('textures',[]).append({'source':i});return len(self.doc['textures'])-1
    def node(self,name,parent=0,translation=None,extras=None):
        if name in self.names:raise ValueError('duplicate node '+name)
        n={'name':name,'children':[],'extras':extras or {}}
        if translation is not None:n['translation']=np.asarray(translation,dtype=float).tolist()
        i=len(self.doc['nodes']);self.doc['nodes'].append(n);self.names[name]=i
        if parent is not None:self.doc['nodes'][parent]['children'].append(i)
        return i
    def mesh(self,m,parent=0,origin=(0,0,0),name=None,extras=None):
        if not len(m.faces):return None
        aa={k:v.copy() for k,v in m.attrs.items()};aa['POSITION']-=np.asarray(origin)
        primitive={'attributes':{k:self.acc(v) for k,v in aa.items()},'indices':self.acc(m.faces.ravel(),index=True),'material':m.material,'mode':4}
        mid=len(self.doc['meshes']);self.doc['meshes'].append({'name':name or m.name,'primitives':[primitive]});i=self.node(name or m.name,parent=parent,extras={**(m.extras or {}),**(extras or {})});self.doc['nodes'][i]['mesh']=mid;return i
    def animation(self,name,tracks):
        """tracks are (node index, path, times, values); all times normalized0..1."""
        samplers=[];channels=[]
        for node,path,times,values in tracks:
            samplers.append({'input':self.acc(np.array(times),target=False),'output':self.acc(np.array(values),target=False),'interpolation':'LINEAR'});channels.append({'sampler':len(samplers)-1,'target':{'node':node,'path':path}})
        self.doc['animations'].append({'name':name,'samplers':samplers,'channels':channels,'extras':{'normalized_time':True,'rest':0,'deployed':1,'presentation_timing':'ARTIST_AUTHORED_NOT_OPERATIONAL'}})
    def write(self,path):
        self.doc['buffers'][0]['byteLength']=len(self.buf)
        js=json.dumps(self.doc,separators=(',',':'),ensure_ascii=False).encode();js+=b' '*((-len(js))%4);binary=bytes(self.buf)+b'\0'*((-len(self.buf))%4)
        out=struct.pack('<4sII',b'glTF',2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
        Path(path).write_bytes(out);return {'path':str(path),'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest(),'nodes':len(self.doc['nodes']),'meshes':len(self.doc['meshes']),'clips':len(self.doc['animations'])}
