#!/usr/bin/env python3
"""claude-design: preserved-source modular C130 r0002 candidate builder.

Physical shapes and timings of newly authored equipment are visual approximations.
This creates editable geometry and real glTF clips, not aircraft engineering or
native Unreal acceptance. r0001 remains an immutable input.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, math
from pathlib import Path
import numpy as np
from gltf_core import *

HERE=Path(__file__).resolve().parent
OUT=HERE.parent
REPO=HERE.parents[3] if len(HERE.parents)>3 else HERE.parent
INPUT_HASH='ad3b1ff76fcff48dbb7dbc4901665f65def89f9db12d56112a00ee86389a0b12'
REF={
 'crew':'https://www.dvidshub.net/image/4610490/16th-expeditionary-special-operations-squadron-provides-air-support',
 'w':'https://www.hurlburt.af.mil/About-Us/Fact-Sheets/Fact-Sheets/Article/2559094/ac-130w-stinger-ii/',
 'w_photo':'https://www.dvidshub.net/image/4610565/16th-expeditionary-special-operations-squadron-provides-air-support',
 'ramp':'https://www.dvidshub.net/image/7368321/',
 'j_ramp':'https://www.dvidshub.net/image/7918477/',
 'j_nacelle':'https://www.dvidshub.net/image/6616476/',
 'j_cockpit':'https://www.dvidshub.net/image/7918484/',
 'j_flaps':'https://www.dvidshub.net/image/6616471/',
 'door':'https://www.dvidshub.net/image/7135325/',
 'gear':'https://www.dvidshub.net/image/229270/c-130-landing-gear-inspection',
}

def evidence(*keys,note='Travel/geometry is an authored visual approximation; native clearance and photographic acceptance pending.'):
    return {'status':'SOURCE_SUPPORTED_PRINCIPLE_ARTIST_AUTHORED_TRAVEL','sources':[REF[k] for k in keys if k in REF],'limitations':note}

def smooth(t):return t*t*(3-2*t)
def staged(t,a,b):return smooth(np.clip((np.asarray(t)-a)/(b-a),0,1))

def cap_for_planes(mesh,planes,name,material):
    """Close exposed extraction edges; caps are small inferred internal surfaces."""
    from scipy.spatial import ConvexHull
    caps=[]
    for i,(n,d) in enumerate(planes):
        norm=np.linalg.norm(n);n=np.asarray(n,float)/norm;d=d/norm;p=mesh.p[np.abs(mesh.p@n-d)<1e-5]
        p=np.unique(np.round(p,7),axis=0)
        if len(p)<3:continue
        u=normalize(np.cross(n,[0,1,0] if abs(n[1])<.8 else [1,0,0]));v=np.cross(n,u)
        xy=np.c_[p@u,p@v]
        try:h=ConvexHull(xy);ps=p[h.vertices]
        except Exception:continue
        c=ps.mean(0);verts=np.vstack([c,ps]);faces=[(0,j+1,((j+1)%len(ps))+1) for j in range(len(ps))]
        caps.append(make_mesh(name+f'_SEAM_CAP_{i}',verts,faces,material,{'geometry_status':'INFERRED_INTERNAL_SEAM','source':'extracted original skin boundary'}))
    return caps

def prepare_common(src):
    body=src[1].clone('fuselage');surfaces=[]
    for side,sgn in [('right',1),('left',-1)]:
        for kind,xlo,xhi,angle in [('flap',3.2,11.4,32),('aileron',11.45,19.7,17)]:
            planes=[([sgn,0,0],xlo),([-sgn,0,0],-xhi),([0,1,0],4.0),([0,-1,0],-5.25),([sgn*.09,0,1],.65),([0,0,-1],-3.0)]
            part,body=extract(body,planes,kind+'_'+side+'_SKIN');x=sgn*(xlo+xhi)/2;z=.65-.09*abs(x)
            surfaces.append({'id':kind+'_'+side,'label':f'{side.title()} {kind}','mesh':part,'planes':planes,'pivot':[x,4.56,z],'axis':([1,0,-sgn*.09] if kind=='flap' or side=='right' else [-1,0,-.09]),'angle':angle,'group':'Flight controls'})
        planes=[([sgn,0,0],1.65),([-sgn,0,0],-8.05),([0,1,0],3.7),([0,-1,0],-5.3),([sgn*.24,0,1],13.75)]
        part,body=extract(body,planes,'elevator_'+side+'_SKIN');x=sgn*4.6
        surfaces.append({'id':'elevator_'+side,'label':f'{side.title()} elevator','mesh':part,'planes':planes,'pivot':[x,4.48,13.75-.24*abs(x)],'axis':[1,0,-sgn*.24],'angle':22,'group':'Flight controls'})
    planes=[([1,0,0],-.5),([-1,0,0],-.5),([0,1,0],5.4),([0,-1,0],-11.75),([0,-.18,1],10.43)]
    part,body=extract(body,planes,'rudder_SKIN');surfaces.append({'id':'rudder','label':'Rudder','mesh':part,'planes':planes,'pivot':[0,5.4,11.402],'axis':[0,1,.18],'angle':25,'group':'Flight controls'})
    return body,surfaces

class Model:
    def __init__(self,mid,label,images,exact_index=True):
        self.id=mid;self.label=label;self.glb=GLB(label,exact_index=exact_index);self.controls=[];self.openings=[];self.log=[];self.known_pivots={0:np.zeros(3)}
        for b,mime in images:self.glb.image(b,mime)
        g=self.glb
        self.mat={}
        self.mat['interior']=g.material('PRESERVED_INTERIOR_NORMAL_MASTER',[.62,.65,.64,1],.05,.86,normal=0)
        self.mat['skin']=g.material('PRESERVED_SKIN_NORMAL_MASTER',[.66,.69,.68,1],.12,.64,normal=1)
        self.mat['gray']=g.material('REPLACEABLE_NEUTRAL_AIRFRAME',[.51,.55,.56,1],.12,.68)
        self.mat['dark']=g.material('BAY_INTERIOR_DARK',[.055,.07,.075,1],.03,.95)
        self.mat['metal']=g.material('ACTUATOR_METAL',[.36,.4,.42,1],.65,.33)
        self.mat['black']=g.material('RUBBER_AND_PROPELLER',[.035,.045,.05,1],.07,.61)
        self.mat['glass']=g.material('COCKPIT_GLASS',[.09,.19,.24,.52],.08,.2)
        self.mat['sensor']=g.material('SENSOR_OPTICS',[.08,.22,.28,1],.25,.22)
        self.mat['screen']=g.material('J_DIGITAL_DISPLAY',[.025,.1,.09,1],.05,.42,emissive=[.04,.28,.18])
        self.mat['houseTint']=g.material('houseTint',[1,1,1,1],.05,.65)
        self.static=g.node('AIRFRAME_COMMON_SOURCE',extras={'part_id':'fuselage','source_revision':'r0001','source_sha256':INPUT_HASH,'shared_master':'C130_COMMON_claude-design_r0002','scale_baked':True})
        self.kit=g.node('MISSION_KIT_'+mid.upper(),extras={'configuration':label,'geometry_status':'VISUAL_APPROXIMATION_NOT_PHOTO_ACCEPTED'})
    def static_mesh(self,m,parent=None):return self.glb.mesh(m,self.static if parent is None else parent)
    def pivot(self,cid,pos,parent=0,extras=None):
        p=np.asarray(pos,float);base=self.known_pivots.get(parent,np.zeros(3));i=self.glb.node('PIVOT_'+cid,parent=parent,translation=p-base,extras={'part_id':cid,**(extras or {})});self.known_pivots[i]=p;return i
    def attach(self,mesh,pivot):return self.glb.mesh(mesh,parent=pivot,origin=self.known_pivots[pivot])
    def control(self,cid,label,pivot,axis,maximum,kind='rotation',duration=3,group='Mechanisms',role=None,ev=None,tracks=None,**kwargs):
        axis=np.asarray(axis,float)
        if maximum<0:axis=-axis;maximum=-maximum
        times=np.linspace(0,1,33);rest=self.glb.doc['nodes'][pivot].get('translation',[0,0,0]);q=smooth(times)
        if tracks is None:
            if kind in ('rotation','continuous'):
                q=times if kind=='continuous' else q;tracks=[(pivot,'rotation',times,[quat(axis,maximum*t) for t in q])]
            else:tracks=[(pivot,'translation',times,[np.asarray(rest)+axis*maximum*t for t in q])]
        self.glb.animation(cid,tracks)
        c={'id':cid,'label':label,'kind':kind,'node':self.glb.doc['nodes'][pivot]['name'],'axis':axis.tolist(),'min':0,'max':maximum,'rest':0,'duration':duration,'group':group,'clip':cid,'units':'metres' if kind=='translation' else 'degrees','normalized_input':True,'evidence':ev or evidence(),'states':{'rest':'canonical','deployed':'presentation endpoint'},**kwargs}
        if role:c['role']=role
        self.controls.append(c);self.glb.doc['nodes'][pivot]['extras']['actuator']={'jointType':{'rotation':'revolute','translation':'prismatic','continuous':'continuous'}[kind],'axis':axis.tolist(),'limits':[0,maximum],'units':c['units'],'control':cid,'canonical_rest':rest,'evidence_status':c['evidence']['status']}
        return c
    def opening(self,cid,aperture,receiver,closure,depth,note):
        self.openings.append({'id':cid,'aperture':aperture,'receiver':receiver,'closure':closure,'minimum_depth_m':depth,'layout_status':'PRESERVED_SOURCE_OR_ILLUSTRATIVE','control':cid,'notes':note,'visual_validation':'PENDING_CURRENT_EXPORT_RENDER'})

def cylinder_shell(name,start,end,radius,wall,material):
    a=tube(name+'_OUTER',start,end,radius,material,cap=False);b=tube(name+'_INNER',start,end,radius-wall,material,cap=False);b.faces=b.faces[:,[0,2,1]]
    return merge([a,b],name)

def six_blades(center,idx,material):
    verts=[];faces=[];c=np.asarray(center)
    for k in range(6):
        a=2*math.pi*k/6;start=len(verts)
        for r,w,sweep in ((.24,.21,0),(.65,.28,.025),(1.2,.27,.1),(1.75,.19,.22),(2.02,.055,.34)):
            u=np.array([math.cos(a),math.sin(a),0]);v=np.array([-math.sin(a),math.cos(a),0]);p=c+u*r+v*sweep
            verts.extend([p+v*w*.5+[0,0,.045],p-v*w*.5+[0,0,-.045]])
        for j in range(4):p=start+2*j;faces.extend([(p,p+1,p+3),(p,p+3,p+2)])
    return make_mesh(f'PROP_{idx}_SIX_SWEPT_BLADES',verts,faces,material,{'tags':['level 1'],'blade_count':6,'geometry_status':'PHOTO_GUIDED_ARTIST_APPROXIMATION'})

def nacelle(name,center,material):
    x,y,z=center;sections=[(-6.09,.43,.43),(-5.8,.59,.61),(-5.25,.61,.65),(-4.2,.57,.61),(-3.25,.49,.46),(-2.75,.31,.3)];verts=[];faces=[];seg=28
    for zz,rx,ry in sections:
        for a in np.linspace(0,2*math.pi,seg,endpoint=False):verts.append((x+rx*math.cos(a),y+ry*math.sin(a),zz))
    for k in range(len(sections)-1):
        for j in range(seg):a=k*seg+j;b=k*seg+(j+1)%seg;faces.extend([(a,b,b+seg),(a,b+seg,a+seg)])
    return make_mesh(name,verts,faces,material,{'tags':['level 1'],'geometry_status':'J_NACELLE_PHOTO_GUIDED_APPROXIMATION','reference':REF['j_nacelle']})

def add_cockpit(model,j):
    g=model.glb;mat=model.mat;p=model.kit
    model.static_mesh(box(('J' if j else 'LEGACY')+'_COCKPIT_PANEL',[-1.12,2.83,-12.45],[1.12,3.34,-12.24],mat['dark']),p)
    for i,x in enumerate([-.88,-.44,0,.44,.88]):
        if j:
            model.static_mesh(box(f'J_MULTIFUNCTION_DISPLAY_{i+1}',[x-.16,2.97,-12.47],[x+.16,3.23,-12.44],mat['screen']),p)
        else:
            model.static_mesh(tube(f'LEGACY_ANALOG_DIAL_{i+1}',[x,3.10,-12.48],[x,3.10,-12.45],.105,mat['metal'],segments=20),p)
    if j:
        for i,x in enumerate([-.65,.65]):model.static_mesh(box(f'J_HUD_GLASS_{i+1}',[x-.18,3.48,-12.55],[x+.18,3.72,-12.52],mat['glass']),p)
    model.log.append({'component':'cockpit','variant':'J digital displays/HUD' if j else 'legacy analogue dial insert','status':'PHOTO_GUIDED_ILLUSTRATIVE_LAYOUT','reference':REF['j_cockpit']})

def attach_wheel(model,mesh,pivot,name,nose=False):
    """Material partition retains every original triangle and all source UVs."""
    center=mesh.center();centroids=mesh.p[mesh.faces].mean(1);radius=np.linalg.norm(centroids[:,1:3]-center[1:3],axis=1);tire=radius>(.30 if nose else .41)
    for mask,suffix,material in [(tire,'TIRE',model.mat['black']),(~tire,'RIM',model.mat['metal'])]:
        part=mesh.subset(mask,name+'_'+suffix);part.material=material;model.attach(part,pivot)

def attach_legacy_prop(model,mesh,pivot,num):
    c=mesh.center();centroids=mesh.p[mesh.faces].mean(1);r=np.linalg.norm(centroids[:,:2]-c[:2],axis=1);hub=r<.43;tip=r>1.87
    for mask,suffix,material in [(hub,'HUB_SOURCE',model.mat['gray']),(~hub&~tip,'BLADES_SOURCE',model.mat['black']),(tip,'TIP_PATCHES',model.mat['gray'])]:
        part=mesh.subset(mask,f'PROP_{num}_{suffix}');part.material=material;model.attach(part,pivot)

# r0003 replaces the provisional system shapes with independent visual modules.
from gun_components import add_gun
from eoir_component import add_sensor

def fitted_gun_interface(meshes,center,radius):
    # Project the retained source skin at each interface-ring angle. This is
    # an installation adapter, not a changed canonical gun component.
    c=np.asarray(center,float);triangles=np.concatenate([m.p[m.faces] for m in meshes]);a=triangles[:,0];e1=triangles[:,1]-a;e2=triangles[:,2]-a
    det=e1[:,1]*e2[:,2]-e1[:,2]*e2[:,1];good=np.abs(det)>1e-9;den=np.where(good,det,1)
    angles=np.linspace(0,2*math.pi,72,endpoint=False);values=[]
    for angle in angles:
        y,z=c[1]+radius*math.cos(angle),c[2]+radius*math.sin(angle)
        u=((y-a[:,1])*e2[:,2]-(z-a[:,2])*e2[:,1])/den;v=(e1[:,1]*(z-a[:,2])-e1[:,2]*(y-a[:,1]))/den
        x=a[:,0]+u*e1[:,0]+v*e2[:,0];mask=good&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(x<-.9)&(x>-2.8)
        values.append(float(x[mask].min()-c[0]) if np.any(mask) else float('nan'))
    val=np.asarray(values);ok=np.isfinite(val)
    if ok.sum()<8:raise ValueError('Too few source-skin observations for gun interface')
    val=np.interp(angles,np.r_[angles[ok]-2*math.pi,angles[ok],angles[ok]+2*math.pi],np.tile(val[ok],3))
    return {'outer_x_offset':val.tolist(),'samples':72,'method':'left external source-skin ray intersection around the installation ring','minimum_offset':float(val.min()),'maximum_offset':float(val.max())}

def build_one(mid,label,src,images,common,surfaces,exact_index=True):
    model=Model(mid,label,images,exact_index=exact_index);mat=model.mat;body=common.clone();interior=src[23].clone('CARGO_CABIN_PRESERVED');j=mid=='ac130j';gunship=mid!='c130'
    # Separate legacy/J powerplant modules rather than swapping prop blades alone.
    if j:
        for num,si in enumerate([2,3,4,5],1):
            c=src[si].center();planes=boxplanes([c[0]-.78,3.0,-5.79],[c[0]+.78,4.53,-2.72]);removed,body=extract(body,planes,f'REMOVED_LEGACY_NACELLE_{num}')
            model.static_mesh(nacelle(f'J_AE2100_STYLE_NACELLE_{num}',c,mat['gray']),model.kit)
            model.static_mesh(box(f'J_LOWER_INTAKE_DUCT_{num}',[c[0]-.27,3.28,-6.10],[c[0]+.27,3.60,-5.28],mat['dark'],omit=['front']),model.kit)
            for k,lo,hi in [
                ('BOTTOM',[c[0]-.32,3.23,-6.12],[c[0]+.32,3.29,-5.80]),
                ('TOP',[c[0]-.32,3.60,-6.12],[c[0]+.32,3.66,-5.80]),
                ('LEFT',[c[0]-.32,3.23,-6.12],[c[0]-.27,3.66,-5.80]),
                ('RIGHT',[c[0]+.27,3.23,-6.12],[c[0]+.32,3.66,-5.80]),
            ]:model.static_mesh(box(f'J_INTAKE_LIP_{num}_{k}',lo,hi,mat['gray']),model.kit)
            model.static_mesh(tube(f'J_EXHAUST_{num}',[c[0],3.85,-2.75],[c[0],3.9,-2.35],.21,mat['metal'],cap=False),model.kit)
            model.log.append({'component':f'J nacelle {num}','replaced_source_triangles':len(removed.faces),'status':'PHOTO_GUIDED_APPROXIMATION','reference':REF['j_nacelle']})
    model.gun_interface_profiles={}
    # Port fuselage mission regions use the retained skin; apertures remove both
    # outer skin and the actual cabin wall. Solid transport infills are the same source.
    for key,lo,hi,center,large in [
        ('gun30',[-2.8,1.75,-8.85],[-1.20,3.30,-6.6],[-2.125,2.55,-7.72],False),
        ('gun105',[-2.8,.99,1.65],[-1.15,3.2,3.45],[-2.022,2.20,2.35],True),
    ]:
        if gunship:model.gun_interface_profiles[key]=fitted_gun_interface([body,src[20]],center,.47 if large else .55)
        patch,body=extract(body,boxplanes(lo,hi),'PANEL_'+key.upper()+'_SOURCE_SKIN')
        if not gunship:model.static_mesh(patch)
        else:
            c=np.asarray(center);radius=.455 if large else .535
            holelo=np.array([lo[0],c[1]-radius,c[2]-radius]);holehi=np.array([hi[0],c[1]+radius,c[2]+radius])
            # A real polygonal circular aperture through skin and inner liner.
            radial=[([0,-math.cos(a),-math.sin(a)],-(c[1]*math.cos(a)+c[2]*math.sin(a)+radius)) for a in np.linspace(0,2*math.pi,48,endpoint=False)]
            holeplanes=[([1,0,0],lo[0]-.1),([-1,0,0],-hi[0]-.1)]+radial
            hole,patch=extract(patch,holeplanes,'REMOVED_'+key+'_APERTURE')
            _,interior=extract(interior,holeplanes,'REMOVED_'+key+'_CABIN_WALL')
            model.static_mesh(patch,model.kit)
            # Aft gun station replaces the port paratroop door module, so no
            # moving door is hidden behind the mounted gun.
            if key=='gun105':
                door=src[20].clone('PANEL_AFT_PORT_GUN_STATION_INFILL');_,door=extract(door,holeplanes,'REMOVED_AFT_DOOR_GUN_PORT');model.static_mesh(door,model.kit)
            # The retained bounded cargo cabin receives the mechanism. Do not
            # seal the mount inside a fictitious box that hides its inboard end.
            model.opening(key,'PANEL_'+key.upper()+'_SOURCE_SKIN','CARGO_CABIN_PRESERVED',None,1.65,'Circular opening through retained skin and cabin liner; visible inboard gun and case collection in existing bounded cabin.')
            add_gun(model,key,center,large)
    # Source doors already lie in holes; remove residual crossing wall triangles
    # precisely at their opening rectangles and retain the source cabin volume.
    for key,lo,hi in [
        ('crew',[-2.4,.89,-10.28],[-1.31,2.38,-9.44]),
        ('para_right',[1.43,1.0,1.83],[2.3,3.01,2.66]),
        ('para_left',[-2.3,1.0,1.83],[-1.43,3.01,2.66]),
    ]:
        if gunship and key=='para_left':continue
        _,body=extract(body,boxplanes(lo,hi),'REMOVED_'+key+'_EXTERIOR_BLOCKER')
        _,interior=extract(interior,boxplanes(lo,hi),'REMOVED_'+key+'_INTERIOR_BLOCKER')
    # Remove only the actual swept inner wheel corridor. The original outer
    # sponson remains the exterior envelope; restoring the whole core skin would
    # put an internal sheet through the retracted wheels.
    for side,sgn,ids in [('left',-1,[7,8]),('right',1,[9,10])]:
        lo=[min(sgn*1.45,sgn*2.455),.35,-3.24];hi=[max(sgn*1.45,sgn*2.455),1.48,-.31]
        _,body=extract(body,boxplanes(lo,hi),'REMOVED_'+side+'_LOWER_WELL_MOUTH')
        directions=[]
        for aa,bb in [(0,1),(0,2),(1,2)]:
            for angle in np.linspace(0,2*np.pi,24,endpoint=False):
                n=np.zeros(3);n[aa]=np.cos(angle);n[bb]=np.sin(angle);directions.append(n)
        directions=np.unique(np.round(directions,8),axis=0)
        for wi in ids:
            swept=np.concatenate([src[wi].p,src[wi].p+[0,1.25,0]])
            planes=[(-n,-float(np.max(swept@n))-.018) for n in directions]
            local,outer=extract(body,boxplanes(swept.min(0)-.025,swept.max(0)+.025),'LOCAL_'+side+'_WHEEL_CORRIDOR')
            _,local=extract(local,planes,'REMOVED_'+side+'_INNER_WHEEL_SWEEP')
            body=merge([outer,local],body.name)
        # A fitted receiver follows the inner side of the original fairing.
        # Its lower edge follows the closed cover, rather than leaving a box
        # wall hanging below that cover or beyond the curved exterior.
        profile=[(1.45,.78),(2.40,1.47),(2.41,1.80),(2.37,2.10),(2.29,2.40),(2.20,2.55),(2.09,2.62),(1.45,2.62)]
        verts=[(sgn*x,y,z) for z in [-3.20,-.35] for x,y in profile];n=len(profile);faces=[]
        for k in range(1,n):
            kk=(k+1)%n;faces.extend([(k,kk,n+kk),(k,n+kk,n+k)])
        for k in range(1,n-1):faces.extend([(0,k+1,k),(n,n+k,n+k+1)])
        model.static_mesh(make_mesh('GEAR_WELL_'+side.upper(),verts,faces,mat['dark'],{'geometry_status':'FITTED_TO_SOURCE_SPONSON','source_outer_skin_preserved':True,'artist_authored_travel_m':1.25}))
    model.log.append({'component':'main landing gear well fit','change':'retained original outer fairing, removed only swept inner wheel corridor; tapered receiver fitted inside original shell and above closed cover','travel_m':1.25,'status':'ARTIST_AUTHORED_GEOMETRY_PENDING_CURRENT_EXPORT_QA'})
    nose_skin,body=extract(body,boxplanes([-.62,.1,-13.65],[.62,2.40,-12.24]),'NOSE_WELL_SOURCE_SKIN')
    # The forward fold needs a short added well ahead of the source opening.
    # The source's aft opening is retained; the original aft closure translates
    # forward/up into it, so there is no replacement bridge across parked tyres.
    _,body=extract(body,boxplanes([-.65,1.24,-13.675],[.65,1.38,-13.64]),'NOSE_FORWARD_LIP_CLEARANCE')
    model.static_mesh(box('GEAR_WELL_NOSE',[-.83,1.48,-13.7],[.83,2.44,-10.85],mat['dark'],omit=['bottom']))
    # Exact first-export triangle probes located source interior ribs crossing
    # the closing ramp side rails. Relieve those small internal pockets only;
    # retain the exterior shell and the rest of the bounded original cabin.
    for s in [-1,1]:
        lo=[min(s*1.47,s*1.66),1.85,5.20];hi=[max(s*1.47,s*1.66),2.37,6.32]
        _,interior=extract(interior,boxplanes(lo,hi),'RELIEVED_CARGO_RAMP_SIDE_RIB')
    model.log.append({'component':'cargo ramp internal side clearance','change':'paired local cabin-rib relief pockets only','bounds_abs_x':[1.47,1.66],'bounds_y':[1.85,2.37],'bounds_z':[5.20,6.32],'basis':'actual exported triangle crossing coordinates','acceptance':'REQUIRES_CURRENT_EXPORT_SWEEP'})
    tint,body=extract(body,boxplanes([-2.8,2.65,-5.0],[-1.20,3.05,-4.4]),'PATCH_houseTint_PORT');tint.material=mat['houseTint'];model.static_mesh(tint)
    model.static_mesh(body);model.static_mesh(interior)
    # Glass is a separate replaceable material; preserved normal maps/UVs remain.
    windows=src[0].clone('COCKPIT_WINDOWS');windows.material=mat['glass'];model.static_mesh(windows)
    add_cockpit(model,j)
    # Every recovered flight surface has its real extracted skin and an actual clip.
    for s in surfaces:
        if not len(s['mesh'].faces):model.log.append({'component':s['id'],'status':'UNRECOVERED_EMPTY_PATCH'});continue
        p=model.pivot(s['id'],s['pivot']);model.attach(s['mesh'],p)
        for cap in cap_for_planes(s['mesh'],s['planes'],s['id'],mat['gray']):
            model.attach(cap,p)
            # The fixed airfoil also has a real internal closing surface. A
            # tiny offset avoids coincident caps at canonical hinge contact.
            fixed=cap.clone(cap.name+'_FIXED_WING');fixed.move([0,-.002,0]);model.static_mesh(fixed)
        model.control(s['id'],s['label'],p,s['axis'],s['angle'],duration=3.2,group=s['group'],ev=evidence('j_flaps',note='Surface skin extracted from source; hinge locations inferred from source shape/photo. Full aerodynamic limits not claimed.'))
    # Propellers: correct hub-centered parent pivots; legacy meshes remain intact.
    for num,si in enumerate([2,3,4,5],1):
        c=src[si].center();c[2]=(-6.26 if j else c[2]);p=model.pivot(f'prop_{num}',c,extras={'tags':['level 1'],'component_type':'propeller','blade_count':6 if j else 4})
        if j:
            model.attach(six_blades(c,num,mat['black']),p);model.attach(tube(f'PROP_{num}_J_SPINNER',c+[0,0,-.45],c+[0,0,.05],.05,mat['gray'],radius_end=.29),p)
        else:attach_legacy_prop(model,src[si],p,num)
        model.control(f'prop_{num}',f'Propeller {num}',p,[0,0,1],360,kind='continuous',duration=1.4,group='Propulsion',ev=evidence('j_nacelle' if j else 'w_photo'))
    # Cargo source-rest reconstruction uses the baked source matrices, not a
    # generic clamshell: upper leaf folds inward, lower ramp lowers separately.
    ramp_p=np.array(src[11].extras['reconstructed_source_pivot']);upper_p=np.array(src[15].extras['reconstructed_source_pivot'])
    ramp=model.pivot('cargo_ramp',ramp_p);upper=model.pivot('cargo_upper_door',upper_p)
    lower=src[11].clone('CARGO_LOWER_RAMP_PRESERVED')
    for s in [-1,1]:
        planes=boxplanes([min(s*1.89,s*2.10),1.90,5.15],[max(s*1.89,s*2.10),2.41,6.11]);trim,lower=extract(lower,planes,'RAMP_OUTER_FLANGE_FIT_RELIEF')
        for cap in cap_for_planes(trim,[([-s,0,0],-1.89)],'CARGO_LOWER_RAMP_FLANGE_CAP_'+str(s),mat['gray']):model.attach(cap,ramp)
    model.attach(lower,ramp);model.attach(src[22].clone('CARGO_RAMP_INTERIOR_PRESERVED'),ramp);model.attach(src[15].clone('CARGO_UPPER_DOOR_PRESERVED'),upper)
    model.log.append({'component':'cargo ramp outer flange fit','change':'only measured outer closing-corner flange protrusions trimmed/capped at absolute X1.89m, Y1.90..2.41m, Z5.15..6.11m','basis':'actual closed-state source ramp/exterior intersections, including prior 4.3mm trim-end contact','not_changed':'overall airframe scale, central ramp floor and original cabin'})
    times=np.linspace(0,1,49);ra=27.5*staged(times,.25,1);ua=20*staged(times,0,.3)
    model.control('cargo_ramp','Cargo ramp and upper-door sequence',ramp,[1,0,0],27.5,duration=7,group='Cargo access',role='access',ev=evidence('ramp','j_ramp'),tracks=[(upper,'rotation',times,[quat([1,0,0],a) for a in ua]),(ramp,'rotation',times,[quat([1,0,0],a) for a in ra])],owns=['cargo_upper_door'],sequence={'open':'upper leaf clears, then ramp lowers','reverse':'ramp raises, then upper leaf closes'})
    model.control('cargo_upper_door','Upper cargo door inspection',upper,[1,0,0],20,duration=3,group='Cargo access',role='access',ev=evidence('j_ramp'),owned_by='cargo_ramp',enabled_if={'control':'cargo_ramp','equals':0})
    model.opening('cargo_ramp','CARGO_APERTURE_ORIGINAL','CARGO_CABIN_PRESERVED',['CARGO_LOWER_RAMP_PRESERVED','CARGO_UPPER_DOOR_PRESERVED'],8.0,'Original full cabin, floor, ribs and aft opening retained. Closing rest reconstructed from original baked part transforms.')
    # Forward entry: lower-sill hinge; actual separate steps fold with door.
    crew_p=np.array([-1.69,.93,-9.84]);crew=model.pivot('crew_door',crew_p);model.attach(src[12].clone('CREW_AIRSTAIR_DOOR_PRESERVED'),crew)
    for k in range(4):
        x=-1.95-k*.24;y=.82-k*.22;stair=box(f'CREW_STAIR_TREAD_{k+1}',[x-.14,y-.055,-10.13],[x+.13,y+.015,-9.55],mat['metal']);stair.rotate(crew_p,[0,0,1],-127);model.attach(stair,crew)
    model.control('crew_door','Forward crew airstair door',crew,[0,0,1],127,duration=4.5,group='Personnel access',role='access',ev=evidence('crew','w_photo',note='Downward opening and stairway photographically supported; tread shape/hinge travel are artist inferred.'))
    model.opening('crew_door','CREW_APERTURE_CUT','CARGO_CABIN_PRESERVED','CREW_AIRSTAIR_DOOR_PRESERVED',1.3,'Original exterior and interior blockers removed at original door; original bounded cabin retained.')
    for side,sgn,ids in [('right',1,[18,19]),('left',-1,[20,21])]:
        if gunship and side=='left':continue
        p0=np.array([sgn*1.98,1.03,2.24]);p=model.pivot('paratroop_'+side,p0)
        for si in ids:model.attach(src[si].clone('PARATROOP_'+side.upper()+f'_SOURCE_{si}'),p)
        tt=np.linspace(0,1,49);up=2.0*staged(tt,.15,1);inward=.38*staged(tt,0,.23);angle=sgn*50*staged(tt,.4,1)
        tr=[p0+[-sgn*v,u,0] for v,u in zip(inward,up)];rr=[quat([0,0,1],a) for a in angle]
        model.control('paratroop_'+side,side.title()+' raised personnel door',p,[0,1,0],2.0,kind='translation',duration=4.5,group='Personnel access',role='access',ev=evidence('door',note='Raised/inward principle supported; curved overhead recovery path artist inferred.'),tracks=[(p,'translation',tt,tr),(p,'rotation',tt,rr)])
        model.opening('paratroop_'+side,'PARATROOP_'+side.upper()+'_APERTURE_CUT','CARGO_CABIN_PRESERVED',[f'PARATROOP_{side.upper()}_SOURCE_{i}' for i in ids],2.0,'Actual skin/cabin cut; overhead final tilt authored to fit receiving volume.')
    # Landing gear: tandem mains travel vertically, nose folds forward.
    for side,sgn,wheels,cover in [('left',-1,[7,8],13),('right',1,[9,10],14)]:
        gp=np.array([sgn*1.866,.66,-1.79]);gear=model.pivot('gear_'+side,gp)
        for n,si in enumerate(wheels,1):
            wc=src[si].center();wheel=model.pivot(f'wheel_{side}_{n}',wc,parent=gear);attach_wheel(model,src[si],wheel,f'WHEEL_{side.upper()}_{n}_PRESERVED')
            model.control(f'wheel_{side}_{n}',f'{side.title()} wheel {n}',wheel,[1,0,0],360,kind='continuous',duration=2.4,group='Wheels',ev=evidence('gear'))
            model.attach(tube(f'MAIN_STRUT_{side}_{n}',wc+[0,.32,0],wc+[0,.88,0],.065,mat['metal']),gear)
            model.static_mesh(tube(f'MAIN_FIXED_TELESCOPIC_STRUT_{side}_{n}',wc+[0,.9,0],wc+[0,2.28,0],.048,mat['metal']))
        dp=np.array([sgn*2.44,1.44,-1.78]);door=model.pivot('gear_door_'+side,dp);model.attach(src[cover].clone('MAIN_GEAR_COVER_'+side.upper()+'_PRESERVED'),door)
        tt=np.linspace(0,1,65);lift=1.25*staged(tt,.18,.72);dangle=sgn*(18*staged(tt,0,.18)-108*staged(tt,.74,1))
        model.control('gear_'+side,side.title()+' main gear sequence',gear,[0,1,0],1.25,kind='translation',duration=7,group='Landing gear',role='gear_sequence',ev=evidence('gear',note='Vertical main-gear principal motion supported; travel and cover linkage are authored pending clearance/photo validation.'),tracks=[(gear,'translation',tt,[gp+[0,h,0] for h in lift]),(door,'rotation',tt,[quat([0,0,1],a) for a in dangle])],owns=['gear_door_'+side],states={'rest':'DOWN: covers hanging open','deployed':'RETRACTED: wheels inside wells and covers shut'})
        model.control('gear_door_'+side,side.title()+' gear-cover inspection',door,[0,0,1],sgn*18,duration=2.2,group='Landing gear',role='gear_door',ev=evidence('gear'),owned_by='gear_'+side,enabled_if={'control':'gear_'+side,'equals':0})
    ngp=np.array([0,1.60,-12.02]);nose=model.pivot('gear_nose',ngp);model.attach(src[16].clone('NOSE_GEAR_STRUT_PRESERVED'),nose);nw=src[17].center();wheel=model.pivot('wheel_nose',nw,parent=nose);attach_wheel(model,src[17],wheel,'NOSE_WHEELS_PRESERVED',nose=True)
    model.control('wheel_nose','Nose wheels',wheel,[1,0,0],360,kind='continuous',duration=2.4,group='Wheels',ev=evidence('gear'))
    ndp=np.array([0,.33,-9.88]);nd=model.pivot('gear_door_nose',ndp)
    aft_panel,aft_links=extract(src[6], [([0,-1,0],-.60)],'NOSE_GEAR_COVER_PRESERVED')
    aft_links.name='NOSE_COVER_FIXED_UPPER_LINKS_PRESERVED';model.static_mesh(aft_links);model.attach(aft_panel,nd)
    # Source nose well forward skin supplies conforming closure leaves. The
    # original aft panel closes the original source hole with an authored
    # compound translation; no extra panel passes through the parked tyres.
    nose_leaves=[]
    for side,sgn in [('left',-1),('right',1)]:
        leaf,_=extract(nose_skin,[([sgn,0,0],0)],'NOSE_WELL_'+side.upper()+'_SOURCE_HATCH')
        edge=leaf.p[np.abs(leaf.p[:,0]-sgn*.62)<1e-5];edge=np.unique(np.round(edge,7),axis=0)
        slope,intercept=np.polyfit(edge[:,2],edge[:,1],1);offset=float(np.min(edge[:,1]-(slope*edge[:,2]+intercept)))-.04
        zmid=float(edge[:,2].mean());lp=np.array([sgn*.62,slope*zmid+intercept+offset,zmid]);axis=normalize(np.array([0,slope,1.]));clear_open=np.zeros(3)
        leaf.rotate(lp,axis,sgn*92).move(clear_open)
        ln=model.pivot('nose_forward_hatch_'+side,lp+clear_open,extras={'hinge_fit':'actual source edge, compound clearing linkage','edge_fit_slope':float(slope),'open_clearing_translation_m':clear_open.tolist()});model.attach(leaf,ln);nose_leaves.append((ln,sgn,axis,lp))
    tt=np.linspace(0,1,65);na=98*staged(tt,.2,.73);da=-8*staged(tt,0,.18)+11*staged(tt,.76,.91)
    nose_tracks=[(nose,'rotation',tt,[quat([1,0,0],a) for a in na]),(nd,'rotation',tt,[quat([1,0,0],a) for a in da]),(nd,'translation',tt,[ndp+[0,.30*up,-.99*fwd] for up,fwd in zip(staged(tt,.91,1),staged(tt,.76,.91))])]
    inspect_tracks=[(nd,'rotation',tt,[quat([1,0,0],-8*smooth(t)) for t in tt])]
    for ln,sgn,axis,lp in nose_leaves:
        ha=sgn*(8*staged(tt,0,.18)-100*staged(tt,.76,.95))
        nose_tracks.append((ln,'rotation',tt,[quat(axis,a) for a in ha]));nose_tracks.append((ln,'translation',tt,[lp.copy() for _ in tt]));inspect_tracks.append((ln,'rotation',tt,[quat(axis,sgn*8*smooth(t)) for t in tt]))
    model.log.append({'component':'nose gear closure fit','change':'preserved original aft panel translates 0.99m forward and 0.30m upward with 3-degree final tilt into original nose opening; added forward well uses original curved skin leaves','no_added_bridge_across_source_wheel_hole':True,'status':'ARTIST_AUTHORED_LINKAGE_PENDING_CURRENT_EXPORT_QA'})
    model.control('gear_nose','Forward-folding nose gear sequence',nose,[1,0,0],98,duration=7,group='Landing gear',role='gear_sequence',ev=evidence('gear',note='Forward-fold principle supported by C130 manual; exact authored travel/linkage not operationally certified.'),tracks=nose_tracks,owns=['gear_door_nose'],states={'rest':'DOWN','deployed':'RETRACTED'})
    model.control('gear_door_nose','Nose gear-cover inspection',nd,[1,0,0],-8,duration=2.2,group='Landing gear',role='gear_door',ev=evidence('gear'),tracks=inspect_tracks,owned_by='gear_nose',enabled_if={'control':'gear_nose','equals':0})
    if gunship:
        add_sensor(model,'eoir_chin',[0,1.15,-13.92])
        sensor=add_sensor(model,'eoir_port',[-1.42,1.18,-5.65])
        model.glb.doc['nodes'][sensor['root']]['rotation']=quat([0,1,0],90)
    model.glb.node('SOCKET_RECEIVER_INTERFACE_UNFITTED',translation=[0,4.55,-9.2],extras={'kind':'GAME_ALIGNMENT_ONLY','physical_receiver':'NOT_AUTHORED_NO_EVIDENCE','validated':False})
    model.glb.doc['nodes'][0]['extras'].update({'model':mid,'configuration':label,'source_hash':INPUT_HASH,'licence':'SOURCE_PROVENANCE_REVIEW_REQUIRED','controls':len(model.controls),'uniform_scene_scale':True,'base_normalization':'r0001 inherited approximate envelope baked into vertices; not photo calibrated','native_unreal':'NOT_RUN','acceptance_report':'../manifest.json'})
    model.glb.doc['asset']['extras']={'unit_dimensions':{'length_m':29.79,'width_m':40.41,'height_m':11.84},'unit_dimensions_provenance':'Inherited approximate r0001 envelope; catalog target differs slightly; photographic acceptance pending'}
    return model

def save_model(model,component=False):
    (OUT/'models').mkdir(exist_ok=True);(OUT/'articulation').mkdir(exist_ok=True)
    dest=OUT/'components'/model.id if component else OUT/'models'
    dest.mkdir(parents=True,exist_ok=True)
    result=model.glb.write(dest/'model.glb' if component else dest/f'{model.id}.glb')
    parked={c['id']:0 for c in model.controls};service=parked.copy();flying=parked.copy()
    for c in model.controls:
        if c.get('role')=='access' and not c.get('owned_by'):service[c['id']]=1
        if c.get('role')=='gear_sequence':flying[c['id']]=1
        if c.get('kind')=='continuous' and c.get('group')=='Propulsion':flying[c['id']]=1
    sidecar={'version':'jcnc.c130-articulation/2.0','revision':'r0003','author':'claude-design','model':model.id,'label':model.label,'file':f'../models/{model.id}.glb','sha256':result['sha256'],'units':'metres','basis':'+X right,+Y up,nose -Z','canonical_rest':'PARKED, gear down; access closed; source covers hanging open; propulsion stopped','controls':model.controls,'sequences':[{'id':'actuate_everything','source':'current control inventory','policy':'concurrent compatible mechanisms; owned_by masters arbitrate; pause/reverse/reset deterministic','cargo':'upper opens before ramp; ramp closes before upper','gear':'covers clear before retraction; covers close after wheels clear'}],'states':{'PARKED':parked,'SERVICE':service,'FLYING':flying},'presets':[{'id':'PARKED','label':'Parked','controls':parked},{'id':'SERVICE','label':'Service','controls':service},{'id':'FLYING','label':'Flying','controls':flying}],'effects':getattr(model,'firing_profiles',[]),'firing_profiles':getattr(model,'firing_profiles',[]),'cameras':[{'id':'hero','position':[-36,20,-35],'target':[0,3,0]},{'id':'port','position':[-38,6,0],'target':[0,3,0]},{'id':'cargo','position':[-8,6,16],'target':[0,2,3]}],'sim_inputs':[],'openings':model.openings,'acceptance':{'structural':'PENDING_CURRENT_EXPORT_QA','photographic':'NOT_ACCEPTED','native_blender':'PENDING','native_unreal':'NOT_RUN','continuous_clearance':'NOT_PROVEN','licensing':'REVIEW_REQUIRED'},'notes':model.log}
    if component:
        sidecar.update(component=True,file='model.glb',canonical_rest='Independent system datum; optics forward -Z; gun visual axis -X',parent_aircraft_dependency=False)
        sidecar['cameras']=[{'id':'hero','position':[-3.1,1.9,3.1],'target':[.1,-.1,0]},{'id':'internal','position':[2.9,1.4,2.1],'target':[.6,-.1,0]}]
    else:
        sidecar['cameras'] += [{'id':'gun30','position':[-5.8,3.1,-9.6],'target':[-2.3,2.5,-7.7]}, {'id':'gun105','position':[-5.5,2.9,5.1],'target':[-2.3,2.2,2.35]}, {'id':'internal30','position':[.6,2.9,-6.3],'target':[-1.1,2.2,-7.7]}, {'id':'internal105','position':[.8,2.9,4.2],'target':[-.8,2.0,2.35]}]
    (dest/'articulation.json' if component else OUT/'articulation'/f'{model.id}.json').write_text(json.dumps(sidecar,indent=2)+'\n')
    return result

def component_inventory(model):
    """Evidence from actual exported vertex/index bytes and canonical transforms."""
    doc=model.glb.doc;buf=model.glb.buf;world={0:np.zeros(3)};rows=[]
    def walk(i,base):
        n=doc['nodes'][i];pos=base+np.array(n.get('translation',[0,0,0]));world[i]=pos
        for c in n.get('children',[]):walk(c,pos)
    walk(0,np.zeros(3))
    for i,n in enumerate(doc['nodes']):
        if 'mesh' not in n:continue
        h=hashlib.sha256();mesh=doc['meshes'][n['mesh']]
        for pr in mesh['primitives']:
            for key,aidx in sorted({**pr['attributes'],'INDICES':pr['indices']}.items()):
                a=doc['accessors'][aidx];v=doc['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)+a.get('byteOffset',0);length=a['count']*DIMS[a['type']]*DTYPE[a['componentType']].itemsize;h.update(key.encode());h.update(bytes(buf[start:start+length]))
        transform={'translation':world[i].tolist(),'rotation':[0,0,0,1],'scale':[1,1,1]};th=hashlib.sha256(json.dumps(transform,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        rows.append({'node':n['name'],'geometry_sha256':h.hexdigest(),'world_rest_transform_sha256':th,'world_rest_transform':transform,'source_node':n.get('extras',{}).get('source_node'),'tags':n.get('extras',{}).get('tags',[])})
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=REPO/'family/r0001/c130-hercules-unified-r0001.glb');parser.add_argument('--only',choices=['c130','ac130','ac130j']);parser.add_argument('--preserve-vertex-records',action='store_true',help='Reproduce the pre-indexed representation without changing authored geometry');args=parser.parse_args()
    data=args.input.read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest!=INPUT_HASH:raise ValueError('claude-design input SHA256 mismatch: '+digest)
    src,images,_=load_source(args.input,canonical=True);common,surfaces=prepare_common(src)
    results=[];inventories={};indexing={}
    configs=json.loads((HERE/'variants.json').read_text())['variants']
    for cfg in configs:
        mid=cfg['id'];label=cfg['label']
        if args.only and mid!=args.only:continue
        model=build_one(mid,label,src,images,common,surfaces,exact_index=not args.preserve_vertex_records);r=save_model(model);results.append(r);inventories[mid]=component_inventory(model);indexing[mid]=model.glb.indexing;print('claude-design BUILT',json.dumps(r),flush=True)
    (OUT/'source'/'exact-indexing-receipts.json').write_text(json.dumps({'operation':'exact_complete_float32_attribute_records','enabled':not args.preserve_vertex_records,'triangle_removal':'none in indexing step; preexisting float32-sliver filter unchanged','models':indexing},indent=2)+'\n')
    (OUT/'source'/'build-receipts.json').write_text(json.dumps({'source_sha256':digest,'source_file':'family/r0001/c130-hercules-unified-r0001.glb','shared_source_meshes':24,'variant_rule':'common master plus interchangeable structural/powerplant/cockpit/mission modules','outputs':results},indent=2)+'\n')
    registry={'version':'jcnc.c130-module-registry/1','revision':'r0003','author':'claude-design','source_sha256':digest,'master':'C130_COMMON_claude-design_r0002','units':'metres','basis':'+X right,+Y up,nose -Z','source_original_meshes':24,'source_preserved_normal_maps':2,'source_ground_alignment_m':GROUND_SHIFT,'variants':configs,'common_parts':[{'id':'fuselage','geometry':'preserved source skin, variant-aware panel/aperture regions'},{'id':'cargo_cabin','geometry':'preserved original interior'},{'id':'landing_gear','mechanism':'vertical tandem main / forward-folding nose'},{'id':'access','mechanism':'staged upper cargo door + lower ramp; lower-sill crew stairs; overhead personnel doors'}]+[{'id':s['id'],'source_triangles':len(s['mesh'].faces),'status':'EXTRACTED_FROM_ORIGINAL_SKIN'} for s in surfaces],'delivery':'self-contained GLB instances generated from one logical source master; full exports duplicate common data for portable use','not_implemented':['native Unreal gameplay controller','photographically accepted exact station drawings','damage catalogue bindings','operational aircraft or weapon physics']}
    (OUT/'articulation'/'component-registry.json').write_text(json.dumps(registry,indent=2)+'\n')
    registry['exported_component_inventory']=inventories
    index={}
    for mid,rows in inventories.items():
        for r in rows:index.setdefault((r['node'],r['geometry_sha256'],r['world_rest_transform_sha256']),[]).append(mid)
    registry['verified_identical_geometry_and_rest']=[{'node':k[0],'geometry_sha256':k[1],'world_rest_transform_sha256':k[2],'variants':v} for k,v in index.items() if len(v)>1]
    registry['incompatibilities']=[{'group':'powerplant','exclusive':['legacy four-blade/nacelle','J six-blade/nacelle']},{'group':'cockpit','exclusive':['legacy analogue insert','J digital displays/HUD']},{'group':'port_forward_panel','exclusive':['transport skin infill','30 mm aperture/mount']},{'group':'port_aft_panel','exclusive':['operating port personnel door','105 mm station']}]
    (OUT/'articulation'/'component-registry.json').write_text(json.dumps(registry,indent=2)+'\n')

if __name__=='__main__':main()
