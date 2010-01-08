################################################################################
#### PyMUI C types
################################################################################

##
## Design rules:
##
## Pointers: pointer classes should accept as first argument an instance of the
##           pointed type or nothing. In last case, the pointer value is zero.
##

import ctypes as _ct

class PyMUICType(object):
    """PyMUICType: base class for all values types accepted by MUI API.
    
    MUI accepts only 32bit integer value type, signed or unsigned.
    So any data shall be have this representation to be given to MUI.
    """

    _iskept = False

    def __long__(self):
        """Return a 32bit integer value usable for MUI.

        Subclasses shall implement it.
        """
        raise AssertionError("Shall be implemented by subclasses")

    @classmethod
    def FromLong(cl, v):
        """x.FromLong(v) -> instance

        Return a new instance object based on the given 32bit integer value.
        
        This function is for PyMUI internal usage only!
        Subclasses shall implement it.
        """
        raise AssertionError("Shall be implemented by subclasses")

    @property
    def value(self):
        """Return a python interpretation of the instance.

        Some ctypes doesn't have 'value' property.
        To have a common API, this mixing add this property if not exists.
        
        By default, the integer representation of the instance is returned.
        """
        return long(self)

    __tp_cache = {}
    
    @classmethod
    def _PointerType(cl):
        name = 'PT_'+cl.__name__
        x = cl.__tp_cache.get(name)
        if x is None:
            x = type(name, (_ct.POINTER(cl), CPointer), {'_type_': cl})
            cl.__tp_cache[name] = x
        return x

    @property
    def _PointerOn(self):
        return self._PointerType()(self)

    @classmethod
    def ArrayOf(cl, n):
        """x.ArrayOf(n) -> PyMUICType type

        Returns a new PyMUICType array type of fixed length given by 'n'.
        The array prototype is the class of x, if x is an PyMUICType instance,
        of x itself if it's a PyMUICType type.
        """

        # Note: I don't cache the returned type here due to the volatile 'n' factor.
        return type('%s_Array_%u' % (cl.__name__, n), (cl*n, _CArray), {'_type_': cl, '_length_': n})
        
class CSimpleValue(PyMUICType):
    def __long__(self):
        return self.value

    @classmethod
    def FromLong(cl, v):
        return cl(v)

# Common base class for CStructure and CArray classes
class CComplexBase(PyMUICType):
    _iskept = True

    def __long__(self):
        return _ct.addressof(self)

    @classmethod
    def FromLong(cl, v):
        return cl.from_address(v)

class CStructure(_ct.Structure, CComplexBase):
    """CStructure mixing class.

    All subclasses shall defines '_fields_' attribute.
    See ctypes module documentation about Structure type.
    """
    
    pass

class _CArray(CComplexBase):
    """_CArray mixing class.

    Private class, shall not be used publicly. Use 'ArrayOf' methods.
    
    All subclasses shall defines '_type_' attribute representing the pointed memory ctype,
    and '_length_' attribute representing the number of slots in the array.
    See ctypes module documentation about Array type.
    """

    def __len__(self):
        return len(self.contents)

class CPointer(PyMUICType):
    """CPointer mixing class

    All subclasses shall defines '_type_' attribute representing the pointed memory ctype.
    See ctypes module documentation about Pointer type.
    """

    _iskept = True

    def __long__(self):
        return _ct.cast(self, _ct.c_void_p).value or 0

    @classmethod
    def FromLong(cl, v):
        return _ct.cast(_ct.c_void_p(v), cl)


### All MUI acceptable base types
# Simples (all represent integer value)
class c_BYTE(_ct.c_byte, CSimpleValue): pass
class c_UBYTE(_ct.c_ubyte, CSimpleValue): pass
class c_SHORT(_ct.c_short, CSimpleValue): pass
class c_USHORT(_ct.c_ushort, CSimpleValue): pass
class c_LONG(_ct.c_long, CSimpleValue): pass
class c_ULONG(_ct.c_ulong, CSimpleValue): pass

