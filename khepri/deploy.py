import sys
from os import path
import time
from math import *
from functools import *
import shutil
sys.path.append(path.dirname(sys.path[0]))

bundle_name = 'Khepri.bundle'
bundle_dll = path.join('Contents', 'KhepriAutoCAD.dll')
bundle_xml = path.join('PackageContents.xml')


developer_plugin_folder = path.join(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))),
                                    'KhepriPlugins',
                                    'KhepriAutoCAD',
                                    'KhepriAutoCAD')
developer_plugin_dll = path.join(developer_plugin_folder,
                                 'bin',
                                 'x64',
                                 'Debug',
                                 'KhepriAutoCAD.dll')
developer_khepri_bundle = path.join(developer_plugin_folder, bundle_name)


khepri_bundle = path.join(path.dirname(path.abspath(__file__)), bundle_name)
khepri_bundle_dll = path.join(khepri_bundle, bundle_dll)
khepri_bundle_xml = path.join(khepri_bundle, bundle_xml)

def update_plugin(force=False):
    if (force or (not path.exists(khepri_bundle_dll)) or
        path.getmtime(developer_plugin_dll) > path.getmtime(khepri_bundle_dll)):
        print('Updating from developer version')
        shutil.rmtree(khepri_bundle)
        shutil.copytree(developer_khepri_bundle, khepri_bundle)
        shutil.copy(developer_plugin_dll, khepri_bundle_dll)

update_plugin()
