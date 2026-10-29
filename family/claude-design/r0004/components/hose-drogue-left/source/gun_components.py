"""claude-design / cg46: photo-guided independent gun visual assemblies.

External appearances and visible animation only. All geometry, limits and
timing are artist authored, not manufacturing, ballistics or operating data.
The pre-2022 aircraft installation is represented; no ground carriage is used.
"""
from __future__ import annotations
import io, math
import numpy as np
from gltf_core import make_mesh, merge, box, tube, sphere, quat, normalize, extract, boxplanes

REFS = {
    'exterior30': 'https://www.dvidshub.net/image/6427944/ac-130j-crew-maintain-proficiency-combat-readiness',
    'interior30': 'https://www.dvidshub.net/image/6317363/ac-130w-supports-uae-us-maritime-surface-warfare-exercise',
    'case30': 'https://www.dvidshub.net/image/3486265/live-fire-training-with-ac-130w',
    'case30j': 'https://www.dvidshub.net/image/3146917/angry-annie-fires-first-rounds',
    'interior105': 'https://www.dvidshub.net/image/3146918/angry-annie-fires-first-rounds',
    'recoil105': 'https://www.dvidshub.net/image/3486262/live-fire-training-with-ac-130w',
    'mount105': 'https://www.dvidshub.net/image/6637434/ac-130j-gunship-trains-with-multinational-forces-during-trojan-footprint-21',
    'exterior105': 'https://www.dvidshub.net/image/5621883/73rd-amu-air-commandos-perform-post-flight-inspection-ac-130j-ghostrider-gunship',
    'case105': 'https://www.dvidshub.net/image/6427973/ac-130j-crew-maintain-proficiency-combat-readiness',
    'smoke': 'https://www.dvidshub.net/image/2392818/new-range-adds-opportunities-air-commandos',
}

def evidence(*keys, note='Visible principle evidenced; dimensions, paths and timing are authored game presentation.'):
    return {'status':'OBSERVED_APPEARANCE_AUTHORED_ANIMATION', 'sources':[REFS[k] for k in keys], 'limitations':note}

