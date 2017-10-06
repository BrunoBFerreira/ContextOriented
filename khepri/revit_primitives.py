import socket
import struct
import sys
import sys
from os import path
import time
from math import *
from functools import *
import shutil
import wincopy
sys.path.append(path.dirname(sys.path[0]))
from khepri.coords import *
from khepri.primitives import *

plugin = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      'Khepri',
                      'KhepriAutoCAD',
                      'KhepriAutoCAD',
                      'bin',
                      'x64',
                      'Debug',
                      'KhepriAutoCAD.dll')

developer_mode = os.path.exists(plugin)

#    Installation
checked_plugin = True
#checked_plugin = False

#One of the methods is to inject a load command in acad.lsp
#acad_lsp = os.path.join(os.path.expanduser("~"), "acad.lsp")
#def set_acad_lsp():
    #def contains_netload(path):
        #if os.path.exists(path):
            #with open(path, "r") as f:
                #if 'KhepriAutoCAD.dll' in f.read():
                    #return True
        #return False
    #global checked_plugin
    #if not checked_plugin:
        #if not contains_netload(acad_lsp):
            #with open(acad_lsp, "a") as acad:
                #acad.write('(command "._NETLOAD" "{0}")\n'.format(plugin.replace("\\","/")))
        #moved_plugin = True

#The previous approach isn't working.
#The next one is to put the bundle in AppData
bundle_name = 'Khepri.bundle'
bundle_dll = os.path.join('Contents', 'KhepriAutoCAD.dll')
bundle_xml = os.path.join('PackageContents.xml')
bundle_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), bundle_name)
bundle_dll_path = os.path.join(bundle_path, bundle_dll)
bundle_xml_path = os.path.join(bundle_path, bundle_xml)

def plugin_folder():
    if os.name == 'nt':
        return os.path.join(os.environ['APPDATA'], 'Autodesk', 'ApplicationPlugins')
    elif os.name == 'posix':
        folder = os.path.join(os.environ['HOME'], 'Autodesk', 'ApplicationAddins')
        os.makedirs(folder, exist_ok=True)
        return folder
    else:
        raise RuntimeError('Unknown operating system:' + os.name)

target_path = os.path.join(plugin_folder(), bundle_name)
target_dll_path = os.path.join(target_path, bundle_dll)
target_xml_path = os.path.join(target_path, bundle_xml)

def check_plugin(force=False):
    global checked_plugin
    if force or not checked_plugin:
        if developer_mode:
            update_plugin()
        print('Checking plugin...', end="", flush=True)
        if os.path.exists(target_path):
            if os.path.exists(bundle_dll_path):
                print('updating plugin...', end="", flush=True)
                try:
                    shutil.move(bundle_dll_path, target_dll_path)
                    shutil.move(bundle_xml_path, target_xml_path)
                except PermissionError:
                    print('\n\nError! Please, close AutoCAD and retry.\n')
                    raise
        else:
            print('copying plugin...', end="", flush=True)
            try:
                shutil.copytree(bundle_path, target_path)
            except PermissionError:
                print('\n\nError! Please, close AutoCAD and retry.\n')
                raise
            # remove dll to allow for updates
            os.remove(bundle_dll_path)
            print('Please, restart AutoCAD')
        print('done', flush=True)
        checked_plugin = True

def update_plugin(force=False):
    if (force or (not os.path.exists(target_dll_path)) or
        os.path.getmtime(plugin) > os.path.getmtime(target_dll_path)):
        shutil.copy(plugin, bundle_dll_path)

def remove_plugin():
    shutil.rmtree(target_path)

#app = AutoCAD()
#doc = app.ActiveDocument
#doc.SendCommand('(command "._NETLOAD" "{0}") '.format(join(path.dirname(path.dirname(path.abspath(__file__))),
#                                                      'Khepri', 'KhepriAutoCAD', 'KhepriAutoCAD', 'bin', 'x64', 'Debug', 'KhepriAutoCAD.dll')).replace("\\","/"))
#db = doc.ModelSpace
#util = doc.Utility

define_backend('Revit', 11001)
check_plugin()

class _XYZ(Packer):
    def __init__(self):
        super().__init__('3d')
    def write(self, conn, p):
        p = loc_in_world(p)
        conn.sendall(self.struct.pack(p.x, p.y, p.z))
    def read(self, conn):
        return xyz(*(self.struct.unpack(recvall(conn, self.struct.size))),
                   world_cs)

