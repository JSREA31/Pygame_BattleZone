import modules.objects as objects
import models.raw_wireframes_BZ as rawBZ
import math
import numpy as np
from copy import deepcopy
import settings

################################################################
## create_obstacle:                                            
##       create Obstacle objects for Library                 
################################################################  
def create_obstacle(type):

    aspect = aspect=[1.0,1.0,2.0]
    if type ==settings.OBJ_TALLBOX:
        nodes = rawBZ.tallboxnodes
        faces = rawBZ.tallboxfaces
    elif type== settings.OBJ_SHORTBOX:
        nodes = rawBZ.shortboxnodes
        faces = rawBZ.shortboxfaces
        aspect = [1.2,1.2,1.75]
    elif type ==settings.OBJ_PYRAMID:
        nodes = rawBZ.pyramidnodes
        faces= rawBZ.pyramidfaces
    elif type ==settings.OBJ_WIDEPYRAMID:
        nodes  =rawBZ.widepyramidnodes
        faces = rawBZ.pyramidfaces        

    edges=[]
    details=[]
    anim=[]
    size=10
    coords=[0.0,5.0,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(-90),0.0,0.0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(0,200,0)
    object = objects.Obstacle("obstacle",nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect)
    return object

################################################################
## create_tank:                                          ## 
##       create Tank Object  for Library                      ##
################################################################  
def create_tank(type):
    nodes = rawBZ.tanknodes
    faces = rawBZ.tankfaces
    edges=rawBZ.tankedges
    details=rawBZ.tankdetails
    anim=rawBZ.tankanim

    size=20
    coords=[0.0,4.9,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(-90),0.0,0.0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(00,255,00)
    type = type
    aspect=[1.0,1.0,2.0]
    object = objects.Tank("tank",nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect)
    return object

################################################################
## create_fast_tank:                             
##       create Tank Object  for Library                
################################################################  
def create_fast_tank(type):
    nodes = rawBZ.fastTanknodes
    faces = rawBZ.fastTankfaces
    edges = rawBZ.fastTankedges
    details=rawBZ.fastTankdetails
    anim=[]

    size=20
    coords=[0.0,5.0,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(-90),0.0,0.0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(00,255,00)
    type = type
    aspect=[1.0,1.0,2.0]
    object = objects.Tank("fast tank",nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect)
    return object


################################################################
## create_missile:                                      
##   create Missile Object for Library                       
################################################################  
def create_missile():
    nodes = rawBZ.projectilenodes
    faces = rawBZ.projectilefaces
    edges=[]
    details=[]
    anim=[]

    size=2
    coords=[0.0,0.0,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(-90),math.radians(90),0.0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(100,200,100)
    type = settings.OBJ_PLAYERMISSILE
    object = objects.Missile("missile",nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect=[1.0,1.0,1.0])
    return object

################################################################
## create_guided_missile:                                 
##       create Guided Missile Object  for Library           
################################################################  
def create_guided_missile():
    nodes = rawBZ.guidedmissilenodes
    faces = rawBZ.guidedmissilfaces
    edges = rawBZ.guidedmissileedges
    details = rawBZ.guidedmissiledetails
    anim = []

    size=20
    coords=[0.0,5.0,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(-90),math.radians(-90),0.0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(00,255,00)
    type = settings.OBJ_GUIDEDMISSILE
    aspect=[1.0,1.0,2.0]
    object = objects.GuidedMissile("guided missile",nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect)
    return object

################################################################
## create_saucer:                                 
##       create flying saucer Object  for Library           
################################################################  
def create_saucer():
    nodes = rawBZ.saucernodes
    faces = rawBZ.saucerfaces
    edges = rawBZ.sauceredges
    details = []
    anim = []

    size=20
    coords=[0.0,-3,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(-90),math.radians(-90),0.0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(00,255,00)
    type = settings.OBJ_SAUCER
    aspect=[1.0,1.0,2.0]
    object = objects.Saucer("flying saucer",nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect)
    return object


################################################################
## create_explosion:                                    
##       create explosion Object for Library                  
################################################################  
def create_explosion():

    explosion=[]

    faces = []
    edges=[]
    details=[]
    anim=[]
    size=10
    coords=[0.0,0.0,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(-90),0.0,0.0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(0,0,0)
    type = settings.OBJ_CHUNK

    sizes=[10,10,20,1,10,10]
    for i,frame in enumerate(rawBZ.chunknodes):
        faces = rawBZ.chunkfaces[i]
        size=sizes[i]        
        object = objects.explosionChunk("chunk"+str(i),frame,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect=[1.0,1.0,2.0])
        explosion.append(object)

    return explosion


################################################################
## create_spatter:                                      
##         create guided missile spatter objects for Library                
################################################################  
def create_spatter():

    spatter=[]

    faces = []
    edges=[]
    details=[]
    anim=[]
    size=1
    coords=[0.0,5,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(90),0,0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(255,0,0)
    type = settings.OBJ_SPATTER

    for i,frame in enumerate(rawBZ.spatternodes):
        object = objects.Spatter("Spatter"+str(i),frame,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect=[1.0,1.0,1.0])
        size=size+1
        spatter.append(object)

    return spatter 


################################################################
##create_projectile_explosion                           
##      create explosion object for Library                   
################################################################ 
def create_projectile_explosion():
    nodes = rawBZ.explosionnodes
    faces=[]
    edges=[]
    details=[]
    anim=[]

    size=3
    coords=[0.0,0.0,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[0.0,0.0,0.0,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(100,255,100)
    type = settings.OBJ_PROJECTILE_IMPACT
    object = objects.projectile_impact_explosion(settings.EVENT_PROJECTILE_IMPACT,nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect=[1.0,1.0,1.0])

    return object


################################################################
## create_logo                                                 
##      create BZ Logo Object                                
################################################################ 
def create_logo():
    nodes = rawBZ.logonodes
    faces=[]
    edges=rawBZ.logoedges
    details=[]
    anim=[]

    size=30
    coords=[0.0,0.0,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[0,np.pi,-np.pi/2,0]
    rotation_delta=[0.0,0.0,0.0,0]
    color=(0,255,0)
    type = settings.OBJ_LOGO
    object = objects.GameObject("logo",nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect=[1.0,1.0,1.0])

    return object

################################################################
## create_dodo:                                 
##       create Elite dodo Object  for Library           
################################################################  
def create_dodo():
    nodes = rawBZ.dodonodes
    faces = rawBZ.dodofaces
    edges = []
    details = []
    anim = []

    size=10
    coords=[0.0,0,0.0,1]
    coords_delta = [0.0,0,0,0]
    rotation_initial=[math.radians(-90),math.radians(-90),0.0,0]
    rotation_delta=[0.01,0.01,0.01,1]
    color=(255,255,255)
    type = settings.OBJ_DODO
    aspect=[1.0,1.0,1.0]
    object = objects.Dodo("Elite Dodo",nodes,faces,edges,details,anim, size,coords,coords_delta, rotation_initial, rotation_delta, color, type,aspect)
    return object


################################################################
## create_object_library                                       
##     add individual objects to Library                     
################################################################ 
def create_object_library():
    object_library={}
    object_library["Tank"] = create_tank(settings.OBJ_TANK)
    object_library["FastTank"] = create_fast_tank(settings.OBJ_FASTTANK)
    object_library["Missile"] = create_missile()
    object_library["GuidedMissile"] = create_guided_missile()
    object_library["Saucer"] = create_saucer()
    object_library["Spatter"] = create_spatter()
    object_library["Explosion_chunks"] = create_explosion()
    object_library["Projectile_explosion"] = create_projectile_explosion()
    object_library["TallBox"] = create_obstacle(settings.OBJ_TALLBOX)
    object_library["ShortBox"] = create_obstacle(settings.OBJ_SHORTBOX)
    object_library["Pyramid"] = create_obstacle(settings.OBJ_PYRAMID)
    object_library["WidePyramid"] = create_obstacle(settings.OBJ_WIDEPYRAMID)
    object_library["Logo"] = create_logo()
    object_library['Dodo'] = create_dodo()
    return object_library

################################################################
## logo_object                                     
##     create vector object of BZ logo                   
################################################################ 
def logo_object(library):
    logo: objects.GameObject
    logo = deepcopy(library["Logo"])
    logo.coords_model[0] = 0
    logo.coords_model[1] = 0
    logo.coords_model[2] = 1
    logo.color = [0, 255, 0]
    logo.name = "Logo"
    logo.static = True
    return (logo)
