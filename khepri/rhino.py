#coding=utf8
from __future__ import division
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from math import *


from khepri.shape import *
from khepri.util import *
from khepri.coords import *
import numbers
import math
import Rhino
import scriptcontext
import rhinoscriptsyntax as rh
import System.Guid

#mport clr
#clr.AddReference("PresentationCore")
#from System.Windows.Media.Media3D import Point3D, Vector3D, Matrix3D

#initialization
render_backend_dir('Rhinoceros')



db = scriptcontext.doc.Objects
vs = scriptcontext.doc.Views
geo = Rhino.Geometry

def rawxyz(x, y, z):
    return geo.Point3d(x, y, z)

rawu0 = rawxyz(0, 0, 0)

def Pt(p):
    p = p.raw_in_world
    return geo.Point3d(p.x, p.y, p.z)

def fromPt(p):
    return xyz(p[0], p[1], p[2])

def Vt(v):
    v = v.raw_in_world
    return geo.Vector3d(v.x, v.y, v.z)

def fromVt(p):
    return vxyz(p[0], p[1], p[2])

def Pl(p):
    t = p.world_transformation
    pl = geo.Plane(geo.Point3d(t[3,0], t[3,1], t[3,2]), 
                   geo.Vector3d(t[0,0], t[0,1], t[0,2]),
                   geo.Vector3d(t[1,0], t[1,1], t[1,2]))
    return pl

def fromPlane(pl):
    return u0(cs_from_o_vx_vy_vz(fromPt(pl.Origin),
                                 fromVt(pl.XAxis),
                                 fromVt(pl.YAxis),
                                 fromVt(pl.ZAxis)))

def _surface_from_curves(curves):
    return db.AddBrep(singleton(geo.Brep.CreatePlanarBreps(curves)))

def _geometry_from_id(id):
    return db.Find(id).Geometry

def _surface_from_id(id):
    curve = _geometry_from_id(id)
    r = db.AddBrep(singleton(geo.Brep.CreatePlanarBreps([curve])))
    return r

def _brep_from_id(id):
    geom = _geometry_from_id(id)
    if isinstance(geom, geo.Brep): return geom
    if isinstance(geom, geo.Extrusion): return geom.ToBrep(True)
    raise ValueError("unable to convert %s into Brep geometry"%id)

def _point_in_surface(id):
    v = rh.BrepClosestPoint(id, rawu0)
    if v:
        return fromPt(v[0])
    else:
        u, v = rh.SurfaceDomain(id, 0), rh.SurfaceDomain(id, 1)
        return rh.EvaluateSurface(id, u[0], v[0])

def is_point_in_surface(id, p):
    return rh.IsPointInSurface(id, Pt(p))

def is_point_on_surface(id, p):
    return rh.IsPointOnSurface(id, Pt(p))

def is_point_on(r, c):
    try:
        return is_point_in_surface(r, c)
    except:
        return is_point_on_surface(r, c)

#The Rhino shape
class shape(base_shape):
    def validate(self, guid):
        if isinstance(guid, System.Guid):
            if guid == System.Guid.Empty:
                raise RuntimeError("The operation failed!")
            else:
                vs.Redraw()
                return native_ref(guid)
        elif isinstance(guid, (tuple, list)):
            if len(guid) == []:
                raise RuntimeError("The operation failed!")
            elif len(guid) == 1:
                return self.validate(guid[0])
            else:
                return union_ref([self.validate(g) for g in guid])
        elif (is_empty_ref(guid) or 
              is_universal_ref(guid) or
              isinstance(guid, (native_ref, multiple_ref))):
            return guid
        else:
            raise ValueError("Unexpected guid: {0}".format(guid))

    def delete(self):
        #Perhaps optimize this in case the shape was not yet realized
        self.realize().do(lambda r: self.destroy(r))

    def destroy(self, guid):
        db.Delete(guid, True)
    
    def copy_ref(self, guid):
        return rh.CopyObject(guid)

    def intersect_ref(self, r0, r1):
        brep0 = _brep_from_id(r0)
        brep1 = _brep_from_id(r1)
        for e in range(5,2,-1):
            tol = pow(10,-e)
            newbreps = geo.Brep.CreateBooleanIntersection([brep0], [brep1], tol)
            if newbreps:
                db.Delete(r0, True)
                db.Delete(r1, True)
                return single_ref_or_union([db.AddBrep(brep) for brep in newbreps])
        c1 = _point_in_surface(r1)
        if is_point_on(r0, c1):
            db.Delete(r0, True)
            return native_ref(r1)
        else:
            c0 = _point_in_surface(r0)
            if is_point_on(r1, c0):
                db.Delete(r1, True)
                return native_ref(r0)
            else:
                db.Delete(r0, True)
                db.Delete(r1, True)
                return empty_ref()

    def subtract_ref(self, r0, r1):
        brep0 = _brep_from_id(r0)
        brep1 = _brep_from_id(r1)
        for e in range(5,2,-1):
            tol = pow(10,-e)
            newbreps = geo.Brep.CreateBooleanDifference([brep0], [brep1], tol)
            if newbreps:
                db.Delete(r0, True)
                db.Delete(r1, True)
                return single_ref_or_union([db.AddBrep(brep) for brep in newbreps])
        c1 = _point_in_surface(r1)
        if is_point_on(r0, c1):
            return subtraction_ref([native_ref(r0), native_ref(r1)])
        else:
            c0 = _point_in_surface(r0)
            if is_point_on(r1, c0):
                db.Delete(r0, True)
                db.Delete(r1, True)
                return empty_ref()
            else:
                db.Delete(r1, True)
                return native_ref(r0)

    def slice_ref(self, r, p, n):
        cutter = rh.AddCutPlane([r], Pt(p), Pt(p + vx(1, p.cs)), Pt(vy(1, p.cs)))
        rs = rh.SplitBrep(r, cutter, True)
        rs = rs or [r]
        for e in rs:
            rh.CapPlanarHoles(e)
        keep, clear = partition(rs, lambda r: (fromPt(rh.SurfaceVolumeCentroid(r)[0]) - p).dot(n) < 0)
        rh.DeleteObjects(clear)
        rh.DeleteObject(cutter)
        if keep == []:
            return empty_ref()
        else:
            return single_ref_or_union(keep)


