#!/usr/bin/env python3
"""claude-design / cg47: ONE C130 master with reversible configuration modules.

Preserve the actual r0003 aircraft and systems. Add local replacement skins,
propulsion options and independent mission equipment, never hidden full planes.
"""
from __future__ import annotations
import copy,hashlib,json,math
from pathlib import Path
import numpy as np
import build_family as base
from gltf_core import load_source,extract,boxplanes,box,tube,make_mesh,quat,normalize
from family_glb import import_model,node_mesh,replace_mesh,module,reparent,compact,subset_component
from loadout_components import add_tanker_pod,add_skyhook,add_jato,lathe_z,_mats,ev

HERE=Path(__file__).resolve().parent;OUT=HERE.parent;PARENT=OUT.parent/'r0003'
BASE_HASH='e7075a4097d1842de0b0353cb27e5e294ee3506ee5d0ecdb47e8eeea22e94e93'

def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
def option(id,label,roots=(),controls=(),note=None):
    d={'id':id,'label':label,'module_roots':list(roots),'control_ids':list(controls)}
    if note:d['note']=note
    return d
def slot(id,label,options):return {'id':id,'label':label,'options':options}

def source_controls(m,prefix):return [c['id'] for c in m.controls if c['id'].startswith(prefix)]

def general_blades(c,num,count,mat):
    v=[];f=[];c=np.asarray(c)
    for k in range(count):
        a=2*math.pi*k/count;u=np.array([math.cos(a),math.sin(a),0]);w=np.array([-math.sin(a),math.cos(a),0]);start=len(v)
        for r,width,sweep in [(.28,.16,0),(.65,.23,.03),(1.25,.22,.11),(1.8,.15,.23),(2.01,.04,.31)]:
            p=c+u*r+w*sweep;v.extend([p-w*width/2+[0,0,-.035],p+w*width/2+[0,0,.035]])
        for j in range(4):a=start+j*2;f.extend([(a,a+1,a+3),(a,a+3,a+2)])
    return make_mesh(f'PROP_{num}_NP2000_STYLE_EIGHT_BLADES',v,f,mat,{'geometry_status':'VISUAL_APPROXIMATION','blade_count':8})

def powerplant_and_cockpit(m,src):
    g=m.glb;names=list(g.names)
    j_engine=module(m,'MODULE_J_POWERPLANTS',[n for n in names if n.startswith(('J_AE2100','J_LOWER_INTAKE','J_INTAKE_LIP','J_EXHAUST'))])
    legacy=module(m,'MODULE_LEGACY_NACELLES');lr=[g.doc['nodes'][legacy]['name']];jr=[g.doc['nodes'][j_engine]['name']];nr=lr.copy()
    for num,si in enumerate([2,3,4,5],1):
        c=src[si].center();part,_=extract(src[1],boxplanes([c[0]-.78,3.,-5.79],[c[0]+.78,4.53,-2.72]),f'LEGACY_NACELLE_{num}_ORIGINAL')
        m.static_mesh(part,legacy)
        pivot=g.names['PIVOT_prop_'+str(num)];pc=m.known_pivots[pivot]
        children=list(g.doc['nodes'][pivot]['children']);jprop=module(m,'MODULE_J_PROP_'+str(num),children,parent=pivot)
        old=module(m,'MODULE_LEGACY_PROP_'+str(num),parent=pivot);m.known_pivots[old]=pc
        base.attach_legacy_prop(m,src[si],old,num)
        eight=module(m,'MODULE_NP2000_PROP_'+str(num),parent=pivot);m.known_pivots[eight]=pc
        m.attach(general_blades(c,num,8,m.mat['black']),eight)
        m.attach(tube(f'PROP_{num}_NP2000_SPINNER',c+[0,0,-.35],c+[0,0,.07],.03,m.mat['gray'],radius_end=.29),eight)
        g.doc['nodes'][pivot]['extras']['blade_count']='loadout-dependent: 4, 6 or 8'
        lr.append(g.doc['nodes'][old]['name']);jr.append(g.doc['nodes'][jprop]['name']);nr.append(g.doc['nodes'][eight]['name'])
    j_cockpit=module(m,'MODULE_J_DIGITAL_COCKPIT',[n for n in list(g.names) if n.startswith(('J_COCKPIT','J_MULTIFUNCTION','J_HUD'))])
    analogue=module(m,'MODULE_LEGACY_COCKPIT');oldkit=m.kit;m.kit=analogue;base.add_cockpit(m,False);m.kit=oldkit
    return [slot('propulsion','Propulsion assembly',[
      option('legacy','Legacy four-blade / T56-style',lr),option('j','J six-blade / AE2100-style',jr),
      option('np2000','Legacy eight-blade NP2000-style',nr,note='Blade-count upgrade reference supported; exact blade section and nacelle retrofit remain approximate.')]),
      slot('cockpit','Flight station',[option('analogue','Legacy analogue',[g.doc['nodes'][analogue]['name']]),option('digital','J digital / HUD',[g.doc['nodes'][j_cockpit]['name']])])]

