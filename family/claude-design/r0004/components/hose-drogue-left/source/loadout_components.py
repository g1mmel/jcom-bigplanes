"""claude-design / cg47: independent visible C-130 mission equipment.

Public-reference-guided game representations. All local dimensions, deployment
paths, pivots and effect timing are authored approximations. Flexible hose and
fabric morphs visualize payout/unfolding; concealed machinery is not simulated.
"""
from __future__ import annotations
import math
import numpy as np
from gltf_core import box,tube,sphere,make_mesh,normalize,quat
from family_glb import module
from gun_components import path_tube,flash_mesh,smoke_mesh,materials as gun_materials

REFS={
 'tanker':'https://www.navair.navy.mil/product/CKC-130-Hercules-Super-Hercules',
 'drogue':'https://www.dvidshub.net/image/8289439/',
 'pod':'https://www.dvidshub.net/image/7758343/',
 'baskets':'https://www.dvidshub.net/image/8942759/',
 'skyhook':'https://www.govinfo.gov/content/pkg/GOVPUB-D301-PURL-LPS20515/pdf/GOVPUB-D301-PURL-LPS20515.pdf',
 'talon':'https://www.hurlburt.af.mil/About-Us/Fact-Sheets/Fact-Sheets/Article/495225/mc-130e-combat-talon-i/',
 'jato':'https://www.dvidshub.net/image/7304591/',
}

def ev(*keys,note='Visible arrangement is reference guided; exact geometry, hinge travel and timing are illustrative game presentation.'):
    return {'status':'REFERENCE_GUIDED_ARTIST_AUTHORED','sources':[REFS[k] for k in keys],'limitations':note}

def _mats(m):
    if hasattr(m,'_loadout_mats'):return m._loadout_mats
    spec={
      'paint':('MISSION_EQUIPMENT_GREY',[.48,.52,.53,1],.15,.58),
      'metal':('MISSION_EXPOSED_METAL',[.40,.43,.45,1],.8,.3),
      'rubber':('REFUEL_HOSE_BLACK',[.017,.022,.025,1],.02,.87),
      'fabric':('DROGUE_WOVEN_OFFWHITE',[.78,.77,.69,1],0,.94),
      'mark':('HOSE_DISTANCE_BAND',[.79,.77,.65,1],0,.75),
      'radome':('HISTORICAL_TALON_RADOME',[.045,.052,.06,1],.05,.68),
      'bottle':('JATO_DULL_BLUE_BODY',[.17,.25,.28,1],.2,.66),
      'dark':('MISSION_RECESS',[.008,.011,.013,1],.05,.98),
    }
    out={key:m.glb.material(*args,double=False) for key,args in spec.items()}
    m.glb.doc['materials'][out['fabric']]['doubleSided']=True
    m._loadout_mats=out;return out

def lathe_z(name,center,profile,material,seg=48,cap=False):
    c=np.asarray(center,float);v=[];f=[]
    for z,r in profile:
        for a in np.linspace(0,2*math.pi,seg,endpoint=False):v.append(c+[r*math.cos(a),r*math.sin(a),z])
    for k in range(len(profile)-1):
        for j in range(seg):a=k*seg+j;b=k*seg+(j+1)%seg;f.extend([(a,b,b+seg),(a,b+seg,a+seg)])
    if cap:
        v.extend([c+[0,0,profile[0][0]],c+[0,0,profile[-1][0]]]);a=len(v)-2;b=len(v)-1;off=(len(profile)-1)*seg
        for j in range(seg):k=(j+1)%seg;f.extend([(a,k,j),(b,off+j,off+k)])
    return make_mesh(name,v,f,material)

def morph_mesh(m,base,target,parent,origin):
    old=m.glb.exact_index;m.glb.exact_index=False
    node=m.glb.mesh(base,parent=parent,origin=origin)
    m.glb.exact_index=old
    prim=m.glb.doc['meshes'][m.glb.doc['nodes'][node]['mesh']]['primitives'][0]
    prim['targets']=[{'POSITION':m.glb.acc(target.p-base.p)}]
    m.glb.doc['meshes'][m.glb.doc['nodes'][node]['mesh']]['weights']=[0]
    m.glb.doc['nodes'][node]['weights']=[0]
    return node