XYZ = _XYZ()

class _XYZArray(object):
    def write(self, conn, ps):
        Int.write(conn, len(ps))
        for p in ps:
            XYZ.write(conn, p)
    def read(self, conn):
        n = Int.read(conn)
        if n == -1:
            raise RuntimeError(String.read(conn))
        else:
            pts = []
            for i in range(n):
                pts.append(XYZ.read(conn))
            return pts    

XYZArray = _XYZArray()

class _Vector3d(Packer):
    def __init__(self):
        super().__init__('3d')
    def write(self, conn, v):
        v = vec_in_world(v)
        conn.sendall(self.struct.pack(v.x, v.y, v.z))
    def read(self, conn):
        return vxyz(*(self.struct.unpack(recvall(conn, self.struct.size))),
                    world_cs)

Vector3d = _Vector3d()

class _Frame3d(object):
    def write(self, conn, p):
        XYZ.write(conn, p)
        Vector3d.write(conn, vx(1, p.cs))
        Vector3d.write(conn, vy(1, p.cs))
        Vector3d.write(conn, vz(1, p.cs))
    def read(self, conn):
        return u0(cs_from_o_vx_vy_vz(XYZ.read(conn),
                                     Vector3d.read(conn),
                                     Vector3d.read(conn),
                                     Vector3d.read(conn)))

Frame3d = _Frame3d()

id_counter = -1
def incr_id_counter():
    global id_counter
    id_counter += 1
    return id_counter

fast_mode = False

class _ElementId(Packer):
    def __init__(self):
        super().__init__('1i')        
    def read(self, conn):
        if fast_mode:
            return incr_id_counter()
        else:
            id = super().read(conn)[0]
            if id == -1:
                raise RuntimeError(String.read(conn))
            else:
                return id

ElementId = _ElementId()
Element = _ElementId()

class _ElementIdArray(object):
    def write(self, conn, ids):
        Int.write(conn, len(ids))
        for id in ids:
            ElementId.write(conn, id)
    def read(self, conn):
        n = Int.read(conn)
        if n == -1:
            raise RuntimeError(String.read(conn))
        else:
            ids = []
            for i in range(n):
                ids.append(ObjectId.read(conn))
            return ids

ElementIdArray = _ElementIdArray()
ElementArray = _ElementIdArray()


def def_remote_operation(name, idx, arg_types, ret_type):
    #print(name, idx)
    globals()[name] = def_op(name, idx, arg_types, ret_type)
    
ops = [#(Void, 'SetDebugMode', Int),
       #(Void, 'SetFastMode', Boolean),
       (ElementId, 'FindOrCreateLevelAtElevation', Double),
       (ElementId, 'UpperLevel', ElementId, Double),
       (ElementId, 'CreatePolygonalFloor', XYZArray, ElementId),
       (ElementId, 'CreatePolygonalRoof', XYZArray, ElementId, ElementId),
       (ElementId, 'CreateColumn', XYZ, ElementId, ElementId, ElementId, Double),
       (ElementId, 'CreateBeam', XYZ, XYZ, ElementId),
       ]
