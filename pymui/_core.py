###############################################################################
# Copyright (c) 2009 Guillaume Roguez
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

import sys, functools, array, ctypes, weakref

try:
    DEBUG = sys.argv[1] == '-v'
except:
    DEBUG = False

def debug(x, *args):
    if DEBUG:
        print x % args

import _muimaster
from _muimaster import *
from defines import *

# MorphOS maps public memory from this address.
# Below it's not a valid address and may lead to CPU bus exception.
_ADDRESS_MIN = 0x10000000

MUI_EventHandlerRC_Eat = (1<<0)
NM_BARLABEL = -1

## Currently private defines, but very useful
MUIA_Window_TabletMessages = 0x804217b7
TABLETA_Dummy        = (TAG_USER + 0x3A000)
TABLETA_TabletZ      = (TABLETA_Dummy + 1)
TABLETA_RangeZ       = (TABLETA_Dummy + 2)
TABLETA_AngleX       = (TABLETA_Dummy + 3)
TABLETA_AngleY       = (TABLETA_Dummy + 4)
TABLETA_AngleZ       = (TABLETA_Dummy + 5)
TABLETA_Pressure     = (TABLETA_Dummy + 6)
TABLETA_ButtonBits   = (TABLETA_Dummy + 7)
TABLETA_InProximity  = (TABLETA_Dummy + 8)
TABLETA_ResolutionX  = (TABLETA_Dummy + 9)
TABLETA_ResolutionY  = (TABLETA_Dummy + 10)
##

################################################################################
#### PyMUI C types
################################################################################

class PyMUICType:
    __pt_cache = {}
        
    @classmethod
    def pointertype(cl):
        n = 'LP_' + cl.__name__
        if n in cl.__pt_cache: return cl.__pt_cache[n]
        ptr = type(n, (ctypes._Pointer, AsCPointer), {'_type_': cl})
        cl.__pt_cache[n] = ptr
        return ptr

    def pointer(self):
        return self.pointertype()(self)

    @classmethod
    def mkarray(cl, c):
        n = cl.__name__ + '_Array_%u' % c
        if n in cl.__pt_cache: return cl.__pt_cache[n]
        ncl = type(n, (ctypes.Array, AsCArray), {'_length_': c, '_type_': cl})
        cl.__pt_cache[n] = ncl
        return ncl

class AsCInteger(PyMUICType):
    keep = False
    
    @classmethod
    def tomui(cl, o):
        if not hasattr(o, 'value'):
            return o, cl(o) # return keep value shall be the source object and not the converted here!
        return o, o.value

    @classmethod
    def asobj(cl, i):
        return cl(i).value

    def __long__(self):
        return self.value

class AsCArray(PyMUICType):
    keep = True

    @classmethod
    def tomui(cl, o):
        if o is None: return None, 0
        if isinstance(o, cl): return o, ctypes.addressof(o)
        x=cl()
        x[:] = o
        return x, ctypes.addressof(x)

    @classmethod
    def asobj(cl, i):
        if i: return cl.from_address(i)
        return None

    def __long__(self):
        return ctypes.addressof(self)

class AsCPointer(PyMUICType):
    keep = True
    
    @classmethod
    def tomui(cl, o):
        if not isinstance(o, cl): o = cl(cl._type_(o))
        return o, o # handled as buffer object by _muimaster, XXX: is it really better? need to be check.

    @classmethod
    def asobj(cl, i):
        if i == 0: cl() # no arguments => NULL pointer
        return cl(cl._type_.from_address(i)) # !!! DANGER !!!

    def __long__(self):
        return ctypes.cast(self, ctypes.c_void_p).value

class AsCString(ctypes.c_char_p, PyMUICType):
    keep = True

    @classmethod
    def tomui(cl, o):
        if o is None: return None, 0
        if not isinstance(o, cl): o = cl(o)
        return o, o

    @classmethod
    def asobj(cl, i):
        if i: return ctypes.string_at(i) # !!! DANGER !!!
        return None

    def __long__(self):
        return ctypes.cast(self, ctypes.c_void_p).value

# Some AmigaOS types
class c_CHAR(ctypes.c_char, AsCInteger): pass
class c_BYTE(ctypes.c_byte, AsCInteger): pass
class c_UBYTE(ctypes.c_ubyte, AsCInteger): pass
class c_SHORT(ctypes.c_short, AsCInteger): pass
class c_USHORT(ctypes.c_ushort, AsCInteger): pass
class c_LONG(ctypes.c_long, AsCInteger): pass
class c_ULONG(ctypes.c_ulong, AsCInteger): pass
class c_APTR(ctypes.c_void_p, AsCInteger): pass # yes! as we use the 'value' method and we don't keep reference.
class c_STRPTR(AsCString): pass
class c_BOOL(c_ULONG): pass
class c_pTextFont(c_APTR): pass
class c_pList(c_APTR): pass
class c_pMinList(c_APTR): pass

# Only used for array
class c_DOUBLE(ctypes.c_double, AsCInteger):
    def __long__(self):
        raise SystemError("c_DOUBLE can't be used as C type in PyMUI")

class c_pDOUBLE(ctypes.POINTER(ctypes.c_double), AsCPointer):
    keep = False
    _type_ = ctypes.c_double

    def __new__(cl, x):
        if not isinstance(x, cl._type_):
            x = cl._type_(x)
        return super(c_pDOUBLE, cl).__new__(cl, x)

    def __init__(self, x):
        if not isinstance(x, self._type_):
            x = self._type_(x)
        super(c_pDOUBLE, self).__init__(x)

class c_pSTRPTR(ctypes.POINTER(c_STRPTR), AsCPointer):
    _type_ = c_STRPTR # XXX: bad! how to change that?

    def __new__(cl, x):
        if isinstance(x, (tuple, list)):
            a = (c_STRPTR*(len(x)+1))()
            a[:-1] = x
            o = super(c_pSTRPTR, cl).__new__(cl)
            o.contents = a[0]
            return o
        return super(c_pSTRPTR, cl).__new__(cl, x)

    def __init__(self, x):
        if isinstance(x, (tuple, list)):
            super(c_pSTRPTR, self).__init__()
        else:
            super(c_pSTRPTR, self).__init__(x)

    @classmethod
    def tomui(cl, o):
        if not isinstance(o, cl): o = cl(o)
        return o, o # handled as buffer object by _muimaster, XXX: is it really better? need to be check.

class c_pObject(c_APTR):
    keep = True

    def __new__(cl, x):
        if isinstance(x, PyBOOPSIObject):
            return ctypes.c_void_p.__new__(cl, x._object)
        return ctypes.c_void_p.__new__(cl, x)

    def __init__(self, x):
        if isinstance(x, PyBOOPSIObject):
            ctypes.c_void_p.__init__(self, x._object)
        else:
            ctypes.c_void_p.__init__(self, x)

    @classmethod
    def asobj(cl, i):
        return _muimaster._BOOPSI2Python(i) # 0 is accepted

class c_TagItem(ctypes.Structure):
    _fields_ = [('ti_Tag', c_ULONG),
                ('ti_Data', c_ULONG)]
class c_pTagItem(ctypes.POINTER(c_TagItem), AsCPointer): pass

class c_ImageSpec(c_STRPTR):
    """Image specification can be a string or an integer.
    MUI pre-defines some integer values: 'MUII_xxx' defines.
    But this class accept also string specification by its address.
    In this case the class knows the difference between an address string
    and a plain integer by compare the given value to 0x10000000.
    If stricly below, it's an plain integer.
    If equals or upper, it's a string address.
    0x10000000 has been choosen because MorphOS map the public memory
    after this value.
    """

    @classmethod
    def asobj(cl, i): # _muimaster always returns a ULONG for i
        if i < _ADDRESS_MIN: return i
        return c_STRPTR.asobj(i)

class c_MenuitemTitle(c_STRPTR):
    """Menuitem title accepts string address and some special integer values.
    Currently only NM_BARLABEL is accepted.
    """

    @classmethod
    def asobj(cl, i):
        if i == NM_BARLABEL: return i
        return c_STRPTR.asobj(i)

def HOOKTYPE(a2_ctypes, a1_ctypes):
    return CFUNCTYPE(c_APTR, a2_ctypes, a1_ctypes)


################################################################################
#### PyMUI internal base classes and routines
################################################################################