# The actual shapes
@shape_constructor(shape)
def point(position=u0()):
    return db.AddPoint(Pt(position))

class curve(shape):
    pass

class closed_curve(curve):
    pass

class surface(shape):
    pass

class solid(shape):
    pass

def is_curve(s):
    return isinstance(s, curve)
def is_surface(s):
    return isinstance(s, surface)
def is_solid(s):
    return isinstance(s, solid)

@shape_constructor(closed_curve)
def circle(center=u0(), radius=1):
    return db.AddCircle(geo.Circle(Pl(center), radius))

@shape_constructor(surface)
def surface_circle(center=u0(), radius=1):
    return _surface_from_curves([geo.Circle(Pl(center), radius).ToNurbsCurve()])

@shape_constructor(curve)
def arc(center=u0(), radius=1, start_angle=0, amplitude=pi):
    if radius == 0:
        return db.AddPoint(Pt(center))
    elif amplitude == 0:
        return db.AddPoint(Pt(add_pol(center, radius, start_angle)))
    elif abs(amplitude) >= 2*pi:
        return db.AddCircle(geo.Circle(Pl(center), radius))
    else:
        return db.AddArc(geo.Arc(Pl(center) if start_angle == 0
                                 else Pl(loc_from_o_phi(center, start_angle)),
                                 radius,
                                 coterminal(amplitude)))

@shape_constructor(surface)
def surface_arc(center=u0(), radius=1, start_angle=0, amplitude=pi):
    if radius == 0:
        return db.AddPoint(Pt(center))
    elif amplitude == 0:
        return db.AddPoint(Pt(addPol(center, radius, start_angle)))
    elif abs(amplitude) >= 2*pi:
        return db.AddCircle(geo.Circle(Pl(center), radius))
    else:
        curves = [geo.Arc(Pl(center) if start_angle == 0
                          else Pl(loc_from_o_phi(center, start_angle)),
                          radius,
                          coterminal(amplitude)).ToNurbsCurve(),
                  geo.Polyline([Pt(center), 
                                Pt(add_pol(center, radius, start_angle))]).ToNurbsCurve(),
                  geo.Polyline([Pt(center), 
                                Pt(add_pol(center, radius, start_angle + amplitude))]).ToNurbsCurve()]
        return _surface_from_curves(curves)
        
@shape_constructor(closed_curve)
def ellipse(center=u0(), radius_x=1, radius_y=1):
    return db.AddEllipse(geo.Ellipse(Pl(center), radius_x, radius_y))

@shape_constructor(surface)
def surface_ellipse(center=u0(), radius_x=1, radius_y=1):
    return _surface_from_curves([geo.Ellipse(Pl(center), radius_x, radius_y).ToNurbsCurve()])

@shape_constructor(curve)
def line(*vertices):
    vs = unvarargs(vertices)
    return db.AddPolyline(geo.Polyline([Pt(v) for v in vs]))

@shape_constructor(curve)
def spline(*positions):
    ps = unvarargs(positions)
    return rh.AddInterpCurve([Pt(p) for p in ps], 3, 1)

@shape_constructor(spline)
def spline_tangents(positions, start_tangent, end_tangent):
    return rh.AddInterpCurve([Pt(p) for p in positions], 3, 1, 
                             Vt(start_tangent),
                             Vt(end_tangent))

@shape_constructor(closed_curve)
def closed_spline(*positions):
    ps = unvarargs(positions)
    return rh.AddInterpCurve([Pt(p) for p in ps]+[Pt(ps[0])], 3, 4)
    

@shape_constructor(closed_curve)
def rectangle(corner=u0(), dx=1, dy=None):
    dy = dy or dx
    dz = 0
    c = corner
    if isinstance(dx, xyz):
        v = loc_in_cs(dx, c.cs) - c
        dx, dy, dz = v.coords
    assert dz == 0, "The rectangle is not planar"
    return db.AddPolyline([Pt(c), 
                           Pt(add_x(c, dx)),
                           Pt(add_xy(c, dx, dy)),
                           Pt(add_y(c, dy)),
                           Pt(c)])
        
@shape_constructor(surface)
def surface_rectangle(corner=u0(), dx=1, dy=None):
    r = rectangle(corner, dx, dy)
    s = rh.AddPlanarSrf(r.realize()._ref)
    r.delete()
    return s
    
@shape_constructor(closed_curve)
def polygon(*vertices):
    vs = unvarargs(vertices)
    return db.AddPolyline(geo.Polyline([Pt(v) for v in vs]+[Pt(vs[0])]))
    
@shape_constructor(surface)
def surface_polygon(*vertices):
    vs = unvarargs(vertices)
    return _surface_from_curves([geo.Polyline([Pt(v) for v in vs]+[Pt(vs[0])]).ToNurbsCurve()])
    
@shape_constructor(polygon)
def regular_polygon(edges=3, center=u0(), radius=1, angle=0, inscribed=False):
    pts = map(Pt, regular_polygon_vertices(edges, center, radius, angle, inscribed))
    return rh.AddPolyline(pts + [pts[0]])

@shape_constructor(surface_polygon)
def surface_regular_polygon(edges=3, center=u0(), radius=1, angle=0, inscribed=False):
    pts = map(Pt, regular_polygon_vertices(edges, center, radius, angle, inscribed))
    border = rh.AddPolyline(pts + [pts[0]])
    srf = rh.AddPlanarSrf([border])
    db.Delete(border, True)
    return srf

