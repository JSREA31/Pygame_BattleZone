import numpy as np
import modules.matrices as mx
import random
from copy import deepcopy
import math
import settings
import time



class GameObject:
    def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type="poly",aspect=[1.0,1.0,1.0]):
        self.name = name
        
        self.type = type
        self.is_visible = True
        self.is_dead = False

        self.nodes_model = nodes
        self.nodes_world = self.nodes_model.copy()
        self.nodes_view = self.nodes_world.copy()
        self.nodes_projected = self.nodes_view.copy()

        self.coords_model  = coords
        self.coords_world = self.coords_model.copy()
        self.coords_view = self.coords_world.copy()
           
        self.faces = faces
        self.edges = edges
        self.details = details
        self.coords_delta = coords_delta 
        self.x_map = 0
        self.z_map = 0


        #set up values for shading
        self.color = color
        
        self.SHADING = 0.8
        self.color_base = np.multiply(self.color,1-self.SHADING)

        #resize
        self.size = size
        self.resize(size)
        self.change_aspect(aspect)
        
        #set center of object
        center=self.find_center(self.nodes_model)

        #set initial rotation of object    
        self.rotation =  rotation_initial
        if self.rotation[0] != 0:
            matrix = mx.rotateXMatrix(self.rotation[0])
            self.nodes_model = center + np.dot(self.nodes_model - center, matrix.T)
        if self.rotation[1] != 0:
            matrix = mx.rotateYMatrix(self.rotation[1])
            self.nodes_model = center + np.dot(self.nodes_model - center, matrix.T)
        if self.rotation[2] != 0:
            matrix = mx.rotateZMatrix(self.rotation[2])
            self.nodes_model = center + np.dot(self.nodes_model - center, matrix.T)

        self.xyz_size=self.get_size(self.nodes_model)
        self.y_offset = self.nodes_model.max(axis = 0)[1]
        self.coords_model[1]=self.coords_model[1]-self.y_offset

        self.rotation=[0.0,0.0,0.0,0]
        self.rotation_delta = rotation_delta
        self.static = True
        self.points = 0
    

    ################################################################
    ## get_size:                                                  
    ##               calculate X,Y,Z size of object               
    ################################################################
    def get_size(self,nodes):
   
       min = nodes.min(axis = 0)
       max = nodes.max(axis = 0)
       return  (max-min)
 

    ################################################################
    ## resize:                                                  
    ##         resize initial nodes to specific X size          
    ################################################################
    def resize(self,size):
        self.xyz_size = self.get_size(self.nodes_model)
        self.scale_factor = [size]/self.xyz_size[0]
        matrix = mx.scaleMatrix([self.scale_factor[0],self.scale_factor[0],self.  scale_factor[0]])
        self.nodes_model = np.dot(self.nodes_model, matrix)
        self.xyz_size = self.get_size(self.nodes_model)


    ################################################################
    ## change_aspectratio:                                     
    ##         resize initial nodes to specific X size       
    ################################################################
    def change_aspect(self,xyz_aspect):
   
        matrix = mx.scaleMatrix([xyz_aspect[0],xyz_aspect[1],xyz_aspect[2]])
        self.nodes_model = np.dot(self.nodes_model, matrix)
    
    
    ################################################################
    ## find_center:                                             
    ##                find center X,Y,Z of object               
    ################################################################
    def find_center(self,nodes):
        if self.type == settings.OBJ_TANK:
           mean=nodes[:-8].mean(axis = 0)
        else:        
            mean = nodes.mean(axis = 0)     # to take the mean of each col
        return mean

    ################################################################
    ## rotate_y:                                              
    ## rotate Y used for initial rotation of static objects      
    ################################################################
    def rotate_y(self):
        object_center=self.find_center(self.nodes_model)     
        matrix = mx.rotateYMatrix(self.rotation[1])
        self.nodes_model = object_center + np.dot(self.nodes_model - object_center, matrix.T)

    ################################################################
    ## update:                                                
    ## base method for updating objects, overriden by children   
    ################################################################
    def update(self,objectList,object_library,player,event_list):
        
        #update object rotation value and xyz position
        if not self.static:
            self.rotation=np.add(self.rotation,self.rotation_delta)
            self.rotation=self.rotation%(2*np.pi)
            self.coords_model = np.add(self.coords_model,self.coords_delta)

        #copy raw model coordinates into world
        self.coords_world = self.coords_model.copy() 


    ################################################################
    ## update_view_coords:                              
    ##                Transform World into View           
    ################################################################
    def update_view_coords(self,player):
    
        center=player.view_center
        #adjust for player position
        self.coords_view = np.add(self.coords_world,player.coords_delta)

        #recenter world around view center
        self.coords_view = np.add(self.coords_view,center)

        #rotate coords around center based on player rotation
        matrix = mx.rotateYMatrix(player.view_rotation)
        self.coords_view = center + np.matmul(matrix, self.coords_view-center)


    ################################################################
    ## update_view_objects:                                       
    ##                Transform objects into View               
    ################################################################
    def update_view_objects(self,player):

        #copy raw Model nodes into world
        self.nodes_world = self.nodes_model.copy()

        if not self.static:
            # Rotate objects around object center
            object_center = self.find_center(self.nodes_world)
        
            # Combine rotation matrices
            rotation_matrix = np.matmul(np.matmul(mx.rotateXMatrix(self.rotation[0]),mx.rotateYMatrix(self.rotation[1])),mx.rotateZMatrix(self.rotation[2]))
        
            # Apply combined rotation matrix to each node
            self.nodes_world = object_center + np.dot(self.nodes_world - object_center, rotation_matrix.T)

        self.nodes_view = self.nodes_world.copy()

        #apply new coordinates to nodes (used for positioing of missile realtive to player)
        matrix = mx.translationMatrix(self.coords_world)     
        self.nodes_world= np.dot(self.nodes_world, matrix)

        # Combine Y and X view rotations into a single matrix
        matrix_y = mx.rotateYMatrix(player.view_rotation)
        matrix_x = mx.rotateXMatrix(player.view_elevation)
        combined_matrix = np.matmul(matrix_x, matrix_y)
        
        object_center = self.find_center(self.nodes_view)
        self.nodes_view = object_center + np.dot(self.nodes_view - object_center, combined_matrix.T)

        #apply new coordinates to view nodes
        matrix = mx.translationMatrix(self.coords_view)     
        self.nodes_view= np.dot(self.nodes_view, matrix)


    ################################################################
    ## update_perspective:                                         ## 
    ##         Perspective projection of objects                  ##
    ################################################################
    def update_perspective(self,center,factor):
    
        z = abs(self.coords_view[2])
        matrix = mx.perspectiveMatrix(factor / z, factor / z, 1)
        self.nodes_projected = center + np.dot(self.nodes_view - center, matrix.T)
     
        
