import socket
import struct
import sys
from os import path
import time
from math import *
from functools import *
import shutil
sys.path.append(path.dirname(sys.path[0]))
from khepri.coords import *
from khepri.primitives import *

# Default implementation that might need overriding

# A Ref is a reference to some external shape representation
# In order to support a functional interface, Refs might need to be consumed and
# recreated at will
class Ref(object):
    def __init__(self, shape, backend, ref=None):
        self.shape = shape
        self.backend = backend
        self.created = 0 if ref is None else 1
        self.deleted = 0
        self.ref = ref

    def validate(self, ref):
        return ref

    def is_realized(self):
        return self.created == self.deleted + 1

    def realize(self):
        if self.created == self.deleted: # not realized
            self.ref = self.validate(self.shape.backend_create(self.backend))
            self.created += 1
            return self.ref
        elif self.created == self.deleted + 1:
            if self.ref:
                return self.ref
            else:
                raise RuntimeException("The object was realized but does not have a reference")
        else:
            raise RuntimeException("Inconsistent creation {0} and deletion {0}".format(self.created, self.deleted))
 
    def mark_deleted(self):
        if self.created == self.deleted + 1:
            self.ref = None
            self.deleted += 1
        else:
            raise RuntimeException("Inconsistent creation {0} and deletion {0}".format(self.created, self.deleted))

    def delete(self):
        refs = self.refs()
        mark_deleted(self)
        for ref in refs:
            self.destroy(ref)

    def ref(self):
        return self.realize().ref()

    def refs(self):
        return self.realize().refs()