def gun_panels(m,src):
    g=m.glb;rows=[]
    for key,lo,hi,center,radius in [
        ('gun30',[-2.8,1.75,-8.85],[-1.20,3.30,-6.6],[-2.125,2.55,-7.72],.535),
        ('gun105',[-2.8,.99,1.65],[-1.15,3.2,3.45],[-2.022,2.20,2.35],.455)]:
        existing=['PANEL_'+key.upper()+'_SOURCE_SKIN','PIVOT_'+key+'_component']
        if key=='gun105':existing.append('PANEL_AFT_PORT_GUN_STATION_INFILL')
        active=module(m,'MODULE_'+key.upper()+'_INSTALLATION',existing)
        blank=module(m,'MODULE_'+key.upper()+'_TRANSPORT')
        patch,_=extract(src[1],boxplanes(lo,hi),'PANEL_'+key.upper()+'_BLANK_SKIN')
        c=np.asarray(center);radial=[([0,-math.cos(a),-math.sin(a)],-(c[1]*math.cos(a)+c[2]*math.sin(a)+radius)) for a in np.linspace(0,2*math.pi,48,endpoint=False)]
        hp=[([1,0,0],lo[0]-.1),([-1,0,0],-hi[0]-.1)]+radial
        liner,_=extract(src[23],hp,'PANEL_'+key.upper()+'_CLOSED_CABIN_LINER')
        if key=='gun105':
            # Make the actual transport door opening in both common skin and
            # cabin. Move its gunship-specific residual pieces to the gun module.
            para=boxplanes([-2.3,1.,1.83],[-1.43,3.01,2.66])
            for name in ['fuselage','CARGO_CABIN_PRESERVED']:
                removed,remain=extract(node_mesh(g,name),para,name+'_AFT_PORT_FIXED_GUN_FILL')
                if len(removed.faces):m.static_mesh(removed,active)
                replace_mesh(g,name,remain)
            _,patch=extract(patch,para,'PARA_BLOCKER_FROM_BLANK')
            _,liner=extract(liner,para,'PARA_LINER_BLOCKER_FROM_BLANK')
            p0=np.array([-1.98,1.03,2.24]);p=m.pivot('paratroop_left',p0,parent=blank)
            for si in [20,21]:m.attach(src[si].clone('PARATROOP_LEFT_SOURCE_'+str(si)),p)
            t=np.linspace(0,1,49);up=2.*base.staged(t,.15,1);inside=.38*base.staged(t,0,.23);angle=-50*base.staged(t,.4,1)
            m.control('paratroop_left','Left raised personnel door',p,[0,1,0],2.,kind='translation',duration=4.5,group='Personnel access',role='access',tracks=[(p,'translation',t,[p0+[v,u,0] for v,u in zip(inside,up)]),(p,'rotation',t,[quat([0,0,1],a) for a in angle])],ev=base.evidence('door'))
        if len(patch.faces):m.static_mesh(patch,blank)
        if len(liner.faces):m.static_mesh(liner,blank)
        if key=='gun30':rows.append(slot('gun30','Forward port emplacement panel',[
            option('blank','Closed transport skin and liner',[g.doc['nodes'][blank]['name']]),
            option('gun','30 mm panel + internal system',[g.doc['nodes'][active]['name']],source_controls(m,'gun30_'))]))
        else:rows.append(slot('aft_port','Aft port panel / door',[
            option('paratroop','Working transport personnel door',[g.doc['nodes'][blank]['name']],['paratroop_left']),
            option('gun105','105 mm panel + internal system',[g.doc['nodes'][active]['name']],source_controls(m,'gun105_'))]))
    return rows

