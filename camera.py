import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

class Camera:
    def __init__(self, x=0.0, y=1.8, z=0.0):
        """
        Kamera.pptx slaytındaki Göz, Bakış ve Yukarı vektör mimarisine 
        uygun olarak tasarlanmış 3B Kamera Sınıfı.
        """
        # Gözün Konumu (Eye X, Y, Z) - Astronotun göz hizası için varsayılan Y=1.8
        self.position = np.array([x, y, z], dtype=float)
        
        # Bakış Açıları (Radyan cinsinden)
        self.yaw = -90.0   # Sol/Sağ rotasyonu
        self.pitch = 0.0   # Yukarı/Aşağı rotasyonu
        
        # Kameranın Hareket Eksenleri (Kamera.pptx sayfa 8-12 yön vektörleri)
        self.front = np.array([0.0, 0.0, -1.0], dtype=float)
        self.up = np.array([0.0, 1.0, 0.0], dtype=float)
        self.right = np.array([1.0, 0.0, 0.0], dtype=float)
        
        self.movement_speed = 0.15
        self.mouse_sensitivity = 0.1

    def update_camera_vectors(self):
        """Kamera açısına göre yön vektörlerini trigonometrik olarak hesaplar"""
        # Dereceyi radyana çevirme hesaplamaları
        yaw_rad = np.radians(self.yaw)
        pitch_rad = np.radians(self.pitch)
        
        # Kamera ön (Front) yön vektörünün hesaplanması (Kamera.pptx matris türevi)
        front_x = np.cos(yaw_rad) * np.cos(pitch_rad)
        front_y = np.sin(pitch_rad)
        front_z = np.sin(yaw_rad) * np.cos(pitch_rad)
        
        self.front = np.array([front_x, front_y, front_z], dtype=float)
        self.front /= np.linalg.norm(self.front)
        
        # Sağ (Right) ve Yukarı (Up) vektörlerinin vektörel çarpım (Cross Product) ile bulunması
        self.right = np.cross(self.front, np.array([0.0, 1.0, 0.0]))
        self.right /= np.linalg.norm(self.right)
        
        self.up = np.cross(self.right, self.front)
        self.up /= np.linalg.norm(self.up)

    def process_mouse_movement(self, xoffset, yoffset):
        """Mouse hareketine göre bakış açısını günceller (Mouse ile Bakış Kontrolü)"""
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity

        self.yaw += xoffset
        self.pitch += yoffset

        # Kamera takla atmasın diye Pitch açısını kısıtlıyoruz (Kamera.pptx uyarısı)
        if self.pitch > 89.0:
            self.pitch = 89.0
        if self.pitch < -89.0:
            self.pitch = -89.0

        self.update_camera_vectors()

    def process_keyboard(self, keys, disable_backward=False):
        """WASD tuşlarına basıldığında kamerayı XZ (zemin) düzleminde yürütür"""
        # Sadece zemin düzleminde yürümek için ön vektörün Y bileşenini sıfırlıyoruz
        move_front = np.array([self.front[0], 0.0, self.front[2]])
        move_front /= np.linalg.norm(move_front)
        
        if keys[pygame.K_w]: # İleri
            self.position += move_front * self.movement_speed
            
        if keys[pygame.K_s] and not disable_backward: # Geri (Sahne 2'de pasif olacak)
            self.position -= move_front * self.movement_speed
            
        if keys[pygame.K_a]: # Sola süzülme
            self.position -= self.right * self.movement_speed
            
        if keys[pygame.K_d]: # Sağa süzülme
            self.position += self.right * self.movement_speed

    def apply_view(self):
        """Hesaplanan vektörleri gluLookAt fonksiyonuna besler (Slayt Kamera Görünüm Dönüşümü)"""
        # Bakılan nokta = Göz Konumu + Ön Yön Vektörü
        center = self.position + self.front
        
        gluLookAt(
            self.position[0], self.position[1], self.position[2], # eyeX, eyeY, eyeZ
            center[0], center[1], center[2],                      # centerX, centerY, centerZ
            self.up[0], self.up[1], self.up[2]                     # upX, upY, upZ
        )