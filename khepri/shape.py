from inspect import getargspec
from .util import *
from .coords import *

immediate_mode = make_parameter(True)

_shape_counter = -1

def incr_shape_counter():
    global _shape_counter
    _shape_counter += 1
    return _shape_counter

class Realizable(type):
    def __call__(self, *args, **kwargs):
        obj = super(Realizable, self).__call__()
        argspec = getargspec(obj.create)
        rArgs = argspec.args
        rDefs = argspec.defaults
        rVarArgs = argspec.varargs
        defaults = dict(zip(rArgs[-len(rDefs):], rDefs) if rDefs else {})
        defaults.update(dict(zip(rArgs[1:], args))) # jump over self
        defaults.update(kwargs)
        defaults.update
        obj._id = incr_shape_counter()
        obj._created = 0
        obj._deleted = 0
        obj._realizer = lambda obj: obj.create.__call__(*args, **kwargs)
        obj._ref = None
        for key, val in defaults.items():
            setattr(obj, key, val)
        if immediate_mode(): obj.realize()
        return obj

#To be compatible with Python 2 and 3
class base_shape(object): #Realizable('Realizable', (object,), {})):
#class baseShape(object):
#    __metaclass__ = Realizable
    
#    def create(self, *args, **kwargs):
#        raise RuntimeException("Missing create method in {0}".format(self))

#    def destroy(self):
#        raise RuntimeException("Missing destroy method in {0}".format(self))

    def __init__(self, ref):
        self._id = incr_shape_counter()
        self._created = 0 if ref is None else 1
        self._deleted = 0
        self._ref = ref

    def create():
        return None

    def validate(self, ref):
        return ref

    def realized(self):
        return self._created == self._deleted + 1

    def realize(self):
        if self._created == self._deleted: # not realized
            self._ref = self.validate(self._realizer(self))
            self._created += 1
            return self._ref
        elif self._created == self._deleted + 1:
            if self._ref:
                return self._ref
            else:
                raise RuntimeException("The object was realized but does not have a reference")
        else:
            raise RuntimeException("Inconsistent creation {0} and deletion {0}".format(self.created, self.deleted))
 
    def mark_deleted(self):
        if self._created == self._deleted + 1:
            self._ref = None
            self._deleted += 1
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
    
    def __repr__(self):
        return "<{0}{1} {2}>".format("" if self.realized() else "virtual ",
                                     self.__class__.__name__,
                                     self._id)


# Different approach, using decorators and hidden classes

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

#Khepri suports native references, union references, and subtraction references
#We also need empty references and universal references, used in the empty shape
#and the universal shape

class _empty_ref(object):
    def contains(self, r):
        return is_empty_ref(r)

    def intersect_1_1(r0, r1):
        return r0

    def intersect_1_1_with_native(r0, r1, s):
        return r0

_the_empty_ref = _empty_ref()

def empty_ref():
    return _the_empty_ref

def is_empty_ref(r):
    return r is _the_empty_ref

###################

class _universal_ref(object):
    def contains(self, r):
        return is_universal_ref(r)

    def intersect_1_1(r0, r1):
        return r1

    def intersect_1_1_with_native(r0, r1, s):
        return r1


_the_universal_ref = _universal_ref()

def universal_ref():
    return _universal_ref()

def is_universal_ref(r):
    return r is _the_universal_ref

