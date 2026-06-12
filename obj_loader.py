import os
import pygame
from OpenGL.GL import *

class OBJModel:
    def __init__(self, filename):
        self.vertices = []
        self.texcoords = []
        self.normals = []
        self.faces = []
        self.mtl_data = {}
        self.current_material = None
        self.dirname = os.path.dirname(filename)
        
        self.fallback_texture_id = None
        self.detect_fallback_texture()
        
        self.gl_list = 0
        self.load_obj(filename)
        self.compile_to_gl_list()

    def detect_fallback_texture(self):
        """MTL dosyası barındırmayan klasörler için ana görseli tespit eder"""
        if not os.path.exists(self.dirname):
            return
        for file in os.listdir(self.dirname):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')) and "lights" not in file.lower():
                # console1.jpg veya benzeri ana dokuyu seçer
                if "1.2" not in file: 
                    full_path = os.path.join(self.dirname, file)
                    self.fallback_texture_id = self.load_texture(full_path)
                    break

    def load_mtl(self, mtl_filename):
        """Modelin materyal (.mtl) dosyasını ve ilişkili texture görselini yükler"""
        path = os.path.join(self.dirname, mtl_filename)
        if not os.path.exists(path):
            return
            
        current_mtl = None
        with open(path, "r") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.split()
                
                if parts[0] == "newmtl":
                    current_mtl = parts[1]
                    self.mtl_data[current_mtl] = {
                        "Kd": [1.0, 1.0, 1.0],
                        "texture_id": None
                    }
                elif current_mtl and parts[0] == "Kd":
                    self.mtl_data[current_mtl]["Kd"] = [float(x) for x in parts[1:4]]
                elif current_mtl and parts[0] == "map_Kd":
                    tex_name = " ".join(parts[1:])
                    tex_path = os.path.join(self.dirname, tex_name)
                    self.mtl_data[current_mtl]["texture_id"] = self.load_texture(tex_path)

    def load_texture(self, path):
        """Görsel dosyasını OpenGL doku belleğine aktarır"""
        if not os.path.exists(path):
            return None
        try:
            img = pygame.image.load(path)
            img_data = pygame.image.tostring(img, "RGBA", 1)
            w, h = img.get_width(), img.get_height()
            
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            return tex_id
        except Exception as e:
            print(f"Doku yükleme hatası ({path}): {e}")
            return None

    def load_obj(self, filename):
        if not os.path.exists(filename):
            print(f"Hata: Model dosyası bulunamadı -> {filename}")
            return

        with open(filename, "r") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.split()
                
                if parts[0] == "mtllib":
                    self.load_mtl(" ".join(parts[1:]))
                elif parts[0] == "v":
                    self.vertices.append([float(x) for x in parts[1:4]])
                elif parts[0] == "vt":
                    self.texcoords.append([float(x) for x in parts[1:3]])
                elif parts[0] == "vn":
                    self.normals.append([float(x) for x in parts[1:4]])
                elif parts[0] == "usemtl":
                    self.current_material = parts[1]
                elif parts[0] == "f":
                    face_vertices = []
                    for p in parts[1:]:
                        vals = p.split('/')
                        v_idx = int(vals[0]) - 1
                        vt_idx = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else None
                        vn_idx = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else None
                        face_vertices.append((v_idx, vt_idx, vn_idx))
                    self.faces.append((face_vertices, self.current_material))

    def compile_to_gl_list(self):
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        
        glEnable(GL_TEXTURE_2D)
        last_bound_texture = None
        current_texture_state = True
        
        for face_vertices, mat_name in self.faces:
            target_texture = None
            use_lighting_color = False
            kd_color = [1.0, 1.0, 1.0]
            
            if mat_name in self.mtl_data:
                mat = self.mtl_data[mat_name]
                if mat["texture_id"] is not None:
                    target_texture = mat["texture_id"]
                else:
                    use_lighting_color = True
                    kd_color = mat["Kd"]
            elif self.fallback_texture_id is not None and len(self.texcoords) > 0:
                target_texture = self.fallback_texture_id

            if target_texture is not None:
                if not current_texture_state:
                    glEnable(GL_TEXTURE_2D)
                    current_texture_state = True
                if target_texture != last_bound_texture:
                    glBindTexture(GL_TEXTURE_2D, target_texture)
                    last_bound_texture = target_texture
                glColor3f(1.0, 1.0, 1.0)
            else:
                if current_texture_state:
                    glDisable(GL_TEXTURE_2D)
                    current_texture_state = False
                    last_bound_texture = None
                if use_lighting_color:
                    glColor3fv(kd_color)
                else:
                    glColor3f(0.6, 0.6, 0.6)

            if len(face_vertices) == 3:
                glBegin(GL_TRIANGLES)
            elif len(face_vertices) == 4:
                glBegin(GL_QUADS)
            else:
                glBegin(GL_POLYGON)

            for v_idx, vt_idx, vn_idx in face_vertices:
                if vn_idx is not None and vn_idx < len(self.normals):
                    glNormal3fv(self.normals[vn_idx])
                if vt_idx is not None and vt_idx < len(self.texcoords) and current_texture_state:
                    glTexCoord2fv(self.texcoords[vt_idx])
                if v_idx < len(self.vertices):
                    glVertex3fv(self.vertices[v_idx])
            glEnd()
            
        glEnable(GL_TEXTURE_2D)
        glEndList()

    def render(self):
        glCallList(self.gl_list)