@shape_constructor(surface)
def surface_from(*curves):
    cs = unvarargs(curves)
    refs = shapes_refs(cs)
    if is_singleton(refs):
        ref = refs[0]
        if isinstance(ref, geo.Point):
            id = ref
        else:
            ids = rh.AddPlanarSrf(refs)
            if ids:
                id = singleton(ids)
            else:
                id = rh.AddPatch(refs, 3, 3)
    elif len(refs) < 0: #Temporary fix for Funda's problem# 5:
        id = rh.AddEdgeSrf(refs)
    else:
        id = rh.AddPlanarSrf(refs)
    delete_shapes(cs)
    return id

@shape_constructor(solid)
def box(corner=u0(), dx=1, dy=None, dz=None):
    dy = dy or dx
    dz = dz or dy
    c = corner
    if isinstance(dx, xyz):
        v = loc_in_cs(dx, c.cs) - c
        dx, dy, dz = v.coords
    return rh.AddBox(map(Pt, 
                         [c,
                          add_x(c, dx),
                          add_xy(c, dx, dy),
                          add_y(c, dy),
                          add_z(c, dz),
                          add_xz(c, dx, dz),
                          add_xyz(c, dx, dy, dz),
                          add_yz(c, dy, dz)]))

@shape_constructor(solid)
def cuboid(b0=None, b1=None, b2=None, b3=None, t0=None, t1=None, t2=None, t3=None):
    b0 = b0 or u0()
    b1 = b1 or add_x(b0, 1)
    b2 = b2 or add_y(b1, 1)
    b3 = b3 or add_y(b0, 1)
    t0 = t0 or add_z(b0, 1)
    t1 = t1 or add_x(t0, 1)
    t2 = t2 or add_y(t1, 1)
    t3 = t3 or add_y(t0, 1)
    return rh.AddBox(map(Pt, [b0, b1, b2, b3, t0, t1, t2, t3]))


@shape_constructor(solid)
def cylinder(base=u0(), radius=1, height=1, top=None):
    base, height = base_and_height(base, top or height)
    return db.AddBrep(
        geo.Cylinder(
            geo.Circle(Pl(base), radius), height).ToBrep(True, True))

@shape_constructor(solid)
def cone(base=u0(), radius=1, height=1, top=None):
    base, height = inverted_base_and_height(base, top or height)
    return db.AddBrep(geo.Brep.CreateFromCone(geo.Cone(Pl(base), height, radius), True))

@shape_constructor(solid)
def cone_frustum(base=u0(), base_radius=1, height=1, top_radius=1, top=None):
    base, height = base_and_height(base, top or height)
    top = top or add_z(base, height)
    bottomCircle = geo.Circle(Pl(base), base_radius)
    topCircle = geo.Circle(Pl(top), top_radius)
    shapeCurve = geo.LineCurve(bottomCircle.PointAt(0), topCircle.PointAt(0))
    axis = geo.Line(bottomCircle.Center, topCircle.Center)
    revsrf = geo.RevSurface.Create(shapeCurve, axis)
    return db.AddBrep(geo.Brep.CreateFromRevSurface(revsrf, True, True))

def _irregular_pyramid(pts0, pt1):
    pts0, pt1 = map(Pt, pts0), Pt(pt1)
    id = rh.JoinSurfaces([rh.AddSrfPt((pt00, pt01, pt1)) 
                          for pt00, pt01 in zip(pts0, pts0[1:] + [pts0[0]])])
    rh.CapPlanarHoles(id)
    return id

def _irregular_pyramid_frustum(pts0, pts1):
    pts0, pts1 = map(Pt, pts0), map(Pt, pts1)
    id = rh.JoinSurfaces([rh.AddSrfPt((pt00, pt01, pt11, pt10))
                          for pt00, pt01, pt10, pt11
                          in zip(pts0, pts0[1:] + [pts0[0]], pts1, pts1[1:] + [pts1[0]])])
    rh.CapPlanarHoles(id)
    return id

@shape_constructor(solid)
def regular_pyramid_frustum(edges=4, base=u0(), base_radius=1, angle=0, height=1, top_radius=1, inscribed=False, top=None):
    base, height = base_and_height(base, top or height)
    top = top or add_z(base, height)
    return _irregular_pyramid_frustum(
        regular_polygon_vertices(edges, base, base_radius, angle, inscribed),
        regular_polygon_vertices(edges, top, top_radius, angle, inscribed))
    
@shape_constructor(solid)
def regular_pyramid(edges=4, base=u0(), radius=1, angle=0, height=1, inscribed=False, top=None):
    base, height = base_and_height(base, top or height)
    top = top or add_z(base, height)
    return _irregular_pyramid(
        regular_polygon_vertices(edges, base, radius, angle, inscribed),
        top)

@shape_constructor(solid)
def regular_prism(edges=4, base=u0(), radius=1, angle=0, height=1, inscribed=False, top=None):
    base, height = base_and_height(base, top or height)
    top = top or add_z(base, height)
    return _irregular_pyramid_frustum(
        regular_polygon_vertices(edges, base, radius, angle, inscribed),
        regular_polygon_vertices(edges, top, radius, angle, inscribed))

@shape_constructor(solid)
def irregular_prism(base_vertices=None, direction=1):
    base_vertices = base_vertices or [ux(), uy(), uxy()]
    dir = vz(direction, base_vertices[0].cs) if is_number(dir) else dir
    return rh.IrregularPyramidFrustum(cbs, map((lambda p: p + dir), cbs))
    
@shape_constructor(solid)
def irregular_pyramid(base_vertices=None, top=None):
    base_vertices = base_vertices or [ux(), uy(), uxy()]
    top = top or uz()
    return _irregular_pyramid(base_vertices, top)

@shape_constructor(solid)
def right_cuboid(base=u0(), width=1, height=1, length=1, top=None):
    base, dz = base_and_height(base, top or length)
    c, dx, dy = add_xy(base, width/-2, height/-2), width, height
    return rh.AddBox(map(Pt, [c,
                              add_x(c, dx),
                              add_xy(c, dx, dy),
                              add_y(c, dy),
                              add_z(c, dz),
                              add_xz(c, dx, dz),
                              add_xyz(c, dx, dy, dz),
                              add_yz(c, dy, dz)]))