def materials(model):
    if hasattr(model,'_gun_materials'): return model._gun_materials
    specs={
        'gun':('GUN_PARKERIZED_DARK',[.035,.043,.048,1],.62,.53),
        'paint':('GUN_MOUNT_PAINT',[.045,.055,.06,1],.26,.72),
        'edge':('GUN_RESTRAINED_WORN_EDGES',[.23,.25,.26,1],.82,.32),
        'steel':('GUN_MACHINED_STEEL',[.36,.38,.40,1],.85,.28),
        'boot':('GUN_FLEXIBLE_CANVAS_BOOT',[.007,.009,.010,1],0,.96),
        'dark':('GUN_RECESSED_CAVITY',[.006,.008,.009,1],.1,.85),
        'yellow':('GUN_105_LEGACY_GUARD_OCHRE',[.55,.37,.09,1],.3,.5),
        'cloth':('GUN_CASE_BAG_KHAKI',[.32,.26,.16,1],0,.95),
        'orange':('GUN_CASE_BAG_ORANGE',[.43,.18,.07,1],0,.95),
        'brass':('EMPTY_CASE_BRASS',[.62,.40,.12,1],.82,.3),
        'brassInside':('EMPTY_CASE_INNER_DARK',[.18,.11,.035,1],.62,.55),
        'flash':('VISUAL_MUZZLE_FLASH',[1,.53,.12,.82],0,.4),
        'flashCore':('VISUAL_MUZZLE_CORE',[1,.91,.64,.94],0,.2),
    }
    m={k:model.glb.material(n,col,metal,rough,double=False,emissive=([1,.35,.045] if k=='flash' else [1,.85,.50] if k=='flashCore' else None)) for k,(n,col,metal,rough) in specs.items()}
    for k in ['flash','flashCore']:model.glb.doc['materials'][m[k]]['doubleSided']=True
    # Original soft emissive plume: crossed alpha cards, never a solid spear.
    # This is a game presentation texture, not an operational flame model.
    from PIL import Image
    u,v=np.meshgrid(np.linspace(0,1,192),np.linspace(-1,1,128))
    width=.13+.65*np.sqrt(u)*(1-u)**.6
    warp=v+.055*np.sin(u*22)*(u*(1-u))
    grainflash=.86+.10*np.sin(u*31+v*17)+.04*np.cos(u*53-v*13)
    alpha=np.exp(-3*(warp/width)**2)*(1-u)**1.45*grainflash
    rgba=np.empty((128,192,4),dtype=np.uint8)
    rgba[:,:,0]=255;rgba[:,:,1]=(194+61*np.exp(-u*7)).astype(np.uint8)
    rgba[:,:,2]=(80+175*np.exp(-u*7)).astype(np.uint8)
    rgba[:,:,3]=(np.clip(alpha,0,1)*230).astype(np.uint8)
    out=io.BytesIO();Image.fromarray(rgba,'RGBA').save(out,format='PNG')
    plume=model.glb.image(out.getvalue(),'image/png')
    for key in ['flash','flashCore']:
        mat=model.glb.doc['materials'][m[key]]
        mat['pbrMetallicRoughness']['baseColorTexture']={'index':plume}
        mat['emissiveTexture']={'index':plume}
        mat['extras']={'presentation_effect':True,'texture':'original analytic soft alpha plume'}
    # Original analytic soft-alpha smoke sprite, packed in every component GLB.
    q=np.linspace(-1,1,128);xx,yy=np.meshgrid(q,q)
    rr=(xx*1.02)**2+(yy*.95)**2
    wisps=.82+.13*np.sin(xx*13+yy*5)+.05*np.cos(yy*23-xx*4)
    alpha=np.clip((1-rr)*.55,0,.55)**1.5*wisps
    rgba=np.empty((128,128,4),dtype=np.uint8);rgba[:,:,:3]=[192,198,201];rgba[:,:,3]=(alpha*230).astype(np.uint8)
    out=io.BytesIO();Image.fromarray(rgba,'RGBA').save(out,format='PNG')
    tex=model.glb.image(out.getvalue(),'image/png')
    m['smoke']=model.glb.material('VISUAL_SOFT_DISSIPATING_SMOKE',[.8,.83,.85,.45],0,1,double=True)
    model.glb.doc['materials'][m['smoke']]['pbrMetallicRoughness']['baseColorTexture']={'index':tex}
    rng=np.random.default_rng(30105);grain=rng.normal(0,1,(128,128))
    yy,xx=np.mgrid[0:128,0:128]
    weave=.45*np.sin(xx*math.pi)+.45*np.sin(yy*math.pi)+.1*grain
    for key in ['gun','paint','boot','yellow','cloth','orange','brass']:
        mat=model.glb.doc['materials'][m[key]];rough=specs[key][3]
        amount=.025 if key not in ['boot','cloth','orange'] else .045
        values=np.clip(rough+amount*grain,0.1,.99)
        texdata=np.zeros((128,128,4),dtype=np.uint8);texdata[:,:,0]=255;texdata[:,:,1]=(values*255).astype(np.uint8);texdata[:,:,2]=255;texdata[:,:,3]=255
        encoded=io.BytesIO();Image.fromarray(texdata,'RGBA').save(encoded,format='PNG');texture=model.glb.image(encoded.getvalue(),'image/png')
        mat['pbrMetallicRoughness']['metallicRoughnessTexture']={'index':texture};mat['pbrMetallicRoughness']['roughnessFactor']=1
        mat['extras']={'finish':'original analytic material micro-roughness; no photo bake','map_channels':'G roughness, B metallic multiplier; linear data'}
    model._gun_materials=m
    return m

def lathe_x(name,c,profile,material,seg=56):
    """Closed or open revolved visual profile, with explicit outward winding."""
    c=np.asarray(c,float);vs=[];fs=[]
    for x,r in profile:
        for a in np.linspace(0,2*math.pi,seg,endpoint=False):vs.append(c+[x,r*math.cos(a),r*math.sin(a)])
    for k in range(len(profile)-1):
        for j in range(seg):
            a=k*seg+j;b=k*seg+(j+1)%seg
            fs.extend([(a,b,b+seg),(a,b+seg,a+seg)])
    return make_mesh(name,vs,fs,material)

def ring_x(name,c,x,r,wall,depth,material,seg=56):
    return lathe_x(name,c,[(x,r),(x+depth,r),(x+depth,r-wall),(x,r-wall),(x,r)],material,seg)

