import math
import numpy as np
import settings

################################################################
## Player Class                                               
##                                                           
################################################################
class Player:
    def __init__(self):
        self.coords_delta = [0,0,0,0]
        self.pXZSpeed = 2
        self.visibility_threshold = 2000
        self.view_rotation = 0.0
        self.pRotSpeed = 0.004

        self.view_elevation=math.radians(-3)
        self.mvfwd = False
        self.mvbwd = False
        self.mvleft = False
        self.mvright = False
        self.fire = False
        self.launchMissile = False
        self.missile_count = 0
        self.tank_count = 0
        self.active_tank_count = 0
        self.active_explosion_chunks =0
        self.coords = np.array([0,0,0,0]).astype(float)
        self.pOrigin = np.array([0,0,0,0]).astype(float)
        self.lives = 5
        self.score = 0
        self.maxMissiles = 2
        self.missile_range=1000
        self.view_center=[]
        self.high_score = 0
        self.moving= False
        self.was_moving= self.moving

    def update_player(self,objectList,event_list,view_center):
        
        self.moving = False

        if self.mvfwd:
            self.moving = True
            self.mvfwd=False
            dx = self.pXZSpeed*np.sin(self.view_rotation)
            dz = self.pXZSpeed*np.cos(self.view_rotation)
            if(self.checkOKtoMove(dx,dz,objectList,event_list)):
                self.coords[0]+=dx
                self.coords[2]+=dz
            else:
                self.coords[0]-=dx*2
                self.coords[2]-=dz*2
            

        if self.mvbwd:
            self.moving = True
            self.mvbwd=False
            dx = -self.pXZSpeed*np.sin(self.view_rotation)
            dz = -self.pXZSpeed*np.cos(self.view_rotation)
            if(self.checkOKtoMove(dx,dz,objectList,event_list)):
                self.coords[0]+=dx
                self.coords[2]+=dz
            else:
                pass
                self.coords[0]-=dx
                self.coords[2]-=dz
            
        if self.mvleft:
            self.moving = True
            self.view_rotation -= self.pRotSpeed
            self.mvleft = False

        if self.mvright:
            self.moving = True
            self.view_rotation += self.pRotSpeed
            self.mvright=False

        if self.fire:
            event_list.append((settings.EVENT_PLAYER_MISSILE,None))
            self.fire=False   
        
        self.coords_delta = self.pOrigin-self.coords

        if self.was_moving != self.moving:
            if self.moving:
                event_list.append((settings.EVENT_SOUND_VOLUME,7,0.1,0.1))
            else:
                event_list.append((settings.EVENT_SOUND_VOLUME,7,0.0,0.0))
        self.was_moving = self.moving

                
    
    def checkOKtoMove(self,dx,dz,objectList,event_list):
        OKtoMove = True
        x_check = self.coords[0]+dx
        z_check  = self.coords[2]+dz

        for object in objectList:
            if object.type !=settings.OBJ_DODO:
                size = object.size*0.7
                if object.coords_model[0] > x_check-size and object.coords_model[0] < x_check+size:
                    if object.coords_model[2] > z_check-size and object.coords_model[2] < z_check+size:
                        OKtoMove=False
                        event_list.append((settings.EVENT_HORIZON_SHAKE,None))
                        event_list.append((settings.EVENT_SOUND_CRASH,None))    
           
        return OKtoMove                   
