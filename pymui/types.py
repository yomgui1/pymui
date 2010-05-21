################################################################################
#### PyMUI C types
################################################################################

## ** Concepts **
##
## This files brings some classes based on ctypes modules and designed to mimic
## C datatypes accepted in MUI API. It's based on the AmigaOS BOOPSI paradigm.
##
## The AmigaOS has been developed for a 32bit architecture,
## so this API has the particularity to pass data using only 32bit integer values,
## that may be unsigned or signed.
## So when more data or floating point values are needed to be transfered between
## functions, a pointer (32bit integer) is used.
##
## So PyMUI types uses this concept also: all instances shall be convertible into
## a 32bit integer value.
##
## Python object references:
## Some Python objects needs to be kept alive like strings, buffers or more complex
## objects.
##
## But to simplify the design and mimic the MUI-C behaviour PyMUICType doesn't
## keep any references! It's to developers to handle that.
##

import ctypes as _ct
from ctypes import addressof, string_at
from _ctypes import PyObj_FromPtr as _PyObj_FromPtr

ENCODING = 'latin-1'

"""
ctype.from_value => create an instance of ctype class, set from a C long value.
o = ctype() => create an instance of ctype class
long(o) => return the C long value from the ctype.
o.value => return an object representing the context of the ctype
o.value = x

Pointer only:
'value' property get/set only long integer, the address of pointed buffer.
use 'contents' to have the pointed object.
"""

#===============================================================================
# Root class of all PyMUI C types
#
# This classes should not be used immediately.
# Use one of sub-categories just after.
#

class PyMUICType(object):
    __ptr_dict = {}
    __ary_dict = {}

    @classmethod
    def PointerType(cl):
        n = 'PT_%s' % cl.__name__
        ncl = PyMUICType.__ptr_dict.get(n)
        if not ncl:
            ncl = _ct.POINTER(cl)
            ncl = type(n, (PyMUICPointerType, ncl), {'_type_': cl})
            PyMUICType.__ptr_dict[n] = ncl
        return ncl

    @classmethod
    def ArrayType(cl, c):
        n = '%s_Array_%u' % (cl.__name__, c)
        ncl = PyMUICType.__ary_dict.get(n)
        if not ncl:
            ncl = _ct.ARRAY(cl, c)
            ncl = type(n, (PyMUICArrayType, ncl), {'_length_': c, '_type_': cl})
            PyMUICType.__ary_dict[n] = ncl
        return ncl

    @classmethod
    def from_value(cl, v):
        "Return an instance of the class where the buffer is initialized with the given value"
        raise NotImplementedError("type %s doesn't implement from_value method" % cl.__name__)

    def __long__(self):
        raise NotImplemented("type doesn't implement __long__ method")


#===============================================================================
# Sub-categories.
#
# PyMUICSimpleType : for types that handles simple buffer taken as a whole.
# PyMUICUnionType  : for types where the buffer is shared between a fixed amount of types.
# PyMUICArrayType  : for types where the buffer can be seen as a group of fixed length,
#                    where all items have the same type.
# PyMUICStructType : for types like a group of fixed number of items of any types.
# PyMUICPointerType: for types to handle a simple integer value representing an address
#                    of another buffer of it own type.
#

class PyMUICSimpleType(PyMUICType):
    def __long__(self):
        return self.value or 0

    @classmethod
    def from_value(cl, v):
        return cl(v)


class PyMUICPointerType(PyMUICType):
    def __long__(self):
        return _ct.cast(self, _ct.c_void_p).value or 0

    @classmethod
    def from_value(cl, v):
        return _ct.cast(_ct.c_void_p(v), cl)

    def __set_value(self, v):
        self.contents = self._type_.from_address(v)

    value = property(fget=__long__, fset=__set_value)


class _PyMUICComplex(PyMUICType):
    def __long__(self):
        return addressof(self)

    @classmethod
    def from_value(cl, v):
        return cl.from_address(v)


class PyMUICUnionType(_PyMUICComplex, _ct.Union): pass
class PyMUICArrayType(_PyMUICComplex): pass
class PyMUICStructureType(_PyMUICComplex, _ct.Structure): pass


#===============================================================================
# Real classes (simples)
#

