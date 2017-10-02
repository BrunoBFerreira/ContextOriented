#from khepri.coords import *
from math import *
from itertools import *
from khepri.matrix44 import *
from khepri.vector3 import *
from khepri.util import *

# should we use the matrix types from presentation core?
#mport clr
#clr.AddReference("PresentationCore")
#from System.Windows.Media.Media3D import Point3D, Vector3D, Matrix3D



#NOTE CS should be frame
#NOTE maybe use __and__ to allow "naked" locations (without frame) to be added
#e.g. p & xy(1,2) or p>>xy(1,2) (go see magic operators)


class CS(object):
    def __init__(self, tr):
        self.transform = tr
    
    def __repr__(self):
        return "CS(...)"

world_cs = CS(Matrix44()) #identity
current_cs = make_parameter(world_cs)

def translated_cs(dx=0, dy=0, dz=0, cs=None):
    cs = cs or current_cs()
    return CS(cs.transform*Matrix44.translation(dx, dy, dz))

def scaled_cs(sx=1, sy=None, sz=None, cs=None):
    sy = sy or sx
    sz = sz or sy
    cs = cs or current_cs()
    return CS(cs.transform*Matrix44.scale(sx, sy, sz))

def x_rotated_cs(phi=0, cs=None):
    cs = cs or current_cs()
    return CS(cs.transform*Matrix44.x_rotation(phi))

def y_rotated_cs(phi=0, cs=None):
    cs = cs or current_cs()
    return CS(cs.transform*Matrix44.y_rotation(phi))

def z_rotated_cs(phi=0, cs=None):
    cs = cs or current_cs()
    return CS(cs.transform*Matrix44.z_rotation(phi))

def equal_cs(cs0, cs1):
    return cs0 is cs1 or cs0.transform == cs1.transform

class coords(object):
    def __init__(self, x=0, y=0, z=0, cs=None, raw=None):
        self.cs = cs or current_cs()
        assert isinstance(self.cs, CS), "{} is not a frame of reference".format(cs)
        self.raw = raw or Vector3(x, y, z)

    @property
    def x(self):
        return self.raw.x
    @property
    def y(self):
        return self.raw.y
    @property
    def z(self):
        return self.raw.z
    @property
    def coords(self):
        return self.raw.x, self.raw.y, self.raw.z
    @property
    def cyl_rho(c):
        return sqrt(c.x**2 + c.y**2)
    @property
    def sph_rho(c):
        return sqrt(c.x**2 + c.y**2 + c.z**2)
    @property
    def phi(c):
        x = c.x
        y = c.y
        return 0 if 0 == x == y else atan2(y, x)
    @property
    def psi(c):
        x, y, z = c.x, c.y, c.z
        if 0 == x == y == z:
            return 0
        else:
            return atan2(sqrt(x*x + y*y), z)
    @property
    def world_transformation(p):
        t = Matrix44.translation(p.x, p.y, p.z)
        if p.cs is world_cs:
            return t
        else:
            return p.cs.transform*t
            
    def __eq__(p, q):
        return p.raw == q.raw

    def __ne__(p, q):
        return p.raw != q.raw


def raw_and_cs(p, q):
    if equal_cs(p.cs, q.cs):
        return p.raw, q.raw, p.cs
    else:
        return p.raw_in_world, q.raw_in_world, world_cs

def raw_vec_and_cs(p, q):
    if equal_cs(p.cs, q.cs):
        return p.raw, q.raw, p.cs
    elif equal_cs(q.cs, world_cs):
        return p.raw, q.raw_in_world, p.cs
    else:
        return p.raw_in_world, q.raw_in_world, world_cs


def cx(p):
    return p.x

def cy(p):
    return p.y

def cz(p):
    return p.z

def pol_rho(p):
    return p.cyl_rho

def pol_phi(p):
    return p.phi

def cyl_rho(p):
    return p.cyl_rho