def beveled_box(name,lo,hi,bevel,material):
    # A small chamfered convex housing, independently editable after import.
    from scipy.spatial import ConvexHull
    lo=np.asarray(lo,float);hi=np.asarray(hi,float);b=min(bevel,float(np.min(hi-lo))*.24)
    pts=[]
    for corner in range(8):
        v=np.array([hi[k] if corner&(1<<k) else lo[k] for k in range(3)])
        for axis in range(3):
            w=v.copy();w[axis]+=(-b if corner&(1<<axis) else b);pts.append(w)
    pts=np.asarray(pts);h=ConvexHull(pts);faces=[]
    for face,eq in zip(h.simplices,h.equations):
        a,b,c=pts[face]
        if np.dot(np.cross(b-a,c-a),eq[:3])<0:face=face[[0,2,1]]
        faces.append(face)
    return make_mesh(name,pts,faces,material)

def path_tube(name,points,r,material,seg=12):
    points=np.asarray(points,float);verts=[];faces=[]
    for i,p in enumerate(points):
        d=normalize(points[min(i+1,len(points)-1)]-points[max(i-1,0)])
        u=normalize(np.cross(d,[0,1,0] if abs(d[1])<.9 else [1,0,0]));v=np.cross(d,u)
        for a in np.linspace(0,2*math.pi,seg,endpoint=False):verts.append(p+r*(math.cos(a)*u+math.sin(a)*v))
    for i in range(len(points)-1):
        for j in range(seg):a=i*seg+j;b=i*seg+(j+1)%seg;faces.extend([(a,b,b+seg),(a,b+seg,a+seg)])
    return make_mesh(name,verts,faces,material)

def flex_boot(name,c,outer,material):
    # A draped membrane. It replaces the incorrect stack of six cone collars.
    vs=[];fs=[];seg=72;radials=9;c=np.asarray(c)
    for k in range(radials):
        t=k/(radials-1);r=outer*(1-t)+.17*t
        for a in np.linspace(0,2*math.pi,seg,endpoint=False):
            wrinkle=.025*math.sin(a*11+.3)*math.sin(math.pi*t)+.014*math.cos(a*7)*math.sin(math.pi*t)
            vs.append(c+[-.035-.19*t+wrinkle,r*math.cos(a),r*math.sin(a)])
    for k in range(radials-1):
        for j in range(seg):a=k*seg+j;b=k*seg+(j+1)%seg;fs.extend([(a,a+seg,b+seg),(a,b+seg,b)])
    return make_mesh(name,vs,fs,material,{'surface':'artist-authored flexible diaphragm; opening remains real','reference':REFS['exterior30']})

def slotted_muzzle(name,c,material):
    """Visible exterior vent sleeve, no concealed weapon construction."""
    seg=64;nx=32;vs=[];fs=[];c=np.asarray(c)
    for x in np.linspace(-1.66,-1.29,nx+1):
        for a in np.linspace(0,2*math.pi,seg,endpoint=False):vs.append(c+[x,.096*math.cos(a),.096*math.sin(a)])
    for k in range(nx):
        x=-1.66+(k+.5)*.37/nx
        for j in range(seg):
            a=2*math.pi*(j+.5)/seg
            slot=any(abs(x-xc)<.026 for xc in [-1.58,-1.48,-1.38]) and abs(math.sin(a))>.42
            if slot:continue
            a0=k*seg+j;b=k*seg+(j+1)%seg;fs.extend([(a0,b,b+seg),(a0,b+seg,a0+seg)])
    m=make_mesh(name,vs,fs,material,{'oblong_vents':'visual exterior holes guided by DVIDS6427944'})
    return m

def case_mesh(name,large,mat):
    length=.45 if large else .16;r=.063 if large else .027;wall=.005 if large else .003
    # Clearly hollow and empty: no projectile tip, primer detail, or load data.
    return lathe_x(name,[0,0,0],[(0,r*.97),(length*.08,r),(length*.88,r*.96),(length,r*.93),(length,r*.93-wall),(length*.12,r-wall),(length*.12,0),(0,0),(0,r*.97)],mat,40)

def bag_mesh(name,c,mat):
    c=np.asarray(c);vs=[];fs=[];seg=40
    for k,(y,rx,rz) in enumerate([(-.79,.29,.24),(-.74,.34,.28),(-.28,.36,.30),(-.22,.32,.265)]):
        for a in np.linspace(0,2*math.pi,seg,endpoint=False):
            wrinkle=1+.035*math.sin(a*7+k*.3)
            vs.append(c+[rx*math.cos(a)*wrinkle,y,rz*math.sin(a)*wrinkle])
    for k in range(3):
        for j in range(seg):a=k*seg+j;b=k*seg+(j+1)%seg;fs.extend([(a,b,b+seg),(a,b+seg,a+seg)])
    fs.extend((0,j+1,j) for j in range(1,seg-1))
    return make_mesh(name,vs,np.asarray(fs)[:,[0,2,1]],mat,{'collection':'internal spent-case bag, open mouth'})