def hose_mesh(name,c,length,drop,material):
    c=np.asarray(c);pts=[c+[0,-drop*t*t,length*t] for t in np.linspace(0,1,65)]
    return path_tube(name,pts,.026,material,seg=10)

def add_tanker_pod(m,side,center):
    g=m.glb;mat=_mats(m);c=np.asarray(center,float);cid='tanker_'+side
    outer=module(m,'MODULE_TANKER_'+side.upper())
    root=m.pivot(cid+'_component',c,parent=outer,extras={'tags':['level 1'],'asset_id':'hose-drogue-pod-visual','revision':'r0004','reference':REFS['pod']})
    m.attach(lathe_z(cid+'_POD_SHELL',c,[(-2.0,.035),(-1.85,.18),(-1.5,.31),(-1.05,.34),(.7,.34),(1.22,.28),(1.45,.21),(1.45,.17),(1.17,.17)],mat['paint']),root)
    m.attach(lathe_z(cid+'_AFT_HOSE_RECESS',c,[(1.46,.17),(.98,.17),(.98,.05)],mat['dark']),root)
    m.attach(box(cid+'_PYLON',c+[-.10,.28,-.65],c+[.10,1.05,.35],mat['paint']),root)
    # Panel seams are narrow material rings, not raised decorative collars.
    for k,z in enumerate([-.92,.72]):m.attach(lathe_z(cid+'_SEAM_'+str(k),c,[(z,.342),(z+.012,.342)],mat['metal']),root)
    exitp=c+[0,0,1.48]
    h0=hose_mesh(cid+'_FLEXIBLE_HOSE',exitp,.20,0,mat['rubber'])
    h1=hose_mesh(cid+'_FLEXIBLE_HOSE',exitp,15.5,1.1,mat['rubber'])
    hose=morph_mesh(m,h0,h1,root,c)
    rest=exitp+[0,0,.2];coupling=m.pivot(cid+'_drogue',rest,parent=root,extras={'component_type':'hose_end_coupling','visual_payout_not_fluid_simulation':True})
    m.attach(lathe_z(cid+'_COUPLING',rest,[(-.12,.10),(0,.11),(.22,.085),(.29,.065)],mat['metal']),coupling)
    g.node('SOCKET_'+cid.upper()+'_CONTACT',parent=coupling,translation=[0,0,.29],extras={'kind':'GAME_ALIGNMENT','fuel_transfer_solver':'NOT_IMPLEMENTED'})
    variants=[];ribtracks=[];fabricnodes=[]
    for variant,opened in [('high',.42),('low',.60)]:
        group=module(m,'MODULE_'+cid.upper()+'_BASKET_'+variant.upper(),parent=coupling,asset_id='drogue-'+variant+'-speed-visual')
        # Child datum equals moving coupling; fold each actual metal rib about
        # its shoulder rather than scaling an entire rigid basket.
        m.known_pivots[group]=rest.copy()
        ribs=20 if variant=='high' else 24
        for k,a in enumerate(np.linspace(0,2*math.pi,ribs,endpoint=False)):
            radial=np.array([math.cos(a),math.sin(a),0]);p=rest+radial*.09+[0,0,.12]
            hinge=m.pivot(cid+'_'+variant+'_rib_'+str(k),p,parent=group)
            length=math.sqrt((opened-.09)**2+.525**2)
            end=p+[0,0,length]
            m.attach(tube(cid+'_'+variant+'_RIB_'+str(k),p,end,.006,mat['metal'],segments=6),hinge)
            axis=np.cross([0,0,1],radial);angle=math.degrees(math.atan2(opened-.09,.525))
            ribtracks.append((hinge,axis,angle))
        verts0=[];verts1=[];faces=[];seg=80
        length=math.sqrt((opened-.09)**2+.525**2)
        for ring,(z,r0,r1) in enumerate([(.12+length*.75,.09,opened*.75),(.12+length,.09,opened)]):
            for a in np.linspace(0,2*math.pi,seg,endpoint=False):
                fold=1+.035*math.sin(a*ribs)
                verts0.append(rest+[r0*math.cos(a)*fold,r0*math.sin(a)*fold,z])
                deployed_z=.12+(.525*.75 if ring==0 else .525)
                verts1.append(rest+[r1*math.cos(a)*fold,r1*math.sin(a)*fold,deployed_z])
        for k in range(seg):q=(k+1)%seg;faces.extend([(k,q,seg+q),(k,seg+q,seg+k)])
        a=make_mesh(cid+'_'+variant+'_FABRIC',verts0,faces,mat['fabric'])
        b=make_mesh(a.name,verts1,faces,mat['fabric'])
        fabricnodes.append(morph_mesh(m,a,b,group,rest));variants.append(g.doc['nodes'][group]['name'])
    t=np.linspace(0,1,49);q=t*t*(3-2*t);spread=np.clip((t-.12)/.72,0,1);spread=spread*spread*(3-2*spread)
    tracks=[(hose,'weights',t,q[:,None]),(coupling,'translation',t,[[0,-1.1*v,1.68+15.3*v] for v in q])]
    tracks += [(node,'weights',t,spread[:,None]) for node in fabricnodes]
    tracks += [(node,'rotation',t,[quat(axis,angle*v) for v in spread]) for node,axis,angle in ribtracks]
    m.control(cid+'_deploy',side.title()+' hose and drogue',coupling,[0,0,1],15.3,kind='translation',duration=7,group='Aerial refuelling',tracks=tracks,ev=ev('pod','drogue','baskets',note='Flexible exterior hose payout, coupling travel and basket unfolding are visual approximations; exact hose/reel and fabric physics not modeled.'),states={'rest':'Basket collapsed at pod outlet','deployed':'Hose extended, basket open'})
    return {'module':g.doc['nodes'][outer]['name'],'component_root':g.doc['nodes'][root]['name'],'basket_high':variants[0],'basket_low':variants[1],'controls':[cid+'_deploy']}