class MAttribute(property):
    def __init__(self, id, isg, ctype, keep=None, doc=None, **kwds):
        self.__isg = isg
        self.__id = id
        assert issubclass(ctype, PyMUICType)
        self.__ctype = ctype

        keep = (ctype.keep if keep is None else keep)
        self.__keep = keep

        if 'i' in isg:
            def init(obj, v):
                v, x = ctype.tomui(v)
                if keep: obj._keep_dict[id] = v
                return long(x)
        else:
            def init(v):
                raise AttributeError("attribute %08x can't be used at init" % self.__id)

        self.init = init

        if 's' in isg:
            def _setter(obj, v):
                v, x = ctype.tomui(v)
                obj._set(id, x)
                if keep: obj._keep_dict[id] = v
        else:
            _setter = None

        if 'g' in isg:
            def _getter(obj):
                return ctype.asobj(obj._get(id))
        else:
            _getter = None

        preSet = kwds.get('preSet')
        postSet = kwds.get('postSet')
        if preSet and postSet:
            def setter(obj, v):
                _setter(obj, preSet(obj, self, v))
                postSet(obj, self, v)
        elif preSet:
            def setter(obj, v):
                _setter(obj, preSet(obj, self, v))
        elif postSet:
            def setter(obj, v):
                _setter(obj, v)
                postSet(obj, self, v)
        else:
            setter = _setter

        preGet = kwds.get('preGet')
        postGet = kwds.get('postGet')
        if preGet and postGet:
            def getter(obj):
                preGet(obj, self)
                return postGet(obj, self, _getter(obj))
        elif preGet:
            def getter(obj, v):
                preGet(obj, self)
                return _getter(obj)
        elif postGet:
            def getter(obj, v):
                return postGet(obj, self, _getter(obj))
        else:
            getter = _getter

        property.__init__(self, fget=getter, fset=setter, doc=doc)

    @property
    def isg(self): return self.__isg
    
    @property
    def id(self): return self.__id
    
    @property
    def ctype(self): return self.__ctype
    
    @property
    def keep(self): return self.__keep

#===============================================================================

class MMethod(property):
    def __init__(self, id, argstypes=None, rettype=None,
                 varargs=False, doc=None, **kwds):
        self.__id = id
        self.__rettp = rettype
        if rettype is None:
            self.__retconv = lambda x: None
        else:
            self.__retconv = rettype.asobj
        
        if argstypes:
            if not isinstance(argstypes, (tuple, list)):
                assert issubclass(argstypes, PyMUICType)
                assert not varargs
                self.__argstp = argstypes
                cb = self.call1
            else:
                assert any(issubclass(tp, PyMUICType) for tp in argstypes)
                self.__argstp = tuple(argstypes)
                self.__varargs = varargs
                if varargs:
                    cb = self.callva
                else:
                    cb = self.call
        else:
            self.__argstp = None
            self.__varargs = False
            cb = self.call0

        self.__cb = cb
        self.__alias = None
        property.__init__(self, fget=lambda obj: functools.partial(self.__cb, obj), doc=doc)

    def __call__(self, obj, *args):
        return self.__cb(obj, *args)

    def alias(self, f):
        @functools.wraps(f)
        def wrapper(obj, *args):
            return f(obj, self, *args)
        return wrapper

    def callva(self, obj, *args):
        if len(self.__argstp) > len(args):
            raise AttributeError("method accepts only %u argument(s), get %u"
                                 % (len(self.__argstp), len(args)))
        data = []
        keep = []
        for tp, v in zip(self.__argstp, args):
            o, a = tp.tomui(v)
            data.append(a)
            if o is not None: keep.append(o)
        for v in args[len(self.__argstp):]:
            data.append(long(v))
            keep.append(v)
       
        return self.__retconv(obj._do(self.__id, tuple(data)))

    def call(self, obj, *args):
        if len(args) != len(self.__argstp):
            raise AttributeError("method accepts only %u argument(s), get %u"
                                 % (len(self.__argstp), len(args)))
        data = []
        keep = []
        for tp, v in zip(self.__argstp, args):
            o, a = tp.tomui(v)
            data.append(a)
            if o is not Non: keep.append(o)

        return self.__retconv(obj._do(self.__id, tuple(data)))
            
    def call0(self, obj):
        return self.__retconv(obj._do(self.__id))

    def call1(self, obj, data):
        o, x = self.__argstp.tomui(data)
        return self.__retconv(obj._do1(self.__id, long(x)))

    @property
    def id(self): return self.__id

#===============================================================================

class Event(object):
    def __init__(self, source):
        self.source = source

    @staticmethod
    def noevent(func):
        @functools.wraps(func)
        def wrapper(self, evt, *args):
            return func(self, *args)
        return wrapper

class InuitionEvent(_muimaster.EventHandler, Event):
    def __init__(self, source):
        _muimaster.EventHandler.__init__(self)
        Event.__init__(self, source)


class AttributeEvent(Event):
    def __init__(self, source, value, not_value):
        Event.__init__(self, source)
        self.value = value
        self.not_value = not_value
        

class AttributeNotify(object):
    def __init__(self, trigvalue, cb, args):
        self.cb = cb
        self.args = args
        self.trigvalue = trigvalue

    def __call__(self, e):
        return self.cb(e, *self.args)

#===============================================================================

class MUIMetaClass(type):
    def __new__(metacl, name, bases, dct):
        clid = dct.pop('CLASSID', None)
        if not clid:
            clid = [base._mclassid for base in bases if hasattr(base, '_mclassid')]
            if not len(clid):
                raise TypeError("No valid MUI class name found")
            clid = clid[0]

        dct['_mclassid'] = clid
        dct['isMCC'] = bool(dct.pop('MCC', False))

        # cache attributes/methods
        attrs = {}
        attrs_id = {}
        meths = {}
        meths_id = {}
        
        for k, v in dct.iteritems():
            if isinstance(v, MAttribute):
                attrs[k] = v
                attrs_id[v.id] = v
            elif isinstance(v, MMethod):
                meths[k] = v
                meths_id[v.id] = v
                
        dct['_pymui_attrs_'] = attrs
        dct['_pymui_attrs_id_'] = attrs_id
        dct['_pymui_meths_'] = meths
        dct['_pymui_meths_id_'] = meths_id
            
        # For super class accesses to methods and attributes,
        # add a version tagged with class name
        for k, v in attrs.iteritems():
           dct[name+'_'+k] = v
        for k, v in meths.iteritems():
           dct[name+'_'+k] = v

        return type.__new__(metacl, name, bases, dct)

#===============================================================================

class BOOPSIMixed:
    @classmethod
    def _getMA(cl, o):
        if type(o) is str:
            return cl._getMAByName(o)
        else:
            return cl._getMAByID(o)
        
    @classmethod
    def _getMAByName(cl, name):
        # lookup in class first
        try:
            return cl._pymui_attrs_[name]
        except KeyError:
            # lookup in super classes
            for b in cl.__bases__:
                try:
                    return b._getMAByName(name)
                except:
                    pass
        raise AttributeError("MUI attribute '%s' not found" % name)

    @classmethod
    def _getMAByID(cl, id):
        # lookup in class first
        try:
            return cl._pymui_attrs_id_[id]
        except KeyError:
            # lookup in super classes
            for b in cl.__bases__:
                try:
                    return b._getMAByID(id)
                except:
                    pass
        raise AttributeError("MUI attribute 0x%08x not found" % id)

    @classmethod
    def _getMM(cl, o):
        if type(o) is str:
            return cl._getMMByName(o)
        else:
            return cl._getMMByID(o)

    @classmethod
    def _getMMByName(cl, name):
        # lookup in class first
        try:
            return cl._pymui_meths_[name]
        except KeyError:
            # lookup in super classes
            for b in cl.__bases__:
                try:
                    return b._getMMByName(name)
                except:
                    pass
        raise AttributeError("MUI method '%s' not found" % name)

    @classmethod
    def _getMMByID(cl, id):
        # lookup in class first
        try:
            return cl._pymui_meths_id_[id]
        except KeyError:
            # lookup in super classes
            for b in cl.__bases__:
                try:
                    return b._getMMByID(id)
                except:
                    pass
        raise AttributeError("MUI method 0x%08x not found" % id)

    def GetAttr(self, attr):
        return self._getMA(attr).__get__(self)

    def SetAttr(self, *args, **kwds):
        if args:
            self._getMA(args[0]).__set__(self, args[1])
            
        for k in kwds:
            setattr(self, k, kwds[k])

    def DoMethod(self, mid, *args):
        """DoMethod(mid, *args) -> value
        """
        return self._getMM(mid)(self, *args)


################################################################################
#### Official Public Classes
################################################################################