###################
class native_ref(object):
    def __init__(self, ref):
        assert not isinstance(ref, (_empty_ref, _universal_ref, native_ref, multiple_ref)), "Not an acceptable ref {0} in {1}".format(r, self)
        self._ref = ref

    def do(self, f):
        f(self._ref)

    def map(self, f):
        return f(self._ref)

    def satisfy(self, f):
        return f(self._ref)

    def contains(self, r):
        assert isinstance(r, 
            (_empty_ref, _universal_ref, native_ref, multiple_ref)),"Not an acceptable ref {0} in {1}".format(r, self)
        return r is self or (isinstance(r, native_ref) and r._ref is self._ref)

    def ref(self):
        return self._ref
    
    def refs(self):
        return (self._ref,)
        
    def copy_ref(self, s):
        return native_ref(s.copy_ref(self._ref))
        
    def intersect_1_1(r0, r1, s):
        return r1.intersect_1_1_with_native(r0, s)
        
    def intersect_1_1_with_native(r1, r0, s):
        return s.intersect_ref(r0._ref, r1._ref)
        
    def subtract_1_1(r0, r1, s):
        return r1.subtract_1_1_with_native(r0, s)

    def subtract_1_1_with_native(r1, r0, s):
        return s.subtract_ref(r0._ref, r1._ref)

    def slice(r, p, n, s):
        return s.slice_ref(r._ref, p, n)


class multiple_ref(object):
    def __init__(self, refs):
        refs = tuple(refs)
        assert len(refs) > 0, "Empty refs"
        for r in refs:
            assert isinstance(r, 
            (native_ref, multiple_ref)),"Not an acceptable ref {0} in {1}".format(r, refs)
        self._refs = refs
    
    def do(self, f):
        for r in self._refs:
            r.do(f)

    def map(self, f):
        return self.__class__([r.map(f) for r in self._refs])

    def satisfy(self, f):
        return all(f, self._refs)

    def contains(self, r):
        assert isinstance(r, 
            (native_ref, multiple_ref)),"Not an acceptable ref {0} in {1}".format(r, self)
        if r is self:
            return True
        else:
            for r1 in self._refs:
                if r1.contains(r):
                    return True
            return False

    def ref(self):
        if len(self._refs) == 1:
            return self._refs[0].ref()
        else:
            raise RuntimeError("The composed ref has more than one member")

    def refs(self):
        return tuple([r for subref in self._refs for r in subref.refs()])

class union_ref(multiple_ref):
    def intersect_1_1(r0, r1, s):
        return intersect_many_1(r0._refs, r1, s)

    def intersect_1_1_with_native(r1, r0, s):
        return intersect_1_many(r0, r1._refs, s)
    
    def subtract_1_1(r0, r1, s):
        return subtract_union_1(r0._refs, r1, s)

    def subtract_1_1_with_native(r1, r0, s):
        return subtract_1_many(r0, r1._refs, s)

    def slice(r, p, n, s):
        return union_ref(filter(lambda r: not is_empty_ref(r),
                         [r0.slice(p, n, s) for r0 in r._refs]))

    def copy_ref(self, s):
        return union_ref([sub.copy_ref(s) for sub in self._refs])

def is_union_ref(r):
    assert(isinstance(r, (native_ref, union_ref, subtraction_ref)))
    return isinstance(r, union_ref)

class subtraction_ref(multiple_ref):
    def intersect_1_1(r0, r1, s):
        return subtract_refs(r0._refs[0].intersect_1_1(r1, s), r0._refs[1:], s)

    def intersect_1_1_with_native(r1, r0, s):
        return subtract_refs(r0.intersect_1_1(r1._refs[0], s), r1._refs[1:], s)

    def subtract_1_1(r0, r1, s):
        return subtract_subtraction_1(r0._refs, r1, s)

    def slice(r, p, n, s):
        return subtract_refs(r._refs[0].slice(p, n, s), r._refs[1:], s)

    def copy_ref(self, s):
        return subtraction_ref([sub.copy_ref(s) for sub in self._refs])

def is_subtraction_ref(r):
    assert(isinstance(r, (native_ref, union_ref, subtraction_ref)))
    return isinstance(r, subtraction_ref)

def intersect_refs(rs, s):
    if len(rs) == 1:
        return rs[0]
    else:
        return rs[0].intersect_1_1(intersect_refs(rs[1:], s), s)

def intersect_1_many(r, rs, s):
    if rs == []:
        return empty_ref()
    else:
        return single_ref_or_empty_ref_or_union(
            list(map(lambda r0, r1: r0.intersect_1_1(r1, s),
                     copy_n_ref(r, len(rs), s),
                     rs)))