def fuel_tanks(m):
    g=m.glb;body=node_mesh(g,'fuselage');roots=[]
    for s,side in [(-1,'left'),(1,'right')]:
        patch,body=extract(body,boxplanes([min(s*7.,s*8.4),2.20,-5.11],[max(s*7.,s*8.4),3.70,2.57]),'EXTERNAL_TANK_'+side.upper()+'_SOURCE')
        group=module(m,'MODULE_EXTERNAL_TANK_'+side.upper());m.static_mesh(patch,group)
        x=s*7.70;m.static_mesh(box('TANK_'+side.upper()+'_ATTACHMENT_PYLON',[x-.10,3.54,-1.9],[x+.10,4.43,.1],m.mat['gray']),group)
        roots.append(g.doc['nodes'][group]['name'])
    replace_mesh(g,'fuselage',body)
    return slot('external_tanks','Underwing fuel tanks',[option('none','Removed'),option('both','Paired source fuel tanks',roots)])

def nose_and_receiver(m):
    g=m.glb;mat=_mats(m);body=node_mesh(g,'fuselage')
    nose,body=extract(body,[([0,0,-1],13.65)],'NOSE_STANDARD_SOURCE')
    ordinary=module(m,'MODULE_STANDARD_NOSE');m.static_mesh(nose,ordinary)
    talon=module(m,'MODULE_TALON_NOSE');modified=nose.clone('HISTORICAL_TALON_DROOPED_RADOME')
    weight=np.clip((-modified.p[:,2]-13.65)/(14.9-13.65),0,1)
    modified.attrs['POSITION'][:,1]-=.25*weight**1.4;modified.attrs['POSITION'][:,2]-=.42*weight**1.2
    modified.attrs['NORMAL']=make_mesh('normals',modified.p,modified.faces).attrs['NORMAL']
    modified.material=mat['radome'];m.static_mesh(modified,talon)
    # Use a real source-skin hatch as the receiving closure; no raised slab.
    hatch,body=extract(body,boxplanes([-.28,4.16,-12.35],[.28,5.5,-11.40]),'RECEIVER_DORSAL_HATCH_SOURCE')
    if not len(hatch.faces):raise ValueError('Receiver patch did not intersect source skin')
    cover=module(m,'MODULE_NO_RECEIVER');m.static_mesh(hatch.clone('RECEIVER_BLANK_CONTINUOUS_SKIN'),cover)
    receiver=module(m,'MODULE_BOOM_RECEIVER');center=hatch.center();h= m.pivot('receiver_hatch',center,parent=receiver)
    m.attach(hatch,h)
    floor=hatch.clone('RECEIVER_RECESSED_WELL_FLOOR').move([0,-.22,0]);floor.material=mat['dark'];m.static_mesh(floor,receiver)
    pp,ix=np.unique(np.round(hatch.p,6),axis=0,return_inverse=True);ff=ix[hatch.faces]
    edges=np.concatenate([ff[:,[0,1]],ff[:,[1,2]],ff[:,[2,0]]]);edges.sort(axis=1);ee,cc=np.unique(edges,axis=0,return_counts=True);boundary=ee[cc==1]
    verts=[];faces=[]
    for aa,bb in boundary:
        a,b=pp[aa],pp[bb];i=len(verts);verts.extend([a,b,b-[0,.22,0],a-[0,.22,0]])
        face=[i,i+1,i+2];normal=np.cross(b-a,-np.array([0,.22,0]))
        if np.dot(normal,center-(a+b)*.5)<0:faces.extend([(i,i+2,i+1),(i,i+3,i+2)])
        else:faces.extend([(i,i+1,i+2),(i,i+2,i+3)])
    m.static_mesh(make_mesh('RECEIVER_RECESSED_WELL_REVEAL',verts,faces,mat['dark']),receiver)
    m.static_mesh(tube('RECEIVER_CONTACT_REPRESENTATION',center+[0,-.20,0],center+[0,-.16,0],.105,mat['metal'],segments=32),receiver)
    g.node('SOCKET_BOOM_RECEIVER_CONTACT',parent=receiver,translation=(center+[0,-.15,0]).tolist(),extras={'kind':'GAME_ALIGNMENT','real_contact_geometry':'NOT_CERTIFIED'})
    # Public exact movement evidence is unresolved; explicit sliding inspection
    # animation is an authored placeholder, unlike the verified donor skin fit.
    t=np.linspace(0,1,49);q=base.smooth(t)
    m.control('receiver_hatch','Receiver cover inspection',h,[0,0,1],1.05,kind='translation',duration=3.0,group='Aerial refuelling',tracks=[(h,'translation',t,[center+[0,-.055*math.sin(math.pi*v),1.05*v] for v in q])],ev=ev('talon',note='Boom-receiving role documented. Cover travel is an explicit illustrative sliding inspection motion; exact hinge/slide mechanism is not accepted.'),states={'rest':'Cover shut','deployed':'Receptacle visible — illustrative cover travel'})
    replace_mesh(g,'fuselage',body)
    return [slot('nose','Nose shell',[option('standard','Standard source nose',[g.doc['nodes'][ordinary]['name']]),option('talon','Historical Talon-style radome',[g.doc['nodes'][talon]['name']],note='Purpose-built nose conversion visual approximation; exact contours not accepted.')]),
            slot('receiver','In-flight fuel receiver',[option('none','No receiver / continuous skin',[g.doc['nodes'][cover]['name']]),option('boom','Dorsal boom receptacle',[g.doc['nodes'][receiver]['name']],['receiver_hatch'],note='Separate from tanker delivery pods; cover motion is illustrative.')])]