class rootclass(PyMUIObject, BOOPSIMixed):
    """rootclass for all other PyMUI classes.

    ATTENTION: You can't create instance of this class!
    """

    __metaclass__ = MUIMetaClass
    CLASSID = "rootclass"

    # filter out parameters for the class C interface
    def __new__(cl, *args, **kwds):
        return super(rootclass, cl).__new__(cl)

    def __init__(self, **kwds):
        super(rootclass, self).__init__()

        self._keep_dict = {}
        self._notify_cbdict = {} 

        # Extra parameters overwrite local ones.
        kwds.update(kwds.pop('pymui_extra', {}))
        
        # A 'struct TagItem' array
        init_tags = (c_TagItem * (len(kwds)+1))()

        # Convert keywords into (attr, value) tuples
        for i, k in enumerate(kwds.keys()):
            attr = self._getMAByName(k)
            init_tags[i].ti_Tag = attr.id
            init_tags[i].ti_Data = attr.init(self, kwds[k])

        self._create(self._mclassid, ctypes.addressof(init_tags), self.__class__.isMCC)

    def AddChild(self, o):
        if getattr(o, '_parent', None) != None:
            raise RuntimeError("already attached")
        self._add(o)
        self._children.add(o) # incref the child object to not lost it during next GC

        # incref also the parent object to be sure that the MUI object remains valid
        # if the parent is disposed.
        # When the child will be deallocated, the PyMUI is decref this parent.
        o._parent = self

    def RemChild(self, o):
        if o not in self._children:
            raise RuntimeError("not attached yet")
        self._rem(o)
        self._children.remove(o)
        self._parent = None

#===============================================================================

class Notify(rootclass):
    CLASSID = MUIC_Notify

    ApplicationObject = MAttribute(MUIA_ApplicationObject , '..g', c_pObject)
    AppMessage        = MAttribute(MUIA_AppMessage        , '..g', c_APTR)
    HelpLine          = MAttribute(MUIA_HelpLine          , 'isg', c_LONG)
    HelpNode          = MAttribute(MUIA_HelpNode          , 'isg', c_STRPTR)
    NoNotify          = MAttribute(MUIA_NoNotify          , '.s.', c_BOOL)
    NoNotifyMethod    = MAttribute(MUIA_NoNotifyMethod    , '.s.', c_ULONG)
    ObjectID          = MAttribute(MUIA_ObjectID          , 'isg', c_ULONG)
    Parent            = MAttribute(MUIA_Parent            , '..g', c_pObject)
    Revision          = MAttribute(MUIA_Revision          , '..g', c_LONG)
    # forbidden: MUIA_UserData (intern usage)
    Version           = MAttribute(MUIA_Version           , '..g', c_LONG)

    def NNSet(self, attr, v):
        attr = self._getMA(attr)
        v, x = attr.ctype.tomui(v)
        self._nnset(attr.id, x)
        if attr.keep and v is not None: self._keep_dict[attr.id] = v

    def _notify_cb(self, a, v, nv):
        attr = self._getMAByID(a)
        v = attr.ctype.asobj(v)
        e = AttributeEvent(self, v, nv)
        for o in self._notify_cbdict[a]:
            if o.trigvalue == MUIV_EveryTime or o.trigvalue == v:
                if o(e): return

    def Notify(self, attr, trigvalue=MUIV_EveryTime, callback=None, *_args, **kwds):
        assert callable(callback)
        attr = self._getMA(attr)
        assert 's' in attr.isg or 'g' in attr.isg
        event = AttributeNotify(trigvalue, callback, kwds.get('args', _args))
        if attr.id in self._notify_cbdict:
            self._notify_cbdict[attr.id].append(event)
        else:
            self._notify(attr.id)
            self._notify_cbdict[attr.id] = [ event ]

    def KillApp(self):
        self.ApplicationObject.Quit()

#===============================================================================

class Family(Notify):
    CLASSID = MUIC_Family
    
    Child = MAttribute(MUIA_Family_Child, 'i..', c_pObject)
    List  = MAttribute(MUIA_Family_List , '..g', c_pMinList)

    def __init__(self, **kwds):
        child = kwds.pop('Child', None)
        super(Family, self).__init__(**kwds)
        if child:
            self.AddTail(child)

    def AddHead(self, o):
        assert isinstance(o, (Family, c_pObject))
        x = self._do1(MUIM_Family_AddHead, long(c_pObject(o)))
        if isinstance(o, Family):
            self._children.add(o)
            o._parent = self
        return x

    def AddTail(self, o):
        assert isinstance(o, (Family, c_pObject))
        x = self._do1(MUIM_Family_AddTail, long(c_pObject(o)))
        if isinstance(o, Family):
            self._children.add(o)
            o._parent = self
        return x

    def Insert(self, o, p):
        assert p in self._children
        assert isinstance(o, (Family, c_pObject))
        x = self._do(MUIM_Family_Insert, (long(c_pObject(o)), long(c_pObject(p))))
        if isinstance(o, Family):
            self._children.add(o)
            o._parent = self
        return x

    def Remove(self, o):
        assert o in self._children
        x = self._do1(MUIM_Family_Remove, long(c_pObject(o)))
        self._children.remove(o)
        o._parent = None
        return x

    def Sort(self, *args):
        a = (c_pObject * (len(args)+1))() # transitive object, not needed to be keep
        a[:] = args
        return self._do1(MUIM_Family_Sort, ctypes.addressof(a))

    def Transfer(self, f):
        if isinstance(f, Family):
            x = self._do1(MUIM_Family_Transfer, long(c_pObject(o)))
            f._children.update(self._children)
            for o in self._children:
                o._parent = f
            del self._children
        elif isinstance(f, c_pObject):
            x = self._do1(MUIM_Family_Transfer, long(o))
        else:
            raise TypeError("Family or c_pObject instance waited as argument, not %s" % type(f))
        return x

#===============================================================================

class Menustrip(Family):
    CLASSID = MUIC_Menustrip
    
    Enabled = MAttribute(MUIA_Menustrip_Enabled, 'isg', c_BOOL)

    InitChange = MMethod(MUIM_Menustrip_InitChange)
    ExitChange = MMethod(MUIM_Menustrip_ExitChange)
    Popup      = MMethod(MUIM_Menustrip_Popup, (c_pObject, c_ULONG, c_LONG, c_LONG))

    def __init__(self, items=None, **kwds):
        super(Menustrip, self).__init__(**kwds)
        if not items: return
        if hasattr(items, '__iter__'):
            for x in items:
                self.AddTail(x)
        else:
            self.AddTail(items)

    @Popup.alias
    def Popup(self, meth, parent, x, y, flags=0):
        meth(self, parent, flags, x, y)

#===============================================================================

class Menu(Family):
    CLASSID = MUIC_Menu
    
    Enabled = MAttribute(MUIA_Menu_Enabled, 'isg', c_BOOL)
    Title   = MAttribute(MUIA_Menu_Title  , 'isg', c_STRPTR)

    def __init__(self, Title, **kwds):
        super(Menu, self).__init__(Title=Title, **kwds)

#===============================================================================

class Menuitem(Family):
    CLASSID = MUIC_Menuitem
    
    Checked       = MAttribute(MUIA_Menuitem_Checked       , 'isg', c_BOOL)
    Checkit       = MAttribute(MUIA_Menuitem_Checkit       , 'isg', c_BOOL)
    CommandString = MAttribute(MUIA_Menuitem_CommandString , 'isg', c_BOOL)
    CopyStrings   = MAttribute(MUIA_Menuitem_CopyStrings   , 'i..', c_BOOL)
    Enabled       = MAttribute(MUIA_Menuitem_Enabled       , 'isg', c_BOOL)
    Exclude       = MAttribute(MUIA_Menuitem_Exclude       , 'isg', c_LONG)
    Shortcut      = MAttribute(MUIA_Menuitem_Shortcut      , 'isg', c_STRPTR)
    Title         = MAttribute(MUIA_Menuitem_Title         , 'isg', c_MenuitemTitle)
    Toggle        = MAttribute(MUIA_Menuitem_Toggle        , 'isg', c_BOOL)
    Trigger       = MAttribute(MUIA_Menuitem_Trigger       , '..g', c_APTR)

    def __init__(self, Title, Shortcut=None, **kwds):
        if Shortcut:
            kwds['Shortcut'] = Shortcut
            if len(Shortcut) > 1:
                kwds['CommandString'] = True
            else:
                kwds['CommandString'] = False
                
        if Title == '-': Title = NM_BARLABEL
        
        super(Menuitem, self).__init__(Title=Title, **kwds)

    def Bind(self, callback, *args):
        self.Notify('Trigger', callback=lambda x: callback(), args=args)

#===============================================================================

