
from math import pi

def format_number(n, accuracy=6):
    """Formats a number in a friendly manner (removes trailing zeros and unneccesary point."""
    
    fs = "%."+str(accuracy)+"f"
    str_n = fs%float(n)
    if '.' in str_n:
        str_n = str_n.rstrip('0').rstrip('.')
    if str_n == "-0":
        str_n = "0"
    #str_n = str_n.replace("-0", "0")
    return str_n
    

def lerp(a, b, i):
    """Linear enterpolate from a to b."""
    return a+(b-a)*i


def division(a, b, n, include_last=True):
    ni = int(n)
    assert(ni == n)
    d = b - a
    for i in range(ni):
        yield a + float(i*d)/n
    if include_last:
        yield b

def map_division(f, a, b, n, include_last=True, *rest):
    if len(rest) == 0:
        return list([f(x) for x in division(a, b, n, include_last)])
    elif len(rest) == 2:
        return [[f(x, y) for y in division(include_last, *rest)]
                for x in division(a, b, n, True)]
    elif 3 <= len(rest) <= 4:
        return [[f(x, y) for y in division(*rest)]
                for x in division(a, b, n, include_last)]
    else:
        raise ValueError("Wrong number of arguments")

class dynamic_scope(object):
    def __init__(self, **dict):
        self.dict = dict
        self.old_dict = {}

    def __enter__(self):
        for k, v in self.dict.items():
            self.old_dict[k] = globals()[k]
        globals().update(self.dict)
        return self.dict

    def __exit__(self, type, value, traceback):
        globals().update(self.old_dict)

"""
foo = 1
bar = 5
print "Out", foo
with dynamic_scope(foo=2, bar=3):
    print "In", foo, bar
    with dynamic_scope(foo=3, bar=4):
        print "In In", foo, bar
    print "In", foo, bar
print "Out", foo, bar
"""
# HACK This must be finished

class changed_parameter(object):
    def __init__(self, p, old_val):
        self.p = p
        self.old_val = old_val

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.p(self.old_val)

def make_parameter(init):
    box = [init]
    def get_or_update(val=None):
        if val == None:
            return box[0]
        else:
            old_val = box[0]
            box[0] = val
            #To allow its use with with (got the joke?)
            return changed_parameter(get_or_update, old_val)
    return get_or_update

class parameter(object):
    def __init__(self, p, val):
        self.p = p
        self.val = val

    def __enter__(self):
        self.old_val = self.p()
        self.p(self.val)
        return self

    def __exit__(self, *args):
        self.p(self.old_val)

"""
foo = make_parameter(1)

print foo()
foo(2)
print foo()

with parameter(foo, 3):
    print foo()
    foo(4)
    print foo()
    with parameter(foo, 5):
        print foo()
    print foo()
print foo()
"""
import numbers
def is_number(obj):
    return isinstance(obj, numbers.Number)

#random numbers

def next_random(previous_random):
    test = 16807*(previous_random % 127773) - 2836*(previous_random // 127773)
    if test > 0:
        if test > 2147483647:
            return test - 2147483647
        else:
            return test
    else:
        return test + 2147483647

random_seed = 12345

def set_random_seed(v):
    global random_seed
    random_seed = v

def new_random():
    global random_seed
    random_seed = next_random(random_seed)
    return random_seed

def random(x):
    if isinstance(x, int):
        return new_random()%x
    else:
        return x*(new_random()/2147483647.0)

def random_range(x0, x1):
    if x0 == x1:
        return x0
    else:
        return x0 + random(x1 - x0)
        
        
        
        
def maximize_combination(op, rs):
    def combine(r0, rs):
        if rs == []:
            return [r0]
        else:
            r1, rs = rs[0], rs[1:]
            r = op(r0, r1)
            if r:
                return [r] + rs
            else:
                return [r1] + combine(r0, rs)

    if rs == []:
        return []
    elif rs[1:] == []:
        return rs
    else:
        def loop(rs, combs, n):
            if rs == []:
                if n == len(combs):
                    return combs
                else:
                    return loop(combs, [], len(combs))
            else:
                r1, rs = rs[0], rs[1:]
                return loop(rs, combine(r1, combs), n)

        return loop(rs([], len(rs)))
        
        
        

def is_singleton(arr):
    return len(arr) == 1

def singleton(arr, err="Expecting just one result but got {0}"):
    if arr:
        if len(arr) == 1:
            return arr[0]
        else:
            raise RuntimeError(err.format(len(arr)))
    else:
        raise RuntimeError("Expecting a sized object but got {0}".format(arr))
    
def tuplify(v, vs):
    if isinstance(v, tuple):
        v0s = v
    elif isinstance(v, list):
        v0s = tuple(v)
    else:
        v0s = (v,)
    return v0s + vs if vs else v0s

def unvarargs(vs):
    if len(vs) == 0:
        return ()
    elif len(vs) == 1 and isinstance(vs[0], (tuple, list)):
        return tuple(vs[0])
    else:
        return vs

old_range = range

def frange(start=0, stop=None, step=1):
    def fxrange():
        x = start
        if step > 0:
            while x <= stop:
                yield x
                x += step
        else:
            while x >= stop:
                yield x
                x += step

    if stop == None:
        stop = start
        start = 0
    if step == 0:
        raise ValueError("Step cannot be zero")
    if isinstance(start, int) and isinstance(stop, int) and isinstance(step, int):
        return old_range(start, stop, step)
    else:
        return [x for x in fxrange()]

range = frange

def and_delete(v, *shapes):
    for s in shapes:
        s.delete()
    return v

def shapes_refs(ss):
    return [r for s in ss for r in s.refs()]

import os
import os.path

#There is a render directory
render_dir = make_parameter(os.path.expanduser('~'))
#with a user-specific subdirectory
render_user_dir = make_parameter('')
#with a backend-specific subdirectory
render_backend_dir = make_parameter('')
#and with subdirectories for static images, movies, etc
render_kind_dir = make_parameter('Render')
#and with subdirectories for white, black, and colored renders
render_color_dir = make_parameter('')
#containing files with different extensions
render_ext = make_parameter('png')

def render_pathname(name):
    return os.path.join(render_dir(),
                        render_user_dir(),
                        render_backend_dir(),
                        render_kind_dir(),
                        render_color_dir(),
                        "{0}.{1}".format(name, render_ext()))

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
    return f

def ensure_file_deleted(f):
    if os.path.exists(f):
        os.remove(f)
    return f


render_width = make_parameter(1024)
render_height = make_parameter(768)

def render_size(width, height):
    render_width(width)
    render_height(height)

is_film_active = make_parameter(False)
film_filename = make_parameter('')
film_frame = make_parameter(0)

def start_film(name):
    is_film_active(True)
    film_filename(name)
    film_frame(0)
    
def frame_filename(name, i):
    return name + '-frame-{:03d}'.format(i)