def cyl_phi(p):
    return p.phi

def cyl_z(p):
    return p.z

def sph_rho(p):
    return p.sph_rho

def sph_phi(p):
    return p.phi

def sph_psi(p):
    return p.psi

class loc(coords):
    def __add__(self, other):
        return other._locAdd(self)

    def __sub__(self, other):
        return other._locSub(self)


class vec(coords):
    def __add__(self, other):
        return other._vecAdd(self)
    
    def __sub__(self, other):
        return other._vecSub(self)

    def __neg__(self):
        return vxyz(0, 0, 0, self.cs, self.raw*-1)

    def __truediv__(self, other):
        if is_number(other):
            return vxyz(0, 0, 0, self.cs, self.raw*(1/other)) 
        else:
             raise ValueError("Vector only divide by number")

    def __mul__(self, other):
        if is_number(other):
            return vxyz(0, 0, 0, self.cs, self.raw*other) 
        else:
             raise ValueError("Vector only divide by number")


class xyz(loc):

    @property
    def raw_in_world(c):
        if c.cs is world_cs:
            return c.raw
        else:
            return c.cs.transform.transform_vec3(c.raw)

    def _vecAdd(p, v):
        pr, vr, cs = raw_vec_and_cs(p, v)
        return xyz(0, 0, 0, cs, vr + pr)

    def _vecSub(p, v):
        pr, vr, cs = raw_vec_and_cs(p, v)
        return xyz(0, 0, 0, cs, vr - pr)

    def _locAdd(q, p):
        # Treat p as a vector in q's cs
        # This might be theoretically incorrect but it is very helpful
        #return xyz(0, 0, 0, q.cs, q.raw + p.raw)
        raise RuntimeError("Positions cannot be added")

    def _locSub(q, p):
        pr, qr, cs = raw_and_cs(p, q)
        return vxyz(0, 0, 0, cs, pr - qr)

    def __repr__(self):
        return "xyz({0},{1},{2}{3})".format(
            self.x, self.y, self.z,
            "" if self.cs is world_cs else ", cs(...))")

class vxyz(vec):

    @property
    def raw_in_world(c):
        if c.cs is world_cs:
            return c.raw
        else:
            r = c.raw
            x, y, z = c.cs.transform.transform4((r.x, r.y, r.z, 0))
            return Vector3(x, y, z)

    
    def _locAdd(v, p):
        pr, vr, cs = raw_vec_and_cs(p, v)
        return xyz(0, 0, 0, cs, pr + vr)

    def _locSub(v, p):
        pr, vr, cs = raw_vec_and_cs(p, v)
        return xyz(0, 0, 0, cs, pr - vr)

    def _vecAdd(w, v):
        wr, vr, cs = raw_and_cs(w, v)
        return vxyz(0, 0, 0, cs, vr + wr)

    def _vecSub(w, v):
        wr, vr, cs = raw_and_cs(w, v)
        return vxyz(0, 0, 0, cs, vr - wr)

    def __repr__(self):
        return "vxyz({0},{1},{2}{3})".format(
            self.x, self.y, self.z,
            "" if self.cs is world_cs else ", cs(...))")

    def cross(v0, v1):
        v0, v1 = vec_in_world(v0), vec_in_world(v1)
        x0, y0, z0 = v0.coords
        x1, y1, z1 = v1.coords
        return vxyz(y0*z1 - z0*y1,
                    z0*x1 - x0*z1,
                    x0*y1 - y0*x1,
                    world_cs)

    def dot(v0, v1):
        v0, v1 = vec_in_world(v0), vec_in_world(v1)
        x0, y0, z0 = v0.coords
        x1, y1, z1 = v1.coords
        return x0*x1 + y0*y1 + z0*z1


def vcyl(rho, phi, z, cs=None):
  return vxyz(rho*cos(phi), rho*sin(phi), z, cs)

def vpol(rho, phi, cs=None):
  return vcyl(rho, phi, 0, cs)

