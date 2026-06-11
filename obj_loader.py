import pygame
from OpenGL.GL import *
import os

class OBJModel:
    def __init__(self, filename, swapyz=False):
        """
        Wavefront .obj dosyalarını okuyan ve OpenGL texture işlemlerini 
        ders slaytlarına (OpenGL Texture.pptx) uygun olarak gerçekleştiren yükleyici sınıfı.
        """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.gl_list = 0
        self.textures = {}

        # Dosyanın bulunduğu dizini bul (Texture yollarını çözmek için)
        self.dirname = os.path.dirname(filename)

        # 1. OBJ Dosyasını Ayrıştırma (Parsing)
        if not os.path.exists(filename):
            print(f"Hata: {filename} dosyası bulunamadı!")
            return

        with open(filename, "r") as f:
            for line in f:
                if line.startswith('#'): continue
                values = line.split()
                if not values: continue
                
                if values[0] == 'v': # Vertex (Tepe Noktası) koordinatları
                    v = list(map(float, values[1:4]))
                    if swapyz:
                        v = [v[0], v[2], v[1]]
                    self.vertices.append(v)
                elif values[0] == 'vn': # Normaller (Işıklandırma hesapları için)
                    v = list(map(float, values[1:4]))
                    if swapyz:
                        v = [v[0], v[2], v[1]]
                    self.normals.append(v)
                elif values[0] == 'vt': # Texture (Kaplama) Koordinatları
                    # Ders slaytındaki (s, t) haritalama düzlemi
                    self.texcoords.append(list(map(float, values[1:3])))
                elif values[0] == 'f': # Yüzeyler (Faces)
                    face = []
                    texcoords = []
                    norms = []
                    for v in values[1:]:
                        w = v.split('/')
                        face.append(int(w[0]))
                        if len(w) >= 2 and len(w[1]) > 0:
                            texcoords.append(int(w[1]))
                        else:
                            texcoords.append(0)
                        if len(w) >= 3 and len(w[2]) > 0:
                            norms.append(int(w[2]))
                        else:
                            norms.append(0)
                    self.faces.append((face, norms, texcoords))

        # 2. Ders Slaytlarına Uygun OpenGL Display List Oluşturma
        # Modeli her karede baştan CPU ile okumamak için ekran kartı hafızasında liste oluşturuyoruz
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        
        # Modele ait aktif bir kaplama varsa etkinleştir
        glEnable(GL_TEXTURE_2D)
        
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            vertices, normals, texture_coords = face
            for i in range(len(vertices)):
                # Eğer modelin normalleri varsa ışıklandırma için bildir
                if normals[i] > 0:
                    glNormal3fv(self.normals[normals[i] - 1])
                
                # Ders slaytındaki glTexCoord2d kuralı: Çizimden hemen önce kaplama koordinatı verilir
                if texture_coords[i] > 0:
                    glTexCoord2f(self.texcoords[texture_coords[i] - 1][0], 
                                 self.texcoords[texture_coords[i] - 1][1])
                
                # Tepe noktasını çiz
                glVertex3fv(self.vertices[vertices[i] - 1])
        glEnd()
        
        glEndList()

    def load_texture(self, texture_name, image_path):
        """
        Ders sunumundaki (OpenGL Texture.pptx) 4 temel adımı uygulayan kaplama yükleme fonksiyonu:
        1. glGenTextures, 2. glBindTexture, 3. Parametrelerin Ayarlanması, 4. glTexImage2D
        """
        if not os.path.exists(image_path):
            print(f"Görsel bulunamadı: {image_path}")
            return False

        # Pygame yardımıyla resmi piksellere döküyoruz
        img = pygame.image.load(image_path)
        img_data = pygame.image.tostring(img, "RGBA", 1)
        width, height = img.get_width(), img.get_height()

        # Adım 1: Texture ID üretme (Slayt sayfa 15)
        tex_id = glGenTextures(1)
        
        # Adım 2: Texture bağlama/aktif etme
        glBindTexture(GL_TEXTURE_2D, tex_id)
        
        # Adım 3: Küçültme ve Büyütme Filtrelerini Ayarlama (Slayt sayfa 19 - GL_LINEAR kuralı)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        # Adım 4: Piksel verilerini Ekran Kartı Belleğine Gönderme (Slayt sayfa 16)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        
        # İleride çağırmak üzere texture ID'sini hafızada sakla
        self.textures[texture_name] = tex_id
        return tex_id

    def render(self, texture_name=None):
        """Modeli ekrana basan fonksiyon"""
        if texture_name and texture_name in self.textures:
            glBindTexture(GL_TEXTURE_2D, self.textures[texture_name])
        glCallList(self.gl_list)