class c_APTR(_ct.c_void_p, CSimpleValue): # c_APTR is not subclass of CPointer, the only possible case
    def __init__(self, x=0):
        if isinstance(x, (c_APTR, CPointer)):
            _ct.c_void_p.__init__(self, long(x))
        else:
            _ct.c_void_p.__init__(self, x)
        
    def __long__(self):
        return self.value or 0

# More complexes
class c_CHAR(_ct.c_char, PyMUICType):
    def __long__(self):
        return ord(self.value)

    @classmethod
    def FromLong(cl, v):
        return cl(chr(v))

class c_BOOL(c_ULONG): # BOOL ctype is a unsigned long in the MOS SDK.
    @property
    def value(self):
        return bool(self)

class c_STRPTR(_ct.c_char_p, CPointer):
    @classmethod
    def FromLong(cl, v):
        return cl(v) # Special case where c_char_p accepts pointer on char

    def __len__(self):
        return len(self.value)

    def __getitem__(self, index):
        return self.value[index]


# Specials
class Iterator_c_pSTRPTR:
    def __init__(self, o):
        self.__o = o
        self.__i = 0

    def __iter__(self):
        return self

    def next(self):
        v = self.__o[self.__i]
        if v.value is None:
            raise StopIteration()
        self.__i += 1
        return v

class c_pSTRPTR(c_STRPTR._PointerType()):
    _type_ = c_STRPTR

    def __init__(self, x=None):
        if x:
            if isinstance(x, (list, tuple)):
                o = c_STRPTR.ArrayOf(len(x)+1)(*x)
                x = o[0]
            super(c_pSTRPTR, self).__init__(x)
        else:
            super(c_pSTRPTR, self).__init__()

    def __iter__(self):
        return Iterator_c_pSTRPTR(self)

class c_FLOAT(_ct.c_float, CSimpleValue):
    def __long__(self):
        # like a C cast of float value
        return long(self.value)

class c_pFLOAT(c_FLOAT._PointerType(), CPointer):
    _type_ = _ct.c_float

class c_DOUBLE(_ct.c_double, CSimpleValue):
    def __long__(self):
        # like a C cast of double value
        return long(self.value)
    
class c_pDOUBLE(c_DOUBLE._PointerType(), CPointer):
    _type_ = _ct.c_double


# Unit testing
if __name__ == '__main__':
    assert c_LONG(-45).value == -45

    o = c_APTR()
    assert o.value is None
    assert long(o) is 0
    assert c_APTR(-45).value == c_ULONG(-45).value

    f = c_FLOAT(3.14)
    assert long(f) == 3

    o = c_pFLOAT(f)
    assert o.contents.value

    ao = long(o)
    o2 = c_pFLOAT.FromLong(ao)
    assert long(o2) == ao

    o = c_STRPTR()
    assert o.value is None
    assert long(o) is 0

    s = 'test'
    o.value = s
    assert o.value == s
    assert long(o) != 0
    assert len(o) == len(s)

    o = c_pSTRPTR()
    assert o.value == 0

    t = ['toto', 'titi', 'tutu']
    o = c_pSTRPTR(t)
    assert isinstance(o[0], c_STRPTR)
    assert o[3].value is None
    assert not any(cmp(a, b.value) for a, b in zip(t, o))

    t = [ c_STRPTR(x) for x in t ]
    o = c_pSTRPTR(t)
    assert isinstance(o[0], c_STRPTR)
    assert o[3].value is None
    assert any(a.value == b.value for a, b in zip(t, o))
    assert long(o[0]) == long(t[0])

    # Auto-casting for c_APTR
    try:
        o = c_APTR(c_CHAR('o'))
    except TypeError:
        pass
    else:
        raise AssertionError("TypeError not raised with casting of non pointer instance into c_APTR")

    x = c_STRPTR('test')
    o = c_APTR(x)
    assert o.value == long(x)

    o = c_APTR(c_APTR(42))
    assert o.value == 42

    print "Module OK!"
