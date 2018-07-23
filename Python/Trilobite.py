from khepri.autocad import *
from contextpy import *

layer_3d = layer("3D")
layer_2d = layer("2D")
layer_analysis = layer("analysis")
layer_space = layer("space")
layer_level = layer("level")

default_level_height = 3
space_index = 0

levels = dict({})
spaces = dict({})
geometry = set()


def add_level(level, elevation):
    if elevation in levels:
        raise ValueError("Level already exists")
    else:
        levels[elevation] = level


def upper_level(level):
    global default_level_height
    new_height = level.elevation + default_level_height
    if new_height in levels:
        return levels[new_height]
    else:
        return Level(new_height)


def set_current_level(level):
    global current_level
    current_level = level


def add_space(space, name):
    if name in spaces:
        raise ValueError("Space already exists")
    else:
        spaces[name] = space


def set_current_space(space):
    global current_space
    current_space = space


def add_geometry(element):
    if element not in geometry:
        geometry.add(element)


def generate():
    for shape in geometry:
        shape.generate()


@around(layer_space)
def generate():
    global current_space
    if current_space is not None:
        for shape in current_space.elements:
            shape.generate()


@around(layer_level)
def generate():
    global current_level
    for shape in current_level.elements:
        shape.generate()


def rotated_v(v, alpha):
    return vpol(pol_rho(v), pol_phi(v) + alpha, v.cs)


def form_closed_shape(bounds):
    for s1, s2 in zip(bounds, bounds[1:] + [bounds[0]]):
        if not s1.intersect(s2):
            return False
    return True


class Level:
    def __init__(self, elevation, name="Level"):
        self.elevation = elevation
        if name == "Level":
            self.name = name + str(len(levels) + 1)
        else:
            self.name = name
        add_level(self, elevation)
        self.elements = set()

    def add_space(self, space):
        self.spaces += space

    def add_element(self, element):
        if element not in self.elements:
            self.elements.add(element)


class Space:
    def __init__(self, bounds, bottom_level=None, top_level=None, interior=True, name="Space"):
        assert len(bounds) > 2
        if not form_closed_shape(bounds):
            raise ValueError("Bounds do not form a closed shape")
        self.bounds = bounds
        if name == "Space":
            global space_index
            self.name = name + str(space_index)
            space_index += 1
        else:
            self.name = name
        if bottom_level is None:
            global current_level
            self.lower_level = current_level
        else:
            self.lower_level = bottom_level
        if top_level is None:
            self.top_level = upper_level(self.lower_level)
        else:
            self.top_level = top_level
        self.interior = interior
        add_space(self, self.name)
        self.elements = set()

    def is_inside(self, p, host):
        return host in self.elements

    def is_inside(self, p):
        f = xy(+inf, p.y)
        new_bound = Bound(p, f)
        count=0
        for b in self.bounds:
            if b.intersect(new_bound):
                if b.orientation(p) == 0:
                    return b.on_bound(p)
                count += 1
        return count % 2 == 1

    def add_element(self, element, pts, host=None):
        if element not in self.elements:
            for p in pts:
                if host is not None:
                    if not self.is_inside(p, host):
                        raise ValueError("Element is not inside the desired space")
                else:
                    if not self.is_inside(p):
                        raise ValueError("Element is not inside the desired space")
            self.elements.add(element)


class Bound:
    def __init__(self, p1, p2, element=None):
        self.p1 = p1
        self.p2 = p2
        self.element = element  # it will be used to associate a wall with a bound, for example

    def is_right(self, p):
        value = copysign(1, (self.p2.x - self.p1.x)*(p.y - self.p1.y) - (self.p2.y - self.p1.y)*(p.x - self.p1.x))
        return value >= 0

    def orientation(self, p):
        val = (p.y - self.p1.y)*(self.p2.x - p.x) - (p.x - self.p1.x)*(self.p2.y - p.y)
        if val == 0:
            return 0
        else:
            return 1 if val > 0 else 2

    def on_bound(self, p):
        return max(self.p1.x, self.p2.x) >= p.x >= min(self.p1.x, self.p2.x) and max(self.p1.y, self.p2.y) >= p.y >= min(
            self.p1.y, self.p2.y)

    def intersect(self, b):
        o1 = self.orientation(b.p1)
        o2 = self.orientation(b.p2)
        o3 = b.orientation(self.p1)
        o4 = b.orientation(self.p2)

        if o1 != o2 and o3 != o4:
            return True

        if o1 == 0 and self.on_bound(b.p1):
            return True

        if o2 == 0 and self.on_bound(b.p2):
            return True

        if o3 == 0 and b.on_bound(self.p1):
            return True

        if o4 == 0 and b.on_bound(self.p2):
            return True

        return False


class Wall:
    def __init__(self, p1, p2, width=0.5, height=3, lvls=[], spcs=[]):
        self.p1 = p1
        self.p2 = p2
        self.width = width
        self.height = height
        self.result = None
        add_geometry(self)
        if lvls:
            for lvl in lvls:
                lvl.add_element(self)
        if spaces:
            for spc in spcs:
                spc.add_element(self, [p1, p2])

    def generate(self):
        if self.result is None:
            v0 = self.p2 - self.p1
            v1 = rotated_v(v0, pi / 2)
            c = loc_from_o_vx_vy(self.p1, v0, v1)
            self.result = box(c - vy(self.width / 2, c.cs), distance(self.p1, self.p2), self.width, self.height)
        return self.result

    @around(layer_3d)
    def generate(self):
        if self.result is None:
            v0 = self.p2 - self.p1
            v1 = rotated_v(v0, pi / 2)
            c = loc_from_o_vx_vy(self.p1, v0, v1)
            self.result = box(c - vy(self.width / 2, c.cs), distance(self.p1, self.p2), self.width, self.height)
        return self.result

    @around(layer_2d)
    def generate(self):
        if self.result is None:
            v0 = self.p2 - self.p1
            v1 = rotated_v(v0, pi / 2)
            c = loc_from_o_vx_vy(self.p1, v0, v1)
            self.result = rectangle(c - vy(self.width / 2, c.cs), distance(self.p1, self.p2), self.width)
        return self.result

    @around(layer_analysis)
    def generate(self):
        if self.result is None:
            v0 = self.p2 - self.p1
            v1 = rotated_v(v0, pi / 2)
            c = loc_from_o_vx_vy(self.p1, v0, v1)
            p2 = c + vx(distance(self.p1, self.p2), c.cs)
            p3 = p2 + vz(self.height)
            p4 = p3 - vx(distance(self.p1, self.p2), c.cs)
            self.result = surface_from(line(c, p2, p3, p4, c))
        return self.result