################################################################
## obstacle                                                   ## 
##         obstacle child object                              ##
################################################################
class Obstacle(GameObject):

    def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect)
        self.radar_color=(200,0,0)
        self.radar_size=1

    def update(self,objectList,object_library,player,event_list):
        #update object rotation value and xyz position
        self.rotation=np.add(self.rotation,self.rotation_delta)
        self.rotation=self.rotation%(2*np.pi)
        self.coords_model = np.add(self.coords_model,self.coords_delta)

        wrap=player.visibility_threshold
        dz = self.coords_model[2]-player.coords[2]
        dx = self.coords_model[0]-player.coords[0]
        new_z_map = int(dz/wrap)
        new_x_map= int(dx/wrap)
        
        if new_z_map != 0:
            if new_z_map==1:
                self.coords_model[2] = self.coords_model[2]-(2*wrap)
            elif new_z_map==-1:
                self.coords_model[2] = self.coords_model[2]+(2*wrap)

        if new_x_map != 0:
            if new_x_map==1:
                self.coords_model[0] = self.coords_model[0]-(2*wrap)
            elif new_x_map==-1:
                self.coords_model[0] = self.coords_model[0]+(2*wrap)
            
        #copy raw model coordinates into world
        self.coords_world = self.coords_model.copy()     