class Application(Notify):
    CLASSID = MUIC_Application

    Active         = MAttribute(MUIA_Application_Active         , 'isg', c_BOOL)
    Author         = MAttribute(MUIA_Application_Author         , 'i.g', c_STRPTR)
    Base           = MAttribute(MUIA_Application_Base           , 'i.g', c_STRPTR)
    Broker         = MAttribute(MUIA_Application_Broker         , '..g', c_APTR)
    BrokerHook     = MAttribute(MUIA_Application_BrokerHook     , 'isg', c_APTR)
    BrokerPort     = MAttribute(MUIA_Application_BrokerPort     , '..g', c_APTR)
    BrokerPri      = MAttribute(MUIA_Application_BrokerPri      , 'i.g', c_LONG)
    Commands       = MAttribute(MUIA_Application_Commands       , 'isg', c_APTR)
    Copyright      = MAttribute(MUIA_Application_Copyright      , 'i.g', c_STRPTR)
    Description    = MAttribute(MUIA_Application_Description    , 'i.g', c_STRPTR)
    DiskObject     = MAttribute(MUIA_Application_DiskObject     , 'isg', c_APTR)
    DoubleStart    = MAttribute(MUIA_Application_DoubleStart    , '..g', c_BOOL)
    DropObject     = MAttribute(MUIA_Application_DropObject     , 'is.', c_pObject)
    ForceQuit      = MAttribute(MUIA_Application_ForceQuit      , '..g', c_BOOL)
    HelpFile       = MAttribute(MUIA_Application_HelpFile       , 'isg', c_STRPTR)
    Iconified      = MAttribute(MUIA_Application_Iconified      , '.sg', c_BOOL)
    MenuAction     = MAttribute(MUIA_Application_MenuAction     , '..g', c_ULONG)
    MenuHelp       = MAttribute(MUIA_Application_MenuHelp       , '..g', c_ULONG)
    Menustrip      = MAttribute(MUIA_Application_Menustrip      , 'i..', c_pObject)
    RexxHook       = MAttribute(MUIA_Application_RexxHook       , 'isg', c_APTR)
    RexxMsg        = MAttribute(MUIA_Application_RexxMsg        , '..g', c_APTR)
    RexxString     = MAttribute(MUIA_Application_RexxString     , '.s.', c_STRPTR)
    SingleTask     = MAttribute(MUIA_Application_SingleTask     , 'i..', c_BOOL)
    Sleep          = MAttribute(MUIA_Application_Sleep          , '.s.', c_BOOL)
    Title          = MAttribute(MUIA_Application_Title          , 'i.g', c_STRPTR)
    UseCommodities = MAttribute(MUIA_Application_UseCommodities , 'i..', c_BOOL)
    UsedClasses    = MAttribute(MUIA_Application_UsedClasses    , 'isg', c_pSTRPTR)
    UseRexx        = MAttribute(MUIA_Application_UseRexx        , 'i..', c_BOOL)
    Version        = MAttribute(MUIA_Application_Version        , 'i.g', c_STRPTR)
    Window         = MAttribute(MUIA_Application_Window         , 'i..', c_pObject)
    WindowList     = MAttribute(MUIA_Application_WindowList     , '..g', c_pList)

    AboutMUI         = MMethod(MUIM_Application_AboutMUI        , c_pObject)
    #AddInputHandler
    #BuildSettingsPanel
    CheckRefresh     = MMethod(MUIM_Application_CheckRefresh)
    #DefaultConfigItem
    InputBuffered    = MMethod(MUIM_Application_InputBuffered)
    Load             = MMethod(MUIM_Application_Load             , c_STRPTR)
    NewInput         = MMethod(MUIM_Application_NewInput         , c_ULONG.pointertype(), rettype=c_ULONG)
    OpenConfigWindow = MMethod(MUIM_Application_OpenConfigWindow , (c_ULONG, c_STRPTR))
    PushMethod       = MMethod(MUIM_Application_PushMethod       , (c_pObject, c_LONG), varargs=True)
    #RemInputHandler
    ReturnID         = MMethod(MUIM_Application_ReturnID         , c_ULONG)
    Save             = MMethod(MUIM_Application_Save             , c_STRPTR)
    ShowHelp         = MMethod(MUIM_Application_ShowHelp         , (c_pObject, c_STRPTR, c_STRPTR, c_LONG))

    def __init__(self, **kwds):
        win = kwds.pop('Window', None)
        super(Application, self).__init__(**kwds)

        # Add Window PyMUIObject passed as argument
        if win: self.AddChild(win)

    def AddChild(self, win):
        assert isinstance(win, Window)
        super(Application, self).AddChild(win)

    def RemChild(self, win):
        win.CloseWindow()
        super(Application, self).RemChild(win)

    def Run(self):
        _muimaster.mainloop(self)

    def Quit(self):
        self.ReturnID(MUIV_Application_ReturnID_Quit)

    @AboutMUI.alias
    def AboutMUI(self, meth, refwin=None):
        meth(self, refwin)

#===============================================================================