class Backend(object):
    def new_ref(self, shape):
        return Ref(shape, self)
    
    def circle(self, center, radius):
        return self.Circle(center, vz(1, center.cs), radius)
    
    def surface_circle(self, center, radius):
        return self.SurfaceCircle(center, vz(1, center.cs), radius)
    
    def _add_surface_from_curve(self, curve):
        res = singleton(self.SurfaceFromCurve(curve))
        return res
        
    def arc(self, center=u0(), radius=1, start_angle=0, amplitude=pi):
        if radius == 0:
            return self.Point(center)
        elif amplitude == 0:
            return self.Point(add_pol(center, radius, start_angle))
        elif abs(amplitude) >= 2*pi:
            return self.Circle(center, vz(1, center.cs), radius)
        else:
            end_angle = start_angle + amplitude
            if end_angle > start_angle:
                return self.Arc(center, vz(1, center.cs), radius, start_angle, end_angle)
            else:
                return self.Arc(center, vz(1, center.cs), radius, end_angle, start_angle)
    
    def surface_arc(self, center=u0(), radius=1, start_angle=0, amplitude=pi):
        if radius == 0:
            return self.Point(center)
        elif amplitude == 0:
            return self.Point(add_pol(center, radius, start_angle))
        elif abs(amplitude) >= 2*pi:
            return self.SurfaceCircle(center, vz(1, center.cs), radius)
        else:
            end_angle = start_angle + amplitude
            if end_angle > start_angle:
                return self.SurfaceArc(center, vz(1, center.cs), radius, start_angle, end_angle)
            else:
                return self.SurfaceArc(center, vz(1, center.cs), radius, end_angle, start_angle)
            
    def ellipse(self, center=u0(), radius_x=1, radius_y=1):
        if radius_x > radius_y:
            return self.Ellipse(center, vz(1, center.cs), vx(radius_x, center.cs), radius_y/radius_x)
        else:
            return self.Ellipse(center, vz(1, center.cs), vy(radius_y, center.cs), radius_x/radius_y)
    
    def surface_ellipse(self, center=u0(), radius_x=1, radius_y=1):
        if radius_x > radius_y:
            return self.SurfaceEllipse(center, vz(1, center.cs), vx(radius_x, center.cs), radius_y/radius_x)
        else:
            return self.SurfaceEllipse(center, vz(1, center.cs), vy(radius_y, center.cs), radius_x/radius_y)
    
    def line(self, pts):
        return self.PolyLine(pts)
    
    def spline(self, pts):
        v0 = pts[1] - pts[0]
        v1 = pts[-1] - pts[-2]
        return self.InterpSpline(pts, v0, v1)
    
    def spline_tangents(self, pts, start_tangent, end_tangent):
        return self.InterpSpline(pts, start_tangent, end_tangent)
    
    def closed_spline(self, pts):
        return self.InterpClosedSpline(pts)       
    
    def rectangle(self, corner=u0(), dx=1, dy=None):
        dy = dy or dx
        dz = 0
        c = corner
        if isinstance(dx, xyz):
            v = loc_in_cs(dx, c.cs) - c
            dx, dy, dz = v.coords
        assert dz == 0, "The rectangle is not planar"
        vertices = [c, add_x(c, dx), add_xy(c, dx, dy), add_y(c, dy), c]
        return self.ClosedPolyLine(vertices)
    
    def surface_rectangle(self, corner=u0(), dx=1, dy=None):
        dy = dy or dx
        dz = 0
        c = corner
        if isinstance(dx, xyz):
            v = loc_in_cs(dx, c.cs) - c
            dx, dy, dz = v.coords
        assert dz == 0, "The rectangle is not planar"
        vertices = [c, add_x(c, dx), add_xy(c, dx, dy), add_y(c, dy), c]
        return self.SurfaceClosedPolyLine(vertices)
        
    def polygon(self, vs):
        return self.ClosedPolyLine(vs)
        
    def surface_polygon(self, vs):
        return self.SurfaceClosedPolyLine(vs)
    
    def regular_polygon(self, edges=3, center=u0(), radius=1, angle=0, inscribed=False):
        vertices = regular_polygon_vertices(edges, center, radius, angle, inscribed)
        vertices.append(vertices[0])
        return self.ClosedPolyLine(vertices)
    
    def surface_regular_polygon(self, edges=3, center=u0(), radius=1, angle=0, inscribed=False):
        return self.SurfaceClosedPolyLine(regular_polygon_vertices(edges, center, radius, angle, inscribed))
            
    def box(self, corner=u0(), dx=1, dy=None, dz=None):
        dy = dy or dx
        dz = dz or dy
        c = corner
        if isinstance(dx, xyz):
            v = loc_in_cs(dx, c.cs) - c
            dx, dy, dz = v.coords
        return self.Box(c, 
                        vx(1, c.cs),
                        vy(1, c.cs),
                        dx, dy, dz)
    
    def cuboid(self, b0=None, b1=None, b2=None, b3=None, t0=None, t1=None, t2=None, t3=None):
        b0 = b0 or u0()
        b1 = b1 or add_x(b0, 1)
        b2 = b2 or add_y(b1, 1)
        b3 = b3 or add_y(b0, 1)
        t0 = t0 or add_z(b0, 1)
        t1 = t1 or add_x(t0, 1)
        t2 = t2 or add_y(t1, 1)
        t3 = t3 or add_y(t0, 1)
        return self.IrregularPyramidFrustum([b0, b1, b2, b3], [t0, t1, t2, t3])
    
    def cylinder(self, base=u0(), radius=1, height=1, top=None):
        base, height = base_and_height(base, top or height)
        return Cylinder(base, radius, add_z(base, height))
    
    def cone(self, base=u0(), radius=1, height=1, top=None):
        base, height = inverted_base_and_height(base, top or height)
        return self.Cone(base, radius, add_z(base, height))
    
    def cone_frustum(self, base=u0(), base_radius=1, height=1, top_radius=1, top=None):
        base, height = base_and_height(base, top or height)
        top = top or add_z(base, height)
        return self.ConeFrustum(base, base_radius, top, top_radius)
    
    def regular_pyramid_frustum(self, edges=4, base=u0(), base_radius=1, angle=0, height=1, top_radius=1, inscribed=False, top=None):
        base, height = base_and_height(base, top or height)
        top = top or add_z(base, height)
        return self.IrregularPyramidFrustum(
            regular_polygon_vertices(edges, base, base_radius, angle, inscribed),
            regular_polygon_vertices(edges, top, top_radius, angle, inscribed))
        
    def regular_pyramid(self, edges=4, base=u0(), radius=1, angle=0, height=1, inscribed=False, top=None):
        base, height = base_and_height(base, top or height)
        top = top or add_z(base, height)
        return self.IrregularPyramid(regular_polygon_vertices(edges, base, radius, angle, inscribed),
                                     top)
    
    def regular_prism(self, edges=4, base=u0(), radius=1, angle=0, height=1, inscribed=False, top=None):
        base, height = base_and_height(base, top or height)
        top = top or add_z(base, height)
        return self._irregular_pyramid_frustum(
            regular_polygon_vertices(edges, base, radius, angle, inscribed),
            regular_polygon_vertices(edges, top, radius, angle, inscribed))
    
    def irregular_prism(self, base_vertices=None, direction=1):
        base_vertices = base_vertices or [ux(), uy(), uxy()]
        dir = vz(direction, base_vertices[0].cs) if is_number(dir) else dir
        return self._irregular_pyramid_frustum(cbs, map((lambda p: p + dir), cbs))
        
    def irregular_pyramid(self, base_vertices=None, top=None):
        base_vertices = base_vertices or [ux(), uy(), uxy()]
        top = top or uz()
        return self.IrregularPyramid(base_vertices, top)
    
    def right_cuboid(self, base=u0(), width=1, height=1, length=1, top=None):
        base, dz = base_and_height(base, top or length)
        return self.CenteredBox(base, vx(1, base.cs), vy(1, base.cs), width, height, dz)
    
    def sphere(self, center=u0(), radius=1):
        return self.Sphere(center, radius)
    
    def text(self, str="", corner=u0(), height=1):
        return self.Text(str, corner, vx(1, corner.cs), vy(1, corner.cs), height)
        
    def text_length(self, str="", height=1):
        return len(str)*height*0.85
    
    def text_centered(self, str="", corner=u0(), height=1):
        return self.Text(str, 
                         add_xy(corner, text_length(str, height)/-2, height/-2),
                         vx(1, corner.cs), vy(1, corner.cs), height)
    
    def torus(self, center=u0(), major_radius=1, minor_radius=1/2):
        return self.Torus(center, vz(1, center.cs), major_radius, minor_radius)
            
    def surface_grid(self, ptss, closed_u=False, closed_v=False):
        return self.SurfaceFromGrid(len(ptss),
                                    len(ptss[0]),
                                    [pt for pts in ptss for pt in pts],
                                    closed_u, 
                                    closed_v,
                                    2)
    
    def solid_grid(self, ptss, closed_u=False, closed_v=False, h=1):
        return self.SolidFromGrid(len(ptss),
                                  len(ptss[0]),
                                  [pt for pts in ptss for pt in pts],
                                  closed_u, 
                                  closed_v,
                                  2,
                                  h)
    