@shape_constructor(solid)
def sphere(center=u0(), radius=1):
    return db.AddSphere(geo.Sphere(Pt(center), radius))


@shape_constructor(shape)
def text(str="", corner=u0(), height=1):
    return rh.AddText(str, Pl(corner), height)
    
def text_length(str="", height=1):
    return len(str)*height*0.9

@shape_constructor(shape)
def text_centered(str="", corner=u0(), height=1):
    return rh.AddText(str, Pl(add_xy(corner, text_length(str, height)/-2, height/-2)), height)

@shape_constructor(shape)
def torus(center=u0(), major_radius=1, minor_radius=1/2):
    return rh.AddTorus(Pl(center), major_radius, minor_radius)

@shape_constructor(shape)
def union(*shapes):
    shapes = filter(lambda s: not is_empty_shape(s),
                    unvarargs(shapes))
    if len(shapes) == 0:
        return empty_ref()
    elif len(shapes) == 1:
        return shapes[0].realize()
    elif any(is_universal_shape(s) for s in shapes):
        return universal_ref()
    else:
        rs = [s.realize() for s in shapes]
        for r in rs:
            assert isinstance(r,(native_ref, multiple_ref)), "BRONCA"
        unions, rs = partition(rs, is_union_ref)
        subtractions, rs = partition(rs, is_subtraction_ref)
        united = rs + [r0 for union in unions for r0 in union._refs] #Avoid this direct reference
        return native_ref_or_union(united + subtractions)

@shape_constructor(shape)
def intersection(*shapes):
    shapes = unvarargs(shapes)
    def create_ref(self, shapes):
        shapes = filter(lambda s: not is_universal_shape(s), shapes)
        if len(shapes) == 0:
            return universal_ref()
        elif len(shapes) == 1:
            return shapes[0].realize()
        elif any(is_empty_shape(s) for s in shapes):
            return empty_ref()
        else:
            return intersect_refs(list(s.realize() for s in shapes), self)    
    return maybe_delete_shapes(shapes, create_ref(shapes[0], shapes))


@shape_constructor(shape)
def subtraction(*shapes):
    shapes = unvarargs(shapes)
    if len(shapes) == 0:
        raise RuntimeError("No shapes to subtract")
    else:
        s = shapes[0]
        ss = filter(lambda s: not is_empty_shape(s), shapes[1:])
        if len(ss) == 0:
            return s.realize()
        elif is_empty_shape(s) or any(is_universal_shape(o) or (o is s)
                                      for o in ss):
            return maybe_delete_shapes(ss, empty_ref())
        else:
            r = s.realize()
            rs = [s0.realize() for s0 in ss]
            return subtract_refs(r, rs, s)

@shape_constructor(solid)
def slice(shape, p=u0(), n=None):
    n = n or vz(1, p.cs)
    p = loc_from_o_vz(p, n)
    res = shape.realize().slice(p, n, shape)
    shape.mark_deleted()
    return res

@shape_constructor(shape)
def extrusion(profile, dir=1):
    dir = dir if isinstance(dir, vxyz) else vz(dir)
    vec = Vt(dir)
    def extrude(r):
        if rh.IsCurve(r):
            return db.AddSurface(geo.Surface.CreateExtrusion(db.Find(r).Geometry, vec))
        else:
            c = rh.SurfaceAreaCentroid(r)[0]
            curve = rh.AddLine(c, c + vec)
            brep = _brep_from_id(r)
            c = db.Find(curve).Geometry
            r = single_ref_or_union([db.AddBrep(face.CreateExtrusion(c, True))
                                     for face in brep.Faces])
            rh.DeleteObject(curve)
            return r
    return and_delete(profile.realize().map(extrude), profile)

def revolve_border(border, axis, start, end):
    res = rh.AddRevSrf(border, axis, start, end)
    rh.CapPlanarHoles(res)
    rh.DeleteObject(border)
    return res

def revolve_borders(profile, axis, start, end, out):
    return [revolve_border(border, axis, start, end)
            for border in rh.DuplicateSurfaceBorder(profile, 1 if out else 2)]

@shape_constructor(shape)
def revolve(shape, c=u0(), v=vz(1), start_angle=0, amplitude=2*pi):
    if isinstance(v, loc): #HACK Should we keep this?
        v = v - c
    axis = [Pt(c), Pt(c + v)]
    start = degrees(start_angle)
    end = degrees(start_angle + amplitude)
    def revol(r):
        if rh.IsCurve(r):
            return native_ref(rh.AddRevSrf(r, axis, start, end))
        elif rh.IsSurface(r) or rh.IsPolysurface(r):
            out_refs = revolve_borders(r, axis, start, end, True)
            in_refs = revolve_borders(r, axis, start, end, False)
            return subtract_refs(single_ref_or_union(out_refs),
                                 [native_ref(r) for r in in_refs],
                                 shape)
        else:
            raise RuntimeError("Can't revolve the shape")
    return and_delete(shape.realize().map(revol), shape)

def sweep_path_curve(path, profile, rotation, scale):
    def transf_t(t, r, s):
        plane = rh.CurvePerpFrame(path, rh.CurveParameter(path, t))
        xform = rh.XformChangeBasis(plane, geo.Plane.WorldXY)
        xform = rh.XformMultiply(xform, rh.XformScale(s))
        xform = rh.XformMultiply(xform, geo.Transform.Rotation(r, geo.Vector3d(0, 0, 1), rawu0))
        return rh.TransformObject(profile, xform, True)
    if rotation == 0 and scale == 1:
        profiles = [transf_t(0.0, 0, 1)]
    else:
        n = 10
        profiles = [transf_t(t, r, s) 
                    for t, r, s in zip(division(0, 1, n),
                                       division(0, rotation, n),
                                       division(1, scale, n))]
    r = rh.AddSweep1(path, profiles)
    rh.DeleteObjects(profiles)
    return r

def solid_sweep_path_curve(path, profile, rotation, scale):
    r = sweep_path_curve(path, profile, rotation, scale)
    rh.CapPlanarHoles(r)
    rh.DeleteObject(profile)
    return r