class Window(Notify):
    CLASSID = MUIC_Window
    
    def __postSetRootObject(self, attr, o):
        if self._children:
            self._children.pop()._parent = None
            self._children.clear()
        if o is not None:
            o._parent = self
            self._children.add(o)

    def __checkForApp(self, attr, o):
        if not self.ApplicationObject:
            raise AttributeError("Window not linked to an application yet")
        return o

    Activate                = MAttribute(MUIA_Window_Activate                , 'isg', c_BOOL)
    ActiveObject            = MAttribute(MUIA_Window_ActiveObject            , '.sg', c_pObject)
    AltHeight               = MAttribute(MUIA_Window_AltHeight               , 'i.g', c_LONG)
    AltLeftEdge             = MAttribute(MUIA_Window_AltLeftEdge             , 'i.g', c_LONG)
    AltTopEdge              = MAttribute(MUIA_Window_AltTopEdge              , 'i.g', c_LONG)
    AltWidth                = MAttribute(MUIA_Window_AltWidth                , 'i.g', c_LONG)
    AppWindow               = MAttribute(MUIA_Window_AppWindow               , 'i..', c_BOOL)
    Backdrop                = MAttribute(MUIA_Window_Backdrop                , 'i..', c_BOOL)
    Borderless              = MAttribute(MUIA_Window_Borderless              , 'i..', c_BOOL)
    CloseGadget             = MAttribute(MUIA_Window_CloseGadget             , 'i..', c_BOOL)
    CloseRequest            = MAttribute(MUIA_Window_CloseRequest            , '..g', c_BOOL)
    DefaultObject           = MAttribute(MUIA_Window_DefaultObject           , 'isg', c_pObject)
    DepthGadget             = MAttribute(MUIA_Window_DepthGadget             , 'i..', c_BOOL)
    DisableKeys             = MAttribute(MUIA_Window_DisableKeys             , 'isg', c_LONG)
    DragBar                 = MAttribute(MUIA_Window_DragBar                 , 'i..', c_BOOL)
    FancyDrawing            = MAttribute(MUIA_Window_FancyDrawing            , 'isg', c_BOOL)
    Height                  = MAttribute(MUIA_Window_Height                  , 'i.g', c_LONG)
    ID                      = MAttribute(MUIA_Window_ID                      , 'isg', c_ULONG)
    InputEvent              = MAttribute(MUIA_Window_InputEvent              , '..g', c_APTR)
    IsSubWindow             = MAttribute(MUIA_Window_IsSubWindow             , 'isg', c_BOOL)
    LeftEdge                = MAttribute(MUIA_Window_LeftEdge                , 'i.g', c_LONG)
    MenuAction              = MAttribute(MUIA_Window_MenuAction              , 'isg', c_LONG)
    Menustrip               = MAttribute(MUIA_Window_Menustrip               , 'i.g', c_pObject)
    MouseObject             = MAttribute(MUIA_Window_MouseObject             , '..g', c_pObject)
    NeedsMouseObject        = MAttribute(MUIA_Window_NeedsMouseObject        , 'i..', c_BOOL)
    NoMenus                 = MAttribute(MUIA_Window_NoMenus                 , 'is.', c_BOOL)
    Open                    = MAttribute(MUIA_Window_Open                    , '.sg', c_BOOL,
                                         preSet=__checkForApp)
    PublicScreen            = MAttribute(MUIA_Window_PublicScreen            , 'isg', c_STRPTR)
    RefWindow               = MAttribute(MUIA_Window_RefWindow               , 'is.', c_pObject)
    RootObject              = MAttribute(MUIA_Window_RootObject              , 'isg', c_pObject,
                                         postSet=__postSetRootObject)
    Screen                  = MAttribute(MUIA_Window_Screen                  , 'isg', c_APTR)
    ScreenTitle             = MAttribute(MUIA_Window_ScreenTitle             , 'isg', c_STRPTR)
    SizeGadget              = MAttribute(MUIA_Window_SizeGadget              , 'i..', c_BOOL)
    SizeRight               = MAttribute(MUIA_Window_SizeRight               , 'i..', c_BOOL)
    Sleep                   = MAttribute(MUIA_Window_Sleep                   , '.sg', c_BOOL)
    TabletMessages          = MAttribute(MUIA_Window_TabletMessages          , 'i.g', c_BOOL)
    Title                   = MAttribute(MUIA_Window_Title                   , 'isg', c_STRPTR)
    TopEdge                 = MAttribute(MUIA_Window_TopEdge                 , 'i.g', c_LONG)
    UseBottomBorderScroller = MAttribute(MUIA_Window_UseBottomBorderScroller , 'isg', c_BOOL)
    UseLeftBorderScroller   = MAttribute(MUIA_Window_UseLeftBorderScroller   , 'isg', c_BOOL)
    UseRightBorderScroller  = MAttribute(MUIA_Window_UseRightBorderScroller  , 'isg', c_BOOL)
    Width                   = MAttribute(MUIA_Window_Width                   , 'i.g', c_LONG)
    Window                  = MAttribute(MUIA_Window_Window                  , '..g', c_APTR)

    __idset = set()

    __attr_map = { 'LeftEdge': { 'centered': MUIV_Window_LeftEdge_Centered,
                                 'moused':   MUIV_Window_LeftEdge_Moused },
                   'TopEdge' : { 'centered': MUIV_Window_TopEdge_Centered,
                                 'moused':   MUIV_Window_TopEdge_Moused },
                   'Height':   { 'default':  MUIV_Window_Height_Default,
                                 'scaled':   MUIV_Window_Height_Scaled },
                   'Width':    { 'default':  MUIV_Window_Width_Default,
                                 'scaled':   MUIV_Window_Width_Scaled },
                   }

    @classmethod
    def __new_ID(cl, i=-1):
        if isinstance(i, basestring):
            i = -1 # XXX: ID bugged when id is string
        if i == -1:
            for i in xrange(1<<10):
                if i not in cl.__idset:
                    cl.__idset.add(i)
                    return i
            raise RuntimeError("No more availables IDs")
        else:
            # use address of string as ID integer, but store the string
            if isinstance(i, basestring):
                s = i
                i = ctypes.addressof(c_STRPTR(i))
            if i in cl.__idset:
                raise RuntimeError("ID %u already taken" % i)
            if s:
                cl.__idset.add(s)
                return i

        cl.__idset.add(i)
        return i

    def __init__(self, Title=None, ID=None, **kwds):
        """Window(Title=None, ID=None, **kwds) -> Window Instance.

        Window MUI class.

        === Specifics parameters ===
        
        - Title: (optional) window title to use. None or not set doesn't touch the attribute.

        - ID: (optional) can be an integer (LONG) or a string.
          If not given, set to None, zero or empty string, ID attribute is not touched.
          If set to -1, a new unique ID is automatically set for you.

        === Special PyMUI attributes (optionals) ===
        
        - LeftEdge      : positive integer as in MUI or a string: 'centered' or 'moused'.
        - RightEdge     : window rigth edge on screen: integer [0-2147482648].
        - TopEdge       : positive integer as in MUI or a string: 'centered' or 'moused'.
        - TopDeltaEdge  : window appears n pixels below the screens title bar, n integer [0-996].
        - BottomEdge    : window bottom edge on screen: integer [0-2147482648].
        - Width         : positive integer as in MUI or a string: 'default' or 'scaled'.
        - WidthMinMax   :
        - WidthScreen   :
        - WidthVisible  :
        - Height        : positive integer as in MUI or a string: 'default' or 'scaled'.
        - HeightMinMax  :
        - HeightScreen  :
        - HeightVisible :
        - Position      : a 2-tuple for (LeftEdge, TopEdge) (overwritten by LeftEdge and TopEdge).
        - Size          : a 2-tuple for (Width, Height) (overwritten by Width and Height).
        - CloseOnRequest: Set it to True add a notification to close the window
                          when CloseRequest attribute is set to True. False by default.

        === Notes ===

        A RootObject is mandatory to create a Window on MUI.
        PyMUI uses a simple Rectangle object by default.
        """
        self.__app = None

        # Auto Window ID handling
        if ID:
            kwds['ID'] = self.__new_ID(ID)

        # A root object is mandatory to create the window
        # Use a dummy rectangle if nothing given
        if 'RootObject' not in kwds:
            kwds['RootObject'] = Rectangle()

        if Title is not None:
            kwds['Title'] = Title

        if 'Position' in kwds:
            kwds['LeftEdge'], kwds['TopEdge'] = kwds.pop('Position')

        if 'LeftEdge' in kwds:
            x = kwds.get('LeftEdge')
            d = self.__attr_map['LeftEdge']
            kwds['LeftEdge'] = d[x] if x in d else x
        elif 'RightEdge' in kwds:
            kwds['LeftEdge'] = -1000 - kwds.pop('RightEdge')

        if 'TopEdge' in kwds:
            x = kwds.get('TopEdge')
            d = self.__attr_map['TopEdge']
            kwds['TopEdge'] = d[x] if x in d else x
        elif 'BottomEdge' in kwds:
            kwds['TopEdge'] = -1000 - kwds.pop('BottomEdge')
        elif 'TopDeltaEdge' in kwds:
            kwds['TopEdge'] = -3 - kwds.pop('TopDeltaEdge')

        if 'Size' in kwds:
            kwds['Width'], kwds['Height'] = kwds.pop('Size')

        if 'Height' in kwds:
            x = kwds.get('Height')
            d = self.__attr_map['Height']
            kwds['Height'] = d[x] if x in d else x
        elif 'HeightMinMax' in kwds:
            kwds['Height'] = 0 - max(min(kwds.pop('HeightMinMax'), 100), 0)
        elif 'HeightScreen' in kwds:
            kwds['Height'] = -200 - max(min(kwds.pop('HeightScreen'), 100), 0)
        elif 'HeightVisible' in kwds:
            kwds['Height'] = -100 - max(min(kwds.pop('HeightVisible'), 100), 0)

        if 'Width' in kwds:
            x = kwds.get('Width')
            d = self.__attr_map['Width']
            kwds['Width'] = d[x] if x in d else x
        elif 'WidthMinMax' in kwds:
            kwds['Width'] = 0 - max(min(kwds.pop('WidthMinMax'), 100), 0)
        elif 'WidthScreen' in kwds:
            kwds['Width'] = -200 - max(min(kwds.pop('WidthScreen'), 100), 0)
        elif 'WidthVisible' in kwds:
            kwds['Width'] = -100 - max(min(kwds.pop('WidthVisible'), 100), 0)

        autoclose = kwds.pop('CloseOnReq', False)

        super(Window, self).__init__(**kwds)
        ro = self.RootObject
        self._children.add(ro)
        ro._parent = self

        if autoclose:
            self.Notify('CloseRequest', True, lambda e: self.CloseWindow())

    def OpenWindow(self):
        self.Open = True

    def CloseWindow(self):
        self.Open = False

    pointer = property(fset=_muimaster._setwinpointer, doc="Window mouse pointer")

#===============================================================================

class AboutMUI(Window):
    CLASSID = MUIC_Aboutmui

    Application = MAttribute(MUIA_Aboutmui_Application, 'i..', c_pObject)

    def __init__(self, app, **kwds):
        super(AboutMUI, self).__init__(Application=app, RefWindow=kwds.pop('RefWindow', None), **kwds)
        # We don't call app.AddChild() because this object do it itself during its OM_NEW
        
#===============================================================================