class SocketBasedBackend(Backend):
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.conn = None

    def connection(self):
        if not self.conn:
            self.conn = self.create_connection()
        return self.conn
            
    def create_connection(self):
        for i in range(10):
            try:
                return socket.create_connection(("127.0.0.1", self.port))
            except (ConnectionRefusedError, socket.timeout):
                print('Please, start/restart ' + self.name)
                time.sleep(8)
                if i == 9:
                    raise
            
    def request_operation(self, name):
        conn = self.connection()
        Int.write(conn, 0)
        String.write(conn, name)
        op = Int.read(conn)
        print('Request for ', name, ' -> ', op)
        if op == -1:
            raise NameError(name + ' is not available')
        else:
            return op

        
types = { 
    'void': Void,
    'byte': Byte,
    'int': Int,
    'double': Double,
    'bool': Boolean,
    'string': String,
    'Length': Length,
    'ObjectId': ObjectId,
    'ElementId': ObjectId,
    'Element': ObjectId,
    'Level': ObjectId,
    'Entity': Entity,
    'Material': ObjectId,
    'Point3d': Point3d,
    'XYZ': Point3d,
    'Vector3d': Vector3d,
    'Frame3d': Frame3d
}

arraytypes = {
    'ObjectId': ObjectIdArray,
    'Point3d' : Point3dArray
}

