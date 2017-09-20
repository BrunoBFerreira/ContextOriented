import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from math import *
from functools import *
import array
import comtypes
import glob
import os
from khepri.shape import *
from khepri.util import *
from khepri.coords import *

# Patch comtypes

def trace_method(cls, name):
    meth = getattr(cls, name)
#    oldname = "___old__" + name
#    setattr(cls, oldname, meth)
    def newmeth(self, *args):
        print(name, "(", args, ")",)
        return meth(self, *args)
    setattr(cls, name, newmeth)

#trace_method(comtypes.automation.IDispatch, '_invoke')
#trace_method(comtypes.automation.IDispatch, 'Invoke')
#trace_method(comtypes.automation.tagVARIANT, '_set_value')
#trace_method(comtypes.safearray.LP_SAFEARRAY_tagVARIANT, 'create')

class cached(object):
    def __init__(self, func):
        self.func = func
        self.cache = None
        self.cached = False
    def __call__(self, *args):
        if self.cached:
            return self.cache
        else:
            self.cache = self.func(*args)
            self.cached = True
            return self.cache

import comtypes.client
# generate modules for ACAD constants
for pattern in ("acax*enu.tlb", "axdb*enu.tlb"):
    pattern = os.path.join(r"C:\Program Files\Common Files\Autodesk Shared",
                           pattern)
    tlib = glob.glob(pattern)[0]
    comtypes.client.GetModule(tlib)
import comtypes.gen.AutoCAD as ACAD

@cached
def AutoCAD(create=True, visible=True):
    try:
        return comtypes.client.GetActiveObject('AutoCAD.Application', dynamic=True)
    except WindowsError:
        if create:
            app = comtypes.client.CreateObject('AutoCAD.Application', dynamic=True)
            app.Visible = visible
            return app
        else:
            raise

"""
@cached
def doc():
    return AutoCAD().ActiveDocument
@cached
def db():
    return doc().ModelSpace
@cached
def util():
    return doc.Utility
"""
app = AutoCAD()
doc = app.ActiveDocument
db = doc.ModelSpace
util = doc.Utility

def rawxyz(x, y, z):
    return array.array('d', (x, y, z))

rawu0 = rawxyz(0, 0, 0)

def Pt(p):
    p = p.raw_in_world
    return rawxyz(p.x, p.y, p.z)

def loc_from_vector_float(v):
    return xyz(v[0], v[1], v[2])

def var_double_3n(pts):
    return array.array('d', [c for p in pts for c in p.raw_in_world])

def create_from_matrix(value):
    from ctypes import (POINTER, Structure, byref, cast, c_long, c_float, c_double, memmove, pointer, sizeof)
    from comtypes import _safearray, IUnknown, com_interface_registry, npsupport
    from comtypes.automation import VARIANT, VT_R8, VT_ARRAY, tagVARIANT
    from comtypes.safearray import _midlSAFEARRAY
    vartype = VT_R8
    itemtype = c_double
    cls = _midlSAFEARRAY(itemtype)
    matrixsize = 4
    rgsa = (_safearray.SAFEARRAYBOUND * 2)()
    rgsa[0].cElements = matrixsize
    rgsa[0].lBound = 0
    rgsa[1].cElements = matrixsize
    rgsa[1].lBound = 0
    pa = _safearray.SafeArrayCreateEx(vartype, 2, rgsa, None)
    pa = cast(pa, cls)
    # Now, fill the data in:
    ptr = POINTER(itemtype)()  # pointer to the item values
    _safearray.SafeArrayAccessData(pa, byref(ptr))
    try:
        nbytes = matrixsize**2 * sizeof(itemtype)
        memmove(ptr, addr, nbytes)
    finally:
        _safearray.SafeArrayUnaccessData(pa)
    var = tagVARIANT()
    memmove(byref(var._), byref(pa), sizeof(pa))
    var.vt = VT_ARRAY | pa._vartype_
    return var