class Area(Notify):
    CLASSID = MUIC_Area

    Background         = MAttribute(MUIA_Background         , 'is.', c_ImageSpec)
    BottomEdge         = MAttribute(MUIA_BottomEdge         , '..g', c_LONG)
    ContextMenu        = MAttribute(MUIA_ContextMenu        , 'isg', c_pObject)
    ContextMenuTrigger = MAttribute(MUIA_ContextMenuTrigger , '..g', c_pObject)
    ControlChar        = MAttribute(MUIA_ControlChar        , 'isg', c_CHAR)
    CycleChain         = MAttribute(MUIA_CycleChain         , 'isg', c_LONG)
    Disabled           = MAttribute(MUIA_Disabled           , 'isg', c_BOOL)
    DoubleBuffer       = MAttribute(MUIA_DoubleBuffer       , 'isg', c_BOOL)
    Draggable          = MAttribute(MUIA_Draggable          , 'isg', c_BOOL)
    Dropable           = MAttribute(MUIA_Dropable           , 'isg', c_BOOL)
    FillArea           = MAttribute(MUIA_FillArea           , 'is.', c_BOOL)
    FixHeight          = MAttribute(MUIA_FixHeight          , 'i..', c_LONG)
    FixHeightTxt       = MAttribute(MUIA_FixHeightTxt       , 'i..', c_STRPTR)
    FixWidth           = MAttribute(MUIA_FixWidth           , 'i..', c_LONG)
    FixWidthTxt        = MAttribute(MUIA_FixWidthTxt        , 'i..', c_STRPTR)
    Font               = MAttribute(MUIA_Font               , 'i.g', c_pTextFont)
    Frame              = MAttribute(MUIA_Frame              , 'i..', c_LONG)
    FrameDynamic       = MAttribute(MUIA_FrameDynamic       , 'isg', c_BOOL)
    FramePhantomHoriz  = MAttribute(MUIA_FramePhantomHoriz  , 'i..', c_BOOL)
    FrameTitle         = MAttribute(MUIA_FrameTitle         , 'i..', c_STRPTR)
    FrameVisible       = MAttribute(MUIA_FrameVisible       , 'isg', c_BOOL)
    Height             = MAttribute(MUIA_Height             , '..g', c_LONG)
    HorizDisappear     = MAttribute(MUIA_HorizDisappear     , 'isg', c_LONG)
    HorizWeight        = MAttribute(MUIA_HorizWeight        , 'isg', c_LONG)
    InnerBottom        = MAttribute(MUIA_InnerBottom        , 'i.g', c_LONG)
    InnerLeft          = MAttribute(MUIA_InnerLeft          , 'i.g', c_LONG)
    InnerRight         = MAttribute(MUIA_InnerRight         , 'i.g', c_LONG)
    InnerTop           = MAttribute(MUIA_InnerTop           , 'i.g', c_LONG)
    InputMode          = MAttribute(MUIA_InputMode          , 'i..', c_LONG)
    LeftEdge           = MAttribute(MUIA_LeftEdge           , '..g', c_LONG)
    MaxHeight          = MAttribute(MUIA_MaxHeight          , 'i..', c_LONG)
    MaxWidth           = MAttribute(MUIA_MaxWidth           , 'i..', c_LONG)
    Pressed            = MAttribute(MUIA_Pressed            , '..g', c_BOOL)
    RightEdge          = MAttribute(MUIA_RightEdge          , '..g', c_LONG)
    Selected           = MAttribute(MUIA_Selected           , 'isg', c_BOOL)
    ShortHelp          = MAttribute(MUIA_ShortHelp          , 'isg', c_STRPTR)
    ShowMe             = MAttribute(MUIA_ShowMe             , 'isg', c_BOOL)
    ShowSelState       = MAttribute(MUIA_ShowSelState       , 'i..', c_BOOL)
    Timer              = MAttribute(MUIA_Timer              , '..g', c_LONG)
    TopEdge            = MAttribute(MUIA_TopEdge            , '..g', c_LONG)
    VertDisappear      = MAttribute(MUIA_VertDisappear      , 'isg', c_LONG)
    VertWeight         = MAttribute(MUIA_VertWeight         , 'isg', c_LONG)
    Weight             = MAttribute(MUIA_Weight             , 'i..', c_LONG)
    Width              = MAttribute(MUIA_Width              , '..g', c_LONG)
    Window             = MAttribute(MUIA_Window             , '..g', c_APTR)
    WindowObject       = MAttribute(MUIA_WindowObject       , '..g', c_pObject)

    def __init__(self, **kwds):
        v = kwds.pop('InnerSpacing', None)
        if v is not None:
            kwds['InnerLeft'], kwds['InnerRight'], kwds['InnerTop'], kwds['InnerBottom'] = v
        g = globals()
        frame = kwds.get('Frame', None)
        if isinstance(frame, str):
            try:
                kwds['Frame'] = g['MUIV_Frame_'+frame]
            except KeyError:
                raise ValueError("Unknown Frame name: MUIV_Frame_%s" % frame)
        imode = kwds.get('InputMode', None)
        if isinstance(imode, str):
            try:
                kwds['InputMode'] = g['MUIV_InputMode_'+imode]
            except KeyError:
                raise ValueError("Unknown InputMode name: MUIV_InputMode_%s" % imode)
        bg = kwds.get('Background', None)
        if isinstance(bg, str) and 'MUII_'+bg in g:
            kwds['Background'] = g['MUII_'+bg]

        super(Area, self).__init__(**kwds)

#===============================================================================

class Dtpic(Area):
    CLASSID = MUIC_Dtpic
    
    Name = MAttribute(MUIA_Dtpic_Name, 'isg',  c_STRPTR)

    def __init__(self, Name=None, **kwds):
        if Name: kwds['Name'] = Name
        super(Dtpic, self).__init__(**kwds)

#===============================================================================

class Rectangle(Area):
    CLASSID = MUIC_Rectangle

    BarTitle = MAttribute(MUIA_Rectangle_BarTitle, 'i.g', c_STRPTR)
    HBar     = MAttribute(MUIA_Rectangle_HBar,     'i.g', c_BOOL)
    VBar     = MAttribute(MUIA_Rectangle_VBar,     'i.g', c_BOOL)

    # Factory class methods

    @classmethod
    def mkHVSpace(cl):
        return cl()

    @classmethod
    def mkHSpace(cl, x):
        return cl(VertWeight=x)

    @classmethod
    def mkVSpace(cl, x):
        return cl(HorizWeight=x)

    @classmethod
    def mkHCenter(cl, o):
        g = Group.HGroup(Spacing=0)
        g.AddChild(cl.HSpace(0), o, cl.HSpace(0))
        return g

    @classmethod
    def mkVCenter(cl, o):
        g = Group.VGroup(Spacing=0)
        return g.AddChild(cl.VSpace(0), o, cl.VSpace(0))

    @classmethod
    def mkHBar(cl, space):
        return cl(HBar=True, InnerTop=space, InnerBottom=space, VertWeight=0)

    @classmethod
    def mkVBar(cl, space):
        return cl(HBar=True, InnerLeft=space, InnerRight=space, HorizWeight=0)

HVSpace = Rectangle.mkHVSpace
HSpace  = Rectangle.mkHSpace
VSpace  = Rectangle.mkVSpace
HCenter = Rectangle.mkHCenter
VCenter = Rectangle.mkVCenter
HBar    = Rectangle.mkHBar
VBar    = Rectangle.mkVBar

#===============================================================================

class Balance(Area):
    CLASSID = MUIC_Balance
    
    Quiet = MAttribute(MUIA_Balance_Quiet, 'i..', c_LONG)

#===============================================================================

class Image(Area):
    CLASSID = MUIC_Image
    
    FontMatch       = MAttribute(MUIA_Image_FontMatch       , 'i..', c_BOOL)
    FontMatchHeight = MAttribute(MUIA_Image_FontMatchHeight , 'i..', c_BOOL)
    FontMatchWidth  = MAttribute(MUIA_Image_FontMatchWidth  , 'i..', c_BOOL)
    FreeHoriz       = MAttribute(MUIA_Image_FreeHoriz       , 'i..', c_BOOL)
    FreeVert        = MAttribute(MUIA_Image_FreeVert        , 'i..', c_BOOL)
    OldImage        = MAttribute(MUIA_Image_OldImage        , 'i..', c_APTR)
    Spec            = MAttribute(MUIA_Image_Spec            , 'i..', c_ImageSpec)
    State           = MAttribute(MUIA_Image_State           , 'is.', c_LONG)

    @classmethod
    def CheckMark(cl, selected=False, key=None):
        kwds = {}
        if key is not None:
            kwds['ControlChar'] = key
            
        return cl(Frame='ImageButton',
                  Background='ButtonBack', 
                  InputMode='Toggle',
                  Spec=MUII_CheckMark,
                  FreeVert=True,
                  Selected=selected,
                  ShowSelState=False,
                  **kwds)

CheckMark = Image.CheckMark

#===============================================================================

class Bitmap(Area):
    CLASSID = MUIC_Bitmap
    # TODO

#===============================================================================

class Bodychunk(Bitmap):
    CLASSID = MUIC_Bodychunk
    # TODO

#===============================================================================