debug_mode = True

def cdecl(sig):
    def parse_c_signature(sig):
        import re
        def parse_c_decl(decl):
            m = re.match(r"^ *(\w+) *(\[\])? *(\w+)$", decl)
            return (arraytypes if m.group(2)=="[]" else types)[m.group(1)]
    
        m = re.match(r"^ *(public|) *(\w+) *(\[\])? +(\w+) *\( *(.*) *\)", sig)
        ret = parse_c_decl(m.group(2)+" foo") # dummy var for return type
        name = m.group(4)
        params_str = m.group(5)
        params = re.findall(r"\w+ +\w+", params_str)
        return (name, [parse_c_decl(decl) for decl in params], ret)
    
    name, arg_types, ret_type = parse_c_signature(sig)

    def add_cdecl_method(cls):
        def create_send_message(opcode):
            def send_message(self, *args):
                assert len(args) == len(arg_types), "%r: %r does not match %r" % (name, args, tuple(type(t).__name__ for t in arg_types))
                conn = self.connection()
                Int.write(conn, opcode);
                if debug_mode:
                    print("{0}{1}".format(name, args), flush=True)
                for arg_type, arg in zip(arg_types, args):
                    arg_type.write(conn, arg)
                return ret_type.read(conn)
            return send_message

        def setup(self, *args):
            opcode = self.request_operation(name)
            func = create_send_message(opcode)
            setattr(cls, name, func)
            return func(self, *args)
            
        setattr(cls, name, setup)
        return cls

    return add_cdecl_method



# AutoCAD

class AutoCADRef(Ref):
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