def sweep_path_profile(path, profile, rotation, scale):
    if rh.IsCurve(profile):
        return single_ref_or_union(sweep_path_curve(path, profile, rotation, scale))
    elif rh.IsSurface(profile):
        o_refs, i_refs = ([solid_sweep_path_curve(path, border, rotation, scale)
                           for border in rh.DuplicateSurfaceBorder(profile, i)]
                          for i in (1, 2))
        if i_refs == []:
            return single_ref_or_union(o_refs)
        else:
            return subtract_refs(single_ref_or_union(o_refs),
                                 single_ref_or_union(i_refs))
    else:
        raise RuntimeError('Continue this')

def delete_all_shapes():
    for id in db.GetObjectList(Rhino.DocObjects.ObjectEnumeratorSettings()):
        db.Delete(id, True)
    vs.Redraw()

@shape_constructor(shape)
def sweep(path, profile, rotation=0, scale=1):
    path_ref = path.realize()
    prof_ref = profile.realize()
    return and_delete(
        path_ref.map(lambda pa:
                     prof_ref.map(lambda pr:
                                  sweep_path_profile(pa, 
                                                     pr,
                                                     rotation,
                                                     scale))),
        path,
        profile)

@shape_constructor(curve)
def surface_boundary(surface):
    return and_delete(surface.realize().map(
        lambda r: single_ref_or_subtraction(rh.DuplicateSurfaceBorder(r))),
                      surface)

# This is not correct. Must fix this ref mess
def adequate_ref(arg):
    if isinstance(arg, (native_ref, multiple_ref)):
        return arg
    elif isinstance(arg, (tuple, list)):
        return single_ref_or_union(arg)
    else:
        return native_ref(arg)

def loft_curve_point(curve, point):
    p = rh.PointCoordinates(point.realize()._ref)
    curve_ref = curve.realize()
    return and_delete(adequate_ref(curve_ref.map(lambda c: rh.ExtrudeCurvePoint(c, p))),
                      curve,
                      point)

def loft_surface_point(surface, point):
    boundary = surface_boundary(surface)
    rs = loft_curve_point(boundary, point)
    rs.do(rh.CapPlanarHoles)
    return adequate_ref(rs)

def loft_profiles_aux(profiles, rails, is_ruled, is_closed):
    profiles_refs = list([profile.realize()._ref
                          for profile in profiles])
    rails_refs = list([rail.realize()._ref
                       for rail in rails])
    if len(rails_refs) == 0:
        return singleton(rh.AddLoftSrf(profiles_refs, None, None, 
                          2 if is_ruled else 0, 0, 0, is_closed))
    elif len(rails_refs) == 1:
        return singleton(rh.AddSweep1(rails_refs[0], profiles_refs))
    elif len(rails_refs) == 2:
        return singleton(rh.AddSweep2(rails_refs, profiles_refs))
    elif len(rails_refs) > 2:
        print('Warning: Rhino only supports two rails but were passed {0}'.format(len(rails)))
        return singleton(rh.AddSweep2(rails_refs[:2], profiles_refs))
    else: #Remove?
        raise RuntimeError('Rhino only supports two rails but were passed {0}'.format(len(rails)))

def loft_profiles(profiles, rails, is_solid, is_ruled, is_closed):
    r = loft_profiles_aux(profiles, rails, is_ruled, is_closed)
    if is_solid:
        rh.CapPlanarHoles(r)
    return and_delete(r, *(profiles + rails))

def loft_curves(profiles, rails, is_ruled=False, is_closed=False):
    return loft_profiles(profiles, rails, False, is_ruled, is_closed)

def loft_surfaces(profiles, rails, is_ruled=False, is_closed=False):
    return loft_profiles(map(surface_boundary, profiles), rails, True, is_ruled, is_closed)

@shape_constructor(shape)
def lofted(profiles, rails=[], is_ruled=False, is_closed=False):
    if all(map(is_curve, profiles)):
        return loft_curves(profiles, rails, is_ruled, is_closed)
    elif all(map(is_surface, profiles)):
        return loft_surfaces(profiles, rails, is_ruled, is_closed)
    elif len(profiles) == 2:
        assert(rails == [])
        p, s = profiles[0], profiles[1]
        if is_point(p):
            pass
        elif is_point(s):
            p, s = s, p
        else:
            raise RuntimeError("{0}: cross sections are not either points or curves or surfaces {1}".format('loft_shapes', profiles))
        if is_curve(s):
            return loft_curve_point(s, p)
        elif is_surface(s):
            return loft_surface_point(s, p)
        else:
            raise RuntimeError("{0}: can't loft the shapes {1}".format('loft_shapes', profiles))
    else:
        raise RuntimeError("{0}: cross sections are neither points nor curves nor surfaces  {1}".format('loft_shapes', profiles))

def loft(profiles, rails=[], is_ruled=False, is_closed=False):
    if len(profiles) == 1:
        raise RuntimeError(quote(loft), 'just one cross section')
    elif all(map(is_point, profiles)):
        assert(rails == [])
        func = ((polygon if is_closed else line) 
                if is_ruled 
                else (closed_spline if is_closed else spline))
        polygon if is_closed else line if is_ruled else closed_spline if is_closed else spline
        return and_delete(func([p.position for p in profiles]),
                          *profiles)
    else:
        return lofted(profiles, rails, is_ruled, is_closed)

def loft_ruled(profiles):
    return loft(profiles, [], True)

@shape_constructor(shape)
def move(shape, translation=vx()):
    v = Vt(translation)
    ref = shape.realize()
    ref.do(lambda r: rh.MoveObject(r, v))
    shape.mark_deleted()
    return ref

@shape_constructor(shape)
def rotate(shape, rotation_angle=pi/2, axis_center=u0(), axis_vector=vz()):
    if isinstance(axis_vector, loc):
        axis_vector = axis_vector - axis_center
    p = Pt(axis_center)
    v = Vt(axis_vector)
    xform = geo.Transform.Rotation(rotation_angle, v, p)
    ref = shape.realize()
    ref.do(lambda r: db.Transform(r, xform, True))
    shape.mark_deleted()
    return ref