def create_from_linearized_matrix(value):
    from ctypes import (POINTER, Structure, byref, cast, c_long, c_float, c_double, memmove, pointer, sizeof)
    from comtypes import _safearray, IUnknown, com_interface_registry
    from comtypes.automation import VARIANT, VT_R8, VT_ARRAY, tagVARIANT
    from comtypes.safearray import _midlSAFEARRAY
    addr, n = value.buffer_info()    
    vartype = VT_R8
    itemtype = c_double
    cls = _midlSAFEARRAY(itemtype)
    matrixsize = 4
    rgsa = (_safearray.SAFEARRAYBOUND * 2)()
    rgsa[0].cElements = matrixsize
    rgsa[0].lBound = 0
    rgsa[1].cElements = matrixsize
    rgsa[1].lBound = 0
    pa = _safearray.SafeArrayCreateEx(vartype, 2, rgsa, None)
    pa = cast(pa, cls)
    # Now, fill the data in:
    ptr = POINTER(itemtype)()  # pointer to the item values
    _safearray.SafeArrayAccessData(pa, byref(ptr))
    try:
        nbytes = matrixsize**2 * sizeof(itemtype)
        memmove(ptr, addr, nbytes)
    finally:
        _safearray.SafeArrayUnaccessData(pa)
    var = tagVARIANT()
    memmove(byref(var._), byref(pa), sizeof(pa))
    var.vt = VT_ARRAY | pa._vartype_
    return var

def variant_array(value):
    from ctypes import (POINTER, Structure, byref, cast, c_long, c_float, c_double, memmove, pointer, sizeof)
    from comtypes import _safearray, IUnknown, com_interface_registry
    from comtypes.automation import VARIANT, VT_VARIANT, VT_SAFEARRAY, VT_ARRAY, tagVARIANT, VT_DISPATCH
    from comtypes.safearray import _midlSAFEARRAY
    vartype = VT_DISPATCH
    itemtype = VARIANT
    cls = _midlSAFEARRAY(itemtype)
    rgsa = (_safearray.SAFEARRAYBOUND * 1)()
    rgsa[0].cElements = len(value)
    rgsa[0].lBound = 0
    pa = _safearray.SafeArrayCreateEx(vartype, 1, rgsa, None)
    pa = cast(pa, cls)
    # Now, fill the data in:
    ptr = POINTER(itemtype)()  # pointer to the item values
    _safearray.SafeArrayAccessData(pa, byref(ptr))
    try:
        for i, a in enumerate(value):
            ptr[i] = a
    finally:
        _safearray.SafeArrayUnaccessData(pa)
    var = tagVARIANT()
    memmove(byref(var._), byref(pa), sizeof(pa))
    var.vt = VT_ARRAY | pa._vartype_
    return var


def test():
    db.AddRegion(db.AddCircle(rawu0, 1))


def transform(com, p):
    t = p.world_transformation
    #Go see method create_from_ndarray in https://github.com/enthought/comtypes/blob/master/comtypes/safearray.py
    #to avoid using numpy
    #com.TransformBy(numpy.transpose(numpy.array([t._row0, t._row1, t._row2, t._row3])))
    #com.TransformBy(create_from_matrix(numpy.transpose(numpy.array([t._row0, t._row1, t._row2, t._row3]))))
    com.TransformBy(create_from_linearized_matrix(array.array('d', t.components())))
    return com

#The AutoCAD shape
class shape(base_shape):
    def validate(self, ref):
        if isinstance(ref, comtypes.client.lazybind.Dispatch):
            return native_ref(ref)
        elif isinstance(ref, (tuple, list)):
            if len(ref) == []:
                raise RuntimeError("The operation failed!")
            elif len(ref) == 1:
                return self.validate(ref[0])
            else:
                return union_ref([self.validate(g) for g in ref])
        elif (is_empty_ref(ref) or 
              is_universal_ref(ref) or
              isinstance(ref, (native_ref, multiple_ref))):
            return ref
        else:
            raise ValueError("Unexpected ref: {0}".format(ref))

    def delete(self):
        #Perhaps optimize this in case the shape was not yet realized
        self.realize().do(lambda r: self.destroy(r))

    def destroy(self, ref):
        db.Delete(ref, True)
    
    def copy_ref(self, ref):
        return rh.CopyObject(ref)

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

@shape_constructor(closed_curve)
def circle(center=u0(), radius=1):
    return transform(db.AddCircle(rawu0, radius), center)

@shape_constructor(surface)
def surface_circle(center=u0(), radius=1):
    return _add_surface_circle(center, radius)

