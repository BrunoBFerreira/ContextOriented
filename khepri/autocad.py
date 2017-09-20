import sys
from os import path
sys.path.append(path.dirname(sys.path[0]))
from khepri.shape import *
from khepri.util import *
from khepri.coords import *
import numbers
import math
from functools import reduce
from khepri.autocad_primitives import *
#from khepri.primitives import *


#initialization
render_backend_dir('AutoCAD')


#The AutoCAD shape
class shape(base_shape):
    def validate(self, ref):
        if isinstance(ref, int):
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
        self.mark_deleted()

    def destroy(self, ref):
        Delete(ref)
    
    def copy_ref(self, ref):
        return Copy(ref)

    def intersect_ref(self, r0, r1):
        Intersect(r0, r1)
        return r0

    def subtract_ref(self, r0, r1):
        Subtract(r0, r1)
        return r0

    def slice_ref(self, r, p, n):
        Slice(r, p, n)
        return r

def and_delete(v, *args):
    for e in args: e.delete()
    return v

def and_mark_deleted(v, *args):
    for e in args: e.mark_deleted()
    return v

# The actual shapes
@shape_constructor(shape)
def point(position=u0()):
    return Point(position)

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
    return Circle(center, vz(1, center.cs), radius)

@shape_constructor(surface)
def surface_circle(center=u0(), radius=1):
    return SurfaceCircle(center, vz(1, center.cs), radius)

def _add_surface_from_curve(curve):
    res = singleton(SurfaceFromCurve(curve))
    return res
    
@shape_constructor(curve)
def arc(center=u0(), radius=1, start_angle=0, amplitude=pi):
    if radius == 0:
        return Point(center)
    elif amplitude == 0:
        return Point(add_pol(center, radius, start_angle))
    elif abs(amplitude) >= 2*pi:
        return Circle(center, vz(1, center.cs), radius)
    else:
        end_angle = start_angle + amplitude
        if end_angle > start_angle:
            return Arc(center, vz(1, center.cs), radius, start_angle, end_angle)
        else:
            return Arc(center, vz(1, center.cs), radius, end_angle, start_angle)

@shape_constructor(surface)
def surface_arc(center=u0(), radius=1, start_angle=0, amplitude=pi):
    if radius == 0:
        return Point(center)
    elif amplitude == 0:
        return Point(add_pol(center, radius, start_angle))
    elif abs(amplitude) >= 2*pi:
        return SurfaceCircle(center, vz(1, center.cs), radius)
    else:
        end_angle = start_angle + amplitude
        if end_angle > start_angle:
            return SurfaceArc(center, vz(1, center.cs), radius, start_angle, end_angle)
        else:
            return SurfaceArc(center, vz(1, center.cs), radius, end_angle, start_angle)
        
@shape_constructor(closed_curve)
def ellipse(center=u0(), radius_x=1, radius_y=1):
    if radius_x > radius_y:
        return Ellipse(center, vz(1, center.cs), vx(radius_x, center.cs), radius_y/radius_x)
    else:
        return Ellipse(center, vz(1, center.cs), vy(radius_y, center.cs), radius_x/radius_y)

@shape_constructor(surface)
def surface_ellipse(center=u0(), radius_x=1, radius_y=1):
    if radius_x > radius_y:
        return SurfaceEllipse(center, vz(1, center.cs), vx(radius_x, center.cs), radius_y/radius_x)
    else:
        return SurfaceEllipse(center, vz(1, center.cs), vy(radius_y, center.cs), radius_x/radius_y)

@shape_constructor(curve)
def line(*vertices):
    pts = unvarargs(vertices)
    return PolyLine(pts)

@shape_constructor(curve)
def spline(*positions):
    pts = unvarargs(positions)
    v0 = pts[1] - pts[0]
    v1 = pts[-1] - pts[-2]
    return InterpSpline(pts, v0, v1)

@shape_constructor(spline)
def spline_tangents(positions, start_tangent, end_tangent):
    return InterpSpline(positions, start_tangent, end_tangent)

@shape_constructor(closed_curve)
def closed_spline(*positions):
    pts = unvarargs(positions)
    return InterpClosedSpline(pts)
    

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
    return ClosedPolyLine(vertices)

@shape_constructor(surface)
def surface_rectangle(corner=u0(), dx=1, dy=None):
    dy = dy or dx
    dz = 0
    c = corner
    if isinstance(dx, xyz):
        v = loc_in_cs(dx, c.cs) - c
        dx, dy, dz = v.coords
    assert dz == 0, "The rectangle is not planar"
    vertices = [c, add_x(c, dx), add_xy(c, dx, dy), add_y(c, dy), c]
    return SurfaceClosedPolyLine(vertices)
    