class c_ULONG(PyMUICSimpleType, _ct.c_ulong): pass
class c_LONG(PyMUICSimpleType, _ct.c_long): pass
class c_UWORD(PyMUICSimpleType, _ct.c_ushort): pass
class c_WORD(PyMUICSimpleType, _ct.c_short): pass
class c_UBYTE(PyMUICSimpleType, _ct.c_ubyte): pass
class c_BYTE(PyMUICSimpleType, _ct.c_byte): pass
class c_CHAR(PyMUICSimpleType, _ct.c_char): pass

# It could be logic to think that c_APTR is a subclass
# of PyMUICPointerType. But it's not the case and remains
# a subclass of PyMUICSimpleType because no items operations
# are possible on c_APTR instances.

class c_APTR(PyMUICSimpleType, _ct.c_void_p):
    def __init__(self, x=None):
        if isinstance(x, PyMUICPointerType):
            x = long(x)
        super(c_APTR, self).__init__(x)

    def __get_value(self):
        return super(c_APTR, self).value or 0

    value = property(fget=__get_value, fset=_ct.c_void_p.value)


# Floating types are a bit special:
# BOOPSI/MUI don't use them directly. They are given only
# by references (pointers) to objects.
#
# So to force user to not use them as methods/attributes
# types __long__ and from_value raise errors.

class _PyMUICFloatType(PyMUICSimpleType):
    def __long__(self):
        raise SyntaxError("Not permited operation")

    @classmethod
    def from_value(cl, value):
        raise SyntaxError("Not permited operation")


class c_FLOAT(_PyMUICFloatType, _ct.c_float): pass
class c_DOUBLE(_PyMUICFloatType, _ct.c_double): pass


# ctypes considers c_char_p/c_wchar_p as simple type
# and non-mutable buffer.
# Amiga STRPTR is more like a pointer on c_char,
# and mutable. CONST_STRPTR is not mutable.
#

class c_CONST_STRPTR(PyMUICPointerType, _ct.c_char_p):
    def __init__(self, x=None):
        assert not x or isinstance(x, basestring)
        super(c_CONST_STRPTR, self).__init__(x)

    def __get_contents(self):
        return _ct.c_char_p.value.__get__(self)

    def __set_contents(self, v):
        _ct.c_char_p.value.__set__(self, v)

    contents = property(fget=__get_contents, fset=__set_contents)

    def __set_value(self, v):
        _ct.c_void_p.value.__set__(self, v)

    value = property(fget=PyMUICPointerType.__long__, fset=__set_value)

    def __getitem__(self, i):
        return self.contents[i]


class c_STRPTR(c_CONST_STRPTR):
    def __setitem__(self, i, v):
        c_CHAR.from_address(long(self)+i).value = v


class c_PyObject(PyMUICSimpleType, _ct.py_object):
    def __long__(self):
        return _ct.c_void_p.from_address(addressof(self)).value or 0

    @classmethod
    def from_value(cl, v):
        return cl(_PyObj_FromPtr(v))


def PointerOn(x):
    return x.PointerType()(x)


################################################################################
#### Usefull types
################################################################################

class c_BOOL(c_LONG):
    def __get_value(self):
        return bool(c_LONG.value.__get__(self))

    value = property(fget=__get_value, fset=c_LONG.value)


class c_pSTRPTR(c_STRPTR.PointerType()):
    _type_ = c_STRPTR

    def __init__(self, x=None):
        # Accept tuple/list as initiator
        if x is None:
            super(c_pSTRPTR, self).__init__()
        else:
            if isinstance(x, (list, tuple)):
                x = c_STRPTR.ArrayType(len(x))(*tuple(c_STRPTR(s) for s in x))[0]
            super(c_pSTRPTR, self).__init__(x)


class c_TagItem(PyMUICStructureType):
    _fields_ = [ ('ti_Tag', c_ULONG),
                 ('ti_Data', c_ULONG) ]


class c_pTextFont(c_APTR): pass
class c_pList(c_APTR): pass
class c_pMinList(c_APTR): pass

class c_Node(PyMUICStructureType): _pack_ = 2
c_Node._fields_ = [ ('ln_Succ', c_Node.PointerType()),
                    ('ln_Pred', c_Node.PointerType()),
                    ('ln_Type', c_UBYTE),
                    ('ln_Pri', c_BYTE),
                    ('ln_Name', c_STRPTR) ]

