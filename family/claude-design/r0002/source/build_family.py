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
REPO=HERE.parents[3]
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
        n=normalize(np.asarray(n,float));p=mesh.p[np.abs(mesh.p@n-d)<1e-5]
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
    def __init__(self,mid,label,images):
        self.id=mid;self.label=label;self.glb=GLB(label);self.controls=[];self.openings=[];self.log=[];self.known_pivots={0:np.zeros(3)}
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
        axis=np.asarray(axis,float);times=np.linspace(0,1,33);rest=self.glb.doc['nodes'][pivot].get('translation',[0,0,0]);q=smooth(times)
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

def add_sensor(model,cid,center):
    mat=model.mat;c=np.asarray(center,float)
    p=model.pivot(cid+'_yaw',c,parent=model.kit,extras={'tags':['level 1'],'component_type':'visual_eoir','reference':REF['w_photo']})
    model.attach(sphere(cid+'_AZIMUTH_SHELL',c,[.3,.26,.3],mat['gray']),p)
    q=model.pivot(cid+'_pitch',c+[0,-.06,0],parent=p,extras={'tags':['level 1']})
    model.attach(sphere(cid+'_OPTICAL_GIMBAL',c+[0,-.09,0],[.235,.22,.235],mat['dark']),q)
    for i,dx in enumerate([-.08,.08]):model.attach(tube(cid+f'_LENS_{i+1}',c+[dx,-.1,-.23],c+[dx,-.1,-.255],.065,mat['sensor'],segments=20),q)
    model.control(cid+'_yaw',cid.replace('_',' ').title()+' azimuth',p,[0,1,0],90,group='Mission sensors',ev=evidence('w_photo',note='Two sensors supported; exact J second-sensor station and all gimbal limits are visual approximations.'))
    model.control(cid+'_pitch',cid.replace('_',' ').title()+' elevation',q,[1,0,0],45,group='Mission sensors',ev=evidence('w_photo'))

def add_gun(model,cid,center,large=False):
    """Visual mount only: no operational bore, ammunition, firing or targeting model."""
    c=np.asarray(center,float);mat=model.mat;length=1.16 if large else 1.08;radius=.105 if large else .052
    parent=model.pivot(cid+'_yaw',c,parent=model.kit,extras={'tags':['level 1'],'component_type':'visual_gun_mount','operational_model':False})
    model.attach(box(cid+'_VISUAL_CRADLE',c+[-.14,-.22,-.24],c+[.5,.22,.24],mat['metal']),parent)
    pitch=model.pivot(cid+'_pitch',c,parent=parent,extras={'tags':['level 1']})
    model.attach(tube(cid+'_TRUNNION',c+[0,0,-.27],c+[0,0,.27],.17 if large else .12,mat['metal']),pitch)
    recoil=model.pivot(cid+'_recoil',c,parent=pitch,extras={'tags':['level 1']})
    model.attach(cylinder_shell(cid+'_BARREL_SHELL',c+[.24,0,0],c+[-length,0,0],radius,.018 if large else .012,mat['metal']),recoil)
    model.attach(tube(cid+'_DARK_MUZZLE_DEPTH',c+[-length+.18,0,0],c+[-length+.175,0,0],radius*.72,mat['dark']),recoil)
    model.attach(tube(cid+'_SLEEVE',c+[.38,0,0],c+[-.32,0,0],radius*1.65,mat['gray']),recoil)
    if large:model.attach(tube(cid+'_VISUAL_RECUPERATOR',c+[.2,.2,0],c+[-.65,.2,0],.075,mat['metal']),pitch)
    model.control(cid+'_yaw',('105 mm' if large else '30 mm')+' mount sweep',parent,[0,1,0],7,group='Mission equipment',ev=evidence('w_photo',note='Visual-only authored mount travel; no operational traverse/elevation specifications.'))
    model.control(cid+'_pitch',('105 mm' if large else '30 mm')+' mount elevation',pitch,[0,0,1],12,group='Mission equipment',ev=evidence('w_photo'))
    model.control(cid+'_recoil',('105 mm' if large else '30 mm')+' visual recoil',recoil,[1,0,0],.12 if large else .07,kind='translation',duration=1.4,group='Mission equipment',ev=evidence(note='Authored reversible presentation stroke, not operational gun mechanics.'))
    model.glb.node(cid+'_MUZZLE_VISUAL_SOCKET',parent=recoil,translation=[-length,0,0],extras={'tags':['level 1'],'kind':'VISUAL_EFFECT_ALIGNMENT','operational_model':False})

