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

bundle_name = 'Khepri.bundle'
bundle_dll = os.path.join('Contents', 'KhepriAutoCAD.dll')
bundle_xml = os.path.join('PackageContents.xml')


developer_plugin_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                       'KhepriPlugins',
                                       'KhepriAutoCAD',
                                       'KhepriAutoCAD')
developer_plugin_dll = os.path.join(developer_plugin_folder,
                                    'bin',
                                    'x64',
                                    'Debug',
                                    'KhepriAutoCAD.dll')
developer_khepri_bundle = os.path.join(developer_plugin_folder, bundle_name)

developer_mode = False
#developer_mode = os.path.exists(developer_plugin_dll)

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
khepri_bundle = os.path.join(os.path.dirname(os.path.abspath(__file__)), bundle_name)
khepri_bundle_dll = os.path.join(khepri_bundle, bundle_dll)
khepri_bundle_xml = os.path.join(khepri_bundle, bundle_xml)

def plugin_folder():
    if os.name == 'nt':
        return os.path.join(os.environ['APPDATA'], 'Autodesk', 'ApplicationPlugins')
    elif os.name == 'posix':
        folder = os.path.join(os.environ['HOME'], 'Autodesk', 'ApplicationAddins')
        os.makedirs(folder, exist_ok=True)
        return folder
    else:
        raise RuntimeError('Unknown operating system:' + os.name)

target = os.path.join(plugin_folder(), bundle_name)
target_dll = os.path.join(target, bundle_dll)
target_xml = os.path.join(target, bundle_xml)

def check_plugin(force=False):
    global checked_plugin
    if force or not checked_plugin:
        if developer_mode:
            update_plugin()
        print('Checking plugin...', end="", flush=True)
        if os.path.exists(target):
            if os.path.exists(khepri_bundle_dll):
                print('updating plugin...', end="", flush=True)
                try:
                    shutil.move(khepri_bundle_dll, target_dll)
                    shutil.move(khepri_bundle_xml, target_xml)
                except PermissionError:
                    print('\n\nError! Please, close AutoCAD and retry.\n')
                    raise
        else:
            print('copying plugin...', end="", flush=True)
            try:
                shutil.copytree(khepri_bundle, target)
            except PermissionError:
                print('\n\nError! Please, close AutoCAD and retry.\n')
                raise
            # remove dll to allow for updates
            os.remove(khepri_bundle_dll)
            print('Please, restart AutoCAD')
        print('done', flush=True)
        checked_plugin = True

def update_plugin(force=False):
    if (force or (not os.path.exists(khepri_bundle_dll)) or
        os.path.getmtime(developer_plugin_dll) > os.path.getmtime(khepri_bundle_dll)):
        print('Updating from developer version')
        shutil.rmtree(khepri_bundle)
        shutil.copytree(developer_khepri_bundle, khepri_bundle)
        shutil.copy(developer_plugin_dll, khepri_bundle_dll)

def remove_plugin():
    shutil.rmtree(target)

#app = AutoCAD()
#doc = app.ActiveDocument
#doc.SendCommand('(command "._NETLOAD" "{0}") '.format(join(path.dirname(path.dirname(path.abspath(__file__))),
#                                                      'Khepri', 'KhepriAutoCAD', 'KhepriAutoCAD', 'bin', 'x64', 'Debug', 'KhepriAutoCAD.dll')).replace("\\","/"))
#db = doc.ModelSpace
#util = doc.Utility

define_backend('AutoCAD', 11000)
check_plugin()