class Text(Area):
    CLASSID = MUIC_Text

    Contents        = MAttribute(MUIA_Text_Contents,    'isg', c_STRPTR)
    ControlChar     = MAttribute(MUIA_Text_ControlChar, 'isg', c_CHAR)
    Copy            = MAttribute(MUIA_Text_Copy,        'isg', c_BOOL)
    HiChar          = MAttribute(MUIA_Text_HiChar,      'isg', c_CHAR)
    PreParse        = MAttribute(MUIA_Text_PreParse,    'i..', c_STRPTR)
    SetMax          = MAttribute(MUIA_Text_SetMax,      'i..', c_BOOL)
    SetMin          = MAttribute(MUIA_Text_SetMin,      'i..', c_BOOL)
    SetVMax         = MAttribute(MUIA_Text_SetVMax,     'is.', c_BOOL)
    Shorten         = MAttribute(MUIA_Text_Shorten,     'isg', c_LONG)
    Shortened       = MAttribute(MUIA_Text_Shortened,   '..g', c_BOOL)

    def __init__(self, Contents='', **kwds):
        super(Text, self).__init__(Contents=Contents, **kwds)

    # Factory class methods

    @classmethod
    def KeyButton(cl, label, key=None):
        kwds = dict(Contents=label,
                    Font=MUIV_Font_Button,
                    Frame=MUIV_Frame_Button,
                    PreParse=MUIX_C,
                    InputMode=MUIV_InputMode_RelVerify,
                    Background=MUII_ButtonBack)
        if key:
            kwds['HiChar'] = key
            kwds['ControlChar'] = key
        return cl(**kwds)

    ALIGN_MAP = {'r': MUIX_R, 'l': MUIX_L, 'c': MUIX_C}

    @classmethod
    def Label(cl, label, align='r'):
        return cl(Contents=label, PreParse=Text.ALIGN_MAP.get(align.lower(), 'r'), Weight=0)

    @classmethod
    def FreeLabel(cl, label, align='r'):
        return cl(Contents=label, PreParse=Text.ALIGN_MAP.get(align.lower(), 'r'))

KeyButton = Text.KeyButton
SimpleButton = functools.partial(Text.KeyButton, key=None)
Label = Text.Label
LLabel = functools.partial(Label, align='l')
CLabel = functools.partial(Label, align='c')
FreeLabel = Text.FreeLabel
LFreeLabel = functools.partial(FreeLabel, align='l')
CFreeLabel = functools.partial(FreeLabel, align='c')

#===============================================================================

class Gadget(Area):
    CLASSID = MUIC_Gadget
    
    Gadget = MAttribute(MUIA_Gadget_Gadget, '..g', c_APTR),

#===============================================================================

class String(Area):
    CLASSID = MUIC_String

    Accept         = MAttribute(MUIA_String_Accept         , 'isg', c_STRPTR)
    Acknowledge    = MAttribute(MUIA_String_Acknowledge    , '..g', c_STRPTR)
    AdvanceOnCR    = MAttribute(MUIA_String_AdvanceOnCR    , 'isg', c_BOOL)
    AttachedList   = MAttribute(MUIA_String_AttachedList   , 'isg', c_pObject)
    BufferPos      = MAttribute(MUIA_String_BufferPos      , '.sg', c_LONG)
    Contents       = MAttribute(MUIA_String_Contents       , 'isg', c_STRPTR)
    DisplayPos     = MAttribute(MUIA_String_DisplayPos     , '.sg', c_LONG)
    EditHook       = MAttribute(MUIA_String_EditHook       , 'isg', c_APTR)
    Format         = MAttribute(MUIA_String_Format         , 'i.g', c_LONG)
    Integer        = MAttribute(MUIA_String_Integer        , 'isg', c_ULONG)
    LonelyEditHook = MAttribute(MUIA_String_LonelyEditHook , 'isg', c_BOOL)
    MaxLen         = MAttribute(MUIA_String_MaxLen         , 'i.g', c_LONG)
    Reject         = MAttribute(MUIA_String_Reject         , 'isg', c_STRPTR)
    Secret         = MAttribute(MUIA_String_Secret         , 'i.g', c_BOOL)

    ALIGN_MAP = {'r': MUIV_String_Format_Right, 'l': MUIV_String_Format_Left, 'c': MUIV_String_Format_Center}

    def __init__(self, Contents='', **kwds):
        format = kwds.get('Format', None)
        if format:
            kwds['Format'] = self.ALIGN_MAP.get(format, format)
        if Contents:
            kwds['Contents'] = Contents
        super(String, self).__init__(**kwds)

#===============================================================================

class Boopsi(String):
    CLASSID = MUIC_Boopsi
    # TODO

#===============================================================================

class Gauge(Area):
    CLASSID = MUIC_Gauge
    # TODO

#===============================================================================

class Scale(Area):
    CLASSID = MUIC_Scale
    # TODO

#===============================================================================

class Colorfield(Area):
    CLASSID = MUIC_Colorfield
    # TODO

#===============================================================================

class Numeric(Area):
    CLASSID = MUIC_Numeric

    CheckAllSizes = MAttribute(MUIA_Numeric_CheckAllSizes , 'isg', c_BOOL)
    Default       = MAttribute(MUIA_Numeric_Default       , 'isg', c_LONG)
    Format        = MAttribute(MUIA_Numeric_Format        , 'isg', c_STRPTR)
    Max           = MAttribute(MUIA_Numeric_Max           , 'isg', c_LONG)
    Min           = MAttribute(MUIA_Numeric_Min           , 'isg', c_LONG)
    Reverse       = MAttribute(MUIA_Numeric_Reverse       , 'isg', c_BOOL)
    RevLeftRight  = MAttribute(MUIA_Numeric_RevLeftRight  , 'isg', c_BOOL)
    RevUpDown     = MAttribute(MUIA_Numeric_RevUpDown     , 'isg', c_BOOL)
    Value         = MAttribute(MUIA_Numeric_Value         , 'isg', c_LONG)

#===============================================================================

class Knob(Numeric):
    CLASSID = MUIC_Knob

#===============================================================================

class Levelmeter(Numeric):
    CLASSID = MUIC_Levelmeter
    # TODO

#===============================================================================

class Numericbutton(Numeric):
    CLASSID = MUIC_Numericbutton

#===============================================================================

class Slider(Numeric):
    CLASSID = MUIC_Slider

    Horiz = MAttribute(MUIA_Slider_Horiz, 'isg', c_BOOL)
    Quiet = MAttribute(MUIA_Slider_Quiet, 'i..', c_BOOL)

#===============================================================================

class Prop(Slider):
    CLASSID = MUIC_Prop
    # TODO

#===============================================================================

class Frimagedisplay(Area):
    CLASSID = MUIC_Frimagedisplay

#===============================================================================

class Framedisplay(Frimagedisplay):
    CLASSID = MUIC_Framedisplay

#===============================================================================

class Imagedisplay(Frimagedisplay):
    CLASSID = MUIC_Imagedisplay

#===============================================================================

class Popimage(Imagedisplay):
    CLASSID = MUIC_Popimage

#===============================================================================

class Popframe(Framedisplay):
    CLASSID = MUIC_Popframe

#===============================================================================

class Popfrimage(Frimagedisplay):
    CLASSID = MUIC_Popfrimage

#===============================================================================

class Pendisplay(Area):
    CLASSID = MUIC_Pendisplay
    # TODO

#===============================================================================

class Poppen(Pendisplay):
    CLASSID = MUIC_Poppen

#===============================================================================

class Group(Area):
    CLASSID = MUIC_Group

    ActivePage   = MAttribute(MUIA_Group_ActivePage   , 'isg', c_LONG)
    Child        = MAttribute(MUIA_Group_Child        , 'i..', c_pObject)
    ChildList    = MAttribute(MUIA_Group_ChildList    , '..g', c_pList)
    Columns      = MAttribute(MUIA_Group_Columns      , 'is.', c_LONG)
    Horiz        = MAttribute(MUIA_Group_Horiz        , 'i..', c_BOOL)
    HorizSpacing = MAttribute(MUIA_Group_HorizSpacing , 'isg', c_LONG)
    LayoutHook   = MAttribute(MUIA_Group_LayoutHook   , 'i..', c_APTR)
    PageMode     = MAttribute(MUIA_Group_PageMode     , 'i..', c_BOOL)
    Rows         = MAttribute(MUIA_Group_Rows         , 'is.', c_LONG)
    SameHeight   = MAttribute(MUIA_Group_SameHeight   , 'i..', c_BOOL)
    SameSize     = MAttribute(MUIA_Group_SameSize     , 'i..', c_BOOL)
    SameWidth    = MAttribute(MUIA_Group_SameWidth    , 'i..', c_BOOL)
    Spacing      = MAttribute(MUIA_Group_Spacing      , 'is.', c_LONG)
    VertSpacing  = MAttribute(MUIA_Group_VertSpacing  , 'isg', c_LONG)

    InitChange   = MMethod(MUIM_Group_InitChange)
    ExitChange   = MMethod(MUIM_Group_ExitChange)

    def __init__(self, **kwds):
        child = kwds.pop('Child', None)
        
        x = kwds.pop('Title', None)
        if x:
            kwds.update(Frame=MUIV_Frame_Group, FrameTitle=x, Background=MUII_GroupBack)

        x = kwds.pop('InnerSpacing', None)
        if x:
            kwds.update(InnerLeft=x[0], InnerRight=x[0], InnerTop=x[1], InnerBottom=x[1])

        super(Group, self).__init__(**kwds)

        # Add RootObject PyMUIObject passed as argument
        if child:
            if hasattr(child, '__iter__'):
                self.AddChild(*child)
            else:
                self.AddChild(child)

    def AddChild(self, *children, **kwds):
        lock = kwds.get('lock', False)
        if lock: self.InitChange()
        try:
            for o in children:
                super(Group, self).AddChild(o)
        finally:
            if lock: self.ExitChange()

    def RemChild(self, *children, **kwds):
        lock = kwds.get('lock', False)
        if lock: self.InitChange()
        try:
            for o in children:
                super(Group, self).RemChild(o)
        finally:
            if lock: self.ExitChange()

    # Factory class methods

    @classmethod
    def HGroup(cl, **kwds):
        kwds['Horiz'] = True
        return cl(**kwds)

    @classmethod
    def VGroup(cl, **kwds):
        kwds['Horiz'] = False
        return cl(**kwds)

    @classmethod
    def ColGroup(cl, n, **kwds):
        kwds['Columns'] = n
        return cl(**kwds)

    @classmethod
    def RowGroup(cl, n, **kwds):
        kwds['Rows'] = n
        return cl(**kwds)

    @classmethod
    def PageGroup(cl, **kwds):
        kwds['PageMode'] = True
        return cl(**kwds)