'''    ('EnableUpdate', [], Void),
       ('DisableUpdate', [], Void),
       ('DeleteAll', [], Int),
       ('Delete', [ObjectId], Void),
       ('DeleteMany', [ObjectIdArray], Void),
       ('Copy', [ObjectId], ObjectId),
       ('View', [XYZ, XYZ, Double], Void),
       ('ViewTop', [], Void),
       ('ViewCamera', [], XYZ),
       ('ViewTarget', [], XYZ),
       ('ViewLens', [], Double),
       ('Sync', [], ObjectId), # FIXME
       ('Point', [XYZ], ObjectId),
       ('PolyLine', [XYZArray], ObjectId),
       ('InterpSpline', [XYZArray, Vector3d, Vector3d], ObjectId),
       ('ClosedPolyLine', [XYZArray], ObjectId),
       ('InterpClosedSpline', [XYZArray], ObjectId),
       ('Circle', [XYZ, Vector3d, Double], ObjectId),
       ('CircleCenter', [ObjectId], XYZ),
       ('CircleNormal', [ObjectId], Vector3d),
       ('CircleRadius', [ObjectId], Double),
       ('Ellipse', [XYZ, Vector3d, Vector3d, Double], ObjectId),
       ('Arc', [XYZ, Vector3d, Double, Double, Double], ObjectId),
       ('CurveDomain', [ObjectId], DoubleArray),
       ('CurveLength', [ObjectId], Double),
       ('CurveFrameAt', [ObjectId, Double], Frame3d),
       ('CurveFrameAtLength', [ObjectId, Double], Frame3d),
       ('NurbSurfaceFrom', [ObjectId], ObjectId),
       ('SurfaceDomain', [ObjectId], DoubleArray),
       ('SurfaceFrameAt', [ObjectId, Double, Double], Frame3d),
       ('SurfaceFromCurve', [ObjectId], ObjectId),
       ('SurfaceFromCurves', [ObjectIdArray], ObjectIdArray),
       ('SurfaceCircle', [XYZ, Vector3d, Double], ObjectId),
       ('SurfaceEllipse', [XYZ, Vector3d, Vector3d, Double], ObjectId),
       ('SurfaceArc', [XYZ, Vector3d, Double, Double, Double], ObjectId),
       ('SurfaceClosedPolyLine', [XYZArray], ObjectId),
       ('MeshFromGrid', [Int, Int, XYZArray, Boolean, Boolean], ObjectId),
       ('SurfaceFromGrid', [Int, Int, XYZArray, Boolean, Boolean, Int], ObjectId),
       ('SolidFromGrid', [Int, Int, XYZArray, Boolean, Boolean, Int, Double], ObjectId),
       ('Text', [String, XYZ, Vector3d, Vector3d, Double], ObjectId),
       ('Sphere', [XYZ, Double], ObjectId),
       ('Torus', [XYZ, Vector3d, Double, Double], ObjectId),
       ('Cylinder', [XYZ, Double, XYZ], ObjectId),
       ('ConeFrustum', [XYZ, Double, XYZ, Double], ObjectId),
       ('Cone', [XYZ, Double, XYZ], ObjectId),
       ('Box', [XYZ, Vector3d, Vector3d, Double, Double, Double], ObjectId),
       ('CenteredBox', [XYZ, Vector3d, Vector3d, Double, Double, Double], ObjectId),
       ('IrregularPyramid', [XYZArray, XYZ], ObjectId),
       ('IrregularPyramidFrustum', [XYZArray, XYZArray], ObjectId),
       ('Extrude', [ObjectId, Vector3d], ObjectId),
       ('Sweep', [ObjectId, ObjectId, Double, Double], ObjectId),
       ('Loft', [ObjectIdArray, ObjectIdArray, Boolean, Boolean], ObjectId),
       ('Revolve', [ObjectId, XYZ, Vector3d, Double, Double], ObjectId),
       ('Thicken', [ObjectId, Double], ObjectId),
       ('Subtract', [ObjectId, ObjectId], ObjectId),
       ('Intersect', [ObjectId, ObjectId], ObjectId),
       ('Slice', [ObjectId, XYZ, Vector3d], ObjectId),
       ('Move', [ObjectId, Vector3d], Void),
       ('Scale', [ObjectId, XYZ, Double], Void),
       ('Rotate', [ObjectId, XYZ, Vector3d, Double], Void),
       ('Mirror', [ObjectId, XYZ, Vector3d, Boolean], ObjectId),
       ('GetPoint', [String], XYZArray),
       ('ZoomExtents', [], Void),
       ('CreateLayer', [String], String),
       ('CurrentLayer', [], String),
       ('SetCurrentLayer', [String], Void),
       ('SetSystemVariableInt', [String, Int], Void),
       ('Render', [Int, Int, String], Int),
       ]
       '''

for ret_type, name, *arg_types in ops:
    globals()[name] = def_op(name, request_operation(name), arg_types, ret_type)



def set_fast_mode(mode):
    global fast_mode
    SetFastMode(mode)
    fast_mode = mode

def set_debug_mode(mode):
    global debug_mode
    SetDebugMode(mode)
    debug_mode = mode
    
'''if False: #developer_mode:
    set_fast_mode(True)
    set_debug_mode(1)
else:
    set_fast_mode(False)
    set_debug_mode(0)
'''

def pack(name, *args):
    conn = current_connection()
    op_info = ops[name]
    op_code = op_info[0]
    op_packers = op_info[1]
    conn.send(op_code);
    for packer, arg in zip(op_packers, args):
        conn.sendall(packer.pack(arg))