ops = [#('SetDebugMode', [Int], Void),
       #('SetFastMode', [Boolean], Void),
       (Void, 'EnableUpdate'),
       (Void, 'DisableUpdate', ),
       (Int, 'DeleteAll', ),
       (Void, 'Delete', ObjectId),
       (Void, 'DeleteMany', ObjectIdArray),
       (ObjectId, 'Copy', ObjectId),
       (Void, 'View', Point3d, Point3d, Double),
       (Void, 'ViewTop', ),
       (Point3d, 'ViewCamera', ),
       (Point3d, 'ViewTarget', ),
       (Double, 'ViewLens', ),
       (ObjectId, 'Sync', ),
       (ObjectId, 'Point', Point3d),
       (ObjectId, 'PolyLine', Point3dArray),
       (ObjectId, 'InterpSpline', Point3dArray, Vector3d, Vector3d),
       (ObjectId, 'ClosedPolyLine', Point3dArray),
       (ObjectId, 'InterpClosedSpline', Point3dArray),
       (ObjectId, 'Circle', Point3d, Vector3d, Double),
       (Point3d, 'CircleCenter', ObjectId),
       (Vector3d, 'CircleNormal', ObjectId),
       (Double, 'CircleRadius', ObjectId),
       (ObjectId, 'Ellipse', Point3d, Vector3d, Vector3d, Double),
       (ObjectId, 'Arc', Point3d, Vector3d, Double, Double, Double),
       (DoubleArray, 'CurveDomain', ObjectId),
       (Double, 'CurveLength', ObjectId),
       (Frame3d, 'CurveFrameAt', ObjectId, Double),
       (Frame3d, 'CurveFrameAtLength', ObjectId, Double),
       (ObjectId, 'NurbSurfaceFrom', ObjectId),
       (DoubleArray, 'SurfaceDomain', ObjectId),
       (Frame3d, 'SurfaceFrameAt', ObjectId, Double, Double),
       (ObjectId, 'SurfaceFromCurve', ObjectId),
       (ObjectIdArray, 'SurfaceFromCurves', ObjectIdArray),
       (ObjectId, 'SurfaceCircle', Point3d, Vector3d, Double),
       (ObjectId, 'SurfaceEllipse', Point3d, Vector3d, Vector3d, Double),
       (ObjectId, 'SurfaceArc', Point3d, Vector3d, Double, Double, Double),
       (ObjectId, 'SurfaceClosedPolyLine', Point3dArray),
       (ObjectId, 'MeshFromGrid', Int, Int, Point3dArray, Boolean, Boolean),
       (ObjectId, 'SurfaceFromGrid', Int, Int, Point3dArray, Boolean, Boolean, Int),
       (ObjectId, 'SolidFromGrid', Int, Int, Point3dArray, Boolean, Boolean, Int, Double),
       (ObjectId, 'Text', String, Point3d, Vector3d, Vector3d, Double),
       (ObjectId, 'Sphere', Point3d, Double),
       (ObjectId, 'Torus', Point3d, Vector3d, Double, Double),
       (ObjectId, 'Cylinder', Point3d, Double, Point3d),
       (ObjectId, 'ConeFrustum', Point3d, Double, Point3d, Double),
       (ObjectId, 'Cone', Point3d, Double, Point3d),
       (ObjectId, 'Box', Point3d, Vector3d, Vector3d, Double, Double, Double),
       (ObjectId, 'CenteredBox', Point3d, Vector3d, Vector3d, Double, Double, Double),
       (ObjectId, 'IrregularPyramid', Point3dArray, Point3d),
       (ObjectId, 'IrregularPyramidFrustum', Point3dArray, Point3dArray),
       (ObjectId, 'Extrude', ObjectId, Vector3d),
       (ObjectId, 'Sweep', ObjectId, ObjectId, Double, Double),
       (ObjectId, 'Loft', ObjectIdArray, ObjectIdArray, Boolean, Boolean),
       (ObjectId, 'Revolve', ObjectId, Point3d, Vector3d, Double, Double),
       (ObjectId, 'Thicken', ObjectId, Double),
       (Void, 'Subtract', ObjectId, ObjectId),
       (Void, 'Intersect', ObjectId, ObjectId),
       (Void, 'Slice', ObjectId, Point3d, Vector3d),
       (Void, 'Move', ObjectId, Vector3d),
       (Void, 'Scale', ObjectId, Point3d, Double),
       (Void, 'Rotate', ObjectId, Point3d, Vector3d, Double),
       (ObjectId, 'Mirror', ObjectId, Point3d, Vector3d, Boolean),
       (Point3dArray, 'GetPoint', String),
       (ObjectIdArray, 'GetAllShapes',),
       (Point3dArray, 'BoundingBox', ObjectIdArray),
       (Void, 'ZoomExtents', ),
       (ObjectId, 'CreateLayer', String),
       (Void, 'SetLayerColor', ObjectId, Byte, Byte, Byte),
       (ObjectId, 'CurrentLayer', ),
       (Void, 'SetCurrentLayer', ObjectId),
       (ObjectId, 'ShapeLayer', ObjectId),
       (Void, 'SetShapeLayer', ObjectId, ObjectId),
       (Void, 'SetSystemVariableInt', String, Int),
       (Int, 'Render', Int, Int, String),
       ]

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