def build_one(mid,label,src,images,common,surfaces):
    model=Model(mid,label,images);mat=model.mat;body=common.clone();interior=src[23].clone('CARGO_CABIN_PRESERVED');j=mid=='ac130j';gunship=mid!='c130'
    # Separate legacy/J powerplant modules rather than swapping prop blades alone.
    if j:
        for num,si in enumerate([2,3,4,5],1):
            c=src[si].center();planes=boxplanes([c[0]-.78,3.0,-5.79],[c[0]+.78,4.53,-2.72]);removed,body=extract(body,planes,f'REMOVED_LEGACY_NACELLE_{num}')
            model.static_mesh(nacelle(f'J_AE2100_STYLE_NACELLE_{num}',c,mat['gray']),model.kit)
            model.static_mesh(box(f'J_LOWER_INTAKE_DARK_{num}',[c[0]-.27,3.28,-6.07],[c[0]+.27,3.54,-5.95],mat['dark']),model.kit)
            model.static_mesh(tube(f'J_EXHAUST_{num}',[c[0],3.85,-2.75],[c[0],3.9,-2.35],.21,mat['metal'],cap=False),model.kit)
            model.log.append({'component':f'J nacelle {num}','replaced_source_triangles':len(removed.faces),'status':'PHOTO_GUIDED_APPROXIMATION','reference':REF['j_nacelle']})
    # Port fuselage mission regions use the retained skin; apertures remove both
    # outer skin and the actual cabin wall. Solid transport infills are the same source.
    for key,lo,hi,center,large in [
        ('gun30',[-2.8,1.75,-8.85],[-1.20,3.30,-6.6],[-2.00,2.55,-7.72],False),
        ('gun105',[-2.8,.99,1.65],[-1.15,3.2,3.45],[-1.93,2.20,2.35],True),
    ]:
        patch,body=extract(body,boxplanes(lo,hi),'PANEL_'+key.upper()+'_SOURCE_SKIN')
        if not gunship:model.static_mesh(patch)
        else:
            c=np.asarray(center);holelo=np.array([lo[0],c[1]-.42,c[2]-.43]);holehi=np.array([hi[0],c[1]+.42,c[2]+.43])
            hole,patch=extract(patch,boxplanes(holelo,holehi),'REMOVED_'+key+'_APERTURE')
            _,interior=extract(interior,boxplanes(holelo+[-.1,0,0],holehi+[.1,0,0]),'REMOVED_'+key+'_CABIN_WALL')
            model.static_mesh(patch,model.kit)
            # Aft gun station replaces the port paratroop door module, so no
            # moving door is hidden behind the mounted gun.
            if key=='gun105':
                door=src[20].clone('PANEL_AFT_PORT_GUN_STATION_INFILL');_,door=extract(door,boxplanes(holelo,holehi),'REMOVED_AFT_DOOR_GUN_PORT');model.static_mesh(door,model.kit)
            receiver=box('BAY_'+key+'_RECEIVING_VOLUME',[c[0]+.03,c[1]-.43,c[2]-.44],[c[0]+.92,c[1]+.43,c[2]+.44],mat['dark'],omit=['left'])
            model.static_mesh(receiver,model.kit)
            model.opening(key,'PANEL_'+key.upper()+'_SOURCE_SKIN',receiver.name,None,.89,'Real skin/cabin-wall aperture; enclosed illustrative gun-mount recess. Source port aft door module replaced on gunships.')
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
    # Main and nose wells are actual bounded volumes, not flat dark polygons.
    for side,s in [('left',-1),('right',1)]:
        lo=[min(s*1.25,s*2.4),.35,-3.40];hi=[max(s*1.25,s*2.4),2.95,-.18]
        _,body=extract(body,boxplanes(lo,hi),'REMOVED_'+side+'_WELL_SKIN')
        model.static_mesh(box('GEAR_WELL_'+side.upper(),[lo[0],.91,lo[2]],[hi[0],2.96,hi[2]],mat['dark'],omit=['bottom']))
    _,body=extract(body,boxplanes([-.62,.1,-13.65],[.62,2.40,-10.95]),'REMOVED_NOSE_WELL_SKIN')
    model.static_mesh(box('GEAR_WELL_NOSE',[-.64,1.48,-13.7],[.64,2.44,-10.9],mat['dark'],omit=['bottom']))
    model.static_mesh(body);model.static_mesh(interior)
    # Glass is a separate replaceable material; preserved normal maps/UVs remain.
    windows=src[0].clone('COCKPIT_WINDOWS');windows.material=mat['glass'];model.static_mesh(windows)
    add_cockpit(model,j)
    # Every recovered flight surface has its real extracted skin and an actual clip.
    for s in surfaces:
        if not len(s['mesh'].faces):model.log.append({'component':s['id'],'status':'UNRECOVERED_EMPTY_PATCH'});continue
        p=model.pivot(s['id'],s['pivot']);model.attach(s['mesh'],p)
        for cap in cap_for_planes(s['mesh'],s['planes'],s['id'],mat['gray']):model.attach(cap,p)
        model.control(s['id'],s['label'],p,s['axis'],s['angle'],duration=3.2,group=s['group'],ev=evidence('j_flaps',note='Surface skin extracted from source; hinge locations inferred from source shape/photo. Full aerodynamic limits not claimed.'))
    # Propellers: correct hub-centered parent pivots; legacy meshes remain intact.
    for num,si in enumerate([2,3,4,5],1):
        c=src[si].center();c[2]=(-6.26 if j else c[2]);p=model.pivot(f'prop_{num}',c,extras={'tags':['level 1'],'component_type':'propeller','blade_count':6 if j else 4})
        if j:
            model.attach(six_blades(c,num,mat['black']),p);model.attach(tube(f'PROP_{num}_J_SPINNER',c+[0,0,-.45],c+[0,0,.05],.05,mat['gray'],radius_end=.29),p)
        else:model.attach(src[si].clone(f'PROP_{num}_LEGACY_SOURCE'),p)
        model.control(f'prop_{num}',f'Propeller {num}',p,[0,0,1],360,kind='continuous',duration=1.4,group='Propulsion',ev=evidence('j_nacelle' if j else 'w_photo'))
    # Cargo source-rest reconstruction uses the baked source matrices, not a
    # generic clamshell: upper leaf folds inward, lower ramp lowers separately.
    ramp_p=np.array(src[11].extras['reconstructed_source_pivot']);upper_p=np.array(src[15].extras['reconstructed_source_pivot'])
    ramp=model.pivot('cargo_ramp',ramp_p);upper=model.pivot('cargo_upper_door',upper_p)
    model.attach(src[11].clone('CARGO_LOWER_RAMP_PRESERVED'),ramp);model.attach(src[22].clone('CARGO_RAMP_INTERIOR_PRESERVED'),ramp);model.attach(src[15].clone('CARGO_UPPER_DOOR_PRESERVED'),upper)
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
            wc=src[si].center();wheel=model.pivot(f'wheel_{side}_{n}',wc,parent=gear);model.attach(src[si].clone(f'WHEEL_{side.upper()}_{n}_PRESERVED'),wheel)
            model.control(f'wheel_{side}_{n}',f'{side.title()} wheel {n}',wheel,[1,0,0],360,kind='continuous',duration=2.4,group='Wheels',ev=evidence('gear'))
            model.attach(tube(f'MAIN_STRUT_{side}_{n}',wc+[0,.32,0],wc+[0,1.28,0],.065,mat['metal']),gear)
        dp=np.array([sgn*2.44,1.44,-1.78]);door=model.pivot('gear_door_'+side,dp);model.attach(src[cover].clone('MAIN_GEAR_COVER_'+side.upper()+'_PRESERVED'),door)
        tt=np.linspace(0,1,65);lift=1.43*staged(tt,.18,.72);dangle=sgn*(18*staged(tt,0,.18)-145*staged(tt,.74,1))
        model.control('gear_'+side,side.title()+' main gear sequence',gear,[0,1,0],1.43,kind='translation',duration=7,group='Landing gear',role='gear_sequence',ev=evidence('gear',note='Vertical main-gear principal motion supported; travel and cover linkage are authored pending clearance/photo validation.'),tracks=[(gear,'translation',tt,[gp+[0,h,0] for h in lift]),(door,'rotation',tt,[quat([0,0,1],a) for a in dangle])],owns=['gear_door_'+side],states={'rest':'DOWN: covers hanging open','deployed':'RETRACTED: wheels inside wells and covers shut'})
        model.control('gear_door_'+side,side.title()+' gear-cover inspection',door,[0,0,1],sgn*18,duration=2.2,group='Landing gear',role='gear_door',ev=evidence('gear'),owned_by='gear_'+side,enabled_if={'control':'gear_'+side,'equals':0})
    ngp=np.array([0,1.60,-12.02]);nose=model.pivot('gear_nose',ngp);model.attach(src[16].clone('NOSE_GEAR_STRUT_PRESERVED'),nose);nw=src[17].center();wheel=model.pivot('wheel_nose',nw,parent=nose);model.attach(src[17].clone('NOSE_WHEELS_PRESERVED'),wheel)
    model.control('wheel_nose','Nose wheels',wheel,[1,0,0],360,kind='continuous',duration=2.4,group='Wheels',ev=evidence('gear'))
    ndp=np.array([0,1.56,-9.92]);nd=model.pivot('gear_door_nose',ndp);model.attach(src[6].clone('NOSE_GEAR_COVER_PRESERVED'),nd)
    tt=np.linspace(0,1,65);na=98*staged(tt,.2,.73);da=-8*staged(tt,0,.18)+47*staged(tt,.76,1)
    model.control('gear_nose','Forward-folding nose gear sequence',nose,[1,0,0],98,duration=7,group='Landing gear',role='gear_sequence',ev=evidence('gear',note='Forward-fold principle supported by C130 manual; exact authored travel/linkage not operationally certified.'),tracks=[(nose,'rotation',tt,[quat([1,0,0],a) for a in na]),(nd,'rotation',tt,[quat([1,0,0],a) for a in da])],owns=['gear_door_nose'],states={'rest':'DOWN','deployed':'RETRACTED'})
    model.control('gear_door_nose','Nose gear-cover inspection',nd,[1,0,0],-8,duration=2.2,group='Landing gear',role='gear_door',ev=evidence('gear'),owned_by='gear_nose',enabled_if={'control':'gear_nose','equals':0})
    if gunship:
        add_sensor(model,'eoir_chin',[0,1.15,-13.92]);add_sensor(model,'eoir_port',[-1.42,1.18,-5.65])
    # A neutral independent replaceable identity patch; no baked faction identity.
    model.static_mesh(box('PATCH_houseTint_PORT',[-2.025,2.65,-5.0],[-2.015,3.05,-4.4],mat['houseTint']))
    model.glb.node('SOCKET_RECEIVER_INTERFACE_UNFITTED',translation=[0,4.55,-9.2],extras={'kind':'GAME_ALIGNMENT_ONLY','physical_receiver':'NOT_AUTHORED_NO_EVIDENCE','validated':False})
    model.glb.doc['nodes'][0]['extras'].update({'model':mid,'configuration':label,'source_hash':INPUT_HASH,'licence':'SOURCE_PROVENANCE_REVIEW_REQUIRED','controls':len(model.controls),'uniform_scene_scale':True,'base_normalization':'r0001 inherited approximate envelope baked into vertices; not photo calibrated'})
    return model

