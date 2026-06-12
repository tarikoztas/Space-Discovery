import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys
import os
import numpy as np

from camera import Camera
from obj_loader import OBJModel
from collision import AABB

class SpaceDiscoveryGame:
    def __init__(self):
        pygame.init()
        self.display_width = 1280
        self.display_height = 720
        pygame.display.set_mode((self.display_width, self.display_height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Uzay Kesif Sahnesi - Tarik Oztas")
        
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        
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
        
        # Kamera başlangıç konumu (Koridorun ortası)
        self.camera = Camera(0.0, 1.5, 12.0)
        
        print("Sadelestirilmis ve optimize edilmis 3B modeller yukleniyor...")
        self.model_spaceship = OBJModel("objects/spaceship.obj")
        self.model_chair = OBJModel("objects/spaceship_chair.obj")
        self.model_console1 = OBJModel("objects/console1/console1.obj")
        self.model_console2 = OBJModel("objects/console2/console2.obj")
        
        self.textures = {}
        self.load_mipmapped_texture("mars_ground", "textures/mars_ground.jpg") 
        self.load_mipmapped_texture("wall_texture", "textures/spaceship_walls.jpg")
        
        self.collision_boxes = []
        self.base_display_list = 0
        self.terrain_display_list = 0
        self.spaceship_display_list = 0
        
        # Fizik motorunu kur ve GPU grafik listelerini derle
        self.build_base_architecture()
        self.compile_graphics_lists()
        
        self.is_running = True
        self.clock = pygame.time.Clock()

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
        """%100 FİZİK KİLİTLEMESİ: Sandalyeler ve dışarıdaki uzay gemisi katı cisme dönüştürüldü"""
        self.collision_boxes.clear()
        
        # 🏢 Koridor Duvar Sınırları
        self.collision_boxes.append(AABB(-2.55, -2.45, 0.0, 4.0, 7.0, 20.0))    
        self.collision_boxes.append(AABB(-2.55, -2.45, 0.0, 4.0, -5.0, 3.0))    
        self.collision_boxes.append(AABB(2.45, 2.55, 0.0, 4.0, 7.0, 20.0))    
        self.collision_boxes.append(AABB(2.45, 2.55, 0.0, 4.0, -5.0, 3.0))   
        
        # 🏢 Sol Oda Ana Mimari Duvar Fiziği
        self.collision_boxes.append(AABB(-14.5, -2.5, 0.0, 4.0, -1.0, -0.95)) # Arka Duvar
        self.collision_boxes.append(AABB(-14.5, -2.5, 0.0, 4.0, 10.95, 11.0)) # Ön Duvar
        self.collision_boxes.append(AABB(-14.5, -14.45, 0.0, 4.0, -1.0, 11.0)) # En Sol Dış Duvar
        self.collision_boxes.append(AABB(-6.0, -2.5, 0.0, 4.0, 3.0, 3.05))   # Kapı Sol Kanat
        self.collision_boxes.append(AABB(-6.0, -2.5, 0.0, 4.0, 6.95, 7.0))   # Kapı Sağ Kanat

        # Console 1 Fiziği
        self.collision_boxes.append(AABB(-14.5, -13.0, 0.0, 3.5, 3.2, 6.8))   

        # Sol Masa Kutu Fiziği
        self.collision_boxes.append(AABB(-10.5, -8.5, 0.0, 1.3, 4.0, 6.0)) 
        
        # 🚨 SOL SANDALYE FİZİĞİ (Katı cisim yapıldı)
        self.collision_boxes.append(AABB(-10.0, -9.0, 0.0, 1.2, 4.6, 5.4))

        # 🏢 Sağ Oda Ana Mimari Duvar Fiziği
        self.collision_boxes.append(AABB(2.5, 14.5, 0.0, 4.0, -1.0, -0.95))  
        self.collision_boxes.append(AABB(2.5, 14.5, 0.0, 4.0, 10.95, 11.0))  
        self.collision_boxes.append(AABB(14.45, 14.5, 0.0, 4.0, -1.0, 11.0)) # En Sağ Dış Duvar
        self.collision_boxes.append(AABB(2.5, 6.0, 0.0, 4.0, 3.0, 3.05))     # Kapı Sol Kanat
        self.collision_boxes.append(AABB(2.5, 6.0, 0.0, 4.0, 6.95, 7.0))     # Kapı Sağ Kanat
        self.collision_boxes.append(AABB(12.5, 14.5, 0.5, 4.0, 2.5, 7.5))    # Console 2 Fiziği

        # Sağ Masa Kutu Fiziği
        self.collision_boxes.append(AABB(8.5, 10.5, 0.0, 1.3, 4.0, 6.0)) 
        
        # 🚨 SAĞ SANDALYE FİZİĞİ (Katı cisim yapıldı)
        self.collision_boxes.append(AABB(9.0, 10.0, 0.0, 1.2, 4.6, 5.4))

        # 🚨 DEVASA UZAY GEMİSİ FİZİĞİ (Dışarıdaki geminin içinden geçiş tamamen engellendi)
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

    def render_optimized_base_and_models(self):
        glColor3f(1.0, 1.0, 1.0)
        if self.textures["wall_texture"]:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.textures["wall_texture"])
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.2, 0.22, 0.25)
            
        # 🏢 Koridor Duvarları Kaplamalı
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
                
        # Odaların kapatıcı dış yan duvar kaplamaları
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
                
        # Üssün İç Taban Zemini
        glDisable(GL_TEXTURE_2D)
        glColor3f(0.12, 0.12, 0.14)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-14.5, 0.01, 20.0); glVertex3f(14.5, 0.01, 20.0)
        glVertex3f(14.5, 0.01, -10.0); glVertex3f(-14.5, 0.01, -10.0)
        glEnd()
        glEnable(GL_TEXTURE_2D)
        
        # --- ODA 1: SOL ODA ASSETLERİ ---
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
        glRotatef(0.0, 0.0, 1.0, 0.0) 
        glScalef(1.0, 1.0, 1.0)
        self.model_console1.render()
        glPopMatrix()

        # --- ODA 2: SAĞ ODA ASSETLERİ ---
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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.is_running = False
                    
        mouse_dx, mouse_dy = pygame.mouse.get_rel()
        self.camera.process_mouse_movement(mouse_dx, -mouse_dy)

    def update(self):
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

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        self.camera.apply_view()
        self.setup_lighting()
        
        glCallList(self.terrain_display_list)
        glCallList(self.base_display_list)
        
        glCallList(self.spaceship_display_list)

        for box in self.collision_boxes:
            box.draw_debug()

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