def cs_from_o_vx_vy(o, vx, vy):
    o = loc_in_world(o)
    vx = vec_in_world(vx)
    vy = vec_in_world(vy)
    vx = unitize(vx)
    vz = unitize(vx.cross(vy))
    vy = vz.cross(vx)
    return cs_from_o_vx_vy_vz(o, vx, vy, vz)

def cs_from_o_vx_vy_vz(o, vx, vy, vz):
    return CS(Matrix44(vx.raw, vy.raw, vz.raw, o.raw))

def cs_from_pts(p0, p1, p2, p3):
    p0, p1, p2, p3 = loc_in_world(p0), loc_in_world(p1), loc_in_world(p2), loc_in_world(p3)
    n0, n1 = p1 - p0, p2 - p0
    n2 = n0.cross(n1)
    if n2.dot(p3 - p0) < 0:
        return cs_from_o_vx_vy(p0, n0, n1)
    else:
        return cs_from_o_vx_vy(p0, n1, n0)

def cs_from_o_vz(o, vz, angle=pi/2):
    o = loc_in_world(o)
    vz = vec_in_world(vz)
    vx = vpol(1, vz.phi + angle)
    vy = unitize(vz.cross(vx))
    vz = unitize(vz)
    return cs_from_o_vx_vy_vz(o, vx, vy ,vz)

def cs_from_o_phi(o, phi):
    o, vx, vy = loc_in_world(o), vec_in_world(vcyl(1, phi, 0, o.cs)), vec_in_world(vcyl(1, phi + pi/2, 0, o.cs))
    vz = vx.cross(vy)
    return cs_from_o_vx_vy_vz(o, vx, vy, vz)

def loc_from_o_vx_vy(o, vx, vy):
    return u0(cs_from_o_vx_vy(o, vx, vy))

def loc_from_o_vz(o, vz, angle=pi/2):
    return u0(cs_from_o_vz(o, vz, angle))

def loc_from_pts(p0, p1, p2, p3):
    return u0(cs_from_pts(p0, p1, p2, p3))

def loc_from_o_phi(o, phi):
    return u0(cs_from_o_phi(o, phi))

def loc_in_cs(p, cs):
    if equal_cs(p.cs, cs):
        return p
    else:
        return xyz(0, 0, 0, cs, cs.transform.get_inverse().transform_vec3(p.raw_in_world))

def vec_in_cs(p, cs):
    if equal_cs(p.cs, cs):
        return p
    else:
        r = p.raw_in_world
        x, y, z = p.cs.transform.get_inverse().transform4((r.x, r.y, r.z, 0))
        return vxyz(0, 0, 0, cs, Vector3(x, y, z))

def loc_in(p, q):
    return loc_in_cs(p, q.cs)

def vec_in(p, q):
    return vec_in_cs(p, q.cs)

def u0(cs=None):
    return xyz(0, 0, 0, cs)

def ux(cs=None):
    return x(1, cs)

def uy(cs=None):
    return y(1, cs)

def uz(cs=None):
    return z(1, cs)

def uxy(cs=None):
    return xy(1, 1, cs)

def uxz(cs=None):
    return xz(1, 1, cs)

def uyz(cs=None):
    return yz(1, 1, cs)

def uxyz(cs=None):
    return xyz(1, 1, 1, cs)

def x(x=1, cs=None):
    return xyz(x, 0, 0, cs)

def y(y=1, cs=None):
    return xyz(0, y, 0, cs)

def z(z=1, cs=None):
    return xyz(0, 0, z, cs)

def xy(x, y, cs=None):
    return xyz(x, y, 0, cs)

def xz(x, z, cs=None):
    return xyz(x, 0, z, cs)

def yz(y, z, cs=None):
    return xyz(0, y, z, cs)

def vx(x=1, cs=None):
    return vxyz(x, 0, 0, cs)

def vy(y=1, cs=None):
    return vxyz(0, y, 0, cs)