@cdecl("public int DeleteAll()")
@cdecl("public void SetView(Point3d position, Point3d target, double lens, bool perspective, string style)")
@cdecl("public void View(Point3d position, Point3d target, double lens)")
@cdecl("public void ViewTop()")
@cdecl("public Point3d ViewCamera()")
@cdecl("public Point3d ViewTarget()")
@cdecl("public double ViewLens()")
@cdecl("public byte Sync()")
@cdecl("public byte Disconnect()")
@cdecl("public void Delete(ObjectId id)")
@cdecl("public void DeleteMany(ObjectId[] ids)")
@cdecl("public ObjectId Copy(ObjectId id)")
@cdecl("public Entity Point(Point3d p)")
@cdecl("public Entity PolyLine(Point3d[] pts)")
@cdecl("public Entity Spline(Point3d[] pts)")
@cdecl("public Entity InterpSpline(Point3d[] pts, Vector3d tan0, Vector3d tan1)")
@cdecl("public Entity ClosedPolyLine(Point3d[] pts)")
@cdecl("public Entity ClosedSpline(Point3d[] pts)")
@cdecl("public Entity InterpClosedSpline(Point3d[] pts)")
@cdecl("public Entity Circle(Point3d c, Vector3d n, double r)")
@cdecl("public Point3d CircleCenter(Entity ent)")
@cdecl("public Vector3d CircleNormal(Entity ent)")
@cdecl("public double CircleRadius(Entity ent)")
@cdecl("public Entity Ellipse(Point3d c, Vector3d n, Vector3d majorAxis, double radiusRatio)")
@cdecl("public Entity Arc(Point3d c, Vector3d n, double radius, double startAngle, double endAngle)")
@cdecl("public Entity Text(string str, Point3d corner, Vector3d vx, Vector3d vy, double height)")
@cdecl("public Entity SurfaceFromCurve(Entity curve)")
@cdecl("public Entity SurfaceCircle(Point3d c, Vector3d n, double r)")
@cdecl("public Entity SurfaceEllipse(Point3d c, Vector3d n, Vector3d majorAxis, double radiusRatio)")
@cdecl("public Entity SurfaceArc(Point3d c, Vector3d n, double radius, double startAngle, double endAngle)")
@cdecl("public Entity SurfaceClosedPolyLine(Point3d[] pts)")
@cdecl("public ObjectId[] SurfaceFromCurves(ObjectId[] ids)")
@cdecl("public Entity Sphere(Point3d c, double r)")
@cdecl("public Entity Torus(Point3d c, Vector3d vz, double majorRadius, double minorRadius)")
@cdecl("public Entity ConeFrustum(Point3d bottom, double base_radius, Point3d top, double top_radius)")
@cdecl("public Entity Cylinder(Point3d bottom, double radius, Point3d top)")
@cdecl("public Entity Cone(Point3d bottom, double radius, Point3d top)")
@cdecl("public Entity Box(Point3d corner, Vector3d vx, Vector3d vy, double dx, double dy, double dz)")
@cdecl("public Entity CenteredBox(Point3d corner, Vector3d vx, Vector3d vy, double dx, double dy, double dz)")
@cdecl("public ObjectId IrregularPyramidMesh(Point3d[] pts, Point3d apex)")
@cdecl("public ObjectId IrregularPyramid(Point3d[] pts, Point3d apex)")
@cdecl("public ObjectId IrregularPyramidFrustum(Point3d[] bpts, Point3d[] tpts)")
@cdecl("public Entity MeshFromGrid(int m, int n, Point3d[] pts, bool closedM, bool closedN)")
@cdecl("public Entity SurfaceFromGrid(int m, int n, Point3d[] pts, bool closedM, bool closedN, int level)")
@cdecl("public Entity SolidFromGrid(int m, int n, Point3d[] pts, bool closedM, bool closedN, int level, double thickness)")
@cdecl("public ObjectId Thicken(ObjectId obj, double thickness)")
@cdecl("public double[] CurveDomain(Entity ent)")
@cdecl("public double CurveLength(Entity ent)")
@cdecl("public Frame3d CurveFrameAt(Entity ent, double t)")
@cdecl("public Frame3d CurveFrameAtLength(Entity ent, double l)")
@cdecl("public ObjectId NurbSurfaceFrom(ObjectId id)")
@cdecl("public double[] SurfaceDomain(Entity ent)")
@cdecl("public Frame3d SurfaceFrameAt(Entity ent, double u, double v)")
@cdecl("public ObjectId Extrude(ObjectId profileId, Vector3d dir)")
@cdecl("public ObjectId Sweep(ObjectId pathId, ObjectId profileId, double rotation, double scale)")
@cdecl("public ObjectId Loft(ObjectId[] profilesIds, ObjectId[] guidesIds, bool ruled, bool closed)")
@cdecl("public void Intersect(ObjectId objId0, ObjectId objId1)")
@cdecl("public void Subtract(ObjectId objId0, ObjectId objId1)")
@cdecl("public void Slice(ObjectId id, Point3d p, Vector3d n)")
@cdecl("public ObjectId Revolve(ObjectId profileId, Point3d p, Vector3d n, double startAngle, double amplitude)")
@cdecl("public void Move(ObjectId id, Vector3d v)")
@cdecl("public void Scale(ObjectId id, Point3d p, double s)")
@cdecl("public void Rotate(ObjectId id, Point3d p, Vector3d n, double a)")
@cdecl("public ObjectId Mirror(ObjectId id, Point3d p, Vector3d n, bool copy)")
@cdecl("public Point3d[] GetPoint(string prompt)")
@cdecl("public ObjectId[] GetAllShapes()")
@cdecl("public Point3d[] BoundingBox(ObjectId[] ids)")
@cdecl("public void ZoomExtents()")
@cdecl("public ObjectId CreateLayer(string name)")
@cdecl("public void SetLayerColor(ObjectId id, byte r, byte g, byte b)")
@cdecl("public void SetShapeColor(ObjectId id, byte r, byte g, byte b)")
@cdecl("public ObjectId CurrentLayer()")
@cdecl("public void SetCurrentLayer(ObjectId id)")
@cdecl("public ObjectId ShapeLayer(ObjectId objId)")
@cdecl("public void SetShapeLayer(ObjectId objId, ObjectId layerId)")
@cdecl("public void SetSystemVariableInt(string name, int value)")
@cdecl("public int Render(int width, int height, string path)")
@cdecl("public int Command(string cmd)")
@cdecl("public void DisableUpdate()")
@cdecl("public void EnableUpdate()")
class AutoCADBackend(SocketBasedBackend):
    def new_ref(self, shape):
        return AutoCADRef(shape, self)