@shape_constructor(shape)
def scale(shape, scale=1.0, center=u0()):
    p = Pt(center)
    s = [scale, scale, scale]
    ref = shape.realize()
    ref.do(lambda r: rh.ScaleObject(r, p, s, False))
    shape.mark_deleted()
    return ref

@shape_constructor(shape)
def mirror(shape, plane_position=u0(), plane_normal=vz(), copy=True):
    p = Pt(plane_position)
    v = Vt(plane_normal)
    xform = rh.XformMirror(p, v)
    ref = shape.realize()
    new_ref = ref.map(lambda r: native_ref(rh.TransformObject(r, xform, copy)))
    if not copy:
        shape.mark_deleted()
    return new_ref

def union_mirror(shape, plane_position=u0(), plane_normal=vz()):
    return union(shape, mirror(shape, plane_position, plane_normal, True))

@shape_constructor(surface)
def surface_grid(ptss, closed_u=False, closed_v=False):
    if closed_v:
        ptss = [pts + [pts[0]] for pts in ptss]
    if closed_u:
        ptss = ptss + [ptss[0]]
    if len(ptss) == 2 and len(ptss[0]) == 2:
        return rh.AddSrfPt(ptss[0] + ptss[1])
    else:
        if len(ptss) == 2:
            ptss = [ptss[0], map(intermediate_loc, ptss[0], ptss[1]), ptss[1]]
        elif len(ptss[0]) == 2:
            ptss = map(lambda cs: [cs[0], intermediate_loc(cs[0], cs[1]), cs[1]], ptss)
        ps = [Pt(pt) for pts in ptss for pt in pts]
        nu = len(ptss)
        nv = len(ptss[0])
        return rh.AddSrfPtGrid((nu, nv),
                               ps,
                               (max(2*int(nu/10)+1,2), max(2*int(nv/10)+1,2)),
                               (closed_u, closed_v))

@shape_constructor(solid)
def thicken(surf, h=1):
    s = rh.OffsetSurface(surf.realize()._ref, h, None, True, True)
    if not s:
        rh.UnselectAllObjects()
        rh.SelectObjects(surf.refs())
        rh.Command("OffsetSrf BothSides=Yes Solid=Yes {0} _Enter".format(h))
        s = single_ref_or_union(rh.LastCreatedObjects())
    surf.delete()
    return s



def map_surface_division(f, surface, nu, nv, include_last_u=True, include_last_v=True):
    id = surface.realize()._ref
    domain_u = rh.SurfaceDomain(id, 0)
    domain_v = rh.SurfaceDomain(id, 1)
    start_u = domain_u[0]
    end_u = domain_u[1]
    start_v = domain_v[0]
    end_v = domain_v[1]
    def surf_f(u, v):
        plane = rh.SurfaceFrame(id, (u, v))
        if rh.IsPointOnSurface(id, plane.Origin):
            return f(fromPlane(plane))
        else:
            return False
    return map_division(surf_f,
                        start_u, end_u, nu, include_last_u,
                        start_v, end_v, nv, include_last_v)

# All shape constructors are defined. Transfer selectors and recognizers to this module

globals().update(shape_ops)


def delete_shapes(shapes):
    for shape in shapes:
        shape.delete()
    vs.Redraw()

def delete_shape(shape):
    shape.delete()
    vs.Redraw()

def delete_all_shapes():
    for id in db.GetObjectList(Rhino.DocObjects.ObjectEnumeratorSettings()):
        db.Delete(id, True)
    vs.Redraw()

def view(camera=False, target=False, lens=False):
    if camera and target and lens:
        if not rh.IsViewMaximized("Perspective"):
            rh.MaximizeRestoreView("Perspective")
        rh.ViewProjection("Perspective", 2)
        rh.ViewCameraLens("Perspective", lens)
        rh.ViewCameraTarget("Perspective", Pt(camera), Pt(target))
        rh.ViewDisplayMode("Perspective", "Shaded")
        vs.Redraw()
        return (camera, target, lens)
    else:
        rh.CurrentView("Perspective")
        camera, target, lens = rh.ViewCamera(), rh.ViewTarget(), rh.ViewCameraLens()
        return (fromPt(camera), fromPt(target), lens)

def view_top():
    if not rh.IsViewMaximized("Top"):
        rh.MaximizeRestoreView("Top")
    rh.ViewProjection("Top", 1)
    rh.ViewDisplayMode("Top", "Wireframe")
    vs.Redraw()

def zoom_extents():
    rh.ZoomExtents(None, True)

def render_view(str):
    rh.RenderResolution([render_width(), render_height()])
    rh.Command("_-Render", False)
    rh.Command('_-SaveRenderWindowAs "{0}"'.format(ensure_dir(render_pathname(str))), False)
    rh.Command("_-CloseRenderWindow", False)

def render_stereo_view(str):
    pass

def save_film_frame(obj=None):
    with render_kind_dir('Film'):
        render_view(frame_filename(film_filename(), film_frame()))
        film_frame(film_frame() + 1)
        return obj

def random_integer_range(*args):
    return random_range(*args)

def prompt_point(str="Select point"):
    return rh.GetPoint(str)

def prompt_integer(str="Integer?"):
    return rh.GetInteger(str)

def prompt_real(str="Real?"):
    return rh.GetReal(str)

def prompt_shape(str="Select shape"):
    sh = rh.GetObject(str)
    if sh:
        return shape_from_ref(sh)
    else:
        return empty_shape()

def get_shape_named(name):
    return shape_from_ref(rh.ObjectsByName(name, False, False, False)[0])

def bounding_box(s):
    return [fromPt(p) for p in rh.BoundingBox([s.refs()])]

def rhino_rgb_from_rgb(c):
    return ((c.red << 0) +
            (c.green << 8) +
            (c.blue << 16))