def flash_mesh(name,c,length,material):
    c=np.asarray(c);vs=[];fs=[];uv=[]
    for k in range(3):
        angle=k*math.pi/3;transverse=np.array([0,math.cos(angle),math.sin(angle)])
        first=len(vs)
        for t,q in [(0,-1),(1,-1),(1,1),(0,1)]:
            vs.append(c+[-length*t,0,0]+transverse*q*length*.28)
            uv.append((t,(q+1)*.5))
        fs.extend([(first,first+1,first+2),(first,first+2,first+3)])
    mesh=make_mesh(name,vs,fs,material,{'presentation_effect':True,'not_projectile':True,'soft_alpha_sprite':'original emissive plume'})
    mesh.attrs['TEXCOORD_0']=np.asarray(uv,float)
    return mesh

def smoke_mesh(name,c,material):
    c=np.asarray(c);v=[];f=[];uv=[]
    # Three crossed soft alpha cards form a low-cost, non-solid smoke puff.
    for k in range(3):
        a=k*math.pi/3;u=np.array([0,math.cos(a),math.sin(a)]);w=np.array([1,0,0]);start=len(v)
        for p,q in [(-1,-1),(1,-1),(1,1),(-1,1)]:v.append(c+u*p*.5+w*q*.5)
        uv.extend([(0,0),(1,0),(1,1),(0,1)]);f.extend([(start,start+1,start+2),(start,start+2,start+3)])
    m=make_mesh(name,v,f,material,{'presentation_effect':True,'soft_alpha_sprite':'authored analytic texture'});m.attrs['TEXCOORD_0']=np.asarray(uv,float);return m