HGroup = Group.HGroup
VGroup = Group.VGroup
ColGroup = Group.ColGroup
RowGroup = Group.RowGroup
PageGroup = Group.PageGroup

#===============================================================================

class List(Group):
    CLASSID = MUIC_List
    # TODO

#===============================================================================

class Floattext(List):
    CLASSID = MUIC_Floattext
    # TODO

#===============================================================================
class Volumelist(List):
    CLASSID = MUIC_Volumelist
    # TODO

#===============================================================================

class Dirlist(List):
    CLASSID = MUIC_Dirlist
    # TODO

#===============================================================================

class Selectgroup(Group):
    CLASSID = MUIC_Selectgroup

#===============================================================================

class Argstring(Group):
    CLASSID = MUIC_Argstring
    # TODO

#===============================================================================

class Menudisplay(Group):
    CLASSID = MUIC_Menudisplay

#===============================================================================

class Mccprefs(Group):
    CLASSID = MUIC_Mccprefs
    # TODO

#===============================================================================

class Register(Group):
    CLASSID = MUIC_Register
    # TODO

#===============================================================================

class Backgroundadjust(Area):
    CLASSID = MUIC_Backgroundadjust
    # TODO

#===============================================================================

class Penadjust(Backgroundadjust):
    CLASSID = MUIC_Penadjust
    # TODO

#===============================================================================

class Settingsgroup(Mccprefs):
    CLASSID = MUIC_Settingsgroup
    # TODO

#===============================================================================

class Settings(Group):
    CLASSID = MUIC_Settings

#===============================================================================

class Frameadjust(Group):
    CLASSID = MUIC_Frameadjust

#===============================================================================

class Virtgroup(Group):
    CLASSID = MUIC_Virtgroup

    Height = MAttribute(MUIA_Virtgroup_Height , '..g' , c_LONG)
    Input  = MAttribute(MUIA_Virtgroup_Input  , 'i..' , c_BOOL)
    Left   = MAttribute(MUIA_Virtgroup_Left   , 'isg' , c_LONG)
    Top    = MAttribute(MUIA_Virtgroup_Top    , 'isg' , c_LONG)
    Width  = MAttribute(MUIA_Virtgroup_Width  , '..g' , c_LONG)

    # Factory class methods

    @classmethod
    def HGroup(cl, **kwds):
        kwds['Horiz'] = True
        return cl(**kwds)

    @classmethod
    def VGroup(cl, **kwds):
        kwds['Horiz'] = False
        return cl(**kwds)

    @classmethod
    def ColGroup(cl, n, **kwds):
        kwds['Columns'] = n
        return cl(**kwds)

    @classmethod
    def RowGroup(cl, n, **kwds):
        kwds['Rows'] = n
        return cl(**kwds)

    @classmethod
    def PageGroup(cl, **kwds):
        kwds['PageMode'] = True
        return cl(**kwds)

HGroupV = Virtgroup.HGroup
VGroupV = Virtgroup.VGroup
ColGroupV = Virtgroup.ColGroup
RowGroupV = Virtgroup.RowGroup
PageGroupV = Virtgroup.PageGroup

#===============================================================================

class Scrollgroup(Group):
    CLASSID = MUIC_Scrollgroup

#===============================================================================

class Scrollbar(Group):
    CLASSID = MUIC_Scrollbar
    # TODO

#===============================================================================

class Listview(Group):
    CLASSID = MUIC_Listview
    # TODO

#===============================================================================

class Radio(Group):
    CLASSID = MUIC_Radio
    # TODO

#===============================================================================

class Cycle(Group):
    CLASSID = MUIC_Cycle

    Active  = MAttribute(MUIA_Cycle_Active  , 'isg', c_LONG)
    Entries = MAttribute(MUIA_Cycle_Entries , 'i..', c_pSTRPTR)

    def __init__(self, Entries, **kwds):
        super(Cycle, self).__init__(Entries=Entries, **kwds)

#===============================================================================

class Coloradjust(Group):
    CLASSID = MUIC_Coloradjust
    
    Blue   = MAttribute(MUIA_Coloradjust_Blue   , 'isg', c_ULONG)
    Green  = MAttribute(MUIA_Coloradjust_Green  , 'isg', c_ULONG)
    ModeID = MAttribute(MUIA_Coloradjust_ModeID , 'isg', c_ULONG)
    Red    = MAttribute(MUIA_Coloradjust_Red    , 'isg', c_ULONG)
    RGB    = MAttribute(MUIA_Coloradjust_RGB    , 'isg', c_ULONG.mkarray(3))

#===============================================================================

class Palette(Group):
    CLASSID = MUIC_Palette
    # TODO

#===============================================================================

class Popstring(Group):
    CLASSID = MUIC_Popstring
    # TODO

#===============================================================================

class Pubscreenadjust(Group):
    CLASSID = MUIC_Pubscreenadjust

#===============================================================================

class Pubscreenpanel(Group):
    CLASSID = MUIC_Pubscreenpanel

#===============================================================================

class Pubscreenlist(Group):
    CLASSID = MUIC_Pubscreenlist
    # TODO

#===============================================================================

class Popobject(Popstring):
    CLASSID = MUIC_Popobject
    # TODO

#===============================================================================

class Poplist(Popobject):
    CLASSID = MUIC_Poplist
    # TODO

#===============================================================================

class Popscreen(Popobject):
    CLASSID = MUIC_Popscreen

#===============================================================================

class Popasl(Popstring):
    CLASSID = MUIC_Popasl
    # TODO

#===============================================================================

class Semaphore(rootclass):
    CLASSID = MUIC_Semaphore
    # TODO

#===============================================================================

class Applist(Semaphore):
    CLASSID = MUIC_Applist

#===============================================================================

class Cclist(Semaphore):
    CLASSID = MUIC_Cclist

#===============================================================================

class Dataspace(Semaphore):
    CLASSID = MUIC_Dataspace
    # TODO

#===============================================================================

class Configdata(Dataspace):
    CLASSID = MUIC_Configdata

#===============================================================================

class Screenspace(Dataspace):
    CLASSID = MUIC_Screenspace

#===============================================================================

class Rootgrp(Group):
    CLASSID = MUIC_Rootgrp

#===============================================================================

class Popmenu(Notify):
    CLASSID = MUIC_Popmenu

#===============================================================================

class Panel(Group):
    CLASSID = MUIC_Panel

#===============================================================================

class Filepanel(Panel):
    CLASSID = MUIC_Panel

#===============================================================================

class Fontpanel(Panel):
    CLASSID = MUIC_Fontpanel

#===============================================================================

class Screenmodepanel(Panel):
    CLASSID = MUIC_Screenmodepanel

#===============================================================================

class Keyadjust(Group):
    CLASSID = MUIC_Keyadjust
    # TODO

#===============================================================================

class Imagebrowser(Group):
    CLASSID = MUIC_Imagebrowser

#===============================================================================

class Colorring(Group):
    CLASSID = MUIC_Colorring

#===============================================================================

class Process(Semaphore):
    CLASSID = MUIC_Process
    # TODO

#===============================================================================

class Aboutpage(Mccprefs):
    CLASSID = MUIC_Aboutpage

################################################################################
#################################  END OF FILE  ################################
################################################################################
