import socket
import struct
import sys
import sys
from os import path
import time
from math import *
from functools import *
import shutil
sys.path.append(path.dirname(sys.path[0]))
from khepri.coords import *

#Python provides sendall but not recvall
def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

class Packer(object):
    def __init__(self, fmt):
        self.struct = struct.Struct(fmt)
    def write(self, conn, *args):
        conn.sendall(self.struct.pack(*args))
    def read(self, conn):
        return self.struct.unpack(recvall(conn, self.struct.size))[0]

class _Byte(Packer):
    def __init__(self):
        super().__init__('1B')
        
Byte = _Byte()

class _Void(Packer):
    def __init__(self):
        super().__init__('1B')
    def read(self, conn):
        return super().read(conn) == 0
    def write(self, conn, b):
        raise RuntimeException('Void should not be serialized!')

Void = _Void()

class _Boolean(Packer):
    def __init__(self):
        super().__init__('1B')
    def read(self, conn):
        return super().read(conn) == 1
    def write(self, conn, b):
        super().write(conn, 1 if b else 0)
        
Boolean = _Boolean()

class _Double(Packer):
    def __init__(self):
        super().__init__('d')
    def read(self, conn):
        d = super().read(conn)
        if isnan(d):
            raise RuntimeError(String.read(conn))
        else:
            return d

Double = _Double()

class _DoubleArray(object):
    def write(self, conn, ds):
        Int.write(conn, len(ds))
        for d in ds:
            Double.write(conn, d)
    def read(self, conn):
        n = Int.read(conn)
        if n == -1:
            raise RuntimeError(String.read(conn))
        else:
            ds = []
            for i in range(n):
                ds.append(Double.read(conn))
            return ds    

DoubleArray = _DoubleArray()

class _Int(Packer):
    def __init__(self):
        super().__init__('i')

Int = _Int()

class _String(object):
    def write(self, conn, str):
        size = len(str)
        array = bytearray()
        while True:
            byte = size & 0x7f
            size >>= 7
            if size:
                array.append(byte | 0x80)
            else:
                array.append(byte)
                break
        conn.send(array)
        conn.sendall(str.encode('utf-8'))
    def read(self, conn):
        size = 0
        shift = 0
        byte = 0x80
        while byte & 0x80:
            try:
                byte = ord(conn.recv(1))
            except TypeError:
                raise IOError('Buffer empty')
            size |= (byte & 0x7f) << shift
            shift += 7
        return recvall(conn, size).decode('utf-8')

String = _String()

class _Point3d(Packer):
    def __init__(self):
        super().__init__('3d')
    def write(self, conn, p):
        p = loc_in_world(p)
        conn.sendall(self.struct.pack(p.x, p.y, p.z))
    def read(self, conn):
        return xyz(*(self.struct.unpack(recvall(conn, self.struct.size))),
                   world_cs)

Point3d = _Point3d()


class _Vector3d(Packer):
    def __init__(self):
        super().__init__('3d')
    def write(self, conn, p):
        p = loc_in_world(p)
        conn.sendall(self.struct.pack(p.x, p.y, p.z))
    def read(self, conn):
        return vxyz(*(self.struct.unpack(recvall(conn, self.struct.size))),
                    world_cs)

Vector3d = _Vector3d()


class _Point3dArray(object):
    def write(self, conn, ps):
        Int.write(conn, len(ps))
        for p in ps:
            Point3d.write(conn, p)
    def read(self, conn):
        n = Int.read(conn)
        if n == -1:
            raise RuntimeError(String.read(conn))
        else:
            pts = []
            for i in range(n):
                pts.append(Point3d.read(conn))
            return pts    

Point3dArray = _Point3dArray()

class _Frame3d(object):
    def write(self, conn, ps):
        raise Error("Bum")
    def read(self, conn):
        return u0(cs_from_o_vx_vy_vz(Point3d.read(conn),
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

class _ObjectId(Packer):
    def __init__(self):
        super().__init__('1i')        
    def read(self, conn):
        if fast_mode:
            return incr_id_counter()
        else:
            id = super().read(conn)
            if id == -1:
                raise RuntimeError(String.read(conn))
            else:
                return id

ObjectId = _ObjectId()
Entity = _ObjectId()

class _ObjectIdArray(object):
    def write(self, conn, ids):
        Int.write(conn, len(ids))
        for id in ids:
            ObjectId.write(conn, id)
    def read(self, conn):
        n = Int.read(conn)
        if n == -1:
            raise RuntimeError(String.read(conn))
        else:
            ids = []
            for i in range(n):
                ids.append(ObjectId.read(conn))
            return ids

ObjectIdArray = _ObjectIdArray()

to_feet = 3.28084

class _Length(object):
    def write(self, conn, l):
        Double.write(conn, l * to_feet)
    def read(self, conn):
        return Double.read(conn) / to_feet
    
Length = _Length()

ElementId = _ObjectId()


conn = False
id_counter = -1

def current_connection():
    global conn
    global id_counter
    if not conn:
        conn = create_connection()
        id_counter = -1
    return conn

backend_port = 0
backend_name = ""

def define_backend(name, port):
    global backend_port
    global backend_name
    backend_port = port
    backend_name = name

def create_connection():
    for i in range(10):
        try:
            return socket.create_connection(("127.0.0.1", backend_port))
        except (ConnectionRefusedError, socket.timeout):
            print('Please, start/restart', backend_name)
            time.sleep(8)
            if i == 9:
                raise

#debug_mode = False
debug_mode = False

def def_op(name, idx, arg_types, ret_type):
    op_code = idx
    def pack(*args):
        assert len(args) == len(arg_types), "%r: %r does not match %r" % (name, args, tuple(type(t).__name__ for t in arg_types))
        conn = current_connection()
        Int.write(conn, op_code);
        if debug_mode:
            print("{0}{1}".format(name, args), flush=True)
        for arg_type, arg in zip(arg_types, args):
            arg_type.write(conn, arg)
        return ret_type.read(conn)
    return pack

def from_python_to_csharp(name):
    return "".join([s.capitalize() for s in name.split('_')])

def disconnect():
    global conn
    if conn:
        Int.write(conn, OpCode.disconnect)
        Int.read(conn)
        conn.close()
        conn = False

def request_operation(name):
    conn = current_connection()
    Int.write(conn, 0)
    String.write(conn, name)
    op = Int.read(conn)
    if op == -1:
        raise NameError(name + ' is not available')
    else:
        return op

def def_remote_operation(name, idx, arg_types, ret_type):
    #print(name, idx)
    globals()[name] = def_op(name, idx, arg_types, ret_type)
    

def pack(name, *args):
    conn = current_connection()
    op_info = ops[name]
    op_code = op_info[0]
    op_packers = op_info[1]
    conn.send(op_code);
    for packer, arg in zip(op_packers, args):
        conn.sendall(packer.pack(arg))