def _add_surface_from_curve(curve):
    res = singleton(db.AddRegion(variant_array([curve])))
    curve.Delete()
    return res

def _add_surface_circle(center, radius):
    return transform(_add_surface_from_curve(db.AddCircle(rawu0, radius)), center)
    
@shape_constructor(curve)
def arc(center=u0(), radius=1, start_angle=0, amplitude=pi):
    if radius == 0:
        return db.AddPoint(Pt(center))
    elif amplitude == 0:
        return db.AddPoint(Pt(add_pol(center, radius, start_angle)))
    elif abs(amplitude) >= 2*pi:
        return transform(db.AddCircle(rawu0, radius), center)
    else:
        endAngle = start_angle + amplitude
        return transform(db.AddArc(rawu0, radius, start_angle, endAngle)
                         if endAngle > start_angle
                         else db.AddArc(rawu0, radius, endAngle, start_angle),
                         center)

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
    return transform(db.AddEllipse(rawu0, rawxyz(radiusX, 0, 0), radiusY/radiusX)
                     if radiusX > radiusY
                     else db.AddEllipse(rawu0, rawxyz(0, radiusY, 0), radiusX/radiusY),
                     center)

@shape_constructor(surface)
def surface_ellipse(center=u0(), radius_x=1, radius_y=1):
    return _surface_from_curves([geo.Ellipse(Pl(center), radius_x, radius_y).ToNurbsCurve()])

@shape_constructor(curve)
def line(*vertices):
    vs = unvarargs(vertices)
    return db.Add3DPoly(var_double_3n(vs))

@shape_constructor(curve)
def spline(*positions):
    pts = unvarargs(positions)
    v0 = Pt(pts[1] - pts[0])
    v1 = Pt(pts[-1] - pts[-2])
    return db.AddSpline(var_double_3n(pts), v0, v1)

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
    vertices = [c, add_x(c, dx), add_xy(c, dx, dy), add_y(c, dy), c]
    return db.Add3DPoly(var_double_3n(vertices))
        
@shape_constructor(surface)
def surface_rectangle(corner=u0(), dx=1, dy=None):
    r = rectangle(corner, dx, dy)
    s = rh.AddPlanarSrf(r.realize()._ref)
    r.delete()
    return s
    
@shape_constructor(closed_curve)
def polygon(*vertices):
    vs = unvarargs(vertices)
    c = db.Add3DPoly(var_double_3n(vs+(vs[0],)))
    c.Closed = True
    return c
    
@shape_constructor(surface)
def surface_polygon(*vertices):
    vs = unvarargs(vertices)
    return _surface_from_curves([geo.Polyline([Pt(v) for v in vs]+[Pt(vs[0])]).ToNurbsCurve()])
    
@shape_constructor(polygon)
def regular_polygon(edges=3, center=u0(), radius=1, angle=0, inscribed=False):
    vertices = regular_polygon_vertices(edges, center, radius, angle, inscribed)
    vertices.append(vertices[0])
    c = db.Add3DPoly(var_double_3n(vertices))
    c.Closed = True
    return c

@shape_constructor(surface_polygon)
def surface_regular_polygon(edges=3, center=u0(), radius=1, angle=0, inscribed=False):
    pts = map(Pt, regular_polygon_vertices(edges, center, radius, angle, inscribed))
    return rh.AddPlanarSrf([rh.AddPolyline(pts + [pts[0]])])

@shape_constructor(surface)
def surface_from(*curves):
    cs = unvarargs(curves)
    refs = _shapes_refs(cs)
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
    else:
        id = rh.AddEdgeSrf(refs)
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
    return transform(db.AddBox(rawxyz(dx/2, dy/2, dz/2),
                               abs(dx), abs(dy), abs(dz)),
                     c)

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
    return _irregular_pyramid_frustum([b0, b1, b2, b3], [t0, t1, t2, t3])


@shape_constructor(solid)
def cylinder(base=u0(), radius=1, height=1, top=None):
    base, height = base_and_height(base, top or height)
    return transform(db.AddCylinder(rawxyz(0, 0, height/2), radius, height),
                     base)

@shape_constructor(solid)
def cone(base=u0(), radius=1, height=1, top=None):
    base, height = inverted_base_and_height(base, top or height)
    return transform(db.AddCone(rawxyz(0, 0, height/2), radius, height),
                     base)

