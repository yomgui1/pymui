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

class PyMUICType(object):
    __ptr_dict = {}
    __ary_dict = {}
    
    def __long__(self):
        raise NotImplemented("type doesn't implement __long__ method")

    @classmethod
    def FromLong(cl, v):
        raise NotImplemented("type doesn't implement FromLong method")

    @classmethod
    def PointerType(cl):
        n = 'PT_%s' % cl.__name__
        ncl = PyMUICType.__ptr_dict.get(n)
        if not ncl:
            ncl = _ct.POINTER(cl)
            ncl = type(n, (ncl, PyMUICPointerType), {'_type_': cl})
            PyMUICType.__ptr_dict[n] = ncl
        return ncl

    @classmethod
    def ArrayType(cl, c):
        n = '%s_Array_%u' % (cl.__name__, c)
        ncl = PyMUICType.__ary_dict.get(n)
        if not ncl:
            ncl = _ct.ARRAY(cl, c)
            ncl = type(n, (ncl, PyMUICArrayType), {'_length_': c, '_type_': cl})
            PyMUICType.__ary_dict[n] = ncl
        return ncl

class PyMUICSimpleType(PyMUICType):
    def __long__(self):
        return self.value or 0

    @classmethod
    def FromLong(cl, v):
        return cl(v)

class PyMUICPointerType(PyMUICType):
    def __long__(self):
        return _ct.cast(self, _ct.c_void_p).value or 0

    @classmethod
    def FromLong(cl, v):
        return cl(v)

class PyMUICArrayType(PyMUICType):
    def __long__(self):
        return _ct.c_ulong.from_address(addressof(self)).value

class PyMUICStructureType(PyMUICType):
    def __long__(self):
        return _ct.c_ulong.from_address(addressof(self)).value

class PyMUICUnionType(PyMUICType):
    def __long__(self):
        return _ct.c_ulong.from_address(addressof(self)).value

class c_ULONG(_ct.c_ulong, PyMUICSimpleType): pass
class c_LONG(_ct.c_long, PyMUICSimpleType): pass
class c_UWORD(_ct.c_ushort, PyMUICSimpleType): pass
class c_WORD(_ct.c_short, PyMUICSimpleType): pass
class c_UBYTE(_ct.c_ubyte, PyMUICSimpleType): pass
class c_BYTE(_ct.c_byte, PyMUICSimpleType): pass
class c_CHAR(_ct.c_char, PyMUICSimpleType): pass

class c_APTR(_ct.c_void_p, PyMUICSimpleType):
    def __long__(self):
        return self.value

class c_STRPTR(_ct.c_char_p, PyMUICSimpleType):
    def __new__(cl, x=0):
        if isinstance(x, str):
            o = c_CONST_STRPTR.__new__(c_CONST_STRPTR)
        else:
            o = _ct.c_char_p.__new__(cl)
        o.value = x
        return o

    def __long__(self):
        return _ct.cast(self, _ct.c_void_p).value or 0
    
    def __getitem__(self, i):
        return self.value[i]

    def __setitem__(self, i, v):
        _ct.POINTER(_ct.c_char).from_address(addressof(self))[i] = v

class c_CONST_STRPTR(c_STRPTR):
    def __setitem__(self, i, v):
        raise NotImplemented("CONST_STRPRT cannot be changed")

class c_STRUCTURE(_ct.Structure, PyMUICType): pass
class c_UNION(_ct.Union, PyMUICType): pass

def PointerOn(x):
    return x.PointerType()(x)


################################################################################
#### Usefull types
################################################################################

class c_TagItem(c_STRUCTURE):
    _fields_ = [ ('ti_Tag', c_ULONG),
                 ('ti_Data', c_ULONG) ]

class c_BOOL(c_LONG): pass

c_pSTRPTR = c_STRPTR.PointerType()

class c_pTextFont(c_APTR): pass
class c_pList(c_APTR): pass
class c_pMinList(c_APTR): pass

class c_Node(c_STRUCTURE): pass
c_Node._fields_ = [ ('ln_Succ', c_Node.PointerType()),
                    ('ln_Pred', c_Node.PointerType()),
                    ('ln_Type', c_UBYTE),
                    ('ln_Pri', c_BYTE),
                    ('ln_Name', c_STRPTR) ]

class c_MinNode(c_STRUCTURE): pass
c_MinNode._fields_ = [ ('mln_Succ', c_MinNode.PointerType()),
                       ('mln_Pred', c_MinNode.PointerType()) ]

class c_Message(c_STRUCTURE):
    _fields_ = [ ('mn_Node', c_Node),
                 ('mn_ReplyPort', c_APTR),
                 ('mn_Length', c_UWORD) ]

################################################################################
#### Test-suite
################################################################################
    
if __name__ == '__main__':
    from sys import getrefcount as rc
    
    o = c_STRPTR('toto') # Shall return a CONST_STRPTR
    assert isinstance(o, PyMUICType)
    assert isinstance(o, PyMUICSimpleType)
    assert isinstance(o, c_CONST_STRPTR)
    assert o[0] == 't'
    try:
        o[0] = 'u'
    except TypeError:
        pass
    else:
        raise AssertionError('setitem shall not be possible on CONST_STRPTR!')

    o = c_STRPTR.ArrayType(3)('a', 'toto', 0)
    assert isinstance(o, PyMUICType)
    assert isinstance(o, PyMUICArrayType)
    assert len(o) == 3
    assert o[0][0] == 'a'
    assert o[1][1] == 'o'
    assert long(o[2]) == 0

    # Python hacking!
    addr = long(o[1])
    assert addr > 0
    x = c_STRPTR(addr)
    assert isinstance(x, c_STRPTR)
    assert x.value == o[1].value
    x[0] = 'p'
    assert x[0] == 'p'
    assert x.value == 'poto'
    s = 'toto'
    assert ord(s[0]) == 112 ### 't' == 'p', Funny, isn't ?

    o = c_BYTE(255)
    assert long(o) == -1

    p = PointerOn(o)
    assert isinstance(p, PyMUICType)
    assert isinstance(p, PyMUICPointerType)
    assert p[0].value == -1

    o = c_STRPTR('tutu')
    cnt = rc(o)
    p = c_APTR(long(o))
    assert long(p) == long(o)
    assert rc(o) == cnt

    x = id('bla')
    o = c_STRPTR(x)
    assert long(o) == x
    
    print "Everything is OK"