################################################################
## Guided Missile                                             ## 
##         Guided Missile child object                        ##
################################################################
class GuidedMissile(GameObject):
    def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect)
        self.mode=1
        self.counter = 0
        self.time_out = 500
        self.mode3_length = 0
        self.mode3_angle = np.pi/7
        self.static = False
        self.angle_to_player=0
        self.delta_angle=0
        self.distance_to_player=0
        self.radar_color=(0,0,0)
        self.radar_size=2
    

    def update(self,objectList,object_library,player,event_list):
            
        def checkCollision():
            x_check = self.coords_model[0]+self.coords_delta[0]*2
            z_check = self.coords_model[2]+self.coords_delta[2]*2
            collision=False

            #check collison with player
            x_player = player.coords[0]
            z_player = player.coords[2]
            size=10
    
            if x_check < x_player+size and x_check > x_player-size:
                    if z_check < z_player+size and z_check > z_player-size:
                        collision=True
                        event_list.append((settings.EVENT_HORIZON_SHAKE,None))
                        event_list.append((settings.EVENT_HIT,None))

            #check collison with other objects
            for object in objectList:
                size = object.size
                if object != self and object.type != settings.OBJ_SPATTER and object.type!=settings.OBJ_DODO:
                    if object.coords_model[0] > x_check-size and object.coords_model[0] < x_check+size:
                        if object.coords_model[2] > z_check-size and object.coords_model[2] < z_check+size:
                            collision=True
                            player.score+=object.points
                                     
            return collision 


        def get_angle():
            dx = player.coords[0]-self.coords_world[0]
            dz = player.coords[2]-self.coords_world[2]
            angle_to_player = math.atan2(dz,dx)
            
            if angle_to_player<0:
                angle_to_player=angle_to_player+2*np.pi
            
            return(angle_to_player)

        self.counter+=1

        if self.coords_model[1]>0:
            self.coords_model[1]=0
            self.coords_delta[1]=0
            
            if self.mode ==1:
                self.angle = get_angle()
                self.rotation[1] = self.angle+np.pi/2
                self.coords_delta[0] = self.speed*np.cos(self.angle)
                self.coords_delta[2] = self.speed*np.sin(self.angle)
            elif self.mode==3:
                self.initial_angle = get_angle()
                self.rotation[1] = self.initial_angle+np.pi/2+self.mode3_angle
                self.coords_delta[0] = self.speed*np.cos(self.initial_angle+self.mode3_angle)
                self.coords_delta[2] = self.speed*np.sin(self.initial_angle+self.mode3_angle)    
                
            event_list.append((settings.EVENT_GUIDED_M_SPATTER,self))  

        
        if self.coords_delta[1]==0 and self.mode==2:
            angle = get_angle()
            self.rotation[1] = angle+np.pi/2
            self.coords_delta[0] = self.speed*np.cos(angle)
            self.coords_delta[2] = self.speed*np.sin(angle)
        elif self.coords_delta[1]==0 and self.mode==3: 
            if self.counter%self.mode3_length==0:
                    self.mode3_angle=self.mode3_angle*-1
                    self.rotation[1] = self.initial_angle+np.pi/2+self.mode3_angle
                    self.coords_delta[0] = self.speed*np.cos(self.initial_angle+self.mode3_angle)
                    self.coords_delta[2] = self.speed*np.sin(self.initial_angle+self.mode3_angle)
                    if self.counter//self.mode3_length>20:self.mode=2
            

        #update object rotation value and xyz position
        self.rotation=np.add(self.rotation,self.rotation_delta)
        self.rotation=self.rotation%(2*np.pi)

        self.coords_model = np.add(self.coords_model,self.coords_delta)
    
        if self.counter>self.time_out:
            self.is_dead=True
            event_list.append((settings.EVENT_SOUND_STOP,5))    
            event_list.append((settings.EVENT_EXPLOSION,self,1))
            
           
        if self.coords_model[1]==0:
            if checkCollision():
                self.is_dead=True
                event_list.append((settings.EVENT_SOUND_STOP,5))  
                event_list.append((settings.EVENT_EXPLOSION,self,1))
                
            

        #copy raw model coordinates into world
        self.coords_world = self.coords_model.copy()
     