def add_skyhook(m,center):
    mat=_mats(m);g=m.glb;c=np.asarray(center,float)
    outer=module(m,'MODULE_FULTON_SKYHOOK');root=m.pivot('fulton_component',c,parent=outer,extras={'tags':['level 1'],'asset_id':'fulton-nose-yoke-visual','revision':'r0004','historical':True,'reference':REFS['skyhook']})
    # The source profile is a generic legacy C130; the purpose-built Talon nose
    # replacement is handled by the family skin module, not this independent yoke.
    tracks=[];t=np.linspace(0,1,49);q=t*t*(3-2*t)
    for side,s in [('left',-1),('right',1)]:
        p=c+[s*.90,-.15,.30];hinge=m.pivot('fulton_'+side+'_arm',p,parent=root)
        # Rest folds aft along each fuselage side; deployed horns point forward
        # and outward in the horizontal plane, as the public USAF history says.
        a=p;b=c+[s*2.25,-.20,3.55]
        m.attach(tube('FULTON_'+side.upper()+'_ARM',a,b,.052,mat['metal'],segments=16),hinge)
        m.attach(tube('FULTON_'+side.upper()+'_GUIDE_TIP',b,b+[s*.08,.03,.28],.035,mat['metal'],segments=12),hinge)
        m.attach(tube('FULTON_'+side.upper()+'_HINGE',p+[0,-.10,0],p+[0,.10,0],.09,mat['paint']),root)
        foot=c+[s*.30,-.045,.25]
        m.attach(tube('FULTON_'+side.upper()+'_MOUNT_BRACE',foot,p,.055,mat['paint']),root)
        m.attach(tube('FULTON_'+side.upper()+'_SECONDARY_BRACE',c+[s*.45,-.053,.45],p+[0,-.07,0],.035,mat['metal']),root)
        tracks.append((hinge,'rotation',t,[quat([0,1,0],s*145*v) for v in q]))
    m.attach(box('FULTON_SKY_ANCHOR_HOUSING',c+[-.14,-.12,-.16],c+[.14,.12,.16],mat['paint']),root)
    g.node('SOCKET_FULTON_PICKUP_LINE',parent=root,translation=[0,0,-.17],extras={'kind':'GAME_ALIGNMENT','human_recovery_simulation':'NOT_IMPLEMENTED'})
    m.control('skyhook_deploy','Fulton recovery yoke',root,[0,1,0],145,duration=5.5,group='Historical equipment',tracks=tracks,ev=ev('skyhook','talon',note='Historical retractable horizontal V and fold-back principle sourced; hinge travel and clearance are artist approximations, no person-recovery choreography.'),states={'rest':'Arms folded back','deployed':'Horizontal V deployed'})
    # These are airframe installation guards, NOT part of the reusable nose yoke.
    guards=module(m,'MODULE_FULTON_FENDING_LINES')
    for side,s in [('left',-1),('right',1)]:
        # Taut line to the actual leading edge of this mesh's outer wingtip.
        # Attachment coordinates are authored fit, not aircraft measurements.
        nose_end=c+[s*.30,0,.15]
        m.static_mesh(tube('FULTON_'+side.upper()+'_FENDING_ATTACHMENT',c+[s*.12,0,.12],nose_end,.035,mat['metal']),guards)
        points=[nose_end,[s*19.7,4.71105,-3.14578]]
        m.static_mesh(path_tube('FULTON_'+side.upper()+'_FENDING_LINE',points,.014,mat['metal'],seg=7),guards)
    return {'module':g.doc['nodes'][outer]['name'],'guards':g.doc['nodes'][guards]['name'],'component_root':g.doc['nodes'][root]['name'],'controls':['skyhook_deploy']}