def save_model(model):
    (OUT/'models').mkdir(exist_ok=True);(OUT/'articulation').mkdir(exist_ok=True)
    result=model.glb.write(OUT/'models'/f'{model.id}.glb')
    parked={c['id']:0 for c in model.controls};service=parked.copy();flying=parked.copy()
    for c in model.controls:
        if c.get('role')=='access' and not c.get('owned_by'):service[c['id']]=1
        if c.get('role')=='gear_sequence':flying[c['id']]=1
    sidecar={'version':'jcnc.c130-articulation/2.0','revision':'r0002','author':'claude-design','model':model.id,'label':model.label,'file':f'../models/{model.id}.glb','sha256':result['sha256'],'units':'metres','basis':'+X right,+Y up,nose -Z','canonical_rest':'PARKED, gear down; access closed; source covers hanging open; propulsion stopped','controls':model.controls,'sequences':[{'id':'actuate_everything','source':'current control inventory','policy':'concurrent compatible mechanisms; owned_by masters arbitrate; pause/reverse/reset deterministic','cargo':'upper opens before ramp; ramp closes before upper','gear':'covers clear before retraction; covers close after wheels clear'}],'states':{'PARKED':parked,'SERVICE':service,'FLYING':flying},'presets':[{'id':'PARKED','label':'Parked','controls':parked},{'id':'SERVICE','label':'Service','controls':service},{'id':'FLYING','label':'Flying','controls':flying}],'effects':[],'cameras':[{'id':'hero','position':[-36,20,-35],'target':[0,3,0]},{'id':'port','position':[-38,6,0],'target':[0,3,0]},{'id':'cargo','position':[-8,6,16],'target':[0,2,3]}],'sim_inputs':[],'openings':model.openings,'acceptance':{'structural':'PENDING_CURRENT_EXPORT_QA','photographic':'NOT_ACCEPTED','native_blender':'PENDING','native_unreal':'NOT_RUN','continuous_clearance':'NOT_PROVEN','licensing':'REVIEW_REQUIRED'},'notes':model.log}
    (OUT/'articulation'/f'{model.id}.json').write_text(json.dumps(sidecar,indent=2)+'\n')
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,default=REPO/'family/r0001/c130-hercules-unified-r0001.glb');parser.add_argument('--only',choices=['c130','ac130','ac130j']);args=parser.parse_args()
    data=args.input.read_bytes();digest=hashlib.sha256(data).hexdigest()
    if digest!=INPUT_HASH:raise ValueError('claude-design input SHA256 mismatch: '+digest)
    src,images,_=load_source(args.input,canonical=True);common,surfaces=prepare_common(src)
    results=[]
    for mid,label in [('c130','C-130H legacy Hercules candidate'),('ac130','AC-130W Stinger II — circa 2021 visual candidate'),('ac130j','AC-130J Ghostrider — J-family visual candidate')]:
        if args.only and mid!=args.only:continue
        model=build_one(mid,label,src,images,common,surfaces);r=save_model(model);results.append(r);print('claude-design BUILT',json.dumps(r),flush=True)
    (OUT/'source'/'build-receipts.json').write_text(json.dumps({'source_sha256':digest,'source_file':'family/r0001/c130-hercules-unified-r0001.glb','shared_source_meshes':24,'variant_rule':'common master plus interchangeable structural/powerplant/cockpit/mission modules','outputs':results},indent=2)+'\n')

if __name__=='__main__':main()