################################################################
## Tank:                                                      ## 
##         Tank object child class                            ##
## Tank Types:                                                ##
## 0 = not move,random rotate, not fire                       ##
## 1 = move between two points, not fire                      ##
## 2 = not move, rotate to face and fire                      ##
## 3 = move between points, maybe rotate abnd fire            ##
## 4 = Fast tank, hunt and fire                               ##
##                                                            ##
## Variables = rot speed, movement speed & firing frequeny    ##
################################################################
class Tank(GameObject):
    
    def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type,aspect):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type,aspect)
        
        self.tank_type = 0
        self.tank_mode = 0
        self.radar_speed = 0.2
        self.animated_nodes = anim
        self.radar_axis = [self.size*-512/2272,0,self.size*-125/2272,0]
        self.rotational_speed = 0.0
        self.speed = 0.5
        self.fire_probability = 0
        self.target_angle = 0
        self.coords_destination = deepcopy(self.coords_model)
        self.coords_start = deepcopy(self.coords_model)
        self.moving = False
        self.can_fire = True
        self.evasive_move= False
        self.evasive_move_count = 0
        self.evasive_duration = 200
        self.firing_distance = 200
        self.rotational_direction = 1
        self.fire_counter = 0
        self.static = False
        self.missile_range=1000
        self.number = 0
        self.time_outs=0
        self.create_time=0
        self.radar_color=(255,0,0)
        self.radar_size=2

        

    def update(self,objectList,object_library,player,event_list):
       
        def flipDirection():
            self.coords_delta_temp = np.multiply(self.coords_delta,-1)
            self.coords_delta = [0,0,0,0]
            self.target_angle = self.rotation[1]-np.pi
            if self.target_angle<0: self.target_angle+=2*np.pi
            temp = deepcopy(self.coords_destination)
            self.coords_destination = deepcopy(self.coords_start)
            self.coords_start = deepcopy(temp)
            self.moving=False

        def checkCollision():
            x_check = self.coords_model[0]+self.coords_delta[0]*2
            z_check = self.coords_model[2]+self.coords_delta[2]*2
            collision=False

            #check collison with player
            x_player = player.coords[0]
            z_player = player.coords[2]
            size=20
    
            if x_check < x_player+size and x_check > x_player-size:
                    if z_check < z_player+size and z_check > z_player-size:
                        event_list.append((settings.EVENT_HORIZON_SHAKE,None))
                        collision=True

            #check collison with other objects
            for object in objectList:
                size = object.size
                if object != self and object.type != settings.OBJ_DODO:
                    if object.coords_model[0] > x_check-size and object.coords_model[0] < x_check+size:
                        if object.coords_model[2] > z_check-size and object.coords_model[2] < z_check+size:
                            collision=True

            return collision                    


        def get_gun_center():
            if self.type == settings.OBJ_TANK:
                gun_center=self.nodes_world[18:21].mean(axis = 0)
            else:
                gun_center  =self.nodes_world[15:18].mean(axis = 0)
            return(gun_center)    


        def rotate_to_face():
            
            if self.delta_angle >np.pi:
                direction=-1
            else:
                direction=1

            self.rotation_delta=[0,0,0,0]
            if abs(self.delta_angle) <0.02:
                self.rotation[1]=self.angle_to_player
            elif self.delta_angle<0:
                self.rotation_delta[1]=-self.rotational_speed * direction
            elif self.delta_angle>0:
                self.rotation_delta[1]=+self.rotational_speed * direction
            
        
        #Update angle to player, delta and distance to player.
        dx = (player.coords[0]-(self.nodes_world[20][0]))
        dz = (player.coords[2]-(self.nodes_world[20][2]))
        self.distance_to_player =math.sqrt(dx**2+dz**2)

        self.angle_to_player = math.atan2(dz,dx)
        if self.angle_to_player<0:
            self.angle_to_player += 2*np.pi

        self.delta_angle= self.angle_to_player - self.rotation[1]    

        #Do tank mode specific movments and rotations
        self.fire_counter+=1
        
        if self.tank_mode==0:
            #Used by type 0 tanks - static tank
            pass     

        elif self.tank_mode==1:
            #Used by type 1 ands 3 tanks - move between two points,turn round and return. if hit obstacle turn.
            if self.moving==True:                                                                           #check if moving
                if abs(self.coords_model[0]-self.coords_destination[0])<2:                                  #check if reached destination
                    if abs(self.coords_model[2]-self.coords_destination[2])<2:
                        flipDirection()                                                                     #yes, flip direction
                        if self.tank_type==3 and self.fire_counter>self.fire_probability:                   #type 3 tank can fire when it is turning
                            self.tank_mode=3
                else:
                    if checkCollision():                                                                    #not reached destination, check to see if it hit anything (player or object()
                        flipDirection()                                                                     #yes, flip direction
                        if self.tank_type==3 and self.fire_counter>self.fire_probability:                   #type 3 tank can fire when it is turning
                            self.tank_mode=3   
            else:                                                                                           #tank not moving, must be turning
                current_angle=self.rotation[1]                                   
                if abs(current_angle-self.target_angle) < self.rotational_speed/2:                          #check if it has turned fully turned and enable movement
                    self.rotation[1] = self.target_angle
                    self.rotation_delta=[0,0,0,0]
                    self.coords_delta = self.coords_delta_temp
                    self.moving=True 
                else:                                                                                       #keep turning
                    self.rotation_delta[1] = self.rotational_speed*self.rotational_direction
       
        elif self.tank_mode==2:
            #Used by type 2 tanks - rotate to face player and then maybe fire
            rotate_to_face()
            gun_center = get_gun_center()                                                                   #tank Mode 2, rotate to face player
            if (self.fire_counter>self.fire_probability and abs(self.delta_angle)<self.rotational_speed/2): #possibility of firing
                event_list.append((settings.EVENT_ENEMY_MISSILE,gun_center,self))
        
        elif self.tank_mode==3:                                                                             #rotate to face player and then go back to moving
            #used by type 3 tanks - rotate to face player, fire and then go back to Mode 1
            rotate_to_face()
            if abs(self.delta_angle)<self.rotational_speed/2:
                if self.fire_counter>self.fire_probability:
                    gun_center = get_gun_center()
                    event_list.append((settings.EVENT_ENEMY_MISSILE,gun_center,self))
                    self.fire_counter=0
                else:
                    self.fire_counter+=1
                    if self.fire_counter==100:
                        self.fire_counter=0
                        self.tank_mode=1
        
        
        elif self.tank_mode == 4:
            if self.moving==True:                                                                           #check if alreday moving
                if checkCollision() and self.evasive_move==False:                                           #has tank hit something?
                    self.evasive_move = True                                                                #yes, go into reverse
                    self.evasive_move_count = self.evasive_duration
                    self.coords_delta = np.multiply(self.coords_delta,-1)
                else:                                                                                       #not hit anything, so keep moving
                    if self.evasive_move==True:                                                             #is it reversing? (it hit something earlier)    
                        #if going backwartds to evade carry on for 100 frames
                        self.evasive_move_count= self.evasive_move_count-1                                  #keep going backwards for evasive_duration frames and then go back to moving
                        if self.evasive_move_count<0:
                            self.evasive_move=False
                            self.can_fire = True 
                            self.coords_delta = np.multiply(self.coords_delta,-1)

                    elif abs(self.delta_angle)>self.rotational_speed/2:                                     #moving but not reversing, check if facing player, if not stop and rotate
                        #if not, stop and rotate
                        #self.can_fire = True  
                        self.moving=False
                        self.coords_delta=[0,0,0,0]
                    else:                                                                                   #moving and still facing player
                        #still facing player check and if close stop and fire
                        if self.distance_to_player<self.firing_distance and self.fire_counter>self.fire_probability:
                            gun_center =get_gun_center()
                            event_list.append((settings.EVENT_ENEMY_MISSILE,gun_center,self))
                            self.can_fire=False
                            self.moving=False
            else:                                                                                       #not moving, must be turning
                rotate_to_face()                                                        #if facing player then start moving towards player again.    
                if abs(self.delta_angle)<self.rotational_speed/2:
                    self.coords_delta = [math.cos(self.rotation[1])*self.speed,0,math.sin(self.rotation[1])*self.speed,0]
                    self.moving=True
                          


        #update model for rotation and movement
        self.rotation=np.add(self.rotation,self.rotation_delta)
        self.rotation=self.rotation%(2*np.pi)
        self.coords_model = np.add(self.coords_model,self.coords_delta)

        #rotate tank radar. 
        matrix = mx.rotateYMatrix(self.radar_speed) 
        for node in self.animated_nodes:
            self.nodes_model[node] = self.radar_axis + np.matmul(matrix, self.nodes_model[node]-self.radar_axis)     

        #check how long tank active and if greater time_out - minus level/3, then launch guided missile
        if time.time()-self.create_time >settings.TANK_TIMEOUT-self.number/3:
            self.create_time = time.time()
            self.time_outs+=1
            event_list.append((settings.EVENT_LAUNCH_GM,self.time_outs))
            


        #copy raw model coordinates into world
        self.coords_world = self.coords_model.copy() 