def catalogue(m,src):
    g=m.glb;slots=powerplant_and_cockpit(m,src)+gun_panels(m,src)+[fuel_tanks(m)]+nose_and_receiver(m)
    chin=module(m,'MODULE_EOIR_CHIN',['PIVOT_eoir_chin_component']);port=module(m,'MODULE_EOIR_PORT',['PIVOT_eoir_port_component'])
    cn=g.doc['nodes'][chin]['name'];pn=g.doc['nodes'][port]['name']
    slots.append(slot('sensors','EO/IR sensor installation',[
      option('none','No external EO/IR'),option('chin','Chin turret',[cn],source_controls(m,'eoir_chin')),
      option('dual','Chin and port turrets',[cn,pn],source_controls(m,'eoir_'),note='Representative MX-20-family visual systems; exact fit/block remains approximate.')]))
    components=[]
    for side,s in [('left',-1),('right',1)]:
        d=add_tanker_pod(m,side,[s*13.35,3.35,-.90]);components.append(('hose-drogue-'+side,d['component_root']))
        slots.append(slot(side+'_tanker',side.title()+' outboard refuelling station',[
          option('none','Empty station'),option('high','Pod + high-speed basket',[d['module'],d['basket_high']],d['controls'],note='Basket type is a visual approximation, not calibrated aerodynamic geometry.'),
          option('low','Pod + low-speed basket',[d['module'],d['basket_low']],d['controls'],note='Baskets are separately swappable; authored size/ribs need exact type acceptance.')]))
    d=add_skyhook(m,[0,2.9,-14.85]);components.append(('fulton-yoke',d['component_root']))
    slots.append(slot('skyhook','Historical recovery equipment',[option('none','No Skyhook'),option('fulton','Fulton yoke + fending lines',[d['module'],d['guards']],d['controls'])]))
    d=add_jato(m);components.append(('jato-kit',d['component_root']))
    slots.append(slot('jato','Historical takeoff-assist kit',[option('none','No JATO bottles'),option('eight','Eight-bottle visual JATO kit',[d['module']],d['controls'],note='Historical legacy-airframe game option; not the complete ski-equipped LC-130 configuration.')]))
    blank={'propulsion':'legacy','cockpit':'analogue','gun30':'blank','aft_port':'paratroop','external_tanks':'both','nose':'standard','receiver':'none','sensors':'none','left_tanker':'none','right_tanker':'none','skyhook':'none','jato':'none'}
    def preset(id,label,status='REFERENCE_GUIDED',note='',**values):return {'id':id,'label':label,'status':status,'values':{**blank,**values},'note':note}
    presets=[preset('transport_h','C-130H transport candidate'),preset('transport_j','C-130J transport candidate',propulsion='j',cockpit='digital'),
      preset('gunship_w','AC-130W-style · circa 2021',status='HISTORICAL',gun30='gun',aft_port='gun105',sensors='dual',receiver='boom'),
      preset('gunship_j','AC-130J-style · circa 2021',status='HISTORICAL',propulsion='j',cockpit='digital',gun30='gun',aft_port='gun105',sensors='dual',receiver='boom'),
      preset('tanker_j','KC-130J-style tanker candidate',propulsion='j',cockpit='digital',left_tanker='high',right_tanker='high'),
      preset('recovery_e','Historical Combat Talon / Fulton candidate',status='HISTORICAL',nose='talon',receiver='boom',skyhook='fulton',note='A dated recovery equipment study; exact MC-130E avionics and interior fit remain incomplete.'),
      preset('legacy_jato','Historical legacy JATO equipment study',status='HISTORICAL',jato='eight',note='Equipment study only; LC-130 skis and its full conversion are not included.'),
      preset('np2000_h','C-130H NP2000-style upgrade candidate',propulsion='np2000')]
    constraints=[
      {'id':'j-flightstation','when':{'propulsion':'j'},'requires':{'cockpit':['digital'],'skyhook':['none'],'jato':['none']},'message':'J propulsion pairs with the J flight station. Skyhook and this JATO kit are historical legacy-airframe options.'},
      {'id':'legacy-flightstation','when':{'propulsion':'legacy'},'requires':{'cockpit':['analogue']},'message':'The legacy reference preset uses the analogue flight station.'},
      {'id':'np2000-flightstation','when':{'propulsion':'np2000'},'requires':{'cockpit':['analogue']},'message':'The modeled NP2000 retrofit retains the legacy flight station.'},
      {'id':'fulton-nose','when':{'skyhook':'fulton'},'requires':{'nose':['talon'],'propulsion':['legacy'],'gun30':['blank'],'aft_port':['paratroop'],'jato':['none']},'message':'Historical Fulton preset requires its Talon-style nose and legacy recovery configuration. Other combinations are custom JCNC.'},
      {'id':'jato-historical','when':{'jato':'eight'},'requires':{'propulsion':['legacy'],'gun30':['blank'],'aft_port':['paratroop'],'skyhook':['none']},'message':'This visual JATO fit represents historical legacy aircraft; combined gunship/Fulton fits are not source-verified.'}]
    return {'version':1,'revision':'r0004','author':'claude-design / cg47','family_id':'c130-family','default_preset':'transport_h','slots':slots,'presets':presets,'constraints':constraints,
            'acceptance':'DRAFT_CONFIGURABLE_FAMILY','notes':['One common fuselage, cabin, flight surfaces and landing gear. Configuration changes swap local modules only.','Preset names describe reference-guided candidates, not accepted real aircraft conversions.','Unmatched selections are custom JCNC. Arbitrary combinations do not establish real compatibility.']},components