@shape_constructor(closed_curve)
def polygon(*vertices):
    vs = unvarargs(vertices)
    return ClosedPolyLine(vs)
    
@shape_constructor(surface)
def surface_polygon(*vertices):
    vs = unvarargs(vertices)
    return SurfaceClosedPolyLine(vs)

@shape_constructor(polygon)
def regular_polygon(edges=3, center=u0(), radius=1, angle=0, inscribed=False):
    vertices = regular_polygon_vertices(edges, center, radius, angle, inscribed)
    vertices.append(vertices[0])
    return ClosedPolyLine(vertices)


@shape_constructor(surface_polygon)
def surface_regular_polygon(edges=3, center=u0(), radius=1, angle=0, inscribed=False):
    return SurfaceClosedPolyLine(regular_polygon_vertices(edges, center, radius, angle, inscribed))

@shape_constructor(surface)
def surface_from(*curves):
    cs = unvarargs(curves)
    refs = shapes_refs(cs)
    if is_singleton(refs):
        return and_mark_deleted(SurfaceFromCurve(refs[0]), *curves)
    else:
        regions = SurfaceFromCurves(refs)
        if is_singleton(regions):
            return and_mark_deleted(regions[0], *curves)
        else:
            raise ValueError("Multiple surfaces were generated, use surfaces_from")

def surfaces_from(*curves):
    cs = unvarargs(curves)
    refs = shapes_refs(cs)
    if is_singleton(refs):
        return and_mark_deleted([SurfaceFromCurve(refs[0])])
    else:
        return and_mark_deleted(SurfaceFromCurves(refs))
        
@shape_constructor(solid)
def box(corner=u0(), dx=1, dy=None, dz=None):
    dy = dy or dx
    dz = dz or dy
    c = corner
    if isinstance(dx, xyz):
        v = loc_in_cs(dx, c.cs) - c
        dx, dy, dz = v.coords
    return Box(c, 
               vx(1, c.cs),
               vy(1, c.cs),
               dx, dy, dz)

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
    return IrregularPyramidFrustum([b0, b1, b2, b3], [t0, t1, t2, t3])


@shape_constructor(solid)
def cylinder(base=u0(), radius=1, height=1, top=None):
    base, height = base_and_height(base, top or height)
    return Cylinder(base, radius, add_z(base, height))

@shape_constructor(solid)
def cone(base=u0(), radius=1, height=1, top=None):
    base, height = inverted_base_and_height(base, top or height)
    return Cone(base, radius, add_z(base, height))

@shape_constructor(solid)
def cone_frustum(base=u0(), base_radius=1, height=1, top_radius=1, top=None):
    base, height = base_and_height(base, top or height)
    top = top or add_z(base, height)
    return ConeFrustum(base, base_radius, top, top_radius)

@shape_constructor(solid)
def regular_pyramid_frustum(edges=4, base=u0(), base_radius=1, angle=0, height=1, top_radius=1, inscribed=False, top=None):
    base, height = base_and_height(base, top or height)
    top = top or add_z(base, height)
    return IrregularPyramidFrustum(
        regular_polygon_vertices(edges, base, base_radius, angle, inscribed),
        regular_polygon_vertices(edges, top, top_radius, angle, inscribed))
    