################################################################
## Missile:                                                   ## 
##         Missile object child class                         ##
################################################################
class Missile(GameObject):
    
    def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect=[1.0,1.0,1.0]):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect)
        self.frames = 0
        self.speed = 8
        self.range = 1000 
        self.range_frames= self.range/self.speed
        self.parent = None
        self.static = False
        self.radar_color=(255,0,0)
        self.radar_size=2

    def update(self,objectList,object_library,player,event_list):
        
        def checkCollision():
            missile_left = self.nodes_view.min(axis = 0)[0]
            missile_right = self.nodes_view.max(axis = 0)[0]
            missile_front=self.coords_view[2]+self.xyz_size[2]
            
            #check collision with player
            if self.type == settings.OBJ_ENEMYMISSILE:
                if (missile_right > (player.view_center[0]-5) and missile_left < (player.view_center[0]+5)):
                    if (missile_front < 5 and missile_front >-5):
                        self.is_dead=True
                        event_list.append((settings.EVENT_HIT,None))
                        event_list.append((settings.EVENT_HORIZON_SHAKE,None))
                        return self.is_dead

            #check collison with other objects
            object:GameObject
            for object in objectList:
                if object != self and object.type != settings.OBJ_SHORTBOX and object.type != settings.OBJ_DODO:
                    object_left = object.nodes_view.min(axis = 0)[0]
                    object_right = object.nodes_view.max(axis = 0)[0]
                    object_height = object.coords_world[1]
                    
                    
                    if object.type == settings.OBJ_PYRAMID or object.type ==settings.OBJ_WIDEPYRAMID:
                        width = abs(object_right-object_left)
                        object_left = object_left+width/5
                        object_right = object_right-width/5
                        
                    elif object.type == settings.OBJ_TANK:
                        width= abs(object_right-object_left)
                        object_left = object_left+width/5
                        object_right = object_right-width/5

                    object_front = object.coords_view[2]-abs(object.get_size(object.nodes_view)[2]/2)
                    object_back = object.coords_view[2]+abs(object.get_size(object.nodes_view)[2]/2)
                    
                    if (missile_front >= object_front and missile_front < object_back and object.coords_model[1]>-3):
                        if (missile_right > object_left and missile_left < object_right):
                            volume_adjustment = (self.range_frames-self.frames)/self.range_frames
                            if object.type == settings.OBJ_TANK or object.type == settings.OBJ_FASTTANK or object.type == settings.OBJ_GUIDEDMISSILE or object.type==settings.OBJ_SAUCER:
                                if self.type != settings.OBJ_ENEMYMISSILE:
                                    self.is_dead = True
                                    object.is_dead = True
                                    event_list.append((settings.EVENT_EXPLOSION,object,volume_adjustment))
                                    event_list.append((settings.EVENT_PROJECTILE_IMPACT,self,volume_adjustment))
                                    
                                    event_list.append((settings.EVENT_SOUND_STOP,1))
                                    player.score+=object.points
                                    return self.is_dead
                            elif object.type == settings.OBJ_TALLBOX or object.type == settings.OBJ_PYRAMID or object.type==settings.OBJ_WIDEPYRAMID:
                                if object.is_visible:
                                    self.is_dead = True
                                    event_list.append((settings.EVENT_PROJECTILE_IMPACT,self,volume_adjustment))
                                    return self.is_dead

        #update upject rotation value and xyz position
        self.rotation=np.add(self.rotation,self.rotation_delta)
        self.rotation=self.rotation%(2*np.pi)
        if not checkCollision():
            self.coords_model = np.add(self.coords_model,self.coords_delta)
        
        self.frames+= 1
        if self.frames>self.range_frames:
            self.is_dead = True

        #copy raw model coordinates into world
        self.coords_world = self.coords_model.copy()
        
        

