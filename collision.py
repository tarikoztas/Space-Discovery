from OpenGL.GL import *

class AABB:
    def __init__(self, min_x, max_x, min_y, max_y, min_z, max_z):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.min_z = min_z
        self.max_z = max_z

    def check_collision(self, px, py, pz, radius=0.25):
        return (px + radius >= self.min_x and px - radius <= self.max_x and
                py + radius >= self.min_y and py - radius <= self.max_y and
                pz + radius >= self.min_z and pz - radius <= self.max_z)

    def draw_debug(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glColor3f(1.0, 0.0, 0.0)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        # Alt
        glVertex3f(self.min_x, self.min_y, self.min_z); glVertex3f(self.max_x, self.min_y, self.min_z)
        glVertex3f(self.max_x, self.min_y, self.min_z); glVertex3f(self.max_x, self.min_y, self.max_z)
        glVertex3f(self.max_x, self.min_y, self.max_z); glVertex3f(self.min_x, self.min_y, self.max_z)
        glVertex3f(self.min_x, self.min_y, self.max_z); glVertex3f(self.min_x, self.min_y, self.min_z)
        # Üst
        glVertex3f(self.min_x, self.max_y, self.min_z); glVertex3f(self.max_x, self.max_y, self.min_z)
        glVertex3f(self.max_x, self.max_y, self.min_z); glVertex3f(self.max_x, self.max_y, self.max_z)
        glVertex3f(self.max_x, self.max_y, self.max_z); glVertex3f(self.min_x, self.max_y, self.max_z)
        glVertex3f(self.min_x, self.max_y, self.max_z); glVertex3f(self.min_x, self.max_y, self.min_z)
        # Dikeler
        glVertex3f(self.min_x, self.min_y, self.min_z); glVertex3f(self.min_x, self.max_y, self.min_z)
        glVertex3f(self.max_x, self.min_y, self.min_z); glVertex3f(self.max_x, self.max_y, self.min_z)
        glVertex3f(self.max_x, self.min_y, self.max_z); glVertex3f(self.max_x, self.max_y, self.max_z)
        glVertex3f(self.min_x, self.min_y, self.max_z); glVertex3f(self.min_x, self.max_y, self.max_z)
        glEnd()
        glEnable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)