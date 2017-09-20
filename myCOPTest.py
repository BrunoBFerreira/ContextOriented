from khepri.autocad import *
from contextpy import *

my3Dlayer = layer("3D")
my2Dlayer = layer("2D")
myAnalysisLayer = layer("analysis")

class Wall:
    def __init__(self, p1, lenght, width, height):
        self.p1 = p1
        self.length = lenght
        self.width = width
        self.height = height

    def generate(self):
        box(self.p1, self.length, self.width, self.height)

    @around(my3Dlayer)
    def generate(self):
        proceed()

    @around(my2Dlayer)
    def generate(self):
        p2 = self.p1 + vx(self.length)
        p3 = p2 + vy(self.width)
        p4 = self.p1 + vy(self.width)
        line(self.p1, p2, p3, p4, self.p1)

    @around(myAnalysisLayer)
    def generate(self):
        p2 = self.p1 + vx(self.length)
        p3 = p2 + vz(self.height)
        p4 = self.p1 + vz(self.height)
        surface_from(line(self.p1, p2, p3, p4, self.p1))

def test(l, w, h):
    w1 = Wall(u0(), l, w, h)
    with activelayer(myAnalysisLayer):
        w1.generate()

delete_all_shapes()
test(10, 2, 3)