def rgb_from_rhino_rgb(rc):
    return rgb(rh.ColorRedValue(rc),
               rh.ColorGreenValue(rc),
               rh.ColorBlueValue(rc))

def shape_color(sh, color=None):
    if color:
        color = rhino_rgb_from_rgb(color)
        sh.realize().do(lambda r: rh.ObjectColor(r, color))
        return sh
    else:
        return rh.ObjectColor(sh.ref())

# layers
create_layer = rh.AddLayer

class current_layer(object):
    def __init__(self, layer):
        self.layer = layer
        self.previous_layer = None

    def __enter__(self):
        self.previous_layer = rh.CurrentLayer(self.layer)
        return self.layer

    def __exit__(self, type, value, traceback):
        rh.CurrentLayer(self.previous_layer)

def shape_layer(shape, layer=None):
    if layer:
        shape.realize().do(lambda r: rh.ObjectLayer(r, layer))
    else:
        return rh.ObjectLayer(shape.realize()._ref)

def shape_from_ref(r):
    with parameter(immediate_mode, False):
        obj = _geometry_from_id(r)
        ref = native_ref(r)
        if isinstance(obj, geo.Point):
            return point.new_ref(ref, fromPt(obj.Location))
        elif isinstance(obj, geo.Curve):
            if rh.IsLine(r) or rh.IsPolyline(r):
                if rh.IsCurveClosed(r):
                    return polygon.new_ref(ref, [fromPt(p) for p in rh.CurvePoints(r)[:-1]])
                else:
                    return line.new_ref(ref, [fromPt(p) for p in rh.CurvePoints(r)])
            elif obj.IsCircle(Rhino.RhinoMath.ZeroTolerance):
                return circle.new_ref(ref, fromPt(rh.CircleCenterPoint(r)), rh.CircleRadius(r))
            elif rh.IsCurveClosed(r):
                return closed_spline.new_ref(ref, [fromPt(p) for p in rh.CurvePoints(r)])
            else:
                return spline.new_ref(ref, [fromPt(p) for p in rh.CurvePoints(r)])
        elif rh.IsObject(r) and rh.IsObjectSolid(r):
            return solid(native_ref(r))
        elif rh.IsSurface(r) or rh.IsPolysurface(r):
            return surface(native_ref(r))
        else:
            raise RuntimeError("{0}: Unknown Rhino object {1}".format('shape_from_ref', r))

def all_shapes():
    return [shape_from_ref(r) for r in rh.AllObjects()]

# For testing
generate_mode(False)

class model(meta_model('meta_model', (object,), {})):
    def setup(self):
        delete_all_shapes()
        view_top()
    def wait(self):
        if not prompt_point("Click to advance, ESC to cancel"):
            raise RuntimeError("Stopped!")

class film(meta_model('meta_model', (object,), {})):
    def setup(self):
        delete_all_shapes()
        view_top()
    def wait(self):
        if not prompt_point("Click to advance, ESC to cancel"):
            raise RuntimeError("Stopped!")

generate_mode(True)
step_mode(True)
########TESTS#######

#import time
#t = time.clock()
#cidadeEspacial(u0(), 8)
#print time.clock() - t


if( __name__ == '__main__' ):
    print("The Khepri library is not intended to be executed, just imported")


def zoom_2d_top():
    view_top()
    zoom_extents()

def reset():
    pass

def view_with_background(camera, target, lens):
    return view(camera, target, lens)

generate_mode(True)
step_mode(False)
immediate_mode(True)


def brep_subbreps(object_id):
    brep = _brep_from_id(object_id)
    ids = []
    for face in brep.Faces:
        newbrep = face.DuplicateFace(True)
        id = scriptcontext.doc.Objects.AddBrep(newbrep)
        ids.append(id)
    return ids

def shape_surfaces(shape):
    ref = shape.realize()
    return ref.map(lambda r: map(shape_from_ref, brep_subbreps(r)))

def shape_edges(shape):
    ref = shape.realize()
    return ref.map(lambda r: map(shape_from_ref, rh.DuplicateEdgeCurves(r)))

def shape_vertices(shape):
    pts = []
    for edge in shape_edges(shape):
        r = edge.ref()
        pt = rh.CurveStartPoint(r)
        if pt not in pts:
            pts.append(pt)
        pt = rh.CurveEndPoint(r)
        if pt not in pts:
            pts.append(pt)
    return map(fromPt, pts)

def show_vertices(shape):
    map(lambda p: sphere(p, 0.05), shape_vertices(shape))

#delete_all_shapes()
#show_vertices(sphere())


# BIM stuff

def load_beam_family(path, *args):
    return False

def load_column_family(path, *args):
    return False

def level(h):
    return h

def level_height(h):
    return h

current_level = make_parameter(level(0))
default_level_to_level_height = make_parameter(3)

def upper_level(lvl=None, height=None):
    lvl = lvl or current_level();
    height = height or default_level_to_level_height()
    return level(level_height(lvl) + height)



import collections
def Record(typename, **fields_dict):
    T = collections.namedtuple(typename, ' '.join(fields_dict.keys()))
    T.__new__.__defaults__ = tuple(fields_dict.values())
    return T

Beam_Family = Record('Beam_Family', path='', map={}, layer=False, width=0.1, height=0.1, profile=False, material=False)
default_beam_family = make_parameter(Beam_Family())

Column_Family = Record('Column_Family', path='', map={}, layer=False, width=0.1, depth=False, is_section_circular=False)
default_column_family = make_parameter(Column_Family())

Slab_Family = Record('Slab_Family', path='', map={}, layer=False, thickness=0.3, coating_thickness=0)
default_slab_family = make_parameter(Slab_Family())

Roof_Family = Record('Roof_Family', path='', map={}, layer=False, thickness=0.3, coating_thickness=0)
default_roof_family = make_parameter(Roof_Family())

Wall_Family = Record('Wall_Family', path='', map={}, layer=False, thickness=0.3)
default_wall_family = make_parameter(Wall_Family())

