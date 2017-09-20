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
        return box(self.p1, self.length, self.width, self.height)

    @around(my3Dlayer)
    def generate(self):
        return box(self.p1, self.length, self.width, self.height)

    @around(my2Dlayer)
    def generate(self):
        p2 = self.p1 + vx(self.length)
        p3 = p2 + vy(self.width)
        p4 = self.p1 + vy(self.width)
        return line(self.p1, p2, p3, p4, self.p1)

    @around(myAnalysisLayer)
    def generate(self):
        p2 = self.p1 + vx(self.length)
        p3 = p2 + vz(self.height)
        p4 = self.p1 + vz(self.height)
        return surface_from(line(self.p1, p2, p3, p4, self.p1))

class Slab:
    def __init__(self, path, thickness):
        self.path = path
        self.thickness = thickness

    def generate(self):
        return extrusion(surface_from(self.path), self.thickness)

    @around(my3Dlayer)
    def generate(self):
        return extrusion(surface_from(self.path), self.thickness)

    @around(my2Dlayer)
    def generate(self):
        return self.path

    @around(myAnalysisLayer)
    def generate(self):
        return surface_from(self.path)

class Door:
    def __init__(self, w, pos1, pos2):
        self.pos1 = pos1
        self.pos2 = pos2
        self.w = w

    def generate(self):
        return subtraction(self.w, box(self.pos1, self.pos2))

    @around(my3Dlayer)
    def generate(self):
        return subtraction(self.w, box(self.pos1, self.pos2))

    @around(my2Dlayer)
    def generate(self):
        """nrho = pol_rho(self.pos1)/cos(abs(pol_phi(self.pos2) - pol_phi(self.pos1)))
        aux1 = pol(nrho, pol_phi(self.pos2))
        line(self.pos1, aux1)
        arc(self.pos1, distance(self.pos1, aux1), pol_phi(self.pos1), pol_phi(self.pos1) + pi/2)"""
        empty_shape()


    @around(myAnalysisLayer)
    def generate(self):
        return subtraction(self.w, box(self.pos1, self.pos2))


def test():
    w1 = Wall(u0(), 10, 0.5, 3)
    with activelayer(myAnalysisLayer):
        d1 = Door(w1.generate(), xyz(4, -0.1, -0.1), xyz(5, 1.2, 2))
        d1.generate()

delete_all_shapes()
test()