@shape_constructor(solid)
def cone_frustum(base=u0(), base_radius=1, height=1, top_radius=1, top=None):
    base, height = base_and_height(base, top or height)
    top = top or add_z(base, height)
    return transform(newShapesCmd("_.cone 0,0,0 {0} _T {1} {2} ".
                                  format(base_radius, top_radius, height)),
                     base)

from ctypes import (POINTER, Structure, byref, cast, c_long, c_float, c_double, memmove, pointer, sizeof)
from comtypes import _safearray, IUnknown, com_interface_registry
from comtypes.automation import VARIANT, VT_VARIANT, VT_SAFEARRAY, VT_ARRAY, tagVARIANT, VT_DISPATCH
from comtypes.safearray import _midlSAFEARRAY

def variant(data):
    return VARIANT(VT_VARIANT, data)

def vararr(*data):
    return list(map(variant, data))

        
def _irregular_pyramid(cbs, ct):
    pts0, pt1 = list(map(Pt, cbs)), Pt(ct)
    pt = pts0[0]
    pts1 = pts0[1:] + [pt]
    faces = ([db.Add3DFace(pt00, pt01, pt1, pt1) 
              for pt00, pt01 in zip(pts0, pts1)] +
             [db.Add3DFace(pt, pt00, pt01, pt01)
              for pt00, pt01 in zip(pts0[1:], pts1[1:])])
    print("About to add regions", faces)
    regions = db.AddRegion(vararr([int(ent.Handle, 16) for ent in faces])) #variant_array(faces))
    print("Added regions", regions)
    #for e in faces: e.Delete()
    #print("Deleted faces")
    res = surfsculp_command(faces)
    print("Surfsculped", res)
    #for e in regions: e.Delete()
    #print("Deleted regions", regions)
    return res


def _irregular_pyramid_frustum(pts0, pts1):
    return sphere().realize()._ref
    pts0 = map(Pt, pts0)
    pts1 = map(Pt, pts1)
    pts0r = pts0[1:] + [pts0[0]]
    pts1r = pts1[1:] + [pts1[0]]
    top = pts0[0]
    bot = pts1[0]
    faces = ([db.Add3DFace(pt00, pt01, pt11, pt10) 
              for pt00, pt01, pt10, pt11 in zip(pts0, pts0r, pts1, pts1r)] + 
             [db.Add3DFace(top, pt00, pt01, pt01)
              for pt00, pt01 in zip(pts0[1:], pts0r[1:])] + 
             [db.Add3DFace(bot, pt00, pt01, pt01) 
              for pt00, pt01 in zip(pts1[1:], pts1r[1:])])
    regions = db.AddRegion(variant_array(faces))
    for e in faces: e.Delete()
    res = surfsculp_command(regions)
    for e in regions: e.Delete()
    return res


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
    return _irregular_pyramid_frustum(cbs, map((lambda p: p + dir), cbs))
    
@shape_constructor(solid)
def irregular_pyramid(base_vertices=None, top=None):
    base_vertices = base_vertices or [ux(), uy(), uxy()]
    top = top or uz()
    return _irregular_pyramid(base_vertices, top)

@shape_constructor(solid)
def right_cuboid(base=u0(), width=1, height=1, length=1, top=None):
    base, dz = base_and_height(base, top or length)
    return transform(db.AddBox(rawxyz(0,0,dz/2), width, height, dz), base)

@shape_constructor(solid)
def sphere(center=u0(), radius=1):
    return db.AddSphere(Pt(center), radius)


@shape_constructor(shape)
def text(str="", corner=u0(), height=1):
    return transform(db.AddText(str, rawu0, height), corner)
    
def text_length(str="", height=1):
    return len(str)*height*0.7

@shape_constructor(shape)
def text_centered(str="", corner=u0(), height=1):
    return transform(db.AddText(str, rawu0, height),
                     add_xy(corner, text_length(str, height)/-2, height/-2))

@shape_constructor(shape)
def torus(center=u0(), major_radius=1, minor_radius=1/2):
    return transform(db.AddTorus(rawu0, major_radius, minor_radius), center)

