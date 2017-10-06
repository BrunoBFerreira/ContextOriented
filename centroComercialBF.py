from TrilobiteCOP import *
from sys import *

delete_all_shapes()

wall_height = 4000
door_height = 3000
wall_thickness = 100
floor_thickness = 300

wall_door_start = 0.1
wall_door_end = 0.3

def shop(p, v, l, w):
    v1 = rotated_v(v, pi / 2)
    c = loc_from_o_vx_vy(p, v, v1)
    w1 = Wall(c + vy(w/2, c.cs), c + vy(-w/2, c.cs), wall_thickness, wall_height)
    w1.generate()
    w2 = Wall(c + vy(-w/2, c.cs), c + vxy(l, -w/2, c.cs), wall_thickness, wall_height)
    w2.generate()
    w3 = Wall(c + vxy(l, -w/2, c.cs), c + vxy(l, w/2, c.cs), wall_thickness, wall_height)
    w3.generate()
    w4 = Wall(c + vxy(l, w/2, c.cs), c + vy(w/2, c.cs), wall_thickness, wall_height)
    w4.generate()
    d1 = Door(w3, c+vxy(wall_door_start*l, w/2, c.cs), c+vxy(wall_door_end*l, w/2, c.cs), door_height)
    d1.generate()

def line_shops(p0, p1, l, w):
    d = distance(p0, p1)
    v = unitize(p1 - p0)
    n = floor(d/l)
    if n == 0:
        raise Exception("Insuficient space!")
    l = d/n
    return [shop(p0 + v*r, v, l, w) for r in division(0, d, n, False)]

def polygonal_shapes(ps, l, w, shape):
    if len(ps) == 2:
        return [shape(ps[0], ps[1], l, w)]
    else:
        p0 = ps[0]
        p1 = ps[1]
        p2 = ps[2]
        v01 = unitize(p1 - p0) * w/2
        v12 = unitize(p2 - p1) * w/2
        p1e = p1 + v01
        p2s = p1 + v12
        return [shape(p0, p1e, l, w)] + polygonal_shapes([p2s] + ps[2:], l, w, shape)


def polygonal_shops(ps, l, w):
    return polygonal_shapes(ps, l, w, line_shops)

def v_in_v(v0, v1):
    v = v0 + v1
    return v*(v0.dot(v0))/(v.dot(v0))

def offset_line(ps, d):
    vs = [rotated_v(unitize(p1 - p0)*d, pi/2) for p0, p1 in zip(ps[:-1], ps[1:])]
    vs = [vs[0]] + [v_in_v(v0, v1) for v0, v1 in zip(vs[:-1], vs[1:])] + [vs[-1]]
    return [p + v for p, v in zip(ps, vs)]

def single_sided_shops(ps, l, w):
    polygonal_shops(offset_line(ps, w/2), l, w)

def double_sided_shops(ps, l, w):
    polygonal_shops(offset_line(ps, w/2), l, w)
    polygonal_shops(offset_line(list(reversed(ps)), w/2), l, w)

def veli(a, b, phi):
    return vxy(a*cos(phi), b*sin(phi))

def L_points(c, la, lb, alpha, dalpha):
    return [c+veli(la, lb, alpha), c+veli(la*sqrt(2), lb*sqrt(2), alpha+dalpha/2), c+veli(la, lb, alpha+dalpha)]

def U_points(c, l, alpha, dalpha):
    return [c+vpol(l, alpha), c+vpol(l*sqrt(2), alpha+dalpha/2), c+vpol(l, alpha+dalpha)]

def single_sided_circular_shops(p, r, l, w, ex, ey):
    for fi in division(0, 2*pi, 4, False):
        single_sided_shops(L_points(p+veli(ex/2*sqrt(2), ey/2*sqrt(2), fi+pi/4), r-ex/2, r-ey/2, fi, pi/2), l, w)
    for fi in division(0, 2*pi, 4, False):
        #mall_exit_door(p+vpol(r, fi + pi/2), veli(ex, ey, fi))
        pass


def double_sided_circular_shops(p, r, l, w, ex, ey):
    for fi in division(0, 2 * pi, 4, False):
        double_sided_shops(
            L_points(p + veli(ex / 2 * sqrt(2), ey / 2 * sqrt(2), fi + pi / 4), r - ex / 2, r - ey / 2, fi, pi / 2), l,
            w)


def double_sided_n_circular_shops(p, r, l, w, ex, ey, e, n):
    if n == 0:
        pass
    else:
        double_sided_circular_shops(p, r, l, w, ex, ey)
        double_sided_n_circular_shops(p, r - 2 * w - e, l, w, ex, ey, e, n - 1)

def colombo(p, r, l, w, ex, ey, n):
    e = max(ex, ey)
    single_sided_circular_shops(p, r, l, w, ex, ey)
    double_sided_n_circular_shops(p, r - 2*w - e, l, w, ex, ey, e, n - 1)
    p0 = p+vxy(-r, -r)
    s1 = Slab(line(p0, p0 + vx(2*r), p0 + vxy(2*r, 2*r), p0+vy(2*r), p0), -floor_thickness)
    s1.generate()

def colombo_atrio(p, r, l, a, ex, ey, n):
    e = max(ex, ey)
    w = (r - a - (n - 1)*e)/(2*n - 1)
    colombo(p, r, l, w, ex, ey, n)

with activelayer(my3DLayer):
    colombo_atrio(xy(0,0), 100000, 12000, 25000, 7000, 7000, 4)

