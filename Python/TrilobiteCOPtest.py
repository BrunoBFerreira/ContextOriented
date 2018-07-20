from khepri.autocad import *
from contextpy import *

my3DLayer = layer("3D")
my2DLayer = layer("2D")
myAnalysisLayer = layer("analysis")

def rotated_v(v, alpha):
    return vpol(pol_rho(v), pol_phi(v) + alpha, v.cs)

class Wall:
    def __init__(self, p1, p2, width = 0.5, height = 3):
        self.p1 = p1
        self.p2 = p2
        self.width = width
        self.height = height
        self.result = empty_shape()


    def generate(self):
        v0 = self.p2 - self.p1
        v1 = rotated_v(v0, pi / 2)
        c = loc_from_o_vx_vy(self.p1, v0, v1)
        self.result = box(c - vy(self.width / 2, c.cs), distance(self.p1, self.p2), self.width, self.height)
        return self.result

    @around(my3DLayer)
    def generate(self):
        v0 = self.p2 - self.p1
        v1 = rotated_v(v0, pi / 2)
        c = loc_from_o_vx_vy(self.p1, v0, v1)
        self.result = box(c - vy(self.width / 2, c.cs), distance(self.p1, self.p2), self.width, self.height)
        return self.result

    @around(my2DLayer)
    def generate(self):
        v0 = self.p2 - self.p1
        v1 = rotated_v(v0, pi / 2)
        c = loc_from_o_vx_vy(self.p1, v0, v1)
        self.result = rectangle(c - vy(self.width / 2, c.cs), distance(self.p1, self.p2), self.width)
        return self.result

    @around(myAnalysisLayer)
    def generate(self):
        v0 = self.p2 - self.p1
        v1 = rotated_v(v0, pi / 2)
        c = loc_from_o_vx_vy(self.p1, v0, v1)
        p2 = c + vx(distance(self.p1, self.p2), c.cs)
        p3 = p2 + vz(self.height)
        p4 = p3 - vx(distance(self.p1, self.p2), c.cs)
        return surface_from(line(c, p2, p3, p4, c))

class Slab:
    def __init__(self, path, thickness=0.2):
        self.path = path
        self.thickness = thickness

    def generate(self):
        return extrusion(surface_from(self.path), self.thickness)

    @around(my3DLayer)
    def generate(self):
        return extrusion(surface_from(self.path), self.thickness)

    @around(my2DLayer)
    def generate(self):
        return self.path

    @around(myAnalysisLayer)
    def generate(self):
        return surface_from(self.path)

class Slab_With_Opening:
    def __init__(self, path, openings, thickness=0.2):
        self.path = path
        self.thickness = thickness
        self.openings = openings

    def generate(self):
        result = extrusion(surface_from(self.path), self.thickness)
        for lns in self.openings:
            result = subtraction(result,
                                 extrusion(surface_from(line(lns)), 2*self.thickness))
        return result

    @around(my3DLayer)
    def generate(self):
        result = extrusion(surface_from(self.path), self.thickness)
        for lns in self.openings:
            result = subtraction(result,
                                 extrusion(surface_from(line(lns)), 2 * self.thickness))
        return result

    @around(my2DLayer)
    def generate(self):
        return self.path

    @around(myAnalysisLayer)
    def generate(self):
        result = surface_from(self.path)
        for lns in self.openings:
            result = subtraction(result,
                                 surface_from(line(lns)))
        return result

class Door:
    def __init__(self, w, p1, p2, h):
        self.p1 = p1
        self.p2 = p2
        self.height = h
        self.w = w

    def generate(self):
        v0 = self.p2 - self.p1
        v1 = rotated_v(v0, pi / 2)
        c = loc_from_o_vx_vy(self.p1, v0, v1)
        return subtraction(self.w.result, box(c - vy((self.w.width / 2) + 0.01, c.cs),
                                              distance(self.p2, self.p1),
                                              self.w.width + 0.01,
                                              self.height))
    @around(my3DLayer)
    def generate(self):
        v0 = self.p2 - self.p1
        v1 = rotated_v(v0, pi / 2)
        c = loc_from_o_vx_vy(self.p1, v0, v1)
        return subtraction(self.w.result, box(c - vy((self.w.width / 2) + 0.01, c.cs),
                                                     distance(self.p2, self.p1),
                                                     self.w.width + 0.01,
                                                     self.height))

    @around(my2DLayer)
    def generate(self):
        """nrho = pol_rho(self.pos1)/cos(abs(pol_phi(self.pos2) - pol_phi(self.pos1)))
        aux1 = pol(nrho, pol_phi(self.pos2))
        line(self.pos1, aux1)
        arc(self.pos1, distance(self.pos1, aux1), pol_phi(self.pos1), pol_phi(self.pos1) + pi/2)"""
        pass


    @around(myAnalysisLayer)
    def generate(self):
        v0 = self.p2 - self.p1
        v1 = rotated_v(v0, pi / 2)
        c = loc_from_o_vx_vy(self.p1, v0, v1)
        p2 = c + vx(distance(self.p1, self.p2), c.cs)
        p3 = p2 + vz(self.height)
        p4 = p3 - vx(distance(self.p1, self.p2), c.cs)
        return subtraction(self.w.result, surface_from(line(c, p2, p3, p4, c)))


def test():
    w1 = Wall(y(10), u0(), 0.5, 3)
    w2 = Wall(u0(), x(10), 1, 3)
    with activelayer(my3DLayer):
        w2.generate()
        w1.generate()
        d1 = Door(w1, x(2), x(4), 1.5)
        d1.generate()

def test2():
    al = activelayer(my3DLayer)
    with al:
        if not(al._getActiveLayers().__contains__(my2DLayer)):
            Slab_With_Opening(line(xyz(0, 0, 0), xyz(10, 0, 0), xyz(10, 10, 0), xyz(0, 10, 0), xyz(0, 0, 0)),
                              [[xyz(2.5, 2.5, 0), xyz(7.5, 2.5, 0), xyz(7.5, 7.5, 0), xyz(2.5, 7.5, 0), xyz(2.5, 2.5, 0)],
                               [xyz(7.5, 2.5, 0), xyz(8.2, 2.5, 0), xyz(8.2, 5, 0), xyz(7.5, 5, 0), xyz(7.5, 2.5, 0)]]).generate()
        else:
            pass


#delete_all_shapes()
#test2()
#surface_from(line(u0(), x(10), y(5), u0()))