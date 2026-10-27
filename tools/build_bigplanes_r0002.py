#!/usr/bin/env python3
"""Build additional draft C-130 mission variants and an independent KC-135R.

Each Hercules variant retains the exact C130_COMMON_r0001 source airframe.
All added mission shapes are intentionally labelled unverified game proxies.
KC-135 derives exclusively from kc135-stratotanker.glb, never C-130.
No source file is modified, no visual acceptance is claimed.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from audit_c130_glb import load_glb
from build_c130_family import (
    ROOT, BASE, EXPECTED, make_variant, encode_glb, node, mat, mesh,
    cylinder, sphere, add_barrel,
)

OUT=ROOT/"family"/"r0002"
KC_SOURCE=ROOT/"kc135-stratotanker.glb"
KC_HASH="3e9d9fb1519adbecea971f2ec3470f3b537fb18e9fae40f1d15622ac058056fd"
# Source KC-135 bbox from a direct GLB audit, not a photo fit.
KC_SOURCE_BOUNDS={"min":[-23.1433,-17.7119,-.215],
                  "max":[23.2137,22.9483,12.4629]}
KC_TARGET={"length_m":41.53,"span_m":39.88,"height_m":12.70}
# Coordinates are game alignment estimates in metres, not aircraft engineering data.
CONFIGS={
    "c130j-super-hercules":{"prop":"j","kit":"none","receiver":"none","delivery":"none","role":"transport"},
    "ac130u-spooky":{"prop":"legacy","kit":"legacy","receiver":"none","delivery":"none","role":"gunship_u"},
    "mc130e-combat-talon-i":{"prop":"legacy","kit":"none","receiver":"documented_receptacle_to_verify","delivery":"wing_pods","role":"talon_e"},
    "mc130h-combat-talon-ii":{"prop":"legacy","kit":"none","receiver":"boom_receptacle_source_fit_pending","delivery":"wing_pods","role":"talon_h"},
    "mc130h-combat-talon-ii-jato":{"prop":"legacy","kit":"none","receiver":"boom_receptacle_source_fit_pending","delivery":"wing_pods","role":"talon_h_jato","fictional":True},
    "mc130j-commando-ii":{"prop":"j","kit":"none","receiver":"boom_receptacle_source_fit_pending","delivery":"wing_pods","role":"commando_j"},
    "hc130j-combat-king-ii":{"prop":"j","kit":"none","receiver":"verify_exact_aircraft","delivery":"wing_pods","role":"rescue_j"},
    "kc130j-tanker":{"prop":"j","kit":"none","receiver":"none","delivery":"wing_pods","role":"tanker_j"},
    "lc130h-ski-hercules":{"prop":"legacy","kit":"none","receiver":"none","delivery":"none","role":"ski_h"},
    "wc130j-weatherbird":{"prop":"j","kit":"none","receiver":"none","delivery":"none","role":"weather_j"},
    "ec130h-compass-call":{"prop":"legacy","kit":"none","receiver":"none","delivery":"none","role":"ec_h"},
    "xc130j-skyhook-jato":{"prop":"j","kit":"ghostrider","receiver":"boom_receptacle_source_fit_pending","delivery":"none","role":"xc_game","fictional":True},
}
ROLE_LABELS={
    "transport":"C-130J Super Hercules (short) — candidate",
    "gunship_u":"AC-130U Spooky — candidate",
    "talon_e":"MC-130E Combat Talon I — candidate",
    "talon_h":"MC-130H Combat Talon II — candidate",
    "talon_h_jato":"MC-130H Combat Talon II + JATO (game variant)",
    "commando_j":"MC-130J Commando II — candidate",
    "rescue_j":"HC-130J Combat King II — candidate",
    "tanker_j":"KC-130J tanker — candidate",
    "ski_h":"LC-130H ski Hercules — candidate",
    "weather_j":"WC-130J Weatherbird — candidate",
    "ec_h":"EC-130H Compass Call — candidate",
    "xc_game":"XC-130J AC-130J + Skyhook + JATO (fictional)",
}
def add_cylinder(doc,buf,name,a,b,r,matid,axis="y",kind="kit_proxy"):
    verts,faces=cylinder(axis,a,b,r)
    return mesh(doc,buf,name,verts,faces,matid,kind)

def add_sphere(doc,buf,name,center,r,matid,kind="kit_proxy"):
    verts,faces=sphere(center,r)
    return mesh(doc,buf,name,verts,faces,matid,kind)

def add_box(doc,buf,name,center,size,matid,kind="kit_proxy"):
    x,y,z=center;dx,dy,dz=(s/2 for s in size)
    v=[(x+sx*dx,y+sy*dy,z+sz*dz) for sx,sy,sz in
       ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    f=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
       (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return mesh(doc,buf,name,v,f,matid,kind)

def kit_pods(doc,buf,metal):
    ids=[]
    for side,lab in ((-1,"STARBOARD"),(1,"PORT")):
        x=side*13.15
        ids.append(add_cylinder(doc,buf,"KIT_DELIVERY_POD_"+lab,
            (x,-4.9,5.05),(x,-2.6,5.05),.34,metal,
            kind="tanker_delivery_pod_STOWED_NO_HOSE"))
        ids.append(add_box(doc,buf,"KIT_DELIVERY_PYLON_"+lab,
            (x,-3.8,5.42),(.20,1.45,.48),metal,
            kind="tanker_delivery_pylon"))
    return ids

def kit_jato(doc,buf,metal):
    ids=[]
    for side,lab in ((-1,"STARBOARD"),(1,"PORT")):
        for k in range(4):
            x=side*(2.05+.07*(k%2))
            y=.4+k*.94
            z=1.42+(.15 if k%2 else 0)
            ids.append(add_cylinder(doc,buf,
                f"KIT_GAME_JATO_{lab}_{k+1}_STOWED",
                (x,y,z),(x,y+.72,z),.15,metal,
                kind="fictional_game_jato_canister_stowed"))
        ids.append(add_box(doc,buf,f"KIT_GAME_JATO_RACK_{lab}",
            (side*2.05,2.15,1.43),(.24,4.4,.22),metal,
            kind="fictional_game_jato_mount"))
    return ids

def add_talon(doc,buf,role,metal,optics):
    ids=[]
    ids.append(add_sphere(doc,buf,"KIT_TALON_TF_TA_NOSE_RADAR_PROXY",
                          (0.,-13.15,3.52),.54,optics,"terrain_following_radar_proxy"))
    for side,lab in ((-1,"STARBOARD"),(1,"PORT")):
        ids.append(add_box(doc,buf,"KIT_TALON_EW_ARRAY_"+lab,
                    (side*1.82,-5.4,4.0),(.18,.55,.16),metal,
                    kind="electronic_warfare_array_proxy"))
    ids.extend(kit_pods(doc,buf,metal))
    if role=="talon_e":
        ids.append(add_box(doc,buf,"KIT_TALON_I_FULTON_MOUNT_OPTIONAL",
            (0.,-12.6,4.72),(.48,.68,.15),metal,
            kind="fulton_optional_configuration_only"))
    return ids

def add_game_skyhook(doc,buf,metal):
    # Fictional and explicitly not a historical Fulton mechanism match.
    ids=[]
    for side,lab in ((-1,"STARBOARD"),(1,"PORT")):
        ids.append(add_cylinder(doc,buf,"KIT_GAME_SKYHOOK_ARM_"+lab,
             (side*.44,-12.1,4.3),(side*1.25,-15.1,5.65),.055,metal,
             axis="y",kind="fictional_skyhook_arm_proxy"))
    return ids

def build_c130(doc0,basebin,name,settings):
    doc,buf=make_variant(doc0,basebin,name,settings)
    metal=mat(doc,"KIT_R0002_METAL_APPROX",(.24,.27,.30,1.))
    dark=mat(doc,"KIT_R0002_DARK_APPROX",(.07,.10,.12,1.))
    role=settings["role"]
    ids=[]
    if role in ("talon_e","talon_h","talon_h_jato"):
        ids.extend(add_talon(doc,buf,role,metal,dark))
    if role in ("talon_h_jato","xc_game"):
        ids.extend(kit_jato(doc,buf,metal))
    if role in ("commando_j","rescue_j","tanker_j"):
        ids.extend(kit_pods(doc,buf,metal))
    if role in ("commando_j","rescue_j"):
        ids.append(add_sphere(doc,buf,"KIT_J_SPECIAL_OPS_SENSOR_PROXY",
                              (.35,-12.3,3.0),.31,dark))
    if role=="gunship_u":
        ids.append(add_barrel(doc,buf,"KIT_AC130U_25MM_PROXY",
                              (2.04,-3.1,2.72),1.1,.075,metal))
        ids.append(add_barrel(doc,buf,"KIT_AC130U_40MM_PROXY",
                              (2.04,.3,2.72),1.1,.12,metal))
        ids.append(add_barrel(doc,buf,"KIT_AC130U_105MM_PROXY",
                              (2.04,4.5,2.62),1.2,.18,metal))
    if role=="ski_h":
        ids.append(add_box(doc,buf,"KIT_LC130_NOSE_SKI_PROXY",
                 (0.,-11.1,.10),(.92,3.0,.15),metal,"ski_game_proxy"))
        for side,lab in ((-1,"STARBOARD"),(1,"PORT")):
            ids.append(add_box(doc,buf,"KIT_LC130_MAIN_SKI_"+lab,
                 (side*2.4,1.8,.10),(.95,4.3,.15),metal,"ski_game_proxy"))
    if role=="weather_j":
        ids.append(add_sphere(doc,buf,"KIT_WC130J_WEATHER_SENSOR_PROXY",
                              (0.,-13.0,3.52),.26,dark))
        ids.append(add_box(doc,buf,"KIT_WC130J_DROPSONDE_PORT_PROXY",
                              (0.,7.6,2.1),(.30,.42,.12),metal))
    if role=="ec_h":
        for k in range(3):
            ids.append(add_box(doc,buf,f"KIT_EC130H_ANTENNA_{k+1}",
                (0.,-4.+k*4.2,6.15),(.18,.72,.7),metal))
    if role=="xc_game":
        ids.extend(add_game_skyhook(doc,buf,metal))
    kit=node(doc,"KIT_R0002_"+role.upper(),children=ids,
             extras={"role":role,"geometry_status":"ARTIST_PROXY_NOT_PHOTO_VERIFIED",
                     "fictional":bool(settings.get("fictional",False)),
                     "receiver_type":settings["receiver"],
                     "delivery_type":settings["delivery"]})
    root=doc["scenes"][0]["nodes"][0]
    doc["nodes"][root]["children"].append(kit)
    doc["nodes"][root]["extras"].update({
        "revision":"r0002","designation":ROLE_LABELS[role],
        "receiver_equipment_status":settings["receiver"],
        "tanker_delivery_status":settings["delivery"],
        "fictional":bool(settings.get("fictional",False)),
        "photographic_acceptance":"NOT_RUN",
        "native_unreal_acceptance":"NOT_RUN",
        "mission_equipment":"PROXY_NOT_VALIDATED"})
    # r0001 has universal *socket definitions*, but they are game-only and
    # must not imply real hardware fitted. Filter irrelevant sockets per variant.
    socket_root=next(n for n in doc["nodes"] if n["name"]=="SOCKETS_GAME_ONLY")
    selected=[]
    for i in socket_root["children"]:
        n=doc["nodes"][i]["name"]
        if "RECEIVER" in n and settings["receiver"]=="none":continue
        if "TANKER_DELIVERY" in n and settings["delivery"]=="none":continue
        if "JATO" in n and role not in ("talon_h_jato","xc_game"):continue
        if "FULTON" in n and role not in ("talon_e","xc_game"):continue
        selected.append(i)
    socket_root["children"]=selected
    doc["buffers"][0]["byteLength"]=len(buf)
    return doc,buf