class Slab:
    def __init__(self, path, thickness=0.2, lvls=[], spcs=[]):
        self.path = path
        self.thickness = thickness
        self.result = None
        add_geometry(self)
        if lvls:
            for lvl in lvls:
                lvl.add_element(self)
        if spaces:
            for spc in spcs:
                spc.add_element(self, path)

    def generate(self):
        if self.result is None:
            self.result = extrusion(surface_from(line(self.path)), self.thickness)
        return self.result

    @around(layer_3d)
    def generate(self):
        if self.result is None:
            self.result = extrusion(surface_from(line(self.path)), self.thickness)
        return self.result

    @around(layer_2d)
    def generate(self):
        if self.result is None:
            self.result = line(self.path)
        return self.result

    @around(layer_analysis)
    def generate(self):
        if self.result is None:
            self.result = surface_from(line(self.path))
        return self.result


class SlabWithOpening:
    def __init__(self, path, openings, thickness=0.2, lvls=[], spcs=[]):
        self.path = path
        self.thickness = thickness
        self.openings = openings
        self.result = None
        if lvls:
            for lvl in lvls:
                lvl.add_element(self)
        if spaces:
            for spc in spcs:
                spc.add_element(self, path)

    def generate(self):
        if self.result is None:
            result = extrusion(surface_from(line(self.path)), self.thickness)
            for lns in self.openings:
                result = subtraction(result,
                                     extrusion(surface_from(line(lns)), 2 * self.thickness))
            self.result = result
        return self.result

    @around(layer_3d)
    def generate(self):
        if self.result is None:
            result = extrusion(surface_from(line(self.path)), self.thickness)
            for lns in self.openings:
                result = subtraction(result,
                                     extrusion(surface_from(line(lns)), 2 * self.thickness))
            self.result = result
        return self.result

    @around(layer_2d)
    def generate(self):
        if self.result is None:
            self.result = line(self.path)
        return self.result

    @around(layer_analysis)
    def generate(self):
        if self.result is None:
            result = surface_from(line(self.path))
            for lns in self.openings:
                result = subtraction(result,
                                     surface_from(line(lns)))
            self.result = result
        return self.result


class Door:
    def __init__(self, w, p1, p2, h, lvls=[], spcs=[]):
        self.p1 = p1
        self.p2 = p2
        self.height = h
        self.w = w
        self.result = None
        if lvls:
            for lvl in lvls:
                lvl.add_element(self)
        if spaces:
            for spc in spcs:
                spc.add_element(self, [p1, p2], w)

    def generate(self):
        if self.result is None:
            v0 = self.p2 - self.p1
            v1 = rotated_v(v0, pi / 2)
            c = loc_from_o_vx_vy(self.p1, v0, v1)
            if self.w.result is None:
                self.w.generate()
            self.w.result = subtraction(self.w.result, box(c - vy((self.w.width / 2) + 0.01, c.cs),
                                                           distance(self.p2, self.p1),
                                                           self.w.width + 0.01,
                                                           self.height))
            self.result = self.w.result  # It is the same now. Update when the doors have an actual shape to be added
        return self.result

    @around(layer_3d)
    def generate(self):
        if self.result is None:
            v0 = self.p2 - self.p1
            v1 = rotated_v(v0, pi / 2)
            c = loc_from_o_vx_vy(self.p1, v0, v1)
            if self.w.result is None:
                self.w.generate()
            self.w.result = subtraction(self.w.result, box(c - vy((self.w.width / 2) + 0.01, c.cs),
                                                           distance(self.p2, self.p1),
                                                           self.w.width + 0.01,
                                                           self.height))
            self.result = self.w.result  # It is the same now. Update when the doors have an actual shape to be added
        return self.result

    @around(layer_2d)
    def generate(self):
        """nrho = pol_rho(self.pos1)/cos(abs(pol_phi(self.pos2) - pol_phi(self.pos1)))
        aux1 = pol(nrho, pol_phi(self.pos2))
        line(self.pos1, aux1)
        arc(self.pos1, distance(self.pos1, aux1), pol_phi(self.pos1), pol_phi(self.pos1) + pi/2)"""
        pass

    @around(layer_analysis)
    def generate(self):
        if self.result is None:
            v0 = self.p2 - self.p1
            v1 = rotated_v(v0, pi / 2)
            c = loc_from_o_vx_vy(self.p1, v0, v1)
            p2 = c + vx(distance(self.p1, self.p2), c.cs)
            p3 = p2 + vz(self.height)
            p4 = p3 - vx(distance(self.p1, self.p2), c.cs)
            if self.w.result is None:
                self.w.generate()
            self.w.result = subtraction(self.w.result, surface_from(line(c, p2, p3, p4, c)))
            self.result = self.w.result  # Check comment in the other version of generate
        return self.result


levels[0] = Level(0, "Level 0")
current_level = levels[0]
current_space = None