def intersect_many_1(rs, r, s):
    if rs == []:
        return empty_ref()
    else:
        return single_ref_or_empty_ref_or_union(
            list(map(lambda r0, r1: r0.intersect_1_1(r1, s), 
                     rs,
                     copy_n_ref(r, len(rs), s))))

def subtract_1_many(r, rs, s):
    if rs == []:
        return r
    else:
        for r0 in rs:
            r = r.subtract_1_1(r0, s)
            if is_empty_ref(r):
                return r
        return r

def subtract_union_1(rs, r, s):
    rs = [r0.subtract_1_1(r1, s) for r0, r1 in zip(rs, copy_n_ref(r, len(rs), s))]
    return union_ref(filter(lambda r: not is_empty_ref(r),rs))

def subtract_subtraction_1(rs, r, s):
    res = rs[0].subtract_1_1(r, s)
    if isinstance(res, subtraction_ref):
        return subtraction_ref(rs + [r])
    else:
        return subtract_refs(res, rs[1:], s)

def subtract_refs(r, rs, self):
    if len(rs) == 0:
        return r
    else:
        unions, rs = partition(rs, is_union_ref)
        subtractions, rs = partition(rs, is_subtraction_ref)
        rs = rs + [r0 for union in unions for r0 in union._refs] #avoid direct reference
        assert(len(subtractions) == 0)
        return r.subtract_1_1(native_ref_or_union(rs), self)

def copy_n_ref(r, n, s):
    return [r.copy_ref(s) for i in range(n-1)]+[r]

def single_ref_or_empty_ref_or_union(rs):
    if len(rs) == 0:
        return empty_ref()
    elif len(rs) == 1:
        return rs[0]
    else:
        return union_ref([r for r in rs])

def single_ref_or_union(rs):
    if len(rs) == 0:
        raise RuntimeError("Must have at least one reference")
    elif len(rs) == 1:
        return native_ref(rs[0])
    else:
        return union_ref([native_ref(r) for r in rs])

def single_ref_or_subtraction(rs):
    if len(rs) == 0:
        raise RuntimeError("Must have at least one reference")
    elif len(rs) == 1:
        return native_ref(rs[0])
    else:
        return subtraction_ref([native_ref(r) for r in rs])

def native_ref_or_union(rs):
    if len(rs) == 0:
        raise RuntimeError("Must have at least one reference")
    elif len(rs) == 1:
        assert(isinstance(rs[0], (native_ref, multiple_ref)))
        return rs[0]
    else:
        return union_ref(rs)

###################
class _empty_shape(object):
    def realize(self):
        return empty_ref()
    def delete(self):
        pass
    def __repr__(self):
        return "<empty_shape>"


_the_empty_shape = _empty_shape()

def empty_shape():
    return _the_empty_shape

def is_empty_shape(s):
    return is_empty_ref(s.realize())

###################

class _universal_shape(object):
    def realize(self):
        return universal_ref()
    def delete(self):
        pass
    def __repr__(self):
        return "<universal_shape>"


_the_universal_shape = _universal_shape()

def universal_shape():
    return _the_universal_shape

def is_universal_shape(s):
    return is_universal_ref(s.realize())
    
# TO SHAPE
def partition(seq, condition):
    a, b = [], []
    for item in seq:
        (a if condition(item) else b).append(item)
    return a, b

def maybe_delete_shapes(shapes, ref):
   for s in shapes:
       if is_empty_shape(s) or is_universal_shape(s):
           pass
       elif ref.contains(s.realize()):
           s.delete()
   return ref


# For testing purposes

generate_mode = make_parameter(False)
step_mode = make_parameter(False)

class meta_model(type):
    def __init__(cls, name, bases, nmspc):
        super(meta_model, cls).__init__(name, bases, nmspc)
        if generate_mode():
            cls().setup()
            cls().create()
            if step_mode():
                cls().wait()