autocad = AutoCADBackend('AutoCAD', 11000)


# Revit

@cdecl("public ElementId FindOrCreateLevelAtElevation(Length elevation)")
@cdecl("public ElementId UpperLevel(ElementId currentLevelId, Length addedElevation)")
@cdecl("public Length GetLevelElevation(Level level)")
@cdecl("public ElementId LoadFamily(string fileName)")
@cdecl("public ElementId FamilyElement(ElementId familyId, string[] namesList, Length[] valuesList)")
@cdecl("public ElementId CreatePolygonalFloor(XYZ[] pts, ElementId levelId)")
@cdecl("public ElementId CreatePolygonalRoof(XYZ[] pts, ElementId levelId, ElementId famId)")
@cdecl("public ElementId CreatePathFloor(XYZ[] pts, double[] angles, ElementId levelId)")
@cdecl("public ElementId CreatePathRoof(XYZ[] pts, double[] angles, ElementId levelId, ElementId famId)")
@cdecl("public Element CreateColumn(XYZ location, ElementId baseLevelId, ElementId topLevelId, ElementId famId)")
@cdecl("public Element CreateColumnPoints(XYZ p0, XYZ p1, Level level0, Level level1, ElementId famId)")
@cdecl("public ElementId[] CreateLineWall(XYZ[] pts, ElementId baseLevelId, ElementId topLevelId, ElementId famId)")
@cdecl("public ElementId CreateSplineWall(XYZ[] pts, ElementId baseLevelId, ElementId topLevelId, ElementId famId, bool closed)")
@cdecl("public Element CreateLineRailing(XYZ[] pts, ElementId baseLevelId, ElementId familyId)") 
@cdecl("public Element CreatePolygonRailing(XYZ[] pts, ElementId baseLevelId, ElementId familyId)")
@cdecl("public ElementId CreateBeam(XYZ p0, XYZ p1, double rotationAngle, ElementId famId)")
@cdecl("public Element SurfaceGrid(XYZ[] linearizedMatrix, int n, int m)")
@cdecl("public void MoveElement(ElementId id, XYZ translation)")
@cdecl("public void RotateElement(ElementId id, double angle, XYZ axis0, XYZ axis1)")
@cdecl("public void CreatePolygonalOpening(XYZ[] pts, Element host)")
@cdecl("public void CreatePathOpening(XYZ[] pts, double[] angles, Element host)")
@cdecl("public Element InsertDoor(Length deltaFromStart, Length deltaFromGround, Element host, ElementId familyId)")
@cdecl("public Element InsertWindow(Length deltaFromStart, Length deltaFromGround, Element host, ElementId familyId)")
@cdecl("public Element InsertRailing(Element host, ElementId familyId)")