def vz(z=1, cs=None):
    return vxyz(0, 0, z, cs)

def vxy(x, y, cs=None):
    return vxyz(x, y, 0, cs)

def vxz(x, z, cs=None):
    return vxyz(x, 0, z, cs)

def vyz(y, z, cs=None):
    return vxyz(0, y, z, cs)

def cyl(rho, phi, z, cs=None):
    return xyz(rho*cos(phi), rho*sin(phi), z, cs)

def vcyl(rho, phi, z, cs=None):
    return vxyz(rho*cos(phi), rho*sin(phi), z, cs)

def pol(rho, phi, cs=None):
    return cyl(rho, phi, 0, cs)

def vpol(rho, phi, cs=None):
    return vcyl(rho, phi, 0, cs)

def sph(rho, phi, psi, cs=None):
    sin_psi = sin(psi)
    return xyz(rho*cos(phi)*sin_psi, rho*sin(phi)*sin_psi, rho*cos(psi), cs)

def vsph(rho, phi, psi, cs=None):
    sin_psi = sin(psi)
    return vxyz(rho*cos(phi)*sin_psi, rho*sin(phi)*sin_psi, rho*cos(psi), cs)

#These exist for backward compatibility
def add_xyz(p, dx, dy, dz):
    return xyz(p.x + dx, p.y + dy, p.z + dz, p.cs)
    
def add_x(p, dx):
    return add_xyz(p, dx, 0, 0)

def add_y(p, dy):
    return add_xyz(p, 0, dy, 0)

def add_z(p, dz):
    return add_xyz(p, 0, 0, dz)

def add_xy(p, dx, dy):
    return add_xyz(p, dx, dy, 0)

def add_xz(p, dx, dz):
    return add_xyz(p, dx, 0, dz)

def add_yz(p, dy, dz):
    return add_xyz(p, 0, dy, dz)

def add_pol(p, rho, phi):
    return add_cyl(p, rho, phi, 0)

def add_cyl(p, rho, phi, z):
    return xyz(p.x + rho*cos(phi), p.y + rho*sin(phi), p.z + z, p.cs)

def add_sph(p, rho, phi, psi):
    sin_psi = sin(psi)
    return xyz(p.x + rho*cos(phi)*sin_psi, 
               p.y + rho*sin(phi)*sin_psi,
               p.z + rho*cos(psi),
               p.cs)



def coterminal(angle):
    k = trunc(angle/(2*pi))
    return angle - k*2*pi

def base_and_height(p0, p1OrH):
    if isinstance(p1OrH, xyz):
        p1 = p1OrH
        return loc_from_o_vz(p0, p1 - p0), distance(p0, p1)
    else:
        h = p1OrH
        return p0, h

def inverted_base_and_height(p0, p1OrH):
    if isinstance(p1OrH, xyz):
        p1 = p1OrH
        return loc_from_o_vz(p1, p0 - p1), distance(p0, p1)
    else:
        h = p1OrH
        return loc_from_o_vz(add_z(p0, h), vz(-1, p0.cs)), h

def loc_in_world(p):
  return xyz(0, 0, 0, world_cs, p.raw_in_world)

def vec_in_world(p):
  return vxyz(0, 0, 0, world_cs, p.raw_in_world)

def unitize(v):
  d = sqrt(v.x**2 + v.y**2 + v.z**2)
  return vxyz(v.x/d, v.y/d, v.z/d, v.cs)

def distance(p, q):
  v = p - q
  return sqrt(v.x**2 + v.y**2 + v.z**2)

def regular_polygon_vertices(edges=3, center=u0(), radius=1, angle=0, inscribed=False):
    r = radius if inscribed else radius/cos(pi/edges)
    return [add_pol(center, r, a) for a in division(angle, angle + 2*pi, edges, False)]

def intermediate_loc (p, q, t=0.5):
    return p + (q - p)*t