def add_jato(m):
    mat=_mats(m);g=m.glb;gm=gun_materials(m)
    jato_fx=g.material('JATO_VISUAL_BLUE_VIOLET_EXHAUST',[.5,.42,1,.72],0,.5,double=True,emissive=[.35,.20,1])
    g.doc['materials'][jato_fx]['pbrMetallicRoughness']['baseColorTexture']=g.doc['materials'][gm['flash']]['pbrMetallicRoughness']['baseColorTexture'].copy()
    outer=module(m,'MODULE_JATO_EIGHT');root=m.pivot('jato_component',[0,0,0],parent=outer,extras={'tags':['level 1'],'asset_id':'legacy-c130-jato-visual-kit','revision':'r0004','historical':True,'reference':REFS['jato']})
    t=np.linspace(0,1,65);fade=np.sin(np.pi*t)**.7;tracks=[]
    for side,s in [('left',-1),('right',1)]:
        for k in range(4):
            # Airframe attachment coordinates are game fit to the inherited skin.
            fitted_x=[2.21874,2.27890,2.30262,2.30550][k]
            c=np.array([s*fitted_x,1.65+.35*k,3.75-.06*k]);cid='JATO_'+side.upper()+'_'+str(k+1)
            bottle=m.pivot(cid,c,parent=root,extras={'tags':['level 1'],'asset_id':'jato-bottle-visual','instance_id':cid})
            g.doc['nodes'][bottle]['rotation']=quat([1,0,0],18)
            body=lathe_z(cid+'_BOTTLE',c,[(-.59,.04),(-.50,.12),(-.36,.145),(.38,.145),(.48,.10),(.58,.06),(.62,.10)],mat['bottle'],seg=28,cap=True)
            m.attach(body,bottle)
            for zz in [-.24,.27]:m.attach(lathe_z(cid+'_CLAMP_'+str(zz),c,[(zz,.153),(zz+.05,.153)],mat['metal'],seg=28),bottle)
            inner=s*(fitted_x-.34)
            m.attach(box(cid+'_BRACKET',[min(inner,c[0]),c[1]-.07,c[2]-.17],[max(inner,c[0]),c[1]+.07,c[2]+.17],mat['paint']),bottle)
            nozzle=c+[0,0,.64];fx=m.pivot(cid+'_exhaust',nozzle,parent=bottle)
            flash=flash_mesh(cid+'_SOFT_EXHAUST',nozzle,2.7,jato_fx);flash.rotate(nozzle,[0,1,0],90)
            m.attach(flash,fx);g.doc['nodes'][fx]['scale']=[0,0,0]
            tracks.append((fx,'scale',t,[[v,v,v] for v in fade]))
            sock=g.node('SOCKET_'+cid+'_EXHAUST',parent=bottle,translation=[0,0,.64],extras={'kind':'VISUAL_FX','operational_data':False})
    m.control('jato_burn','JATO visual exhaust',root,[0,0,1],1,kind='translation',duration=4.8,group='Historical equipment',tracks=tracks,ev=ev('jato',note='Historical bottle kit and takeoff exhaust appearance only. No thrust, propellant, ignition logic or aircraft performance model.'),states={'rest':'Bottles fitted, exhaust off','deployed':'Visual burn cycle complete'})
    c=m.controls[-1];c.update(kind='cycle',units='normalized visual cycle',preview_cycles=1)
    return {'module':g.doc['nodes'][outer]['name'],'component_root':g.doc['nodes'][root]['name'],'controls':['jato_burn']}