def main():
    original=HERE/'inputs/r0003-ac130j.glb';art=HERE/'inputs/r0003-ac130j-articulation.json'
    if not original.exists():original.write_bytes((PARENT/'models/ac130j.glb').read_bytes())
    if not art.exists():art.write_bytes((PARENT/'articulation/ac130j.json').read_bytes())
    assert hashlib.sha256(original.read_bytes()).hexdigest()==BASE_HASH
    m,old=import_model(original,art);g=m.glb
    src,images,sha=load_source(HERE/'inputs/c130-hercules-unified-r0001.glb',canonical=True);assert sha==base.INPUT_HASH
    cat,components=catalogue(m,src)
    from ramp_repair import repair_ramp
    repair=repair_ramp(m);dump(OUT/'qa/ramp-master-repair.json',repair)
    g.doc['asset']['generator']='claude-design C130 single modular master r0004'
    g.doc['nodes'][0]['extras'].update(model='c130-family',revision='r0004',configuration='Loadouts catalogue',acceptance='DRAFT_CONFIGURABLE_FAMILY',loadout_catalog='../loadouts/catalog.json',shared_airframe_instances=1)
    g.doc['nodes'][m.kit]['name']='MISSION_MODULES';g.names['MISSION_MODULES']=m.kit;g.names.pop('MISSION_KIT_AC130J',None)
    default=next(p for p in cat['presets'] if p['id']==cat['default_preset'])['values']
    active=set()
    for s in cat['slots']:
        for op in s['options']:
            if op['id']==default[s['id']]:active.update(op['module_roots'])
    for n in g.doc['nodes']:
        if n.get('extras',{}).get('loadout_module_root'):
            enabled=n['name']in active;n['scale']=[1,1,1] if enabled else [0,0,0];n['extras']['default_enabled']=enabled
    compact(g);base.OUT=OUT;receipt=base.save_model(m);dump(OUT/'loadouts/catalog.json',cat)
    ap=OUT/'articulation/c130-family.json';a=json.loads(ap.read_text());a.update(revision='r0004',designation='C-130 MODULAR FAMILY',loadout_catalog='../loadouts/catalog.json',default_loadout=cat['default_preset'])
    a['cameras'] += [{'id':'tanker','position':[-23,9,18],'target':[-13.35,3.0,5.0]},{'id':'skyhook','position':[-13,8,-26],'target':[0,3,-15]},{'id':'jato','position':[-9,6,8],'target':[-1.9,2.4,3.7]},{'id':'receiver','position':[-3,8,-14],'target':[0,4.5,-11.85]}]
    a['acceptance'].update(structural='PENDING_CURRENT_EXPORT_QA',photographic='NOT_ACCEPTED',native_blender='PENDING',native_unreal='NOT_RUN')
    dump(ap,a)
    # Canonical component exports have no aircraft meshes, libraries or images
    # outside their own embedded data dependency graph.
    comp=[]
    for cid,root in components:
        rec,controls=subset_component(m,root,OUT/'components'/cid/'model.glb',m.controls)
        sidecar={'version':'jcnc.c130-articulation/2.0','revision':'r0004','author':'claude-design','component':True,'model':cid,'label':cid.replace('-',' ').title(),'file':'model.glb','sha256':rec['sha256'],'controls':controls,'sequences':[],'states':{},'presets':[],'effects':[],'cameras':[],'sim_inputs':[],'units':'metres','basis':'+X right,+Y up,nose -Z','acceptance':{'photographic':'NOT_ACCEPTED','native_unreal':'NOT_RUN'}}
        dump(OUT/'components'/cid/'articulation.json',sidecar);comp.append({'id':cid,'root':root,**rec})
    dump(OUT/'qa/build-loadout-receipt.json',{'author':'claude-design','revision':'r0004','parent_sha256':BASE_HASH,'shared_airframe_instances':1,'model':receipt,'components':comp,'slots':len(cat['slots']),'options':sum(len(s['options'])for s in cat['slots']),'presets':len(cat['presets'])})
    print('claude-design BUILT',json.dumps(receipt),flush=True)

if __name__=='__main__':main()
