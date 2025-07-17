import numpy as np
import math
import random
from copy import deepcopy
import pygame

import modules.library_builder as lib
import modules.player as player
import modules.objects as objects
import models.raw_wireframes_BZ as rawBZ
import settings
import time

from operator import itemgetter



################################################################
# volcano particle class
##
################################################################
class volcano_particle:
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0


################################################################
# Main Game Class
##
################################################################
class Game:

    STYLE_SHADED = 1
    STYLE_FILLED = 2
    STYLE_HLRWF = 3
    STYLE_WF = 4
    STYLE_DEBUG = 5

    def __init__(self, width, height):
        self.player = player.Player()
        pygame.init()
        
        self.sound_on = True
        self.sound_text = "SOUND IS ON; M TO MUTE"
        self.sounds_init()

        self.render_style = self.STYLE_SHADED
        self.render_style_text = "SHADING; R TO CHANGE"

        self.height = height
        self.width = width
        self.screen = pygame.display.set_mode((width, height))

        # self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        # self.width,self.height = pygame.display.get_window_size()

        self.paused = False
        self.game_over = False
        self.objects = []
        self.event_list = []

        self.reticule1_data = rawBZ.reticule1
        self.reticule2_data = rawBZ.reticule2

        self.view_center = [self.width/2, self.height/2, 0, 0]
        self.player.view_center = self.view_center
        self.collison_view_center=deepcopy(self.view_center)
        self.font = pygame.freetype.Font(None, 12)
        self.font2 = pygame.freetype.Font(None, 20)
        pygame.display.set_caption('BattleZone')
        pygame.key.set_repeat(100, 10)
        self.background_color = (0, 0, 0)
        self.sky_color = (20, 30, 20)

        self.horizon_data = rawBZ.scenary1
        self.create_horizon_bitmap()
        self.horizon_jitter = 0

        self.object_text = ""

        self.clock = pygame.time.Clock()
        self.fps = 60

        self.factor = 3000

        self.radar_theta = 0

        self.object_library = lib.create_object_library()
        self.logo = lib.logo_object(self.object_library)

        self.volcano_particles = [volcano_particle() for i in range(5)]
        

        self.windscreen_frame = 1
        self.windscreen_delay = 200
        self.windscreen_delay_counter = 0
        self.windscreen_data = rawBZ.windscreen
        self.timings = []

        self.title_screen = True
        self.frame_counter = 0
        self.color_counter = 200
        self.color_increment = 5
        self.player.active_tank_count = 0
        self.max_tanks = 1

        self.end_screen=False
        self.scroll_text = "ARROW KEYS TO MOVE; SPACE TO FIRE; P TO PAUSE; M TO MUTE; R TO CHANGE RENDER STYLE"
        self.scroll_pos = 0
        self.start_time = time.time()
    

    ################################################################
    # main loop:
    # Main loop
    ################################################################
    def loop(self):
        self.place_obstacles()

        self.running = True

        while self.running:
            if not self.paused:
                
                self.add_enemy()    
                self.screen.fill(self.background_color)
                
                self.display_horizon(self.player.view_rotation)
                self.display_objects(self.update_z_buffer())

                self.display_radar(x_size=200, range=1000, x_position=self.width /
                                   2-100, y_position=10, display_obstacles=True)
                self.draw_reticule()
                #self.display_debug_text()

                self.display_lives()
                self.display_score()

                self.objects = [
                    object for object in self.objects if object.is_dead != True]

                self.display_proximity()                

                if time.time()-self.start_time > settings.SAUCER_INTERVAL + random.randint(-20,20):
                    self.event_list.append((settings.EVENT_LAUNCH_SAUCER,None))
                    self.start_time=time.time()

                for event in self.event_list:
                    object: objects.GameObject
                    if event[0] == settings.EVENT_HIT:
                        if self.sound_on:
                            pygame.mixer.Channel(8).play(self.hit_ahhh_sound)
                        self.player.lives -= 1
                    elif event[0] == settings.EVENT_LAUNCH_GM:
                        self.launch_guided_missile(event[1])
                    elif event[0] == settings.EVENT_LAUNCH_SAUCER:
                        self.launch_saucer()    
                    elif event[0] == settings.EVENT_PLAYER_MISSILE:
                        self.launch_player_missile()
                    elif event[0] == settings.EVENT_EXPLOSION:
                        object= event[1]    
                        self.add_explosion(object.type, object.coords_model, object.color,event[2])
                    elif event[0] == settings.EVENT_PROJECTILE_IMPACT:
                        object= event[1]  
                        self.add_projectile_impact_explosion(
                            object.coords_model, object.color, object.rotation,event[2])
                    elif event[0] == settings.EVENT_ENEMY_MISSILE:
                        self.launch_enemy_missile(event[1], event[2])
                    elif event[0] == settings.EVENT_GUIDED_M_SPATTER:
                        self.add_guided_missile_ground_spatter(event[1])
                    elif event[0] == settings.EVENT_HORIZON_SHAKE:
                        if self.horizon_jitter == 0:
                            self.horizon_jitter = 11
                    elif event[0] == settings.EVENT_SOUND_STOP:
                        pygame.mixer.Channel(event[1]).stop()
                    elif event[0] == settings.EVENT_SOUND_VOLUME:
                        if self.sound_on:
                            pygame.mixer.Channel(event[1]).set_volume(event[2],event[3])
                    elif event[0] == settings.EVENT_SOUND_CRASH:
                        if self.sound_on:
                            if pygame.mixer.Channel(9).get_busy() == False:
                                pygame.mixer.Channel(9).play(self.crash_sound)      

                self.event_list = []    

                if self.title_screen:
                    self.display_title_screen()
                    self.player.mvright = True
                elif self.end_screen:
                    self.display_end_screen()
                    self.player.mvright = True
                else:    
                    self.get_input()
                    self.render_vector_text(self.sound_text,10,self.height-10,0.4,(0,255,0))
                    self.render_vector_text(self.render_style_text,self.width-350,self.height-10,0.4,(0,255,0))

                self.player.update_player(
                    self.objects, self.event_list, self.view_center)
                
                if self.player.lives<1 and self.title_screen==False and self.end_screen==False:
                    self.end_screen=True
                    self.frame_counter = 0 

                pygame.display.flip()
                self.frame_counter += 1    
                self.clock.tick(self.fps)
            else:
                self.get_input()
    ################################################################
    # update_z_buffer:
    # create depth sorted list of visible objects
    ################################################################

    def update_z_buffer(self):

        zbuffer = []
        object: objects.GameObject
        self.player.missile_count = 0
        self.player.active_tank_count = 0
        self.player.active_explosion_chunks = 0

        for object in self.objects:
            if object.type == settings.OBJ_PLAYERMISSILE:
                self.player.missile_count += 1
            elif object.type==settings.OBJ_FASTTANK or object.type==settings.OBJ_TANK:
                self.player.active_tank_count += 1
            elif object.type==settings.OBJ_CHUNK:
                self.player.active_explosion_chunks += 1

            object.update(self.objects, self.object_library,self.player, self.event_list)
            object.update_view_coords(self.player)
            object.update_view_objects(self.player)
            object.update_perspective(self.view_center, self.factor)
            zbuffer.append((object.coords_view[2], object))
    

        #zbuffer = sorted(zbuffer, key=lambda x: x[0], reverse=True)
        zbuffer.sort(key=itemgetter(0), reverse=True)
        return (zbuffer)

    ################################################################
    # display_objects:
    # update objects, zsort & render
    ################################################################
    def display_objects(self, zbuffer):
        self.plotting = 0
        for zobject in zbuffer:
            object = zobject[1]
            if self.is_visible(object):
                self.plotting += 1
                if object.type == settings.OBJ_PROJECTILE_IMPACT or object.type == settings.OBJ_SPATTER:
                    self.plot_explosion(object)
                elif object.type == settings.OBJ_LOGO:
                    self.plot_logo(object)
                else:
                    self.plot_object(object, self.render_style)

    ###############################################################
    # plot_explosion:
    # render player missile->obstacle explosion
    ###############################################################
    def plot_explosion(self, object: objects.GameObject):
        for node in object.nodes_projected:
            x = node[0]
            y = node[1]
            z = node[2]
            pygame.draw.circle(self.screen, (object.color),
                               (x, y), int(150/z)+1, 0)

    ################################################################
    # plot_object:
    # render polygons based on mean of z
    ################################################################
    def plot_object(self, object: objects.GameObject, style):

        if style == self.STYLE_SHADED:
            polygons = self.z_sort_polygons(object)
            self.draw_shaded(object, polygons)
        elif style == self.STYLE_FILLED:
            polygons = self.z_sort_polygons(object)
            self.draw_filled(object, polygons)
        elif style == self.STYLE_HLRWF:
            polygons = self.z_sort_polygons(object)
            self.draw_hlr_wireframe(object, polygons)
        elif style == self.STYLE_WF:
            polygons = self.z_sort_polygons(object)
            self.draw_wireframe(object, polygons)
        elif style == self.STYLE_DEBUG:
            self.draw_debug(object)

    ################################################################
    # draw_shaded   :
    # draw shaded object
    ################################################################

    def draw_shaded(self, object: objects.GameObject, polygons):

        temp_z = list(list(zip(*polygons))[3])
        max_z = np.max(temp_z)
        min_z = np.min(temp_z)
        if max_z == min_z:
            max_z = min_z + 1
        z_range = max_z - min_z

        shade_adjust = object.SHADING/z_range
        shade_range = np.multiply(object.color, shade_adjust)

        for polygon in polygons:
            xy_data = polygon[1]
            if polygon[2]:  # only plot clockwise = True
                depth = max_z-polygon[3]  # maxZ - mean_z for this polygon
                shade_add = np.multiply(shade_range, depth)
                color = np.add(object.color_base, shade_add)
                z_adjust = 1-1 / (self.player.visibility_threshold)*polygon[3]*0.4
                color = np.multiply(color, z_adjust)
                pygame.draw.polygon(self.screen, color, xy_data, 0)
                pygame.draw.aalines(
                    self.screen, self.background_color, True, xy_data, 1)

    ################################################################
    # draw_filled   :
    # draw filled Object
    ################################################################
    def draw_filled(self, object: objects.GameObject, polygons):

        for polygon in polygons:
            xy_data = polygon[1]
            if polygon[2]:
                z_adjust = 1-1/self.player.visibility_threshold*polygon[0]*0.4
                color = np.multiply(object.color, z_adjust)
                pygame.draw.polygon(
                    self.screen, self.background_color, xy_data, 0)
                pygame.draw.aalines(self.screen, color, True, xy_data, 2)

    ################################################################
    # draw_hlr_wireframe   :
    # draw wireframe with hidden lines removed
    ################################################################
    def draw_hlr_wireframe(self, object: objects.GameObject, polygons):

        for polygon in polygons:
            xy_data = polygon[1]
            if polygon[2]:
                z_adjust = 1-1/self.player.visibility_threshold*polygon[0]*0.4
                color = np.multiply(object.color, z_adjust)
                pygame.draw.aalines(self.screen, color, True, xy_data, 1)

    ################################################################
    # draw_wireframe   :
    # draw classic vector wireframe
    ################################################################
    def draw_wireframe(self, object: objects.GameObject, polygons):

        for polygon in polygons:
            xy_data = polygon[1]
            z_adjust = 1-0.7/self.player.visibility_threshold*polygon[0]*0.4
            color = np.multiply(object.color, z_adjust)
            glow_color = np.multiply(color, 0.5)
            pygame.draw.lines(self.screen, glow_color, True, xy_data, 2)
            pygame.draw.aalines(self.screen, color, True, xy_data, 1)

    ################################################################
    # draw_debug   :
    # draw filled Object with Debug data
    ################################################################
    def draw_debug(self, object: objects.GameObject):

        if len(object.faces) > 0:
            polygons = self.z_sort_polygons(object)
            self.draw_shaded(object, polygons)

            for i, polygon in enumerate(polygons):
                xy_data = polygon[1]

                if polygon[2]:
                    text = str(i)
                else:
                    text = ""

                x = 0
                y = 0
                for node in xy_data:
                    x += node[0]
                    y += node[1]
                x = x/len(xy_data)
                y = y/len(xy_data)

                plot = (x, y)
                self.font.render_to(self.screen, (plot), text, (255, 255, 255))

        if len(object.edges) > 0:
            for edge in object.edges:
                x1 = object.nodes_projected[edge[0], 0]
                y1 = object.nodes_projected[edge[0], 1]
                x2 = object.nodes_projected[edge[1], 0]
                y2 = object.nodes_projected[edge[1], 1]

                pygame.draw.aaline(
                    self.screen, object.color, (x1, y1), (x2, y2))

            for i, node in enumerate(object.nodes_projected):
                x_plot = int(node[0])
                y_plot = int(node[1])
                x = int(object.nodes_model[i, 0])
                y = int(object.nodes_model[i, 1])
                z = int(object.nodes_model[i, 2])
                # text = str(x)+", "+str(y)+", "+str(z)
                text = str(i)
                self.font2.render_to(
                    self.screen, (x_plot, y_plot), text, (100, 100, 255))

    ################################################################
    # z_sort_polygons   :
    # zSort, determine CWSise and add detail layers
    ################################################################
    def z_sort_polygons(self, object: objects.GameObject):
        polygons = []
        for polygon in object.faces:
            xy_data = []
            z_data = []
            for node in polygon:
                z_data.append(object.nodes_view[node, 2])
                xy_data.append(
                    (object.nodes_projected[node, 0], object.nodes_projected[node, 1]))

            # back surface cull based on rotation of nodes
            clockwise = True
            if len(object.faces) > 1:
                x0 = xy_data[0][0]
                y0 = xy_data[0][1]
                x1 = xy_data[1][0]
                y1 = xy_data[1][1]
                x2 = xy_data[2][0]
                y2 = xy_data[2][1]
                cp = (x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)
                if cp > 0:
                    clockwise = False

            mean_z = np.mean(z_data)
            polygons.append((mean_z, xy_data, clockwise, mean_z))

        # add detail, must have lower mean_z than substrate poly to be always visible
        if len(object.details) > 0:
            self.add_detail_polygons(object, polygons)

        # polygons = sorted(polygons, key = lambda x: x[1],reverse=True)
        return (sorted(polygons, reverse=True))

    ################################################################
    # add_detail_polygons:
    # adjust surface level details so Z<than substrate layer
    ################################################################
    def add_detail_polygons(self, object: objects.GameObject, polygons):

        for detail in object.details:
            detail_polygon = detail[0]
            substrate_polygon = detail[1]

            mean_z = polygons[substrate_polygon][0]
            xy_data = polygons[detail_polygon][1]
            clockwise = polygons[detail_polygon][2]

            polygons.insert(detail_polygon+1, (mean_z-0.01,
                            xy_data, clockwise, mean_z))
            polygons.pop(detail_polygon)

    ################################################################
    # is_visible:
    # check if object is within field of view
    ################################################################
    def is_visible(self, object: objects.GameObject):

        x = object.coords_view[0]
        y = object.coords_view[1]
        z = object.coords_view[2]
        size = object.xyz_size[0]/2*self.factor/z

        if z < 0.01:
            object.is_visible = False
            return False
        elif z > self.player.visibility_threshold:
            object.is_visible = False
            return False
        elif (x-self.width/2+size) < (-self.width*z/(1.5*self.factor)):
            object.is_visible = False
            return False
        elif (x-self.width/2-size) > (self.width*z/(1.5*self.factor)):
            object.is_visible = False
            return False
        elif abs(y-self.height/2) > (self.height*z/(0.8*self.factor)):
            object.is_visible = False
            return False
        else:
            object.is_visible = True
            return True

    ################################################################
    # display_radar:
    # render radar plot
    ################################################################
    def display_radar(self, x_size, range, x_position, y_position, display_obstacles):
       
        y_size = x_size
        magnification_factor = x_size/(range*2)
        x_center = x_size/2
        y_center = y_size/2

        radar_view = pygame.Surface((x_size, y_size))
        radar_view.fill(self.sky_color)
        radar_view.set_colorkey(self.sky_color)
        for object in self.objects:
            object: objects.GameObject
            
            if object.type != settings.OBJ_SHORTBOX and object.type != settings.OBJ_TALLBOX and object.type != settings.OBJ_PYRAMID and object.type != settings.OBJ_DODO and object.type != settings.OBJ_WIDEPYRAMID:
                is_obstacle= False
            else:
                is_obstacle=True
                         
            
            if display_obstacles == True or is_obstacle== False:
                x = (object.coords_view[0] -
                     self.view_center[0])*magnification_factor
                y = object.coords_view[2]*-magnification_factor
                object_theta = np.pi+math.atan2(-y, -x)

                distance_from_center = (x**2 + y**2)**0.5    
                x = int(x + x_center)
                y = int(y + y_center)
                
                
                if is_obstacle==False and distance_from_center <x_size/2:
                    abs_delta =object_theta - self.radar_theta 
                    if abs_delta <0.07 and abs_delta>0:
                        if self.sound_on:
                            self.channel_6.stop()
                            self.channel_6.set_volume(0.1,0.1)
                            self.channel_6.play(self.radar_sound)
                            

               

                delta_theta = min((2 * np.pi) - abs(object_theta -
                                  self.radar_theta), abs(object_theta - self.radar_theta))
                radar_arc = math.radians(45)
                color_base = 0.6

           

                if delta_theta > radar_arc:
                    color = np.multiply(object.radar_color, color_base)
                else:
                    coloradjust = np.multiply(
                        object.radar_color, ((1-color_base)*delta_theta/radar_arc))
                    color = np.subtract(object.radar_color, coloradjust)


                size = object.radar_size
                
                pygame.draw.circle(radar_view, color, (x, y), size)

        radius = 0.95*x_size/2
        X = x_center + radius*math.cos(self.radar_theta)
        Y = y_center + radius*math.sin(self.radar_theta)

        color = (255, 0, 0)
        # draw radar sweep
        pygame.draw.aaline(radar_view, (255, 0, 0),
                           (x_center, y_center), (X, Y))

        # draw field of view lines
        pygame.draw.line(radar_view, (50, 0, 0),
                         (x_center, y_center), (75, 0), 5)
        pygame.draw.line(radar_view, (50, 0, 0),
                         (x_center, y_center), (x_size-75, 0), 5)
        pygame.draw.aaline(radar_view, (150, 0, 0),
                           (x_center, y_center), (75, 0))
        pygame.draw.aaline(radar_view, (150, 0, 0),
                           (x_center, y_center), (x_size-75, 0))

        # draw mask and outer circle
        pygame.draw.circle(radar_view, (self.sky_color),
                           (x_center, y_center), x_center+50, 50)
        pygame.draw.circle(radar_view, (100, 0, 0),
                           (x_center, y_center), x_center, 5)
        pygame.draw.circle(radar_view, (255, 0, 0),
                           (x_center, y_center), x_center, 1)

        # draw player
        pygame.draw.rect(radar_view, (255, 0, 0),
                         ((x_center-1, y_center-1), (2, 2)))

        self.screen.blit(radar_view, (x_position, y_position))
        self.radar_theta = (self.radar_theta+0.05) % (2*np.pi)

    ################################################################
    # display_horizon:
    # display Horizon
    ################################################################
    def display_horizon(self, view_rotation):

        increment = self.horizon_bitmap_width/(2 * np.pi)
        rotation = view_rotation % (2 * np.pi)
        y_start = self.y_screen_center - self.horizon_bitmap_height
        y_end = self.horizon_bitmap_height
        plot_start_x = int(increment * rotation)

        self.jitter_offset = 0

        if self.horizon_jitter > 0:

            if self.horizon_jitter % 2 == 0:
                self.jitter_offset = 10
            else:
                self.jitter_offset = 0
                
            self.horizon_jitter = self.horizon_jitter-1
            #self.collison_view_center[1] = self.view_center[1]+self.jitter_offset

        y_start = y_start - self.jitter_offset
        

        # do we need to wrap round and add from start of bitmap
        remaining_horizon = self.horizon_bitmap_width - plot_start_x

        if remaining_horizon < self.width:
            wrap_around = True
            x1_start = 0
            width1 = remaining_horizon
            x2_start = remaining_horizon
            width2 = self.width - remaining_horizon
        else:
            wrap_around = False
            x1_start = 0
            x2_start = None
            width1 = self.width
            width2 = None

        pygame.draw.rect(self.screen, (self.sky_color), ((
            0, 0), (self.width, self.y_screen_center-self.jitter_offset)))
        pygame.draw.line(self.screen, (0, 100, 0), (0, self.y_screen_center -
                         self.jitter_offset), (self.width, self.y_screen_center-self.jitter_offset), 4)
        pygame.draw.aaline(self.screen, (0, 255, 0), (0, self.y_screen_center -
                           self.jitter_offset), (self.width, self.y_screen_center-self.jitter_offset))

        if not wrap_around:
            self.screen.blit(self.horizon_bitmap, (x1_start,
                             y_start), ((plot_start_x, 0), (width1, y_end)))
        else:
            self.screen.blit(self.horizon_bitmap, (x1_start,
                             y_start), ((plot_start_x, 0), (width1, y_end)))
            self.screen.blit(self.horizon_bitmap, (x2_start,
                             y_start), ((0, 0), (width2, y_end)))

        self.update_volcano()

        if (plot_start_x > 2900 and plot_start_x < 4900):
            self.draw_volcano(plot_start_x)

    ################################################################
    # update_volcano      :
    # create new particles, adjust velcocity, kill particles
    ################################################################

    def update_volcano(self):
        particle: volcano_particle
        for particle in self.volcano_particles:
            if particle.active:
                particle.y = particle.y + particle.velocity_y
                particle.x = particle.x + particle.velocity_x
                particle.velocity_y = particle.velocity_y+0.1
                if particle.velocity_y > 5:
                    particle.velocity_y = 5
                if particle.y > 140:
                    particle.active = False
            else:
                activate = random.randrange(50)
                if activate < 1:
                    particle.active = True
                    particle.x = 0
                    particle.y = 0
                    particle.velocity_x = random.uniform(-1.5, 1.5)
                    particle.velocity_y = random.uniform(-3, -6)

    ################################################################
    # draw_volcano:
    # draw active volcano partticles
    ################################################################
    def draw_volcano(self, plot_start_x):
        particle: volcano_particle
        x_offset = 4595-plot_start_x
        y_offset = self.y_screen_center-140

        for particle in self.volcano_particles:
            if particle.active:
                pygame.draw.circle(self.screen, (0, 200, 0),
                                   (x_offset+particle.x, y_offset+particle.y), 2)

    ################################################################
    # create_horizon_bitmap:
    # create bit map of emntire horizon
    ################################################################

    def create_horizon_bitmap(self):

        x_mag = 1.5
        y_mag = x_mag
        self.horizon_bitmap = pygame.Surface((4096*x_mag, 164*y_mag))
        self.horizon_bitmap.fill((self.sky_color))

        x_start = 0
        y_start = self.horizon_bitmap.get_height()

        for i in range(0, len(self.horizon_data)):
            instruction = self.horizon_data[i]
            if instruction[2] == 0:
                x_start = x_start+instruction[0]*x_mag
                y_start = y_start-instruction[1]*y_mag
            else:
                # plot a point
                xend = x_start+instruction[0]*x_mag
                yend = y_start-instruction[1]*y_mag
                color = (0, instruction[2]*18, 0)
                glow_color = np.multiply(color, 0.5)
                pygame.draw.line(self.horizon_bitmap, (glow_color),
                                 (x_start, y_start), (xend, yend), 4)
                pygame.draw.aaline(self.horizon_bitmap, (color),
                                   (x_start, y_start), (xend, yend))
                x_start = xend
                y_start = yend

        self.y_screen_center = self.height/2
        self.horizon_bitmap_width = self.horizon_bitmap.get_width()
        self.horizon_bitmap_height = self.horizon_bitmap.get_height()

    ################################################################
    # draw_reticule       :
    # add gun sights to screen
    ################################################################
    def draw_reticule(self):

        x_mag = 1
        y_mag = x_mag
        x_start = self.width/2
        y_start = self.height/2

        if self.is_in_target():
            reticule_data = self.reticule2_data
        else:
            reticule_data = self.reticule1_data

        for i in range(0, len(reticule_data)):
            instruction = reticule_data[i]
            if instruction[2] == 0:
                x_start = x_start+instruction[0]*x_mag
                y_start = y_start-instruction[1]*y_mag
            else:
                # plot a point
                xend = x_start+instruction[0]*x_mag
                yend = y_start-instruction[1]*y_mag
                color = (0, instruction[2]*18, 0)
                pygame.draw.line(self.screen, (color),
                                 (x_start, y_start), (xend, yend), 2)
                x_start = xend
                y_start = yend

    ################################################################
    # checkTarget       :
    # is there a tank in the reticule?
    ################################################################

    def is_in_target(self):

        reticule_left = -0.5+self.width/2
        reticule_right = 0.5+self.width/2
        object: objects.GameObject
        for object in self.objects:
            if object.is_visible and object.type == settings.OBJ_TANK:
                object_left = object.nodes_view.min(axis=0)[0]
                object_right = object.nodes_view.max(axis=0)[0]
                if (reticule_right > object_left and reticule_left < object_right):
                    return True

        return False

    ################################################################
    # adddebugText:
    # add debug text to screen
    ################################################################
    def display_debug_text(self):
        # debug text - remove
        self.object_text = "Debug Data |"
        # self.object_text+="x_player:"+str(int(self.player.coords[0]))+"|"
        # self.object_text+="PLayerY:"+str(int(self.player.coords[1]))+"|"
        # self.object_text+="z_player:"+str(int(self.player.coords[2]))+"|"
        # self.object_text+="Rotation:"+str(int(np.degrees(self.player.view_rotation)%360))+"|"
        # self.object_text+="|"
        # self.object_text+="Model X:"+str(int(self.objects[0].coords_model[0])) +"|"
        # self.object_text+="Model Y:"+str(int(self.objects[0].coords_model[1])) +"|"
        # self.object_text+="Model Z:"+str(int(self.objects[0].coords_model[2])) +"|"
        # self.object_text+="|"
        # self.object_text+="World X:"+str(int(self.objects[0].coords_world[0])) +"|"
        # self.object_text+="World Y:"+str(int(self.objects[0].coords_world[1])) +"|"
        # self.object_text+="World Z:"+str(int(self.objects[0].coords_world[2])) +"|"
        # self.object_text+="|"
        # self.object_text+="View X:"+str(int(self.objects[0].coords_view[0])) +"|"
        # self.object_text+="View Y:"+str(int(self.objects[0].coords_view[1])) +"|"
        # self.object_text+="View Z:"+str(int(self.objects[0].coords_view[2])) +"|"
        # self.object_text+="|"
        # self.object_text+="delta X:"+str(int(self.objects[0].coords_world[0]-self.player.coords[0]))+"|"
        # self.object_text+="delta Z:"+str(int(self.objects[0].coords_world[2]-self.player.coords[2]))+"|"

        # self.object_text+="|"

        # self.object_text+="angle1:"+str(self.objects[0].angle1)+"|"
        # self.object_text+="angle2:"+str(self.objects[0].angle2)+"|"
        self.object_text += "FPS:"+str(int(self.clock.get_fps()))+"|"
        self.object_text += "plotting:"+str(self.plotting)+"|"
        self.object_text += "|"
        self.object_text += "Missile Active " + \
            str(self.player.missile_count) + "|"
        self.object_text += "Lives "+str(self.player.lives) + "|"
        self.object_text += "Enemies "+str(self.player.active_tank_count) + "|"

        self.object_text += "Timer "+str(int(time.time()-self.start_time)) + "|"

        self.render_text(self.object_text, self.width-120, 100)

    ################################################################
    # render_text:
    # render text at X,Y, color, size
    ################################################################
    def render_text(self, text, x, y):

        lines = text.split('|')
        for line in lines:
            self.font.render_to(self.screen, (x, y), line, (255, 255, 255))
            y += 15

    ################################################################
    # get_input:
    # get Keyboard input
    ################################################################

    def get_input(self):

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.fire = True

                elif event.key == pygame.K_p:
                    self.paused = not self.paused

                elif event.key == pygame.K_m:
                    self.sound_on = not self.sound_on
                    if self.sound_on:
                        self.sound_text = "SOUND IS ON; M TO MUTE"
                        self.channel_10.play(self.ambient_sound, loops=-1)
                        self.channel_7.set_volume(0.0,0.0)
                        self.channel_7.play(self.tank_sound, loops=-1)
                    else: 
                       self.sound_text = "SOUND IS OFF; M TO UNMUTE"
                       pygame.mixer.fadeout(1000)    
                elif event.key == pygame.K_r:
                    self.render_style+= 1
                    if self.render_style > self.STYLE_WF:
                        self.render_style = self.STYLE_SHADED
                    if self.render_style == self.STYLE_SHADED:
                        self.render_style_text = "SHADING"
                    elif self.render_style == self.STYLE_FILLED:
                        self.render_style_text = "FILLED"
                    elif self.render_style == self.STYLE_HLRWF:
                        self.render_style_text = "HIDDEN LINE REMOVAL"
                    elif self.render_style == self.STYLE_WF:
                        self.render_style_text = "SIMPLE VECTOR"
                    self.render_style_text += "; R TO CHANGE"        
        if keys[pygame.K_UP]:   
            self.player.mvfwd = True
        elif keys[pygame.K_DOWN]:
            self.player.mvbwd = True

        if keys[pygame.K_LEFT]:
            self.player.mvleft = True
        elif keys[pygame.K_RIGHT]:
            self.player.mvright = True

           

    ################################################################
    # launch_guided_missile:
    # launch a Guided Missile (enemy)
    ################################################################

    def launch_guided_missile(self,time_outs):
        new_object: objects.GuidedMissile
        new_object = deepcopy(self.object_library["GuidedMissile"])
        new_object.color = (0, 255, 255)
        new_object.radar_color = new_object.color
        angle = self.player.view_rotation
        new_object.rotation[1] = -angle
        new_object.rotation_delta = [0.0, 0.0, 0, 0]
        new_object.coords_model[0] = self.player.coords[0]+600*np.sin(angle)
        new_object.coords_model[1] = -60
        new_object.coords_model[2] = self.player.coords[2]+600*np.cos(angle)
        new_object.coords_delta = [0, 0.5, 0, 0]
        new_object.time_out = 2000
    
        
        if self.player.tank_count<10 and time_outs==1:
            new_object.mode = 1
            new_object.points = 2000
            new_object.counter = 0
        elif self.player.tank_count<20 or time_outs==2:
            new_object.mode = 3
            new_object.points = 3000
            new_object.counter = new_object.mode3_length/2
        else:
            new_object.mode =2
            new_object.points = 5000
            new_object.counter = 0

        new_object.speed = 4+time_outs
        new_object.mode3_length = 18
        

        new_object.name = "GuidedMissile"
        self.objects.append(new_object)
        if self.sound_on:
            self.channel_5.play(self.warning_sound)

    ################################################################
    # launch_saucer:
    # launch a Guided Missile (enemy)
    ################################################################

    def launch_saucer(self):
        new_object: objects.Saucer
        new_object = deepcopy(self.object_library["Saucer"])
        new_object.speed = 1
        new_object.color = [255, 255, 0]
        new_object.radar_color = new_object.color
        new_object.points = 7500

        left_or_right = random.randint(1, 2)
        if left_or_right == 1:
            direction = 1
        else:
            direction = -1

        angle = self.player.view_rotation-np.pi/4*direction

        new_object.coords_model[0] = self.player.coords[0]+800*np.sin(angle)
        new_object.coords_model[1] = -200
        new_object.coords_model[2] = self.player.coords[2]+800*np.cos(angle)

        angle = self.player.view_rotation-np.pi/2*direction
        new_object.coords_delta[0] = -new_object.speed*np.sin(angle)
        new_object.coords_delta[1] = 0.5
        new_object.coords_delta[2] = -new_object.speed*np.cos(angle)

        new_object.rotation_delta = [0.0, 0.05, 0, 0]
        new_object.time_out = 1200
        new_object.name = "Saucer"

        self.channel_2.set_volume(0)
        if self.sound_on:
            self.channel_2.play(self.saucer_sound,loops=-1)
        self.objects.append(new_object)

    ################################################################
    # launch_player_missile:
    # launch a player Missile
    ################################################################

    def launch_player_missile(self):

        if self.player.missile_count < self.player.maxMissiles:
            new_object: objects.Missile
            angle = self.player.view_rotation
            new_object = deepcopy(self.object_library["Missile"])
            new_object.speed = 6
            new_object.range = self.player.missile_range
            new_object.range_frames = new_object.range/new_object.speed
            dx = new_object.speed*np.sin(angle)
            dz = new_object.speed*np.cos(angle)
            new_object.coords_delta = [dx, 0.0, dz, 0]
            new_object.type = settings.OBJ_PLAYERMISSILE
            new_object.coords_model[0] = self.player.coords[0]+dx
            new_object.coords_model[1] = 0
            new_object.coords_model[2] = self.player.coords[2]+dz
            new_object.rotation[1] = -angle
            
            self.objects.append(new_object)
            if self.sound_on:
                self.channel_1.play(self.player_missile_sound)
    ################################################################
    # launch_enemy_missile:
    # launch a enemy Missile
    ################################################################
    def launch_enemy_missile(self, gun_center, parent):

        angle = parent.rotation[1]-math.radians(90)

        new_object: objects.Missile
        new_object = deepcopy(self.object_library["Missile"])
        new_object.type = settings.OBJ_ENEMYMISSILE
        new_object.speed = 10
        new_object.range = parent.missile_range
        new_object.range_frames = new_object.range/new_object.speed
        dx = -new_object.speed*np.sin(angle)
        dz = new_object.speed*np.cos(angle)
        new_object.coords_delta = [dx, 0, dz, 0]
        new_object.color = parent.color
        new_object.coords_model[0] = gun_center[0]
        new_object.coords_model[1] = 0
        new_object.coords_model[2] = gun_center[2]
        new_object.rotation[1] = angle
        new_object.parent = parent
        parent.fire_counter = 0
      

        self.objects.append(new_object)
        if self.sound_on:
            self.channel_4.play(self.enemy_missile_sound)


    ################################################################
    # add_guided_missile_ground_spatter
    # add ground effect for GM Missile
    ################################################################
    def add_guided_missile_ground_spatter(self, parent):

        parent: objects.GameObject
        coords = parent.coords_model
        color = parent.color

        new_object = deepcopy(self.object_library["Spatter"][0])
        new_object.rotaion = parent.rotation
        new_object.coords_model[0] = coords[0]
        new_object.coords_model[1] = coords[1]+5
        new_object.coords_model[2] = coords[2]
        new_object.color = color
        new_object.radar_color = color
        new_object.parent = parent

        self.objects.append(new_object)

    ################################################################
    # add_explosion
    # add explosion when player missile hits enemy
    ################################################################
    def add_explosion(self, type, coords, color,volume):
        volume = 0.2 + volume * 0.8
        
        if type == settings.OBJ_TANK:
            chunks = [0, 1, 2, 3, 1, 0]
            if self.sound_on:
                self.channel_3.set_volume(volume, volume)
                self.channel_3.play(self.tank_explode_sound)
        elif type == settings.OBJ_FASTTANK:
            chunks = [0, 1, 2, 1, 1, 0]
            if self.sound_on:
                self.channel_3.set_volume(volume, volume)
                self.channel_3.play(self.tank_explode_sound)
        elif type == settings.OBJ_GUIDEDMISSILE:
            chunks = [1, 4, 0, 5, 0, 4]
            if self.sound_on:
                self.channel_5.set_volume(volume, volume)
                self.channel_5.play(self.guidedm_explode_sound)
        elif type == settings.OBJ_SAUCER:
            chunks = [1, 4, 0, 5, 0, 4, 1, 4, 0, 5, 0, 4]
            if self.sound_on:
                self.channel_2.set_volume(volume, volume)
                self.channel_2.play(self.saucer_explode_sound)

        for chunk in chunks:
            self.add_explosion_chunk(chunk, coords, color)

    ################################################################
    # add_explosion_chunk
    # add specific explosion chunk to object lis
    ################################################################
    def add_explosion_chunk(self, chunk, coords, color):
        new_object: objects

        new_object = deepcopy(self.object_library["Explosion_chunks"][chunk])

        random_xyz = [
            random.uniform(-10, 10), random.uniform(-5, 5), random.uniform(-10, 10), 0]
        new_object.coords_model = np.add(coords, random_xyz)

        new_object.velocity = [
            random.uniform(-1, 1), random.uniform(-2, -0.5), random.uniform(-1, 1), 0]
        new_object.rotation_delta = [
            random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), 0]
        new_object.color = color

        self.objects.append(new_object)

    ################################################################
    # addprojectile explosion
    # explosion when player missile hits obstacle
    ################################################################
    def add_projectile_impact_explosion(self, coords, color, rotation,volume):
        volume = volume * 0.3
        new_object = deepcopy(self.object_library["Projectile_explosion"])
        new_object.coords_model = coords
        new_object.color = color
        new_object.rotation[1] = rotation[1]
        self.objects.append(new_object)

        if self.sound_on:
                self.channel_0.set_volume(volume, volume)
                self.channel_0.play(self.projectile_impact_sound)


    ################################################################
    # place_obstacles
    # place obstacles in game
    ################################################################
    def place_obstacles(self):
        for i in range(0, 30):
            newObstacle: objects.GameObject
            newObstacle = deepcopy(self.object_library["TallBox"])
            newObstacle.coords_model[0] = random.uniform(-2000, 2000)
            newObstacle.coords_model[2] = random.uniform(-2000, 2000)
            newObstacle.rotation[1] = random.uniform(-np.pi, np.pi)
            newObstacle.rotate_y()
            newObstacle.name = "Tallbox_"+str(i)
            self.objects.append(newObstacle)

        for i in range(0, 30):
            newObstacle: objects.GameObject
            newObstacle = deepcopy(self.object_library["ShortBox"])
            newObstacle.coords_model[0] = random.uniform(-2000, 2000)
            newObstacle.coords_model[2] = random.uniform(-2000, 2000)
            newObstacle.rotation[1] = random.uniform(-np.pi, np.pi)
            newObstacle.rotate_y()
            newObstacle.name = "ShortBox_"+str(i)
            self.objects.append(newObstacle)

        for i in range(0, 30):
            newObstacle: objects.GameObject
            newObstacle = deepcopy(self.object_library["Pyramid"])
            newObstacle.coords_model[0] = random.uniform(-1000, 1000)
            newObstacle.coords_model[2] = random.uniform(-1000, 1000)
            newObstacle.rotation[1] = random.uniform(-np.pi, np.pi)
            newObstacle.rotate_y()
            newObstacle.name = "Pyramid_"+str(i)
            self.objects.append(newObstacle)

        for i in range(0, 30):
            newObstacle: objects.GameObject
            newObstacle = deepcopy(self.object_library["WidePyramid"])
            newObstacle.coords_model[0] = random.uniform(-2000, 2000)
            newObstacle.coords_model[2] = random.uniform(-2000, 2000)
            newObstacle.rotation[1] = random.uniform(-np.pi, np.pi)
            newObstacle.rotate_y()
            newObstacle.name = "WidePyramid_"+str(i)
            self.objects.append(newObstacle)

        newDodo: objects.GameObject
        newDodo = deepcopy(self.object_library["Dodo"])
        newDodo.coords_model[0] = 0
        newDodo.coords_model[1] = -100
        newDodo.coords_model[2] = 0
        newDodo.name = "Dodo"
        newDodo.rotation_delta = [0.01, 0.01, -0.01, 1]
        self.objects.append(newDodo)

    ################################################################
    # add_enemy
    # manage addition of enemy tanks, missiles and saucers
    ################################################################
    def add_enemy(self):

        if self.player.tank_count>40:
            self.max_tanks = 3
        elif self.player.tank_count>30:
            self.max_tanks = 2     
        
        if self.player.active_tank_count < self.max_tanks and self.player.active_explosion_chunks < 1:
            if self.player.tank_count<5:
                # first 5 levels add simple tank that is either static or moves but does not fire
                if random.randrange(0,10)<2:
                    self.add_tank(0)
                else:
                    self.add_tank(1)
            elif self.player.tank_count<20:
                #next 15 levels add some tanks that can fire (type 2 and 3)
                difficulty = random.randrange(10)
                if difficulty<2:
                    self.add_tank(1)
                elif difficulty<4:
                    self.add_tank(2)
                else:
                    self.add_tank(3)        
            else:
                #all tanks now fire and move
                difficulty=random.randrange(10)
                if difficulty<7:
                    self.add_tank(3)
                else:
                    self.add_tank(4)    
                    
            self.player.tank_count+=1


    ################################################################
    # add_tank
    # adds tank based on type
    # 0 = not move,random rotate, not fire                      
    # 1 = move between two points, not fire                     
    # 2 = not move, rotate to face and fire                     
    # 3 = move between points, maybe rotate abnd fire         
    # 4 = Fast tank, hunt and fire      
    ################################################################    
    def add_tank(self,type):
        newTank:objects.Tank
        newTank = deepcopy(self.object_library["Tank"])
        
        if random.uniform(-1, 1) > 0:
            xdirection = 1
        else:
            xdirection = -1

        if random.uniform(-1, 1) > 0:
            zdirection = 1
        else:
            zdirection = -1
        
        newTank.coords_model[0] = self.player.coords[0]+random.uniform(300, 450)*xdirection
        newTank.coords_model[2] = self.player.coords[0]+random.uniform(300, 450)*zdirection
        newTank.name = "Tank" + str(newTank.tank_type)
        newTank.number = self.player.tank_count+1
        newTank.speed  = 0.5 + self.player.tank_count/20

        if type==0:
            newTank.rotation[1] = random.uniform(-np.pi, np.pi)
            newTank.rotation_delta = [0, random.uniform(-0.01, 0.01), 0, 0]
            newTank.tank_type = 0
            newTank.tank_mode = 0
            newTank.points = 1000
        
        elif type==1:
            newTank.coords_start = newTank.coords_model

            if random.uniform(-1, 1) > 0:
                xdirection = 1
            else:
                xdirection = -1

            if random.uniform(-1, 1) > 0:
                zdirection = 1
            else:
                zdirection = -1

            if random.uniform(-1, 1) > 0:
                newTank.rotational_direction = 1
            else:
                newTank.rotational_direction = -1

            newTank.coords_destination[0] = newTank.coords_model[0] + random.uniform(150, 500)*xdirection
            newTank.coords_destination[2] = newTank.coords_model[2] + random.uniform(150, 500)*zdirection
            dx = newTank.coords_destination[0]-newTank.coords_model[0]
            dz = newTank.coords_destination[2]-newTank.coords_model[2]
            newTank.rotation[1] = math.atan2(dz, dx)
            newTank.coords_delta = [math.cos(newTank.rotation[1])*newTank.speed, 0, math.sin(newTank.rotation[1])*newTank.speed, 0]
            newTank.rotational_speed = 0.033
            newTank.fire_probability = 1e55
            newTank.tank_type = 1
            newTank.tank_mode = 1
            newTank.moving = True
            newTank.points = 1500
        elif type==2:
            newTank.rotation[1] = random.uniform(-np.pi, np.pi)
            newTank.rotational_speed = 0.033
            newTank.fire_probability = 500
            newTank.tank_type = 2
            newTank.tank_mode = 2
            newTank.points = 1500
        elif type==3:
            newTank.coords_start = newTank.coords_model
            
            if random.uniform(-1, 1) > 0:
                xdirection = 1
            else:
                xdirection = -1

            if random.uniform(-1, 1) > 0:
                zdirection = 1
            else:
                zdirection = -1

            if random.uniform(-1, 1) > 0:
                newTank.rotational_direction = 1
            else:
                newTank.rotational_direction = -1

            newTank.coords_destination[0] = newTank.coords_model[0] + random.uniform(150, 500)*xdirection
            newTank.coords_destination[2] = newTank.coords_model[2] + random.uniform(150, 500)*zdirection
            dx = newTank.coords_destination[0]-newTank.coords_model[0]
            dz = newTank.coords_destination[2]-newTank.coords_model[2]
            newTank.rotation[1] = math.atan2(dz, dx)
            newTank.coords_delta = [math.cos(newTank.rotation[1])*newTank.speed, 0, math.sin(newTank.rotation[1])*newTank.speed, 0]
            newTank.rotational_speed = 0.033
            newTank.fire_probability = 100
            newTank.tank_type = 3
            newTank.tank_mode = 1
            newTank.moving = True
            newTank.points = 2000
        elif type==4:
            newTank = deepcopy(self.object_library["FastTank"])
            newTank.rotation[1] = random.uniform(-np.pi, np.pi)
            newTank.rotational_speed = 0.033
            newTank.speed  =0.5 + self.player.tank_count/20
            newTank.fire_probability = 100
            newTank.tank_type = 4
            newTank.tank_mode = 4
            newTank.moving = False
            newTank.can_fire = True
            newTank.color = [0, 255, 0]
            newTank.name = "FastTank" + str(newTank.tank_type)
            newTank.points = 3000


        newTank.create_time=time.time()
        self.objects.append(newTank)


    ################################################################
    # render_vector_text
    # draw string to screen using vectopr fon
    ################################################################
    def render_vector_text(self, string, x, y, size, color):

        pixelsize = 24*size
        x_mag = size
        y_mag = size
        x_start = x
        y_start = y

        for i, letter in enumerate(string):
            ASCIIcode = ord(letter)
            index = ASCIIcode-64

            if index == -32:  # space character
                index = 27
            elif index < 0:
                index += 44  # number characters

            x_start = x+(i*pixelsize)
            for instruction in rawBZ.characterset[index]:
                if instruction[2] == 0:
                    x_start = x_start+instruction[0]*x_mag
                    y_start = y_start-instruction[1]*y_mag
                else:
                    xend = x_start+instruction[0]*x_mag
                    yend = y_start-instruction[1]*y_mag
                    pygame.draw.aaline(
                        self.screen, (color), (x_start, y_start), (xend, yend))
                    x_start = xend
                    y_start = yend

            x_start = x+(i*pixelsize)
    
    ################################################################
    # display_scroll_text
    # scrolling instructions for title screen
    ################################################################
    def display_scroll_text(self):
        size = 0.6
        y = self.height - 10
        text_length = len(self.scroll_text) * 24 * size
        x = self.width - (self.scroll_pos % (text_length + self.width))
        self.render_vector_text(self.scroll_text, x, y, size, (0, 255, 0))
        self.scroll_pos += 3


    ################################################################
    # draw_windscreen_crack
    # draw cracked screen when all player lives lost
    ################################################################

    def draw_windscreen_crack(self):
        x_start = self.view_center[0]
        y_start = self.view_center[1]
        x_mag = 1.2
        y_mag = 0.7
        color = [0, 1, 0]
        for frame in range(self.windscreen_frame):
            for instruction in self.windscreen_data[frame]:
                if instruction[2] == 0:
                    x_start = x_start+instruction[0]*x_mag
                    y_start = y_start-instruction[1]*y_mag
                else:
                    xend = x_start+instruction[0]*x_mag
                    yend = y_start-instruction[1]*y_mag
                    plotcolor = np.multiply(color, instruction[2]*18)
                    pygame.draw.line(self.screen, (plotcolor),
                                     (x_start, y_start), (xend, yend), 2)
                    x_start = xend
                    y_start = yend

                self.windscreen_delay_counter += 1
                if self.windscreen_delay_counter > self.windscreen_delay:
                    self.windscreen_delay_counter = 0
                    self.windscreen_frame += 1
                    if self.windscreen_frame == 9:
                        self.windscreen_frame = 8


    ################################################################
    # display_lives
    # display remaining player lives
    ################################################################
    def display_lives(self):
        if self.player.lives < 1:
            self.game_over = True
        else:
            tank_icon="@"
            start_x = self.width-300
            start_y = 30
            size = 1
            icon_width = 50
            for life in range(self.player.lives):
                self.render_vector_text(tank_icon,start_x,start_y,size,(255,0,0))
                start_x+=icon_width*size


    ################################################################
    # display_score
    # display remaining player lives
    ################################################################    
    def display_score(self):
        start_x = self.width-300
        start_y = 65
        size = 0.75
        score_length=6
        score_string="SCORE "
        l=len(str(self.player.score))
        score_string = score_string +"0"*(score_length-l)+str(self.player.score)
        self.render_vector_text(score_string,start_x,start_y,size,(255,0,0))

        if self.player.score>self.player.high_score:
            self.player.high_score=self.player.score
        
        start_x = self.width-300
        start_y = 90

        score_string="HIGH  "
        l=len(str(self.player.high_score))
        score_string = score_string +"0"*(score_length-l)+str(self.player.high_score)
        self.render_vector_text(score_string,start_x,start_y,size,(255,0,0))   

       

    ################################################################
    # display_proximity
    # display proximity info on enemy tanks
    ################################################################
    def display_proximity(self):
        start_x = 30
        start_y = 65
        size = 0.5
        
        tanks = [object for object in self.objects if (object.type == settings.OBJ_FASTTANK or object.type==settings.OBJ_TANK)]
        tank:objects.Tank
        
        for i,tank in enumerate(tanks):
            proximity_string = "ENEMY "+str(tank.number)+ " IS "
            if tank.coords_view[2]<0:
                proximity_string+="BEHIND"  
            elif tank.coords_view[0]>605+(0.18*tank.distance_to_player):
                proximity_string+="TO THE RIGHT"
            elif  tank.coords_view[0]<595-(0.18*tank.distance_to_player):
                proximity_string+="TO THE LEFT"
            elif tank.coords_view[2]>0:
                proximity_string+="IN FRONT"
                if tank.distance_to_player<1000:
                    proximity_string += " AND IN RANGE"
                   
            self.render_vector_text(proximity_string,start_x,start_y,size,(255,0,0))
            start_y+=20

    ################################################################
    # plot_logo
    # draw BZ logo for title screen
    ################################################################
    
    def plot_logo(self):
        x_mag = 10
        y_mag = x_mag
        delay_start=350
        delay_end = 2000
        y_start=self.view_center[1]+500
        x_start=self.view_center[0]-50

        if self.frame_counter >2400:
            self.frame_counter=1
            x = x_start
            y = y_start-self.frame_counter*2
        elif self.frame_counter>delay_end:
            x = x_start
            y = y_start-(delay_start+self.frame_counter-delay_end)*2     
        elif self.frame_counter>delay_start:
            x = x_start
            y = y_start-delay_start*2
        else:
            x = x_start
            y = y_start-self.frame_counter*2
            

        nodes = self.logo.nodes_model
        edges = self.logo.edges
        for edge in edges:
            X1 = x+nodes[edge[0]][0]*x_mag
            Y1 = y+nodes[edge[0]][1]*y_mag
            X2 = x+nodes[edge[1]][0]*x_mag
            Y2 = y+nodes[edge[1]][1]*y_mag

            pygame.draw.line(self.screen, self.logo.color,
                               (X1, Y1), (X2, Y2),2)

    ################################################################
    # display_title_screen
    # draw title screen and manage game initialisation
    ################################################################
    def display_title_screen(self):
        
        start_x=self.width/2-210
        start_y = self.height/2+200
        size=1
        self.render_vector_text("PRESS FIRE TO PLAY",start_x,start_y,size,(0,self.color_counter,0))
        self.player.pRotSpeed=0.001

        self.plot_logo()
        self.display_scroll_text()
        
        self.color_counter+=self.color_increment
        if self.color_counter==255 or self.color_counter==100:
            self.color_increment *= -1

        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.title_screen = False
                    self.player.lives = 5
                    self.player.score = 0
                    self.player.active_tank_count = 0
                    self.active_explosion_chunks = 0
                    self.frame_counter = 0
                    self.player.missile_count = 0
                    self.player.tank_count = 0
                    self.player.was_moving = False
                    self.max_tanks = 1
                    self.objects=[]
                    self.player.pRotSpeed=0.005
                    self.place_obstacles()
                    self.start_time = time.time()


    ################################################################
    # display_end_screen
    # draw title screen and manage game initialisation
    ################################################################
    def display_end_screen(self):
        self.player.pRotSpeed=0.001
        self.draw_windscreen_crack() 

        if self.frame_counter>100 and self.frame_counter<1000:
            start_x=self.width/2-160
            start_y = self.height/2+200
            size=1.5
            self.render_vector_text("GAME OVER",start_x,start_y,size,(0,self.color_counter,0))

           
        elif self.frame_counter>=1000:
            self.title_screen=True
            self.end_screen = False
            self.player.lives = 5
            self.player.score = 0
            self.player.active_tank_count = 0
            self.active_explosion_chunks = 0
            self.frame_counter = 0
            self.player.missile_count = 0
            self.player.tank_count = 0
            self.player.was_moving = False
            self.max_tanks = 1
            self.objects=[]
            self.player.pRotSpeed=0.005
            self.place_obstacles()
            self.start_time = time.time()
        
        
        self.color_counter+=self.color_increment
        if self.color_counter==255 or self.color_counter==100:
            self.color_increment *= -1

        if self.frame_counter>100:

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.title_screen=True
                        self.end_screen=False
                    self.frame_counter=0

    def sounds_init(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(11)
        # Grad BM-21 MLRS.wav by SoundFX.studio -- https://freesound.org/s/456266/ -- License: Attribution NonCommercial 4.0
        self.player_missile_sound = pygame.mixer.Sound('sounds/456266__soundfxstudio__grad-bm-21-mlrs.wav')
        self.channel_1 =pygame.mixer.Channel(1)
        self.channel_1.set_volume(1.0,1.0)  

        # UFO Activity 02.wav by LilMati -- https://freesound.org/s/512118/ -- License: Creative Commons 0
        self.saucer_sound = pygame.mixer.Sound('sounds/512118__lilmati__ufo-activity-02.wav')
        self.channel_2 =pygame.mixer.Channel(2)
        self.channel_2.set_volume(1.0,1.0)  

        # Explosion.wav by Bird_man -- https://freesound.org/s/275155/ -- License: Creative Commons 0
        self.tank_explode_sound = pygame.mixer.Sound('sounds/275155__bird_man__explosion.wav')
        self.channel_3 =pygame.mixer.Channel(3)
        self.channel_3.set_volume(1.0,1.0) 

        # 05780 space missile.wav by Robinhood76 -- https://freesound.org/s/273332/ -- License: Attribution NonCommercial 4.0
        self.enemy_missile_sound = pygame.mixer.Sound('sounds/273332__robinhood76__05780-space-missile.wav')
        self.channel_4 =pygame.mixer.Channel(4)
        self.channel_4.set_volume(1.0,1.0)

        # construct_explosion.wav by psychedelic_hands -- https://freesound.org/s/145791/ -- License: Attribution 3.0
        self.saucer_explode_sound = pygame.mixer.Sound('sounds/145791__psychedelic_hands__construct_explosion.wav')

        # Siren warning: NBC Alarm (Nuclear - Biological - Chemical threat) by Breviceps -- https://freesound.org/s/533588/ -- License: Creative Commons 0
        self.warning_sound = pygame.mixer.Sound('sounds/533588__breviceps__siren-warning-nbc-alarm-nuclear-biological-chemical-threat.wav') 
        self.guidedm_explode_sound = pygame.mixer.Sound('sounds/565947__robinhood76__10091-water-bomb-exploding.wav')
        self.channel_5 =pygame.mixer.Channel(5)
        self.channel_5.set_volume(0.75,0.75)

        # Sonar.wav by hth2000 -- https://freesound.org/s/166701/ -- License: Creative Commons 0
        self.radar_sound = pygame.mixer.Sound('sounds/166701__hth2000__sonar.wav')
        self.channel_6 =pygame.mixer.Channel(6)
        self.channel_6.set_volume(0.1,0.1) 

        # WAR-TANK, LEOPARD-ENGINE STAND BY-Leopard 2A4 48000 cc diesel engine close by-0003.wav by JoniHeinonen -- https://freesound.org/s/161897/ -- License: Attribution 3.0
        self.tank_sound = pygame.mixer.Sound('sounds/161897__joniheinonen__war-tank-leopard-engine-stand-by-leopard-2a4-48000-cc-diesel-engine-close-by-0003.wav')
        self.channel_7 = pygame.mixer.Channel(7)
        self.channel_7.set_volume(0.0,0.0)
        self.channel_7.play(self.tank_sound, loops=-1)

        # Explosion and Scream.wav by 18hiltc -- https://freesound.org/s/186943/ -- License: Attribution 4.0
        # Explosion.wav by steveygos93 -- https://freesound.org/s/80400/ -- License: Attribution 3.0
        self.hit_ahhh_sound = pygame.mixer.Sound('sounds/186943__18hiltc__explosion-and-scream.wav')
        self.channel_8 = pygame.mixer.Channel(8)
        self.channel_8.set_volume(1.0,1.0)
       
        # Sound Design Elements Impact SFX PS 014 by AudioPapkin -- https://freesound.org/s/752582/ -- License: Creative Commons 0
        self.crash_sound = pygame.mixer.Sound('sounds/752582__audiopapkin__sound-design-elements-impact-sfx-ps-014.wav')
        self.channel_9 = pygame.mixer.Channel(9)
        self.channel_9.set_volume(1.0,1.0)
       
        # CD_CONTACT_002FX_Space.wav by kevp888 -- https://freesound.org/s/706606/ -- License: Attribution 4.0
        self.ambient_sound = pygame.mixer.Sound('sounds/706606__kevp888__cd_contact_002fx_space.wav')
        self.channel_10 = pygame.mixer.Channel(10)
        self.channel_10.set_volume(1.0,1.0)
        if self.sound_on:
            self.channel_10.play(self.ambient_sound, loops=-1) 

        # Messy Splat 3a by FoolBoyMedia -- https://freesound.org/s/237928/ -- License: Attribution 4.0
        self.channel_0 = pygame.mixer.Channel(0)
        self.projectile_impact_sound = pygame.mixer.Sound('sounds/237928__foolboymedia__messy-splat-3a.wav')
        self.channel_0.set_volume(1.0,1.0)
        