@shape_constructor(solid)
def regular_pyramid(edges=4, base=u0(), radius=1, angle=0, height=1, inscribed=False, top=None):
    base, height = base_and_height(base, top or height)
    top = top or add_z(base, height)
    return IrregularPyramid(regular_polygon_vertices(edges, base, radius, angle, inscribed),
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
    return IrregularPyramid(base_vertices, top)

@shape_constructor(solid)
def right_cuboid(base=u0(), width=1, height=1, length=1, top=None):
    base, dz = base_and_height(base, top or length)
    return CenteredBox(base, vx(1, base.cs), vy(1, base.cs), width, height, dz)

@shape_constructor(solid)
def sphere(center=u0(), radius=1):
    return Sphere(center, radius)

@shape_constructor(shape)
def text(str="", corner=u0(), height=1):
    return Text(str, corner, vx(1, corner.cs), vy(1, corner.cs), height)
    
def text_length(str="", height=1):
    return len(str)*height*0.85

@shape_constructor(shape)
def text_centered(str="", corner=u0(), height=1):
    return Text(str, 
                add_xy(corner, text_length(str, height)/-2, height/-2),
                vx(1, corner.cs), vy(1, corner.cs), height)

@shape_constructor(shape)
def torus(center=u0(), major_radius=1, minor_radius=1/2):
    return Torus(center, vz(1, center.cs), major_radius, minor_radius)

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
        shapes = list(filter(lambda s: not is_universal_shape(s), shapes))
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
        ss = list(filter(lambda s: not is_empty_shape(s), shapes[1:]))
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
    res = shape.realize().slice(p, n, shape)
    shape.mark_deleted()
    return res

@shape_constructor(shape)
def extrusion(profile, dir=1):
    dir = dir if isinstance(dir, vxyz) else vz(dir)
    def extrude(r):
        return native_ref(Extrude(r, dir))
    return and_delete(profile.realize().map(extrude), profile)

@shape_constructor(shape)
def revolve(shape, c=u0(), v=vz(1), start_angle=0, amplitude=2*pi):
    if isinstance(v, loc): #HACK Should we keep this?
        v = v - c
    def revol(r):
        return native_ref(Revolve(r, c, v, start_angle, amplitude))
    return and_delete(shape.realize().map(revol), shape)

@shape_constructor(shape)
def sweep(path, profile, rotation=0, scale=1):
    path_ref = path.realize()
    prof_ref = profile.realize()
    return and_delete(
        path_ref.map(lambda pa:
                     prof_ref.map(lambda pr:
                                  native_ref(Sweep(pa, 
                                                   pr,
                                                   rotation,
                                                   scale)))),
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
    return Loft(profiles_refs, rails_refs, is_ruled, is_closed)

def loft_profiles(profiles, rails, is_solid, is_ruled, is_closed):
    profiles = list(profiles)
    rails = list(rails)
    r = loft_profiles_aux(profiles, rails, is_ruled, is_closed)
#    if is_solid:
#        rh.CapPlanarHoles(r)
    return and_delete(r, *(profiles + rails))

def loft_curves(profiles, rails, is_ruled=False, is_closed=False):
    return loft_profiles(profiles, rails, False, is_ruled, is_closed)

def loft_surfaces(profiles, rails, is_ruled=False, is_closed=False):
    return loft_profiles(profiles, rails, True, is_ruled, is_closed)

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
    ref = shape.realize()
    ref.do(lambda r: Move(r, translation))
    shape.mark_deleted()
    return ref

@shape_constructor(shape)
def rotate(shape, rotation_angle=pi/2, axis_center=u0(), axis_vector=vz()):
    if isinstance(axis_vector, loc):
        axis_vector = axis_vector - axis_center
    ref = shape.realize()
    ref.do(lambda r: Rotate(r, axis_center, axis_vector, rotation_angle))
    shape.mark_deleted()
    return ref

@shape_constructor(shape)
def scale(shape, scale=1.0, center=u0()):
    ref = shape.realize()
    ref.do(lambda r: Scale(r, center, scale))
    shape.mark_deleted()
    return ref

@shape_constructor(shape)
def mirror(shape, plane_position=u0(), plane_normal=vz(), copy=True):
    ref = shape.realize()
    new_ref = ref.map(lambda r: native_ref(Mirror(r, plane_position, plane_normal, copy)))
    if not copy:
        shape.mark_deleted()
    return new_ref

def union_mirror(shape, plane_position=u0(), plane_normal=vz()):
    return union(shape, mirror(shape, plane_position, plane_normal, True))

@shape_constructor(surface)
def surface_grid(ptss, closed_u=False, closed_v=False):
    return SurfaceFromGrid(len(ptss),
                           len(ptss[0]),
                           [pt for pts in ptss for pt in pts],
                           closed_u, 
                           closed_v,
                           2)

@shape_constructor(solid)
def solid_grid(ptss, closed_u=False, closed_v=False, h=1):
    return SolidFromGrid(len(ptss),
                         len(ptss[0]),
                         [pt for pts in ptss for pt in pts],
                         closed_u, 
                         closed_v,
                         2,
                         h)


@shape_constructor(solid)
def thicken(surf, h=1):
    return surf.realize().map(lambda r: native_ref(Thicken(r, h)))




# BIM

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


# All shape constructors are defined. Transfer selectors and recognizers to this module

globals().update(shape_ops)


vbCr = "\r\n"

def delete_all_shapes():
    DeleteAll()

def bounding_box(shapes = []):
    return tuple(BoundingBox(shapes))

def all_shapes():
    return AllShapes()


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
        View(camera, target, lens)
#        doc.SendCommand("_.vscurrent _conceptual ")
#        doc.SetVariable("PERSPECTIVE", 1)
#        doc.SendCommand("_.dview  _z {0} _po {1} {2} _d {3}".format(
#            lens, 
#            loc_string(target),
#            loc_string(camera),
#            distance(camera, target)) + vbCr)
        return camera, target, lens
    else:
        return ViewCamera(), ViewTarget(), ViewLens()

def view_top():
    ViewTop()
    #FIXME doc.SendCommand("_.vscurrent _2dwireframe ")

def zoom_extents():
    ZoomExtents()

def render_view(name):
    SetSystemVariableInt("SKYSTATUS", 2)
    Render(render_width(),
           render_height(),
           ensure_file_deleted(ensure_dir(render_pathname(name))))

def render_stereo_view(str):
    pass

def save_film_frame(obj=None):
    with render_kind_dir('Film'):
        render_view(frame_filename(film_filename(), film_frame()))
        film_frame(film_frame() + 1)
        return obj

def prompt_point(str="Select point"):
    res = GetPoint(str)
    return res[0] if len(res) > 0 else False

def prompt_integer(str="Integer?"):
    return rh.GetInteger(str)

def prompt_real(str="Real?"):
    return rh.GetReal(str)

# layers
def create_layer(name, color=False):
    layer = CreateLayer(name)
    if color:
        SetLayerColor(layer, rgb_red(color), rgb_green(color), rgb_blue(color))
    return layer

def _current_layer(name=None):
    if name:
        SetCurrentLayer(name)
    else:
        name = CurrentLayer()
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

white_floor_layer = False
black_floor_layer = False
dark_gray_layer = False
white_layer = False
black_layer = False
floor_layer = make_parameter(False)
shapes_layer = make_parameter(False)

def ensure_layers_exist():
    global white_floor_layer
    global black_floor_layer
    global dark_gray_layer
    global white_layer
    global black_layer
    global floor_layer
    global shapes_layer
    if not white_floor_layer:
        white_floor_layer = create_layer('Floor')
        black_floor_layer = create_layer('FloorBlack')
        dark_gray_layer = create_layer('DarkGray')
        white_layer = create_layer('White')
        black_layer = create_layer('Black')

def white_renders():
    ensure_layers_exist()
    render_color_dir("White")
    render_size(1920, 1080)
    floor_layer(white_floor_layer)
    shapes_layer(dark_gray_layer)
    current_layer(dark_gray_layer)

def black_renders():
    ensure_layers_exist()
    render_color_dir("Black")
    render_size(1920, 1080)
    floor_layer(black_floor_layer)
    shapes_layer(dark_gray_layer)
    current_layer(dark_gray_layer)

floor_distance = make_parameter(10)
floor_extra_width = make_parameter(2000)
floor_extra_factor = make_parameter(20)

def make_floor_for_bounding_box(bb):
    p0, p1 = bb
    w = max(floor_extra_factor()*distance(p0, p1), floor_extra_width())
    with current_layer(floor_layer()):
        box(xyz(min(p0.x, p1.x) - w,
	        min(p0.y, p1.y) - w,
	        p0.z - 1 - floor_distance()),
            xyz(max(p0.x, p1.x) + w,
	        max(p0.y, p1.y) + w,
		p0.z - 0 - floor_distance()))

def make_floor():
    return make_floor_for_bounding_box(bounding_box())

def make_background(c, t, f, w, h, d):
    wp, hp = (w*d)/f, (h*d)/f
    dp = norm_c(t - c)*d
    p, l = loc_from_o_z(c + dp, c - t), 2*max(wp, hp)
    with current_layer(floor_layer()):
        box(p + vxy(-l/2, -l/2), l, l, -0.001)

def view_with_background(camera, target, lens):
    bb = bounding_box()
    make_floor_for_bounding_box(bb)
    if floor_layer() is black_floor_layer:
        farthest_p = argmax(lambda p: distance(camera, p), bbox_corners(bb))
        make_background(camera, target, lens, 50, 40, distance(camera, farthest_p))
    return view(camera, target, lens)


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

'''
from tkinter import *
master = Tk()
def create_sliders(f, *params):
    sliders = []
    def callback(val):
        try:
            DisableUpdate()
            delete_all_shapes()
            f(*[slider.get() for slider in sliders])
        finally:
            EnableUpdate()
    for name, inf, sup, res, cur in params:
        w = Scale(master, label=name, from_=inf, to=sup, resolution=res, command=callback, orient=HORIZONTAL)
        w.set(cur)
        w.pack()
        sliders.append(w)
'''
if( __name__ == '__main__' ):
    print("The Khepri library is not intended to be executed, just imported")