def add_gun(model,cid,center,large=False):
    c=np.asarray(center,float);g=model.glb;m=materials(model);label='105 mm' if large else '30 mm';asset='m102-airborne-visual' if large else 'gau23-visual'
    root=model.pivot(cid+'_component',c,parent=model.kit,extras={'tags':['level 1'],'asset_id':asset,'revision':'r0003','component_type':'photo_guided_aircraft_visual_system','operational_model':False,'configuration':'circa 2021 earlier installation','reference':REFS['exterior105' if large else 'exterior30']})
    def attach(mesh,parent):
        # Per-face box-projected UVs retain geometric smooth normals and provide
        # a stable fine finish map independent of aircraft textures.
        if 'TEXCOORD_0' not in mesh.attrs and not (mesh.extras or {}).get('presentation_effect'):
            ff=mesh.faces;pts=mesh.p[ff];fnorm=np.cross(pts[:,1]-pts[:,0],pts[:,2]-pts[:,0]);drop=np.argmax(np.abs(fnorm),axis=1)
            attrs={key:value[ff].reshape((-1,value.shape[1])) for key,value in mesh.attrs.items()}
            uv=np.empty((len(ff),3,2));local=pts-c
            for ax,uvaxes in [(0,(2,1)),(1,(0,2)),(2,(0,1))]:
                mask=drop==ax;uv[mask]=local[mask][:,:,list(uvaxes)]*5
            attrs['TEXCOORD_0']=uv.reshape(-1,2);mesh.attrs=attrs;mesh.faces=np.arange(len(ff)*3).reshape(-1,3)
        return model.attach(mesh,parent)
    def fit_interface(mesh,boot=False):
        profile=getattr(model,'gun_interface_profiles',{}).get(cid)
        if profile is not None:
            points=mesh.p;dy=points[:,1]-c[1];dz=points[:,2]-c[2];a=np.mod(np.arctan2(dz,dy),2*math.pi);radius=np.hypot(dy,dz)
            xp=np.asarray(profile['outer_x_offset']);aa=np.linspace(0,2*math.pi,len(xp)+1);delta=np.interp(a,aa,np.r_[xp,xp[0]])
            weight=np.clip((radius-.17)/(outer-.17),0,1) if boot else 1
            points[:,0]+=delta*weight
            mesh.attrs['NORMAL']=np.zeros_like(points)
            normals=np.cross(points[mesh.faces[:,1]]-points[mesh.faces[:,0]],points[mesh.faces[:,2]]-points[mesh.faces[:,0]])
            for k in range(3):np.add.at(mesh.attrs['NORMAL'],mesh.faces[:,k],normals)
            mesh.attrs['NORMAL']=normalize(mesh.attrs['NORMAL'])
            mesh.extras={**(mesh.extras or {}),'installation_adapter':'conformed to retained source skin; independent canonical component unchanged'}
        return mesh
    def fixed(mesh):return attach(mesh,root)
    outer=.47 if large else .55
    fixed(fit_interface(ring_x(cid+'_FUSELAGE_INTERFACE_RING',c,-.028,outer+.028,.035,.045,m['paint'])))
    fixed(fit_interface(flex_boot(cid+'_DRAPED_APERTURE_BOOT',c,outer,m['boot']),boot=True))
    # Separate bolt ring, recessed into the real circular receiving opening.
    bolts=[]
    for k in range(24):
        a=2*math.pi*k/24;v=c+[-.039,(outer+.009)*math.cos(a),(outer+.009)*math.sin(a)]
        bolts.append(tube(cid+f'_FLANGE_BOLT_{k}',v,v+[-.012,0,0],.008,m['steel'],segments=6))
    fixed(fit_interface(merge(bolts,cid+'_FLANGE_FASTENERS')))
    # The receiver and supporting equipment live inboard (+X), not outside.
    # Lower 30 mm support follows the narrower cabin section. Its .36 datum
    # is inboard of the retained skin at every tested support/base vertex.
    fixed(beveled_box(cid+'_INBOARD_BASE',c+[.21 if large else .36,-.69 if large else -1.06,-.37],c+[1.48,-.56 if large else -.99,.37],.025,m['paint']))
    if not large:
        for zi,z in enumerate([-.31,.31]):fixed(beveled_box(cid+f'_BASE_SUPPORT_{zi}',c+[.36,-1.00,z-.025],c+[.56,-.49,z+.025],.012,m['paint']))
    yaw=model.pivot(cid+'_yaw',c+[.30,0,0],parent=root)
    pitch=model.pivot(cid+'_pitch',c+[.30,0,0],parent=yaw)
    attach(tube(cid+'_TRUNNION',c+[.30,0,-.28],c+[.30,0,.28],.105 if not large else .14,m['steel'],segments=40),yaw)
    for z in [-.31,.31]:attach(beveled_box(cid+('_TRUNNION_PLATE_L' if z<0 else '_TRUNNION_PLATE_R'),c+[.17,-.50,z-.035],c+[.46,.17,z+.035],.025,m['paint']),yaw)
    recoil=model.pivot(cid+'_recoil',c+[.30,0,0],parent=pitch)
    muzzle=-1.92 if large else -1.68
    if large:
        profile=[(muzzle,.104),(muzzle+.025,.11),(muzzle+.09,.11),(muzzle+.10,.084),(-1.38,.087),(-1.35,.103),(-1.29,.103),(-1.28,.088),(-.35,.115),(.45,.15),(1.49,.15),(1.50,.003),(.12,.003),(muzzle,.065),(muzzle,.104)]
        attach(lathe_x(cid+'_BARREL_AND_COLLARS',c,profile,m['gun']),recoil)
        attach(ring_x(cid+'_MUZZLE_RIM',c,muzzle,.108,.040,.028,m['edge']),recoil)
        # Visually legible earlier airborne cradle/guard, no wheels or trailer.
        housing=beveled_box(cid+'_BREECH_VISUAL_HOUSING',c+[1.32,-.20,-.23],c+[1.72,.19,.23],.025,m['gun'])
        _,housing=extract(housing,boxplanes(c+[1.50,-.105,-.105],c+[1.80,.105,.105]),cid+'_BREECH_VISUAL_HOUSING')
        attach(housing,recoil)
        attach(box(cid+'_CASE_EXIT_CAVITY',c+[1.50,-.105,-.105],c+[1.70,.105,.105],m['dark'],omit=['right']),recoil)
        breech=model.pivot(cid+'_case_exit_cover',c+[1.72,0,0],parent=recoil)
        attach(beveled_box(cid+'_CASE_EXIT_COVER',c+[1.705,-.115,-.115],c+[1.735,.115,.115],.010,m['gun']),breech)
        for s in [-1,1]:
            z=s*.26
            attach(path_tube(cid+f'_YELLOW_GUARD_{s}',[c+[.38,-.31,z],c+[1.60,-.31,z],c+[1.92,-.1,z],c+[1.92,.29,z],c+[.62,.29,z]],.024,m['yellow']),pitch)
            attach(beveled_box(cid+f'_YELLOW_CRADLE_PLATE_{s}',c+[.46,-.37,z-.018],c+[1.26,-.17,z+.018],.025,m['yellow']),pitch)
        attach(tube(cid+'_GUARD_CROSSBAR',c+[1.92,.29,-.26],c+[1.92,.29,.26],.025,m['yellow']),pitch)
        for z in [-.24,.24]:
            attach(tube(cid+('_SPRING_CORE_L' if z<0 else '_SPRING_CORE_R'),c+[.08,.24,z],c+[.62,.24,z],.029,m['steel']),pitch)
            pts=[c+[.08+.52*t,.24+.06*math.cos(t*22*math.pi),z+.06*math.sin(t*22*math.pi)] for t in np.linspace(0,1,177)]
            attach(path_tube(cid+('_VISIBLE_SPRING_L' if z<0 else '_VISIBLE_SPRING_R'),pts,.009,m['steel'],8),pitch)
        attach(beveled_box(cid+'_SIDE_ACTUATOR_COVER',c+[.45,-.49,.30],c+[.85,-.27,.47],.025,m['yellow']),pitch)
        # Spent-case receiving area is inside the cabin, empty at rest.
        fixed(box(cid+'_INTERNAL_CASE_TRAY',c+[1.36,-1.10,-.35],c+[2.04,-1.05,.38],m['paint']))
        fixed(box(cid+'_INTERNAL_CASE_TRAY_EDGE',c+[1.36,-1.10,.34],c+[2.04,-.98,.38],m['paint']))
    else:
        attach(lathe_x(cid+'_SINGLE_BARREL',c,[(muzzle,.05),(muzzle+.03,.05),(-1.29,.052),(-.41,.060),(-.38,.087),(.55,.087),(.55,.025),(muzzle,.025),(muzzle,.05)],m['gun']),recoil)
        attach(slotted_muzzle(cid+'_VENTED_MUZZLE_SLEEVE',c,m['edge']),recoil)
        attach(ring_x(cid+'_MUZZLE_RIM',c,muzzle,.096,.061,.025,m['edge']),recoil)
        attach(ring_x(cid+'_MUZZLE_REAR_COLLAR',c,-1.31,.095,.045,.024,m['gun']),recoil)
        receiver=beveled_box(cid+'_INBOARD_RECEIVER',c+[.30,-.19,-.22],c+[1.18,.22,.22],.025,m['gun'])
        _,receiver=extract(receiver,boxplanes(c+[.91,-.25,.085],c+[1.18,-.055,.215]),cid+'_INBOARD_RECEIVER')
        attach(receiver,recoil)
        attach(box(cid+'_DOWNWARD_CASE_EXIT_CAVITY',c+[.91,-.205,.085],c+[1.18,-.055,.215],m['dark'],omit=['bottom']),recoil)
        attach(beveled_box(cid+'_RECEIVER_TOP_COVER',c+[.37,.20,-.19],c+[1.10,.255,.19],.015,m['paint']),recoil)
        attach(tube(cid+'_RECEIVER_ROUND_SIDE_COVER',c+[.78,.02,.23],c+[.78,.02,.29],.12,m['gun'],segments=40),recoil)
        attach(ring_x(cid+'_BARREL_RETAINING_COLLAR',c,-.32,.11,.035,.10,m['paint']),recoil)
        # Broad curved guide belts: continuous thin support ribbons and shallow
        # link-like outer plates, instead of the earlier bead/cube loops.
        for zi,z in enumerate([-.28,.28]):
            points=[c+[.45+.61*t,.26+.38*math.sin(t*math.pi),z] for t in np.linspace(0,1,31)]
            for offset in [-.077,.077]:
                attach(path_tube(cid+f'_FEED_GUIDE_RAIL_{zi}_{int(offset>0)}',[q+[0,0,offset] for q in points],.014,m['gun']),pitch)
            for k in range(24):
                t=k/23;pos=c+[.45+.61*t,.26+.38*math.sin(t*math.pi),z]
                link=beveled_box(cid+f'_FEED_GUIDE_LINK_{zi}_{k}',pos+[-.017,-.014,-.080],pos+[.017,.014,.080],.005,m['paint'])
                attach(link,pitch)
        # Shallow visible receiver details, not functional concealed mechanisms.
        for k in range(6):
            x=.40+k*.125
            attach(beveled_box(cid+f'_RECEIVER_RIB_{k}',c+[x,-.14,-.236],c+[x+.018,.15,-.222],.004,m['edge']),recoil)
        for k,(x,y) in enumerate([(.40,-.13),(.40,.15),(1.08,-.13),(1.08,.15),(.74,.18)]):
            attach(tube(cid+f'_RECEIVER_FASTENER_{k}',c+[x,y,.231],c+[x,y,.243],.014,m['steel'],segments=6),recoil)
        attach(path_tube(cid+'_DARK_SERVICE_CABLE',[c+[1.05,-.17,.28],c+[1.2,-.28,.33],c+[1.16,-.5,.34],c+[.92,-.56,.30]],.013,m['boot']),pitch)
        bagc=c+[.95,-.19,.17]
        fixed(bag_mesh(cid+'_INTERNAL_SPENT_CASE_BAG',bagc,m['orange'] if model.id=='ac130j' else m['cloth']))
        fixed(box(cid+'_BAG_DARK_INNER_BASE',bagc+[-.25,-.77,-.20],bagc+[.25,-.75,.20],m['dark']))
        fixed(path_tube(cid+'_BAG_MOUTH_STIFFENER',[bagc+[.32*math.cos(a),-.22,.265*math.sin(a)] for a in np.linspace(0,2*math.pi,65)],.012,m['paint']))
        for zi,z in enumerate([-.12,.46]):fixed(beveled_box(cid+f'_BAG_RETAINING_STRAP_{zi}',c+[.61,-.96,z],c+[.67,-.39,z+.025],.006,m['cloth']))
    model.control(cid+'_yaw',label+' mount sweep',yaw,[0,1,0],7,duration=3,group='Mission equipment',ev=evidence('exterior105' if large else 'exterior30'))
    model.control(cid+'_pitch',label+' mount elevation',pitch,[0,0,1],12,duration=3,group='Mission equipment',ev=evidence('mount105' if large else 'exterior30'))
    stroke=.10 if large else .035
    model.control(cid+'_recoil',label+' recoil inspection',recoil,[1,0,0],stroke,kind='translation',duration=1.4,group='Mission equipment',owned_by=cid+'_fire_cycle',ev=evidence('recoil105' if large else 'case30'))
    g.node(cid+'_MUZZLE_VISUAL_SOCKET',parent=recoil,translation=[muzzle-.30,0,0],extras={'kind':'VISUAL_EFFECT_ALIGNMENT','forward_local':[-1,0,0],'operational_model':False})
    exitpos=c+([1.73,-.03,0] if large else [.99,-.08,.15])
    g.node(cid+'_CASE_EJECT_SOCKET',parent=pitch,translation=exitpos-model.known_pivots[pitch],extras={'kind':'INTERNAL_SPENT_CASE_VISUAL','collection':'internal_handling_area' if large else 'internal_bag'})
    case=model.pivot(cid+'_case',exitpos,parent=pitch,extras={'tags':['level 1'],'asset_id':('EMPTY_105_CASE_VISUAL' if large else 'EMPTY_30_CASE_VISUAL'),'no_projectile':True})
    cm=case_mesh(cid+'_SPENT_CASE',large,m['brass']);cm.move(exitpos);attach(cm,case)
    g.doc['nodes'][case]['scale']=[.0001]*3
    flash=model.pivot(cid+'_flash',c+[muzzle,0,0],parent=recoil,extras={'presentation_effect':True})
    attach(flash_mesh(cid+'_MUZZLE_FLASH',c+[muzzle,0,0],.98 if large else .53,m['flash']),flash)
    attach(flash_mesh(cid+'_MUZZLE_FLASH_CORE',c+[muzzle-.003,0,0],.61 if large else .32,m['flashCore']),flash)
    g.doc['nodes'][flash]['scale']=[.0001]*3
    smoke=model.pivot(cid+'_smoke',c+[muzzle-.23,0,0],parent=root,extras={'presentation_effect':True})
    attach(smoke_mesh(cid+'_MUZZLE_SMOKE',c+[muzzle-.23,0,0],m['smoke']),smoke);g.doc['nodes'][smoke]['scale']=[.0001]*3
    # One complete reversible visual cycle; case becomes visible at the real
    # inboard socket, moves into its receiving space and is consumed at end.
    times=np.unique(np.r_[np.linspace(0,1,129),.025,.035,.06,.10,.14,.19,.22,.26,.35,.48,.60,.70,.82,.88,.94,.98,1.])
    rec=[];caset=[];caser=[];cases=[];fl=[];sm=[];smp=[]
    casebase=np.asarray(g.doc['nodes'][case]['translation']);smokebase=np.asarray(g.doc['nodes'][smoke]['translation'])
    for t in times:
        r=np.interp(t,[0,.025,.06,.14,.42,1],[0,0,stroke,stroke*.4,0,0]);rec.append([r,0,0])
        a=np.clip((t-.24)/.48,0,1);b=a*a*(3-2*a)
        if large:delta=np.array([.30*b,-.94*b,.08*math.sin(math.pi*b)])
        else:delta=np.array([-.01*b,-.64*b,.02*math.sin(math.pi*b)])
        recover=1-np.clip((t-.88)/.12,0,1)
        caset.append(casebase+delta*recover);caser.append(quat([0,0,1],(180 if large else 125)*b*recover))
        visibility=np.interp(t,[0,.235,.24,.82,.88,1],[.0001,.0001,1,1,.0001,.0001]);cases.append([visibility]*3)
        strength=np.interp(t,[0,.025,.035,.06,.095,.10,1],[.0001,.0001,1,.75,.0001,.0001,.0001]);fl.append([strength]*3)
        size=np.interp(t,[0,.045,.08,.30,.62,.88,1],[.0001,.0001,.2,.75,1.25,.0001,.0001])*(1.4 if large else .8);size=max(size,.0001);sm.append([size]*3)
        smp.append(smokebase+np.array([-.45*b,.24*b,.06*b])*recover)
    tracks=[(recoil,'translation',times,rec),(case,'translation',times,caset),(case,'rotation',times,caser),(case,'scale',times,cases),(flash,'scale',times,fl),(smoke,'scale',times,sm),(smoke,'translation',times,smp)]
    if large:
        coverbase=np.asarray(g.doc['nodes'][breech]['translation'])
        cover=[coverbase+[0,0,-np.interp(t,[0,.16,.23,.75,.86,1],[0,0,.30,.30,0,0])] for t in times]
        tracks.append((breech,'translation',times,cover))
    g.animation(cid+'_fire_cycle',tracks)
    control={'id':cid+'_fire_cycle','label':label+' firing cycle','kind':'cycle','node':g.doc['nodes'][recoil]['name'],'clip':cid+'_fire_cycle','min':0,'max':1,'rest':0,'duration':3.4 if large else .9,'group':'Visual firing','units':'normalized presentation phase','preview_cycles':2 if large else 6,'owns':[cid+'_recoil'],'evidence':evidence('recoil105' if large else 'case30','case105' if large else 'case30j','smoke',note='Visible firing principles and interior case collection evidenced. This reversible demonstration uses authored timing, travel and case trajectory; no ballistic or operating model.'),'states':{'rest':'ready, no visible case or flash','deployed':'complete, ready; case consumed in interior receiving space'},'presentation_only':True}
    model.controls.append(control)
    profile={'control_id':control['id'],'asset_id':asset,'muzzle_socket':cid+'_MUZZLE_VISUAL_SOCKET','ejection_socket':cid+'_CASE_EJECT_SOCKET','case_node':cid+'_SPENT_CASE','case_transform':g.doc['nodes'][case]['name'],'flash_node':g.doc['nodes'][flash]['name'],'smoke_node':g.doc['nodes'][smoke]['name'],'collection':'internal_handling_area' if large else 'internal_bag','presentation_only':True,'outside_case_ejection':False,'case_visibility_interval':[.24,.82],'no_targeting_or_ballistics':True,'spent_lifecycle':'case appears at internal exit; falls inside; consumed at end; preview reset restores hidden state'}
    model.firing_profiles=getattr(model,'firing_profiles',[])+[profile]
    model.log.append({'component':asset,'reference':REFS['exterior105' if large else 'exterior30'],'changes':'separate aircraft installation; single barrel; internal receiver, spent-case collection, visible recoil and flash; original geometry','status':'PHOTO_GUIDED_REVIEW_NOT_PHOTOREAL_ACCEPTANCE'})
    return {'root':root,'root_name':g.doc['nodes'][root]['name'],'asset_id':asset,'control_ids':[cid+s for s in ['_yaw','_pitch','_recoil','_fire_cycle']], 'firing_profile':profile}
