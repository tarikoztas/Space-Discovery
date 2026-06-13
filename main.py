import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys
import os
import numpy as np
import random

from camera import Camera
from obj_loader import OBJModel
from collision import AABB

# DURUM (STATE) MIMARISI
STATE_MARS_EXPLORE = 1
STATE_TAKEOFF_SCREEN = 2
STATE_SPACE_FLIGHT = 3
STATE_LANDING_SCREEN = 4 
STATE_EARTH_LANDING = 5  

class SpaceDiscoveryGame:
    def __init__(self):
        pygame.init()
        pygame.font.init() 
        self.display_width = 1280
        self.display_height = 720
        pygame.display.set_mode((self.display_width, self.display_height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Uzay Kesif Sahnesi - Tarik Oztas")
        
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        
        self.current_state = STATE_MARS_EXPLORE
        
        # Zamanlayıcılar
        self.takeoff_start_time = 0
        self.takeoff_duration = 3000 
        
        self.landing_screen_start_time = 0
        self.landing_screen_duration = 3000
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0) 
        glEnable(GL_LIGHT1) 
        self.setup_lighting()
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, (self.display_width / self.display_height), 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        
        self.camera = Camera(0.0, 1.5, 12.0)
        
        print("3B modeller yukleniyor...")
        self.model_spaceship = OBJModel("objects/spaceship.obj")
        self.model_chair = OBJModel("objects/spaceship_chair.obj")
        self.model_console1 = OBJModel("objects/console1/console1.obj")
        self.model_console2 = OBJModel("objects/console2/console2.obj")
        
        self.textures = {}
        self.load_mipmapped_texture("mars_ground", "textures/mars_ground.jpg") 
        self.load_mipmapped_texture("wall_texture", "textures/spaceship_walls.jpg")
        
        self.hud_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.show_trigger_text = False 
        
        self.star_positions = []
        self.generate_starfield(count=300)
        
        # 🚀 SPACE FLIGHT ELEMENTLERI
        self.space_stars = [] 
        self.generate_space_starfield(300) 
        
        self.asteroids = [] 
        self.generate_asteroids(20)
        
        self.cosmic_planets = []
        self.generate_cosmic_planets(6)
        
        # DİKEY İNİŞ VE BULUT ELEMENTLERİ
        self.earth_clouds = []
        self.generate_earth_clouds(15) 
        
        # DİKEY İNİŞ SİMÜLASYONU DEĞİŞKENLERİ
        self.landing_y = 250.0       
        self.landing_x = 0.0         
        self.landing_velocity = 0.0   
        self.landing_gravity = 0.010  
        self.engine_thrust = 0.024    
        self.landing_finished = False 
        self.landing_success = True   
        
        self.world_z = -1000.0 
        
        self.damage_flash_time = 0 
        self.flight_speed = 0.5 
        
        self.collision_boxes = []
        self.base_display_list = 0
        self.terrain_display_list = 0
        self.spaceship_display_list = 0
        
        self.build_base_architecture()
        self.compile_graphics_lists()
        
        self.is_running = True
        self.clock = pygame.time.Clock()

    def generate_starfield(self, count):
        for _ in range(count):
            x = random.uniform(-250.0, 250.0)
            y = random.uniform(20.0, 180.0)
            z = random.uniform(-280.0, 100.0)
            self.star_positions.append((x, y, z))

    def generate_space_starfield(self, count):
        for _ in range(count):
            self.space_stars.append([
                random.uniform(-120.0, 120.0),
                random.uniform(-120.0, 120.0),
                random.uniform(-950.0, 20.0)
            ])

    def generate_asteroids(self, count):
        for _ in range(count):
            self.asteroids.append([
                random.uniform(-25.0, 25.0), 
                random.uniform(-12.0, 12.0), 
                random.uniform(-250.0, -40.0), 
                random.uniform(0.8, 2.3) 
            ])

    def generate_cosmic_planets(self, count):
        color_palette = [
            (0.2, 0.7, 1.0),  
            (1.0, 0.4, 0.1),  
            (0.6, 0.1, 0.9),  
            (0.9, 0.1, 0.2),  
            (1.0, 0.8, 0.2),  
            (0.1, 0.9, 0.6)   
        ]
        for i in range(count):
            side_x = random.choice([-1.0, 1.0]) * random.uniform(20.0, 50.0)
            y_pos = random.uniform(-10.0, 10.0)
            z_pos = random.uniform(-900.0, -250.0)
            radius = random.uniform(8.0, 15.0)
            color = color_palette[i % len(color_palette)]
            self.cosmic_planets.append([side_x, y_pos, z_pos, radius, color])

    def generate_earth_clouds(self, count):
        for _ in range(count):
            cx = random.uniform(-80.0, 80.0)
            cy = random.uniform(15.0, 180.0) 
            cz = random.uniform(-30.0, -10.0) 
            c_scale_x = random.uniform(4.0, 12.0)
            c_scale_y = random.uniform(1.5, 3.5)
            self.earth_clouds.append([cx, cy, cz, c_scale_x, c_scale_y])

    def load_mipmapped_texture(self, name, path):
        if not os.path.exists(path):
            self.textures[name] = None
            return
        img = pygame.image.load(path)
        img_data = pygame.image.tostring(img, "RGBA", 1)
        w, h = img.get_width(), img.get_height()
        
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, w, h, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        self.textures[name] = tex_id

    def setup_lighting(self):
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.12, 0.08, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.45, 0.25, 1.0])
        
        glLightfv(GL_LIGHT1, GL_POSITION, [0.0, 3.5, 5.0, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.05, 0.05, 0.1, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.4, 0.6, 0.9, 1.0])

    def build_base_architecture(self):
        self.collision_boxes.clear()
        self.collision_boxes.append(AABB(-2.55, -2.45, 0.0, 4.0, 7.0, 20.0))    
        self.collision_boxes.append(AABB(-2.55, -2.45, 0.0, 4.0, -5.0, 3.0))    
        self.collision_boxes.append(AABB(2.45, 2.55, 0.0, 4.0, 7.0, 20.0))    
        self.collision_boxes.append(AABB(2.45, 2.55, 0.0, 4.0, -5.0, 3.0))   
        self.collision_boxes.append(AABB(-14.5, -2.5, 0.0, 4.0, -1.0, -0.95)) 
        self.collision_boxes.append(AABB(-14.5, -2.5, 0.0, 4.0, 10.95, 11.0)) 
        self.collision_boxes.append(AABB(-14.5, -14.45, 0.0, 4.0, -1.0, 11.0)) 
        self.collision_boxes.append(AABB(-6.0, -2.5, 0.0, 4.0, 3.0, 3.05))   
        self.collision_boxes.append(AABB(-6.0, -2.5, 0.0, 4.0, 6.95, 7.0))   
        self.collision_boxes.append(AABB(-14.5, -13.0, 0.0, 3.5, 3.2, 6.8))   
        self.collision_boxes.append(AABB(-10.5, -8.5, 0.0, 1.3, 4.0, 6.0)) 
        self.collision_boxes.append(AABB(-10.0, -9.0, 0.0, 1.2, 4.6, 5.4))
        self.collision_boxes.append(AABB(2.5, 14.5, 0.0, 4.0, -1.0, -0.95))  
        self.collision_boxes.append(AABB(2.5, 14.5, 0.0, 4.0, 10.95, 11.0))  
        self.collision_boxes.append(AABB(14.45, 14.5, 0.0, 4.0, -1.0, 11.0)) 
        self.collision_boxes.append(AABB(2.5, 6.0, 0.0, 4.0, 3.0, 3.05))     
        self.collision_boxes.append(AABB(2.5, 6.0, 0.0, 4.0, 6.95, 7.0))     
        self.collision_boxes.append(AABB(12.5, 14.5, 0.5, 4.0, 2.5, 7.5))   
        self.collision_boxes.append(AABB(8.5, 10.5, 0.0, 1.3, 4.0, 6.0)) 
        self.collision_boxes.append(AABB(9.0, 10.0, 0.0, 1.2, 4.6, 5.4))
        self.collision_boxes.append(AABB(-4.0, 4.0, 0.0, 5.0, -120.0, -88.0))

    def compile_graphics_lists(self):
        self.terrain_display_list = glGenLists(1)
        glNewList(self.terrain_display_list, GL_COMPILE)
        self.render_terrain_geometry()
        glEndList()

        self.base_display_list = glGenLists(1)
        glNewList(self.base_display_list, GL_COMPILE)
        self.render_optimized_base_and_models()
        glEndList()
        
        self.spaceship_display_list = glGenLists(1)
        glNewList(self.spaceship_display_list, GL_COMPILE)
        glPushMatrix()
        glEnable(GL_TEXTURE_2D)
        if self.model_spaceship.fallback_texture_id is not None:
            glBindTexture(GL_TEXTURE_2D, self.model_spaceship.fallback_texture_id)
            glColor3f(1.0, 1.0, 1.0)
            
        glTranslatef(0.0, self.get_terrain_height(0.0, -100.0) + 0.5, -100.0) 
        glScalef(4.0, 4.0, 4.0) 
        self.model_spaceship.render()
        glPopMatrix()
        glEndList()

    def cleanup_mars_assets(self):
        print("\n[BELLEK TEMİZLİĞİ] Mars verileri ekran kartindan temizleniyor...")
        if self.terrain_display_list != 0:
            glDeleteLists(self.terrain_display_list, 1)
            self.terrain_display_list = 0
        if self.base_display_list != 0:
            glDeleteLists(self.base_display_list, 1)
            self.base_display_list = 0
            
        self.model_console1 = None
        self.model_console2 = None
        self.model_chair = None
        self.collision_boxes.clear()
        self.star_positions.clear()
        
        self.camera.position = [0.0, 0.0, 0.0]
        print("[BELLEK TEMİZLİĞİ] Islem tamamlandi. Sadece uzay elementleri aktif.")

    def get_terrain_height(self, x, z):
        if -15.0 < z < 15.0 and -18.0 < x < 18.0:
            return 0.0 
        return (np.sin(x * 0.12) * np.cos(z * 0.12) * 3.5) - 1.0

    def render_terrain_geometry(self):
        if self.textures["mars_ground"]:
            glBindTexture(GL_TEXTURE_2D, self.textures["mars_ground"])
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.6, 0.2, 0.1)
            
        step = 4
        size = 120
        glBegin(GL_QUADS)
        for x in range(-size, size, step):
            for z in range(-size, size, step):
                h1 = self.get_terrain_height(x, z)
                h2 = self.get_terrain_height(x+step, z)
                h3 = self.get_terrain_height(x+step, z+step)
                h4 = self.get_terrain_height(x, z+step)
                
                glNormal3f(0.0, 1.0, 0.0)
                glTexCoord2f(x/8.0, z/8.0); glVertex3f(x, h1, z)
                glTexCoord2f((x+step)/8.0, z/8.0); glVertex3f(x+step, h2, z)
                glTexCoord2f((x+step)/8.0, (z+step)/8.0); glVertex3f(x+step, h3, z+step)
                glTexCoord2f(x/8.0, (z+step)/8.0); glVertex3f(x, h4, z+step)
        glEnd()
        glEnable(GL_TEXTURE_2D)

    def draw_wall_segment(self, x1, y1, z1, x2, y2, z2):
        glBegin(GL_QUADS)
        glNormal3f(0.0, 0.0, 1.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(x1, y1, z1)
        glTexCoord2f(2.0, 0.0); glVertex3f(x2, y1, z1)
        glTexCoord2f(2.0, 1.0); glVertex3f(x2, y2, z2)
        glTexCoord2f(0.0, 1.0); glVertex3f(x1, y2, z2)
        glEnd()

    def draw_table_cylinder_leg(self, cx, cz, max_y):
        radius = 0.15 
        slices = 16
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.25, 0.27, 0.30) 
        
        glBegin(GL_QUAD_STRIP)
        for i in range(slices + 1):
            angle = 2.0 * np.pi * i / slices
            x = cx + radius * np.cos(angle)
            z = cz + radius * np.sin(angle)
            
            glNormal3f(np.cos(angle), 0.0, np.sin(angle))
            glVertex3f(x, 0.0, z)   
            glVertex3f(x, max_y, z) 
        glEnd()
        glEnable(GL_TEXTURE_2D)

    def render_sky_elements(self):
        glDisable(GL_LIGHTING) 
        glDisable(GL_TEXTURE_2D) 
        
        glPushMatrix()
        glTranslatef(0.0, 80.0, -300.0) 
        glColor3f(1.0, 0.85, 0.1) 
        quadric = gluNewQuadric()
        gluSphere(quadric, 18.0, 32, 32) 
        gluDeleteQuadric(quadric)
        glPopMatrix()
        
        glColor3f(1.0, 1.0, 1.0) 
        glPointSize(3.0) 
        glBegin(GL_POINTS)
        for pos in self.star_positions:
            glVertex3fv(pos)
        glEnd()
        
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)

    def render_optimized_base_and_models(self):
        glColor3f(1.0, 1.0, 1.0) 
        if self.textures["wall_texture"]:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.textures["wall_texture"])
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.2, 0.22, 0.25)
            
        glBegin(GL_QUADS)
        glNormal3f(1.0, 0.0, 0.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(-2.5, 0.0, 7.0)
        glTexCoord2f(4.0, 0.0); glVertex3f(-2.5, 0.0, 20.0)
        glTexCoord2f(4.0, 1.0); glVertex3f(-2.5, 4.0, 20.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(-2.5, 4.0, 7.0)
        
        glTexCoord2f(0.0, 0.0); glVertex3f(-2.5, 0.0, -5.0)
        glTexCoord2f(3.0, 0.0); glVertex3f(-2.5, 0.0, 3.0)
        glTexCoord2f(3.0, 1.0); glVertex3f(-2.5, 4.0, 3.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(-2.5, 4.0, -5.0)
        
        glTexCoord2f(0.0, 0.0); glVertex3f(2.5, 0.0, 7.0)
        glTexCoord2f(4.0, 0.0); glVertex3f(2.5, 0.0, 20.0)
        glTexCoord2f(4.0, 1.0); glVertex3f(2.5, 4.0, 20.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(2.5, 4.0, 7.0)
        
        glTexCoord2f(0.0, 0.0); glVertex3f(2.5, 0.0, -5.0)
        glTexCoord2f(3.0, 0.0); glVertex3f(2.5, 0.0, 3.0)
        glTexCoord2f(3.0, 1.0); glVertex3f(2.5, 4.0, 3.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(2.5, 4.0, -5.0)
        glEnd()
        
        self.draw_wall_segment(-2.5, 4.0, -5.0, 2.5, 4.0, 20.0) 
        
        room_list = [(-8.5, 0.0, 5.0), (8.5, 0.0, 5.0)]
        for rx, ry, rz in room_list:
            self.draw_wall_segment(rx-6.0, 0.0, rz-6.0, rx+6.0, 4.0, rz-6.0) 
            self.draw_wall_segment(rx-6.0, 0.0, rz+6.0, rx+6.0, 4.0, rz+6.0) 
            self.draw_wall_segment(rx-6.0, 4.0, rz-6.0, rx+6.0, 4.0, rz+6.0) 
            
            if rx < 0:
                self.draw_wall_segment(rx-6.0, 0.0, rz-6.0, rx-6.0, 4.0, rz+6.0) 
                self.draw_wall_segment(-6.0, 0.0, rz-2.0, -2.5, 4.0, rz-2.0)    
                self.draw_wall_segment(-6.0, 0.0, rz+2.0, -2.5, 4.0, rz+2.0)    
            else:
                self.draw_wall_segment(rx+6.0, 0.0, rz-6.0, rx+6.0, 4.0, rz+6.0) 
                self.draw_wall_segment(2.5, 0.0, rz-2.0, 6.0, 4.0, rz-2.0)     
                self.draw_wall_segment(2.5, 0.0, rz+2.0, 6.0, 4.0, rz+2.0)     
                
        if self.textures["wall_texture"]:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.textures["wall_texture"])
        glBegin(GL_QUADS)
        glNormal3f(1.0, 0.0, 0.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(-14.5, 0.0, -1.0)
        glTexCoord2f(4.0, 0.0); glVertex3f(-14.5, 0.0, 11.0)
        glTexCoord2f(4.0, 1.0); glVertex3f(-14.5, 4.0, 11.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(-14.5, 4.0, -1.0)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(-1.0, 0.0, 0.0)
        glTexCoord2f(0.0, 0.0); glVertex3f(14.5, 0.0, -1.0)
        glTexCoord2f(4.0, 0.0); glVertex3f(14.5, 0.0, 11.0)
        glTexCoord2f(4.0, 1.0); glVertex3f(14.5, 4.0, 11.0)
        glTexCoord2f(0.0, 1.0); glVertex3f(14.5, 4.0, -1.0)
        glEnd()
                
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.12, 0.12, 0.14)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-14.5, 0.01, 20.0); glVertex3f(14.5, 0.01, 20.0)
        glVertex3f(14.5, 0.01, -10.0); glVertex3f(-14.5, 0.01, -10.0)
        glEnd()
        glEnable(GL_TEXTURE_2D)
        
        rx_sol, ry_sol, rz_sol = -8.5, 0.0, 5.0
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.35, 0.35, 0.38)
        glBegin(GL_QUADS)
        glVertex3f(-10.5, 1.2, 6.0); glVertex3f(-8.5, 1.2, 6.0)
        glVertex3f(-8.5, 1.2, 4.0); glVertex3f(-10.5, 1.2, 4.0)
        glEnd()
        glEnable(GL_TEXTURE_2D)
        self.draw_table_cylinder_leg(-9.5, 5.0, 1.2)
        
        glPushMatrix()
        glTranslatef(rx_sol - 1.0, ry_sol + 0.05, rz_sol)
        glScalef(0.30, 0.30, 0.30)
        self.model_chair.render()
        glPopMatrix()
        
        glPushMatrix()
        glBindTexture(GL_TEXTURE_2D, 0) 
        glTranslatef(rx_sol - 5.0, ry_sol, rz_sol)
        glScalef(1.0, 1.0, 1.0)
        self.model_console1.render()
        glPopMatrix()

        rx_sag, ry_sag, rz_sag = 8.5, 0.0, 5.0
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.35, 0.35, 0.38)
        glBegin(GL_QUADS)
        glVertex3f(8.5, 1.2, 6.0); glVertex3f(10.5, 1.2, 6.0)
        glVertex3f(10.5, 1.2, 4.0); glVertex3f(8.5, 1.2, 4.0)
        glEnd()
        glEnable(GL_TEXTURE_2D)
        self.draw_table_cylinder_leg(9.5, 5.0, 1.2)
        
        glPushMatrix()
        glTranslatef(rx_sag + 1.0, ry_sag + 0.05, rz_sag)
        glScalef(0.30, 0.30, 0.30)
        self.model_chair.render()
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(rx_sag + 4.8, ry_sag + 1.5, rz_sag)
        glRotatef(-90.0, 0.0, 1.0, 0.0) 
        glScalef(1.8, 1.8, 1.8)
        self.model_console2.render()
        glPopMatrix()

    def draw_hud_2d_text(self, font_obj, text, x, y, r=255, g=235, b=59):
        text_surface = font_obj.render(text, True, (r, g, b), (0, 0, 0, 150))
        text_data = pygame.image.tostring(text_surface, "RGBA", 1)
        tw, th = text_surface.get_width(), text_surface.get_height()
        
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tw, th, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display_width, self.display_height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x - tw/2, y - th/2)
        glTexCoord2f(1, 1); glVertex2f(x + tw/2, y - th/2)
        glTexCoord2f(1, 0); glVertex2f(x + tw/2, y + th/2)
        glTexCoord2f(0, 0); glVertex2f(x - tw/2, y + th/2)
        glEnd()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_LIGHTING)
        glDeleteTextures([tex_id])

    def draw_handcrafted_cockpit_hud(self):
        """EL CIZIMI 2B KOKPIT PANEL MASKESI (Pencereler tam merkezde ve TAM OPAK)"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.display_width, self.display_height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        half_h = self.display_height / 2
        
        # 🛸 1. ALT GÖVDE PANELİ
        glColor4f(0.1, 0.11, 0.14, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(0, half_h + 100) 
        glVertex2f(self.display_width, half_h + 100)
        glVertex2f(self.display_width, self.display_height)
        glVertex2f(0, self.display_height)
        glEnd()
        
        # 🛸 2. ÜST TAVAN PANELİ
        glColor4f(0.08, 0.09, 0.11, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.display_width, 0)
        glVertex2f(self.display_width, half_h - 150) 
        glVertex2f(0, half_h - 150)
        glEnd()
        
        # 🛸 3. YAN DESTEK SÜTUNLARI
        glColor4f(0.07, 0.08, 0.1, 1.0)
        glBegin(GL_TRIANGLES)
        glVertex2f(0, half_h - 150); glVertex2f(160, half_h - 150); glVertex2f(0, half_h + 100)
        glVertex2f(self.display_width, half_h - 150); glVertex2f(self.display_width - 160, half_h - 150); glVertex2f(self.display_width, half_h + 100)
        glEnd()
        
        # 🟢 4. NEON SİBER ÇİZGİLER VE NİŞANGAH
        glLineWidth(3.0)
        glColor3f(0.0, 1.0, 0.3)
        glBegin(GL_LINES)
        glVertex2f(0, half_h - 150); glVertex2f(self.display_width, half_h - 150)
        glVertex2f(0, half_h + 100); glVertex2f(self.display_width, half_h + 100)
        glVertex2f(160, half_h - 150); glVertex2f(0, half_h + 100)
        glVertex2f(self.display_width - 160, half_h - 150); glVertex2f(self.display_width, half_h + 100)
        
        cx, cy = self.display_width / 2, half_h - 25
        glVertex2f(cx - 25, cy); glVertex2f(cx + 25, cy)
        glVertex2f(cx, cy - 25); glVertex2f(cx, cy + 25)
        glEnd()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_LIGHTING)

    def render_takeoff_screen(self):
        glClearColor(0.02, 0.02, 0.05, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_hud_2d_text(self.title_font, "KALKIS BASLIYOR...", self.display_width / 2, self.display_height / 2, 255, 64, 64)

    def render_landing_screen(self):
        glClearColor(0.0, 0.05, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw_hud_2d_text(self.title_font, "DUNYA'YA INIS BASLIYOR...", self.display_width / 2, self.display_height / 2, 64, 255, 128)

    def render_space_flight_scene(self):
        if pygame.time.get_ticks() - self.damage_flash_time < 200:
            glClearColor(0.3, 0.0, 0.0, 1.0)
        else:
            glClearColor(0.0, 0.0, 0.02, 1.0)
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        self.camera.apply_view()
        
        glTranslatef(0.0, -1.0, 0.0)
        
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        
        # ⚪ 1. UZAY KAFESİ YILDIZLARI
        glColor3f(1.0, 1.0, 1.0)
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for star in self.space_stars:
            glVertex3fv(star)
        glEnd()
        
        # 2. DERİN UZAY ARKA PLAN GEZEGENLERİ
        for planet in self.cosmic_planets:
            glPushMatrix()
            glTranslatef(planet[0], planet[1], planet[2])
            glColor3fv(planet[4]) 
            quadric = gluNewQuadric()
            gluSphere(quadric, planet[3], 16, 16) 
            gluDeleteQuadric(quadric)
            glPopMatrix()
        
        # 🪨 3. KARŞIDAN HIZLA GELEN METEORLAR 
        glColor3f(0.5, 0.4, 0.35) 
        for ast in self.asteroids:
            glPushMatrix()
            glTranslatef(ast[0], ast[1], ast[2])
            quadric = gluNewQuadric()
            gluSphere(quadric, ast[3], 8, 8) 
            gluDeleteQuadric(quadric)
            glPopMatrix()
            
        # 🌍 4. HEDEF GEZEGEN DÜNYA
        glPushMatrix()
        glTranslatef(0.0, 0.0, self.world_z)
        glColor3f(0.1, 0.5, 0.9) 
        quadric = gluNewQuadric()
        gluSphere(quadric, 30.0, 32, 32) 
        
        glColor3f(0.2, 0.8, 0.3)
        gluSphere(quadric, 30.1, 16, 16)
        gluDeleteQuadric(quadric)
        glPopMatrix()
        
        glEnable(GL_LIGHTING)
        
        glTranslatef(0.0, 1.0, 0.0)
        
        # 🛸 5. EL ÇİZİMİ KOKPİT HUD PANELİ
        self.draw_handcrafted_cockpit_hud()
        
        # Telemetri Gösterge Yazıları
        distance_to_earth = abs(self.world_z - (-10.0))
        self.draw_hud_2d_text(self.hud_font, f"HEDEF MESAFE: {int(distance_to_earth)} KM", 260, self.display_height - 65, 0, 255, 255)
        self.draw_hud_2d_text(self.hud_font, "KALKAN: AKTIF (100%)", self.display_width - 260, self.display_height - 65, 0, 255, 64)

    def render_earth_landing_scene(self):
        """🎮 SAHNE RENDERI: Dünya atmosferinde ÜÇÜNCÜ ŞAHIS geniş açılı dikey iniş alanı sahnesi"""
        glClearColor(0.05, 0.3, 0.55, 1.0) 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Geniş açı (ferah FOV) TPP Kamera Matrisi
        gluLookAt(self.landing_x, self.landing_y + 8.0, 60.0,  
                  self.landing_x, self.landing_y - 2.0, 0.0,   
                  0.0, 1.0, 0.0)                               
        
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        
        # ☁️ SABİT ARKA PLAN BULUTLARI (Sağa sola gidiş referansı)
        glColor4f(1.0, 1.0, 1.0, 0.35) 
        for cloud in self.earth_clouds:
            glPushMatrix()
            glTranslatef(cloud[0], cloud[1], cloud[2])
            glScalef(cloud[3], cloud[4], 2.0) 
            quad = gluNewQuadric()
            gluSphere(quad, 1.0, 8, 8)
            gluDeleteQuadric(quad)
            glPopMatrix()
            
        # 🚨 1. TOPRAK GÖRÜNÜMLÜ KAHVERENGİ OVAL ZEMİN (Ufuk Sınırı Ayrımı)
        glColor3f(0.45, 0.24, 0.1) # Gerçekçi kahverengi toprak tonu
        glBegin(GL_QUADS)
        glVertex3f(-100.0, 0.0, -100.0)
        glVertex3f(100.0, 0.0, -100.0)
        glVertex3f(100.0, 0.0, 100.0)
        glVertex3f(-100.0, 0.0, 100.0)
        glEnd()
            
        self.setup_lighting()
        
        # 🏢 TEKNOLOJİK İNİŞ PİSTİ (Toprağın hemen üst katmanında parlar)
        glPushMatrix()
        glTranslatef(0.0, 0.01, 0.0) 
        
        glColor3f(0.25, 0.28, 0.33)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-25.0, 0.0, -25.0)
        glVertex3f(25.0, 0.0, -25.0)
        glVertex3f(25.0, 0.0, 25.0)
        glVertex3f(-25.0, 0.0, 25.0)
        glEnd()
        
        glLineWidth(4.0)
        glColor3f(1.0, 0.75, 0.0)
        glBegin(GL_LINES)
        glVertex3f(-6.0, 0.05, -6.0); glVertex3f(6.0, 0.05, -6.0)
        glVertex3f(6.0, 0.05, -6.0); glVertex3f(6.0, 0.05, 6.0)
        glVertex3f(6.0, 0.05, 6.0); glVertex3f(-6.0, 0.05, 6.0)
        glVertex3f(-6.0, 0.05, 6.0); glVertex3f(-6.0, 0.05, -6.0)
        glEnd()
        glPopMatrix()
        
        # 🚀 UZAY GEMİSİ
        glPushMatrix()
        glTranslatef(self.landing_x, self.landing_y, 0.0) 
        glRotatef(180.0, 0.0, 1.0, 0.0)                  
        glRotatef(-90.0, 1.0, 0.0, 0.0)                  
        glScalef(2.5, 2.5, 2.5)                           
        
        glEnable(GL_TEXTURE_2D)
        if self.model_spaceship and self.model_spaceship.fallback_texture_id is not None:
            glBindTexture(GL_TEXTURE_2D, self.model_spaceship.fallback_texture_id)
            glColor3f(1.0, 1.0, 1.0)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.8, 0.8, 0.8)
            
        if self.model_spaceship:
            self.model_spaceship.render()
        glPopMatrix() 
        glDisable(GL_TEXTURE_2D)
        
        # 🚨 KESİN ÇÖZÜM: BAĞIMSIZ VE EN ÜSTE ÇİZİLEN ÜÇGEN ALEV MOTORU
        if pygame.key.get_pressed()[pygame.K_SPACE] and self.landing_y > 12.1 and not self.landing_finished:
            glPushMatrix()
            glDisable(GL_LIGHTING)     # Işıkları kapat (Alev karanlıkta kalmasın, kendi rengiyle parlasın)
            glDisable(GL_TEXTURE_2D)   # Dokuyu kapat
            glDisable(GL_DEPTH_TEST)   # 🚨 KRİTİK: Derinlik testini kapat! Alev geminin altında kalıp gizlenmesin, en öne zorla çizilsin!
            
            # Kameranın tam karşısında, geminin altına (Y ekseninde -4.0 birim aşağısına) ve 
            # kameraya biraz daha yakın olsun diye Z ekseninde +1.0 öne konumlandırıyoruz
            glTranslatef(self.landing_x, self.landing_y - 12.0, 1.0)
            glScalef(1.5, 1.5, 1.5)  # Alevi biraz büyütüyoruz

            # --- 1. KATMAN: DIŞ GENİŞ TURUNCU ALEV ---
            glColor3f(1.0, 0.5, 0.0)   # Canlı Turuncu
            glBegin(GL_TRIANGLES)
            glVertex3f(-1.5, 0.0, 0.0)  # Sol taban
            glVertex3f(1.5, 0.0, 0.0)   # Sağ taban
            glVertex3f(0.0, -5.5, 0.0)  # Aşağıya doğru sivrilen uç
            glEnd()
            
            # --- 2. KATMAN: İÇ SICAK KIRMIZI ÇEKİRDEK ---
            glColor3f(0.9, 0.1, 0.0)   # Kor Kırmızı
            glBegin(GL_TRIANGLES)
            glVertex3f(-0.8, 0.01, 0.0) # Sol iç taban
            glVertex3f(0.8, 0.01, 0.0)  # Sağ iç taban
            glVertex3f(0.0, -3.5, 0.0)  # İç kısa sivri uç
            glEnd()
            
            glEnable(GL_DEPTH_TEST)    # Derinlik testini eski haline getir
            glEnable(GL_LIGHTING)      # Işıkları geri aç
            glPopMatrix()
            
            
        # 📊 KULLANICI ARAYÜZÜ (HUD) GÖSTERGELERİ
        self.draw_hud_2d_text(self.hud_font, f"İRTİFA: {int((self.landing_y - 5.0) * 10)-70} METRE", 160, 50, 0, 255, 255)
        
        hiza_renk = (0, 255, 64) if abs(self.landing_x) <= 6.0 else (255, 64, 64)
        self.hud_hiza_metni = "RAMPA HIZALAMASI: UYGUN" if abs(self.landing_x) <= 6.0 else "RAMPADAN UZAKLASTIN!"
        self.draw_hud_2d_text(self.hud_font, f"{self.hud_hiza_metni} (X: {self.landing_x:.1f})", 260, 100, hiza_renk[0], hiza_renk[1], hiza_renk[2])
        
        if self.landing_finished:
            if self.landing_success:
                self.draw_hud_2d_text(self.title_font, "INIS BASARILI! RAMPA GUVENLI", self.display_width / 2, self.display_height / 2 - 50, 0, 255, 64)
            else:
                self.draw_hud_2d_text(self.title_font, "SERT INIS VEYA ISABETSIZ KAZA!", self.display_width / 2, self.display_height / 2 - 50, 255, 64, 64)
        else:
            color_alert = (0, 255, 64) if self.landing_velocity < 1.5 else (255, 64, 64)
            self.draw_hud_2d_text(self.hud_font, f"INIS HIZI: {self.landing_velocity:.2f} M/S", self.display_width - 160, 50, color_alert[0], color_alert[1], color_alert[2])

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                elif event.key == pygame.K_e and self.current_state == STATE_MARS_EXPLORE and self.show_trigger_text:
                    self.current_state = STATE_TAKEOFF_SCREEN
                    self.takeoff_start_time = pygame.time.get_ticks()
                    
        if self.current_state == STATE_MARS_EXPLORE:
            mouse_dx, mouse_dy = pygame.mouse.get_rel()
            self.camera.process_mouse_movement(mouse_dx, -mouse_dy)

    def update(self):
        if self.current_state == STATE_MARS_EXPLORE:
            keys = pygame.key.get_pressed()
            old_position = self.camera.position.copy()
            self.camera.process_keyboard(keys)
            
            px, py, pz = self.camera.position
            
            collision_detected = False
            for box in self.collision_boxes:
                if box.check_collision(px, py, pz, radius=0.25):
                    self.camera.position = old_position
                    collision_detected = True
                    break
                    
            if not collision_detected:
                current_ground_height = self.get_terrain_height(self.camera.position[0], self.camera.position[2])
                self.camera.position[1] = current_ground_height + 1.5

            distance_to_ship_border = abs(pz - (-88.0))
            if -6.0 <= px <= 6.0 and distance_to_ship_border <= 4.0:
                self.show_trigger_text = True
            else:
                self.show_trigger_text = False
                
        elif self.current_state == STATE_TAKEOFF_SCREEN:
            current_time = pygame.time.get_ticks()
            if current_time - self.takeoff_start_time >= self.takeoff_duration:
                self.cleanup_mars_assets() 
                self.current_state = STATE_SPACE_FLIGHT
                
        elif self.current_state == STATE_SPACE_FLIGHT:
            keys = pygame.key.get_pressed()
            
            speed_modifier = self.flight_speed
            if keys[pygame.K_w]:
                speed_modifier *= 2.5
                
            if keys[pygame.K_a]:
                for ast in self.asteroids: ast[0] += 0.4
                for star in self.space_stars: star[0] += 0.4
                for planet in self.cosmic_planets: planet[0] += 0.15 
            if keys[pygame.K_d]:
                for ast in self.asteroids: ast[0] -= 0.4
                for star in self.space_stars: star[0] -= 0.4
                for planet in self.cosmic_planets: planet[0] -= 0.15 
                
            for star in self.space_stars:
                star[2] += speed_modifier * 4.0
                if star[2] > 10.0:
                    star[2] = -950.0
                    star[0] = random.uniform(-120.0, 120.0)
                    star[1] = random.uniform(-120.0, 120.0)
            
            for planet in self.cosmic_planets:
                planet[2] += speed_modifier * 0.35 
                if planet[2] > 30.0:
                    planet[2] = random.uniform(-950.0, -700.0)
                    planet[0] = random.choice([-1.0, 1.0]) * random.uniform(20.0, 50.0)
                    
            for ast in self.asteroids:
                ast[2] += speed_modifier * 3.0 
                
                distance_to_player = np.sqrt(ast[0]**2 + ast[1]**2 + ast[2]**2)
                if distance_to_player < (ast[3] + 0.5) and abs(ast[2]) < 2.0:
                    print("[ALARM] Kalkan Darbe Aldı! Meteora Çarpıldı!")
                    self.damage_flash_time = pygame.time.get_ticks() 
                    ast[2] = -250.0 
                    ast[0] = random.uniform(-25.0, 25.0)
                
                if ast[2] > 10.0:
                    ast[2] = -250.0
                    ast[0] = random.uniform(-25.0, 25.0)
                    ast[1] = random.uniform(-12.0, 12.0)
                    
            self.world_z += speed_modifier * 0.8
            
            if self.world_z >= -45.0:
                print("\n[SİSTEM] Dünya atmosferine girildi. İniş ekranına geçiliyor.")
                self.current_state = STATE_LANDING_SCREEN
                self.landing_screen_start_time = pygame.time.get_ticks() 
                
        elif self.current_state == STATE_LANDING_SCREEN:
            current_time = pygame.time.get_ticks()
            if current_time - self.landing_screen_start_time >= self.landing_screen_duration:
                self.current_state = STATE_EARTH_LANDING
                
        elif self.current_state == STATE_EARTH_LANDING:
            if not self.landing_finished:
                keys = pygame.key.get_pressed()
                
                self.landing_velocity += self.landing_gravity
                
                if keys[pygame.K_SPACE]:
                    self.landing_velocity -= self.engine_thrust
                    
                if keys[pygame.K_a]:
                    self.landing_x -= 0.18
                if keys[pygame.K_d]:
                    self.landing_x += 0.18
                    
                self.landing_y -= self.landing_velocity
                
                if self.landing_y > 200.0:
                    self.landing_y = 200.0
                    self.landing_velocity = 0.0
                    
                if self.landing_y <= 12.0:
                    self.landing_y = 12.0
                    self.landing_finished = True
                    
                    if self.landing_velocity < 1.5 and abs(self.landing_x) <= 6.0:
                        self.landing_success = True
                        print("\n[MİSYON] Başarılı TPP İnişi! Dünyaya hoş geldiniz.")
                    else:
                        self.landing_success = False
                        print("\n[MİSYON] Başarısız İniş! Sert düşüş ya da pist dışı kaza.")

    def render(self):
        if self.current_state == STATE_MARS_EXPLORE:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()
            self.camera.apply_view()
            self.setup_lighting()
            self.render_sky_elements()
            glCallList(self.terrain_display_list)
            glCallList(self.base_display_list)
            glCallList(self.spaceship_display_list)
            
            """
            for box in self.collision_boxes:
                box.draw_debug()
            """

            if self.show_trigger_text:
                self.draw_hud_2d_text(self.hud_font, "Ucus Moduna Gecmek Icin 'E' Tusuna Bas", self.display_width / 2, self.display_height / 2 + 100)
                
        elif self.current_state == STATE_TAKEOFF_SCREEN:
            self.render_takeoff_screen()
            
        elif self.current_state == STATE_SPACE_FLIGHT:
            self.render_space_flight_scene()
            
        elif self.current_state == STATE_LANDING_SCREEN:
            self.render_landing_screen()
            
        elif self.current_state == STATE_EARTH_LANDING:
            self.render_earth_landing_scene()

        pygame.display.flip()

    def run(self):
        while self.is_running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = SpaceDiscoveryGame()
    game.run()