################################################################
## Spatter                                                    ## 
##         Spatter child object                               ##
################################################################
class Spatter(GameObject):

     def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect=[1.0,1.0,1.0]):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect)
        self.counter = 0
        self.animation_delay = 5
        self.frame = 0
        self.parent = None
        self.static = False
        self.radar_color=(0,0,0)
        self.radar_size=2


     def update(self,objectList,object_library,player,event_list):
        self.counter += 1
        if self.counter>self.animation_delay:
            self.is_dead=True
            
            if self.frame == 7:
                self.frame = -1
            frame = self.frame + 1

            new_object = deepcopy(object_library["Spatter"][frame])
            new_object.frame=frame
            new_object.coords_model = deepcopy(self.coords_model)
            new_object.rotation[1] = self.rotation[1]
            new_object.color = self.color
            new_object.radar_color = self.radar_color
            new_object.parent = self.parent
            objectList.append(new_object)
            
        self.coords_delta = self.parent.coords_delta
        #update object rotation value and xyz position
        self.rotation=np.add(self.rotation,self.rotation_delta)
        self.rotation=self.rotation%(2*np.pi)
        self.coords_model = np.add(self.coords_model,self.coords_delta)

        #copy raw model coordinates into world
        self.coords_world = self.coords_model.copy()
        if self.parent.is_dead:
            self.is_dead=True


