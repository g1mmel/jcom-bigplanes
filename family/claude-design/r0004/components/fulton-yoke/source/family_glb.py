"""claude-design / cg47: lossless import and shared-node module authoring.

The r0003 export is the input, not a fresh procedural substitute airframe.
Only selected skin patches and the repaired ramp are replaced. All other
existing mesh/animation bytes are retained through dependency compaction.
"""
from __future__ import annotations
import copy, json, struct
from pathlib import Path
import numpy as np
from gltf_core import GLB, Mesh, DTYPE, DIMS
from build_family import Model

def read_glb(path):
    b=Path(path).read_bytes();size,kind=struct.unpack_from('<II',b,12)
    d=json.loads(b[20:20+size]);n,k=struct.unpack_from('<II',b,20+size)
    return d,bytearray(b[28+size:28+size+d['buffers'][0]['byteLength']])

def access(doc,buf,i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
    dt=DTYPE[a['componentType']];n=DIMS[a['type']]
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return np.ndarray((a['count'],n),dtype=dt,buffer=buf,offset=offset,
                      strides=(v.get('byteStride',dt.itemsize*n),dt.itemsize)).copy()

def import_model(model_path,articulation_path):
    doc,buf=read_glb(model_path);a=json.loads(Path(articulation_path).read_text())
    m=Model('c130-family','C-130 configurable family',[])
    m.glb.doc=doc;m.glb.buf=buf;m.glb.names={n['name']:i for i,n in enumerate(doc['nodes'])}
    for n in doc['nodes']:n.setdefault('children',[])
    m.controls=copy.deepcopy(a['controls']);m.openings=copy.deepcopy(a.get('openings',[]))
    m.firing_profiles=copy.deepcopy(a.get('firing_profiles',[]));m.log=copy.deepcopy(a.get('notes',[]))
    m.static=m.glb.names['AIRFRAME_COMMON_SOURCE'];m.kit=m.glb.names['MISSION_KIT_AC130J']
    m.known_pivots={}
    def walk(i,t):
        n=doc['nodes'][i];p=np.asarray(t)+n.get('translation',[0,0,0]);m.known_pivots[i]=p
        for ch in n.get('children',[]):walk(ch,p)
    walk(0,np.zeros(3))
    return m,a

def node_mesh(g,node):
    i=g.names[node] if isinstance(node,str) else node;n=g.doc['nodes'][i]
    primitives=g.doc['meshes'][n['mesh']]['primitives']
    if len(primitives)!=1:raise ValueError('Expected one primitive '+n['name'])
    p=primitives[0]
    return Mesh(n['name'],{k:access(g.doc,g.buf,v).astype(float) for k,v in p['attributes'].items()},
                access(g.doc,g.buf,p['indices']).astype(np.int64).reshape(-1,3),p.get('material',0),copy.deepcopy(n.get('extras',{})))

def replace_mesh(g,node,mesh):
    i=g.names[node] if isinstance(node,str) else node
    tmp=g.mesh(mesh,parent=None,name='REPLACEMENT_BUFFER_'+str(i))
    if tmp is None:raise ValueError('Empty replacement '+str(node))
    g.doc['nodes'][i]['mesh']=g.doc['nodes'][tmp]['mesh']
    del g.names[g.doc['nodes'][tmp]['name']];g.doc['nodes'].pop()

def reparent(g,node,parent):
    node=g.names[node] if isinstance(node,str) else node
    parent=g.names[parent] if isinstance(parent,str) else parent
    for n in g.doc['nodes']:
        if node in n.get('children',[]):n['children'].remove(node)
    g.doc['nodes'][parent].setdefault('children',[]).append(node)

def module(m,name,nodes=(),parent=0,asset_id=None):
    i=m.glb.node(name,parent=parent,extras={'loadout_module_root':True,'canonical_scale':[1,1,1],
         'tags':['level 1'],'module_id':name,'asset_id':asset_id or name,'revision':'r0004',
         'visibility_semantics':'configuration selection only; zero default scale is not a physical stow animation'})
    m.known_pivots[i]=m.known_pivots.get(parent,np.zeros(3)).copy()
    for n in nodes:reparent(m.glb,n,i)
    return i

def compact(g):
    """Drop superseded buffers/materials; preserve every remaining attribute byte."""
    d=g.doc
    def remap(collection,used):
        ids=sorted(set(used));mapping={old:new for new,old in enumerate(ids)}
        d[collection]=[d[collection][old] for old in ids];return mapping
    meshmap=remap('meshes',[n['mesh'] for n in d['nodes'] if 'mesh'in n])
    for n in d['nodes']:
        if 'mesh'in n:n['mesh']=meshmap[n['mesh']]
    primitives=[p for m in d['meshes'] for p in m['primitives']]
    matmap=remap('materials',[p['material'] for p in primitives if 'material'in p])
    for p in primitives:
        if 'material'in p:p['material']=matmap[p['material']]
    texrefs=[]
    def textures(o):
        if isinstance(o,dict):
            for key,val in o.items():
                if key.endswith('Texture') and isinstance(val,dict) and 'index'in val:texrefs.append(val)
                elif key!='extras':textures(val)
        elif isinstance(o,list):
            for item in o:textures(item)
    textures(d['materials'])
    if d.get('textures'):
        tx=remap('textures',[t['index'] for t in texrefs])
        for t in texrefs:t['index']=tx[t['index']]
        im=remap('images',[t['source'] for t in d['textures'] if 'source'in t])
        for t in d['textures']:
            if 'source'in t:t['source']=im[t['source']]
        if d.get('samplers'):
            sm=remap('samplers',[t['sampler'] for t in d['textures'] if 'sampler'in t])
            for t in d['textures']:
                if 'sampler'in t:t['sampler']=sm[t['sampler']]
    accs=[]
    for p in primitives:
        accs.extend(p['attributes'].values())
        if 'indices'in p:accs.append(p['indices'])
        for target in p.get('targets',[]):accs.extend(target.values())
    for a in d.get('animations',[]):
        for s in a['samplers']:accs.extend([s['input'],s['output']])
    am=remap('accessors',accs)
    for p in primitives:
        p['attributes']={k:am[v] for k,v in p['attributes'].items()}
        if 'indices'in p:p['indices']=am[p['indices']]
        for target in p.get('targets',[]):
            for k,v in target.items():target[k]=am[v]
    for a in d.get('animations',[]):
        for s in a['samplers']:s['input']=am[s['input']];s['output']=am[s['output']]
    usedviews=[a['bufferView'] for a in d['accessors'] if 'bufferView'in a]+[im['bufferView'] for im in d.get('images',[]) if 'bufferView'in im]
    vm=remap('bufferViews',usedviews)
    for a in d['accessors']:
        if 'bufferView'in a:a['bufferView']=vm[a['bufferView']]
    for im in d.get('images',[]):
        if 'bufferView'in im:im['bufferView']=vm[im['bufferView']]
    b=bytearray()
    for v in d['bufferViews']:
        while len(b)%4:b.append(0)
        old=v.get('byteOffset',0);payload=g.buf[old:old+v['byteLength']]
        v['byteOffset']=len(b);v['buffer']=0;b.extend(payload)
    g.buf=b;d['buffers']=[{'byteLength':len(b)}]
    for key in ['images','textures','samplers','animations']:
        if d.get(key)==[]:d.pop(key,None)

def subset_component(model,root_name,path,controls):
    """Independent subtree with local datum, its clips, and embedded resources."""
    original=model.glb;root=original.names[root_name];wanted=[]
    def visit(i):
        wanted.append(i)
        for ch in original.doc['nodes'][i].get('children',[]):visit(ch)
    visit(root);mapping={old:new for new,old in enumerate(wanted)}
    g=GLB(root_name);g.doc=copy.deepcopy(original.doc);g.buf=bytearray(original.buf)
    g.doc['nodes']=[copy.deepcopy(original.doc['nodes'][i]) for i in wanted]
    for n in g.doc['nodes']:n['children']=[mapping[x] for x in n.get('children',[])]
    for n in g.doc['nodes']:
        if n.get('extras',{}).get('loadout_module_root'):
            enabled=not n['name'].endswith('_BASKET_LOW')
            n['scale']=[1,1,1] if enabled else [0,0,0];n['extras']['default_enabled']=enabled
    g.doc['nodes'][0]['translation']=[0,0,0];g.doc['nodes'][0]['scale']=[1,1,1]
    g.doc['nodes'][0]['extras'].update(independent_component=True,parent_aircraft_dependency=False)
    g.doc['scene']=0;g.doc['scenes']=[{'name':root_name,'nodes':[0]}]
    g.doc['asset']['extras']={'independent_component':root_name,'units':'metres','basis':'+Y up; local mounting datum','parent_aircraft_dependency':False}
    anim=[]
    for a in original.doc.get('animations',[]):
        channels=[copy.deepcopy(c) for c in a['channels'] if c['target']['node']in mapping]
        if not channels:continue
        b=copy.deepcopy(a);b['channels']=channels
        for c in channels:c['target']['node']=mapping[c['target']['node']]
        used=sorted({c['sampler'] for c in channels});sm={v:i for i,v in enumerate(used)}
        b['samplers']=[b['samplers'][i] for i in used]
        for c in channels:c['sampler']=sm[c['sampler']]
        anim.append(b)
    g.doc['animations']=anim;g.names={n['name']:i for i,n in enumerate(g.doc['nodes'])}
    compact(g);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);receipt=g.write(path)
    selected=[copy.deepcopy(c) for c in controls if c['node']in g.names]
    return receipt,selected