@shape_constructor(shape)
def union(*shapes):
    shapes = list(filter(lambda s: not is_empty_shape(s),
                         unvarargs(shapes)))
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
            return empty_ref()
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
    r = singleton(rh.AddSweep1(path, profiles))
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
    if len(ptss) == 2 and len(ptss[0]) == 2:
        return rh.AddSrfPt(ptss[0] + ptss[1])
    else:
        if len(ptss) == 2:
            ptss = [ptss[0], map(intermediate_point, ptss[0], ptss[1]), ptss[1]]
        elif len(ptss[0]) == 2:
            ptss = map(lambda cs: [cs[0], intermediate_point(cs[0], cs[1]), cs[1]], ptss)
        return rh.AddSrfPtGrid((len(ptss), len(ptss[0])),
                               [Pt(pt) for pts in ptss for pt in pts],
                               (3, 3),
                               (closed_u, closed_v))

@shape_constructor(solid)
def thicken(surf, h=1):
    s = rh.OffsetSurface(surf.realize()._ref, h, None, True, True)
    if not s:
        rh.UnselectAllObjects()
        rh.SelectObjects(surf.refs())
        rh.Command("OffsetSrf BothSides=Yes Solid=Yes {0} _Enter".format(h))
        s = single_ref_or_union(rh.LastCreatedObjects())
    surf.mark_deleted()
    return s


# All shape constructors are defined. Transfer selectors and recognizers to this module

globals().update(shape_ops)


vbCr = "\r\n"

def delete_all_shapes():
    doc.SendCommand("_.erase _all" + vbCr)

### Special commands
def loc_string(p):
    p = p.raw_in_world
    return "{0},{1},{2}".format(p.x, p.y, p.z)

def newShapesCmd(str):
    prev = db.count
    doc.SendCommand(str)
    curr = db.count
    if curr < prev:
        raise RuntimeError("Items were eliminated")
    elif curr == prev:
        raise RuntimeError("No new items")
    elif curr > prev + 1:
        raise RuntimeError("More than one new items")
    else:
        return db.Item(prev)

def handle(obj):
    return obj.handle

def handent_string(handle):
    return '(handent "' + handle + '")'

def handent(object):
    return handent_string(handle(object))

def handents(objects):
    return ' '.join(map(handent, objects))

def surfsculp_command(objs):
    return newShapesCmd("._surfsculpt {0}{1}".format(handents(objs), vbCr))

####

def view(camera=False, target=False, lens=False):
    if camera and target and lens:
        doc.SendCommand("_.vscurrent _conceptual ")
        doc.SetVariable("PERSPECTIVE", 1)
        doc.SendCommand("_.dview  _z {0} _po {1} {2} _d {3}".format(
            lens, 
            loc_string(target),
            loc_string(camera),
            distance(camera, target)) + vbCr)
        return camera, target, lens
    else:
        return "This must be finished"

def view_top():
    doc.SendCommand("_.-view _top ")
    doc.SendCommand("_.vscurrent _2dwireframe ")

def zoom_extents():
    app.ZoomExtents()

def render_view(str):
    pass

def render_stereo_view(str):
    pass
    
def prompt_point(str="Select point"):
    return loc_from_vector_float(util.GetPoint(rawu0, str))

def prompt_integer(str="Integer?"):
    return rh.GetInteger(str)

def prompt_real(str="Real?"):
    return rh.GetReal(str)


# layers
def create_layer(name, color=None):
    layer = doc.layers.Add(name)
    if color:
        layer.color = color
    return name

def _current_layer(name=None):
    if name:
        doc.SetVariable("CLAYER", name)
    else:
        name = doc.GetVariable("CLAYER")
    return name

class current_layer:
    def __init__(self, layer):
        self.layer = layer
        self.previous_layer = None

    def __enter__(self):
        self.previous_layer = _current_layer()
        _current_layer(self.layer)
        return self.layer

    def __exit__(self, type, value, traceback):
        _current_layer(self.previous_layer)



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
#cidadeEspacial(u0(), 16)
#print time.clock() - t

#cone(xyz(1,2,3),1,xyz(1,2,30))
#cone(xyz(1,2,3),1,xyz(1,20,3))
#cone(xyz(1,2,3),1,xyz(10,2,3))

#circle(xyz(1,2,3), radius=3)
#cylinder(xyz(1,2,3), height=5)



if( __name__ == '__main__' ):
    print("The Khepri library is not intended to be executed, just imported")