################################################################
## explosionChunk                                              ## 
##         Spatter child object                               ##
################################################################
class explosionChunk(GameObject):

     def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect=[1.0,1.0,1.0]):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect)
        self.velocity=[0,0,0,0]
        self.static = False
        self.radar_color=(255,0,0)
        self.radar_size=1


     def update(self,objectList,object_library,player,event_list):
        #update x,y,z
        self.coords_model = np.add(self.coords_model,self.velocity)

        #check to see if chunk hits ground
        if self.coords_model[1]>4:
            self.is_dead=True      

        #adjust y velocity for gravity, check terminal velocity
        self.velocity[1] = self.velocity[1]+0.05
        if self.velocity[1]>1.5:
            self.velocity[1]=1.5

        #call parent class update to do rotation etc    
        super().update(objectList,object_library,player,event_list)
            

################################################################
## projectile_impact_explosion                                ## 
##         missile explosion child object                     ##
################################################################
class projectile_impact_explosion(GameObject):

     def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect=[1.0,1.0,1.0]):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect)
        self.counter=0
        self.static = False
        self.radar_color=(255,0,0)
        self.radar_size=1


     def update(self,objectList,object_library,player,event_list):
        self.counter+=1
        #increase size of explosion
        scale_factor = 1+self.counter/100
        matrix = mx.scaleMatrix([scale_factor,scale_factor,scale_factor])
        self.nodes_model = np.dot(self.nodes_model, matrix)

        if self.counter>20:
            self.is_dead=True

        #call parent class update to do rotation etc    
        super().update(objectList,object_library,player,event_list)    


################################################################
## Saucer                             
##                 flying saucer child object                 
################################################################
class Saucer(GameObject):

     def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect=[1.0,1.0,1.0]):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect)
        self.counter=0
        self.time_out = 0
        self.speed = 0
        self.static = False
        self.radar_color=(0,0,0)
        self.radar_size=2


     def update(self,objectList,object_library,player,event_list):
        self.counter+=1

        if self.coords_model[1]== -1:
            self.coords_delta[1] = 0

        if self.counter>self.time_out:
            self.coords_delta[1] = -0.5

        if self.coords_model[1] <- 200:
            self.is_dead=True
            event_list.append((settings.EVENT_SOUND_STOP,2))   

        #call parent class update to do rotation etc    
        super().update(objectList,object_library,player,event_list)
        volume = (200+self.coords_model[1])/200
        event_list.append((settings.EVENT_SOUND_VOLUME,2,volume,volume))   

        

################################################################
## Dodo                            
##                 Elite Dodo child object                 
################################################################
class Dodo(GameObject):

     def __init__(self,name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect=[1.0,1.0,1.0]):
        super().__init__(name, nodes,faces, edges, details, anim, size,coords,coords_delta,rotation_initial,rotation_delta, color, type, aspect)
        self.static = False
        self.radar_color=(0,0,0)
        self.radar_size=0