class c_MinNode(PyMUICStructureType): pass
c_MinNode._fields_ = [ ('mln_Succ', c_MinNode.PointerType()),
                       ('mln_Pred', c_MinNode.PointerType()) ]

class c_Message(PyMUICStructureType):
    _pack_ = 2
    _fields_ = [ ('mn_Node', c_Node),
                 ('mn_ReplyPort', c_APTR),
                 ('mn_Length', c_UWORD) ]


################################################################################
#### Test-suite
################################################################################
    
if __name__ == '__main__':
    from sys import getrefcount as rc
    import gc

    o = c_ULONG.PointerType()()
    assert o.value == 0

    x = c_ULONG(45)
    o.value = addressof(x)
    assert o.value == addressof(x)
    assert o.contents.value == o.contents.value

    o = c_BYTE(255)
    assert long(o) == -1

    p = PointerOn(o)
    assert isinstance(p, PyMUICType)
    assert isinstance(p, PyMUICPointerType)
    assert p[0].value == -1

    x = 'toto'
    o = c_CONST_STRPTR()
    assert isinstance(p, PyMUICPointerType)
    assert o.value == 0 and o.contents is None
    v = _ct.cast(_ct.c_char_p(x), _ct.c_void_p).value
    o.value = v
    assert o.value == v
    assert o.contents == x
    o.contents = ''
    assert o.value != 0 and not o.contents

    o = c_CONST_STRPTR('titi')
    assert o.contents == 'titi'

    o = c_STRPTR()
    assert isinstance(p, PyMUICPointerType)
    assert o.value == 0 and o.contents is None
    v = _ct.cast(_ct.c_char_p(x), _ct.c_void_p).value
    o.value = v
    assert o.value == v
    assert o.contents == x
    assert o[0] == 't'
    o[0] = 'u'
    assert o[0] == 'u' and o.contents == 'uoto'
    o.contents = ''
    assert o.value != 0 and not o.contents

    x = 'fklgkf'
    c = rc(x)
    o = c_STRPTR(x)
    assert o.contents == x
    assert rc(x) == c+1

    o = c_CONST_STRPTR.ArrayType(3)('a', 'toto', 0)
    assert isinstance(o, PyMUICType)
    assert isinstance(o, PyMUICArrayType)
    assert len(o) == 3
    assert o[0][0] == 'a'
    assert o[1][1] == 'o'
    assert long(o[2]) == 0

    # Python hacking!
    addr = long(o[1])
    assert addr > 0
    x = c_STRPTR.from_value(addr)
    assert isinstance(x, c_STRPTR)
    assert x.value == o[1].value
    x[0] = 'p'
    assert x[0] == 'p'
    assert x.contents == 'poto'
    s = 'toto'
    assert ord(s[0]) == 112 ### 't' == 'p', Funny, isn't ?

    o = c_STRPTR('tutu')
    cnt = rc(o)
    p = c_APTR(long(o))
    assert long(p) == long(o)

    x = id('bla')
    try:
        o = c_STRPTR(x)
    except AssertionError:
        pass
    else:
        raise AssertionError('c_STRPTR(x) shall not accept integer but string')

    x = ['one', 'two', 'three', None]
    o = c_pSTRPTR(x)
    assert len(o._objects) > 0
    assert long(o) != 0
    v = o[:4]
    assert len(v) == 4
    assert [o.contents for o in v] == x

    o = c_STRPTR()
    x = c_APTR(o)
    assert x.value == 0

    s = "123456789\xF4\0\033x" # len = 13
    TestClass = type('TestClass',
                     (PyMUICStructureType, ),
                     {'_fields_': [ ('Data', (c_UBYTE*len(s))) ]})
    o = TestClass()
    o.Data[:] = [ ord(x) for x in s ]
    assert len(o.Data) == len(s)

    x = [1, 2, 3]
    o = c_PyObject(x)
    assert id(x) == long(o)
    assert o.value is x
    o.value = None
    assert o.value is None
    assert long(o) != 0 # yep, it's address of the None object

    o = c_PyObject()
    assert long(o) == 0
    try:
        o.value
    except ValueError:
        pass
    else:
        raise AssertionError("c_PyObject().value shall raise a ValueError exception")

    a = c_BOOL()
    b = c_BOOL(1)
    c = c_BOOL(0)
    d = c_BOOL(True)
    assert a.value == c.value
    assert b.value == d.value

    print "Module OK"