@cdecl("public void CreateFamily(string familyTemplatesPath, string familyTemplateName, string familyName)")
@cdecl("public void CreateFamilyExtrusionTest(XYZ[] pts, double height)")
@cdecl("public void InsertFamily(string familyName, XYZ p)")

@cdecl("public Material GetMaterial(string name)")
@cdecl("public void ChangeElementMaterial(Element element, Material material)")

@cdecl("public void HighlightElement(ElementId id)")
@cdecl("public ElementId[] GetSelectedElements()")
@cdecl("public bool IsProject()")
@cdecl("public void DeleteAllElements()")
@cdecl("public void SetView(XYZ camera, XYZ target, double focal_length)")
@cdecl("public void EnergyAnalysis()")

class RevitBackend(SocketBasedBackend):
    pass

revit = RevitBackend('Revit', 11001)

################################################################################



# Current backends

current_backends = make_parameter(())

def backend(b):
    current_backends((b,))

def add_backend(b):
    current_backends(current_backends() + (b,))


immediate_mode = make_parameter(True)

shape_ops = {}

def shape_constructor(superclass):
    if hasattr(superclass, 'shape_class'):
        superclass = superclass.shape_class
    def shape_constructor(fn):
        from inspect import getargspec
        from functools import wraps
        argspec = getargspec(fn)
        rArgs = argspec.args
        rDefs = argspec.defaults
        rVarArgs = argspec.varargs
        defaults = dict(zip(rArgs[-len(rDefs):], rDefs) if rDefs else {})
        shape_class = type(fn.__name__, (superclass,),{})
        shape_ops["is_" + fn.__name__] = lambda obj: isinstance(obj, shape_class)
        for arg in rArgs:
            shape_ops[fn.__name__ + "_" + arg] = (lambda arg: lambda obj: getattr(obj, arg))(arg)
        if rVarArgs:
            shape_ops[fn.__name__ + "_" + rVarArgs] = lambda obj: getattr(obj, rVarArgs)
        def new_ref(ref, *args, **kwargs):
            fields = dict(defaults)
            fields.update(dict(zip(rArgs, args)))
            fields.update(kwargs)
            if rVarArgs:
                fields.update({rVarArgs: unvarargs(args)})
            obj = shape_class(ref)
            for key, val in fields.items():
                setattr(obj, key, val)
            return obj
        def actual_fn(*args, **kwargs):
            obj = new_ref(None, *args, **kwargs)
            obj._realizer = lambda obj: fn(*args, **kwargs)
            if immediate_mode(): obj.realize()
            return obj
        new_fn = wraps(fn)(facade_function(actual_fn, argspec))
        new_fn.new_ref = new_ref
        new_fn.shape_class = shape_class
        return new_fn
    return shape_constructor

def facade_function(fn, argspec):
    from inspect import formatargspec
    ns = {'_fn': fn}
    ns.update(globals())
    return eval('lambda %s: _fn%s'%
                (formatargspec(*argspec)[1:-1],
                 formatargspec(*argspec[0:3])),
                ns)


class shape(object):
    def __init__(self):
        self.refs = { }

    def ref_for_backend(self, backend):
        ref = self.refs.get(backend)
        if ref == None:
            ref = backend.new_ref(self)
            self.refs[backend] = ref
        return ref
    
    def realize(self, backends=None):
        backends = backends or current_backends()
        return [self.backend_realize(backend) for backend in backends]

    def backend_realize(self, backend):
        return self.ref_for_backend(backend).realize()

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



"""

class Sphere(Shape):
    def __init__(self, center, radius):
        Shape.__init__(self)
        self.center = center
        self.radius = radius
        if immediate_mode:
            self.realize()
    
    def backend_create(self, backend):
        return backend.Sphere(self.center, self.radius)

        
def sphere(center=u0(), radius=1):
    return Sphere(center, radius)

"""