Panel_Family = Record('Panel_Family', path='', map={}, layer=False, thickness=0.01, material='Glass')
default_panel_family = make_parameter(Panel_Family())

def is_vertical(p0, p1):
    return (p0-p1).cyl_rho < 1e-10

create_bim_layers = make_parameter(True)

def bim_shape_layer(shape, layer = None):
    if layer:
        if create_bim_layers():
            return shape_layer(shape, layer)
    else:
        return shape_layer(shape)

def shape_reference(s):
    return s.realize()._ref

@shape_constructor(solid)
def beam(p0, p1, angle=0, family=None):
    family = family or default_beam_family()
    h, w = family.height, family.width
    if is_vertical(p0, p1):
        s = right_cuboid(p0, w, h, p1, angle)
    else:
        cb, dz = base_and_height(p0, p1)
        s = right_cuboid(loc_in_world(cb + vy(-(h/2))),
                         family.width,
                         h,
                         loc_in_world(cb + vyz(-(h/2), dz)),
                         angle)
    bim_shape_layer(s, family.layer)
    return shape_reference(s)
    
@shape_constructor(solid)
def column(center, bottom_level=None, top_level=None, family=None):
    bottom_level = bottom_level or current_level()
    top_level = top_level or upper_level(bottom_level)
    family = family or default_column_family()
    width = family.width
    s = box(center + vxyz(-(width/2), -(width/2), level_height(bottom_level)),
            width,
            width,
            level_height(top_level) - level_height(bottom_level))
    bim_shape_layer(s, family.layer)
    return shape_reference(s)

@shape_constructor(solid)
def slab(vertices, level=None, family=None):
    level = level or current_level()
    family = family or default_slab_family()
    if is_list(vertices) and is_loc(vertices[0]):
        v = vz(level_height(level) - 
               family.thickness +
               family.coating_thickness)
        s = irregular_prism(map(lambda p: p + v, vertices),
                            family.thickness)
        bim_shape_layer(s, family.layer)
        return shape_reference(s)
    else:
        path = vertices if is_list(vertices) else [vertices]
        def loop(p):
            if p == []:
                return []
            else:
                e = p[0]
                if not len(p) == 1:
                    raise RuntimeError('Unfinished')
                if is_line(e):
                    raise RuntimeError('Unfinished')
                elif is_polygon(e):
                    vertices = polygon_vertices(e)
                    v = vz(level_height(level) -
                           family.thickness +
                           family.coating_thickness)
                    s = irregular_prism(map(lambda p: p + v, vertices),
                                        family.thickness)
                    bim_shape_layer(s, family.layer)
                    return shape_reference(s)
                elif is_arc(e):
                    raise RuntimeError('Unfinished')
                elif is_circle(e):
                    s = extrusion(surface_circle(circle_center(e) +
                                                 vz(-circle_center(e).z) +
                                                 vz(level_height(level)),
                                                 circle_radius(e)),
                                  vz(family.coating_thickness - family.thickness))
                    bim_shape_layer(s, family.layer)
                    return shape_reference(s)
                else:
                    raise RuntimeError('Unknown path component', e)
        return loop(path)

@shape_constructor(solid)
def slab_opening(slab_id, path):
    layer = bim_shape_layer(slab_id)
    s = subtraction(slab_id, slab(path, slab_level(slab_id), slab_family(slab_id)))
    bim_shape_layer(s, layer)
    return shape_reference(s)

@shape_constructor(solid)
def roof(vertices, level=None, family=None):
    level = level or current_level()
    family = family or default_roof_family()
    v = vz(level_height(level) - family.thickness + family.coating_thickness)
    s = irregular_prism(map(lambda p: p + v, vertices), family.thickness)
    bim_shape_layer(s, family.layer)
    return shape_reference(s)

@shape_constructor(solid)
def wall(p0, p1, bottom_level=None, top_level=None, family=None):
    bottom_level = bottom_level or current_level()
    top_level = top_level or upper_level(bottom_level)
    family = family or default_wall_family()
    base_height = level_height(bottom_level)
    h = level_height(top_level) - base_height
    z = base_height + h/2
    s = right_cuboid(p0 + vz(z), family.thickness, h, p1 + vz(z))
    bim_shape_layer(s, family.layer)
    return shape_reference(s)
  
@shape_constructor(solid)
def walls(vertices, bottom_level=None, top_level=None, family=None):
    bottom_level = bottom_level or current_level()
    top_level = top_level or upper_level(bottom_level)
    family = family or default_wall_family()
    v = vz(level_height(bottom_level))
    s = thicken(extrusion(line(map(lambda p: p + v, vertices)),
                          level_height(top_level) - level_height(bottom_level)),
                family.thickness)
    bim_shape_layer(s, family.layer)
    return shape_reference(s)

@shape_constructor(solid)
def door(wall, loc, family=None):
    family = family or default_door_family()
    wall_e = walls_family(wall).thickness
    wall_level = walls_bottom_level(wall)
    return shape_reference(
        subtraction(wall, box(loc + vz(level_height(wall_level)),
                              family.width,
                              wall_e, family.height)))

@shape_constructor(solid)
def panel(vertices, level=None, family=None):
    level = level or current_level()
    family = family or default_panel_family()
    p0, p1, p2 = vertices[1], vertices[0], vertices[2]
    n = vz(family.thickness/2, cs_from_o_vx_vy(p0, p1 - p0, p2 - p0))
    s = irregular_prism(map(lambda v: loc_in_world(v - n), vertices), vec_in_world(n*2))
    bim_shape_layer(s, family.layer)
    return shape_reference(s)


def slab_rectangle(p, len, width, level=None, family=None):
    level = level or current_level()
    family = family or default_slab_family()
    return slab([p, p + vx(len), p + vxy(len, width), p + vy(width)], level, family)
  
def roof_rectangle(p, len, width, level=None, family=None):
    level = level or current_level()
    family = family or default_roof_family()
    return roof([p, p + vx(len), p + vxy(len, width), p + vy(width)], level, family)
