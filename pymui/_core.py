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

import sys, functools, array, weakref

try:
    DEBUG = sys.argv[1] == '-v'
except:
    DEBUG = False

def debug(x, *args):
    if DEBUG:
        print x % args

try:
    import _muimaster
    from _muimaster import *
except:
    class _muimaster:
        class EventHandler: pass
        _setwinpointer = None
    class PyMUIObject(object): pass

from defines import *
from types import *
import ctypes as _ct

MUI_EventHandlerRC_Eat = (1<<0)
NM_BARLABEL = -1
MUI_MAXMAX = 10000

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
#### Usefull types
################################################################################

class c_PyObject(_ct.py_object, CPointer):
    def __long__(self):
        x = self.value
        return (0 if x is None else id(x))

    @classmethod
    def FromLong(cl, v):
        return cl(_muimaster._APTR2Python(v))

class c_BoopsiObject(_ct.c_ulong, CPointer):
    def __init__(self, x=None):
        if x is not None:
            if not isinstance(x, (long, int)):
                assert isinstance(x, PyBOOPSIObject)
                x = x._object
            super(c_BoopsiObject, self).__init__(x)
        else:
            super(c_BoopsiObject, self).__init__()
            
    @property
    def value(self):
        return _muimaster._BOOPSI2Python(_ct.c_ulong.value.__get__(self))

    def __long__(self):
        return _ct.c_ulong.value.__get__(self)

    @classmethod
    def FromLong(cl, v):
        return cl(v)

    def _keep(self):
        return self.value

class c_MUIObject(c_BoopsiObject): pass

class c_Hook(c_PyObject):
    _argtypes_ = (long, long)
    
    def __new__(cl, *args, **kwds):
        return c_PyObject.__new__(cl)

    def __init__(self, x=None, argstypes=None):
        if x:
            if argstypes is None:
                argstypes = self._argtypes_
                
            if argstypes[0] is None:
                if argstypes[1] is None:
                    f = lambda a, b: x()
                elif argstypes[1] is long:
                    f = lambda a, b: x(b)
                else:
                    f = lambda a, b: x(argstypes[1].FromLong(b))
            elif argstypes[1] is None:
                if argstypes[0] is long:
                    f = lambda a, b: x(a)
                else:
                    f = lambda a, b: x(argstypes[0].FromLong(a))
            else:
                if argstypes[0] is long:
                    if argstypes[1] is long:
                        f = lambda a, b: x(a, b)
                    else:
                        f = lambda a, b: x(a, argstypes[1].FromLong(b))
                elif argstypes[1] is long:
                    f = lambda a, b: x(argstypes[0].FromLong(a), b)
                else:
                    f = lambda a, b: x(argstypes[0].FromLong(a), argstypes[1].FromLong(b))
                
            c_PyObject.__init__(self, _muimaster._CHook(f))
        else:
            c_PyObject.__init__(self)

    def __long__(self):
        x = self.value
        return (0 if x is None else x.address)

    @classmethod
    def FromLong(cl, v):
        return cl(_muimaster._CHook(v))

class c_Node(CStructure): pass
c_Node._fields_ = [ ('ln_Succ', c_Node._PointerType()),
                    ('ln_Pred', c_Node._PointerType()),
                    ('ln_Type', c_UBYTE),
                    ('ln_Pri', c_BYTE),
                    ('ln_Name', c_STRPTR) ]

class c_MinNode(CStructure): pass
c_MinNode._fields_ = [ ('mln_Succ', c_MinNode._PointerType()),
                       ('mln_Pred', c_MinNode._PointerType()) ]

class c_Message(CStructure):
    _fields_ = [ ('mn_Node', c_Node),
                 ('mn_ReplyPort', c_APTR),
                 ('mn_Length', c_UWORD) ]

class c_pTextFont(c_APTR): pass
class c_pList(c_APTR): pass
class c_pMinList(c_APTR): pass

class c_TagItem(CStructure):
    _fields_ = [('ti_Tag', c_ULONG),
                ('ti_Data', c_ULONG)]

c_pTagItem = c_TagItem._PointerType()

class c_MenuitemTitle(c_STRPTR):
    """Menuitem title accepts string address and some special integer values.
    Currently only NM_BARLABEL is accepted.
    """

    def __long__(self):
        return c_LONG(c_STRPTR.__long__(self)).value

    @property
    def value(self):
        return (c_STRPTR.value.__get__(self) if long(self) != NM_BARLABEL else NM_BARLABEL)

class c_ListTitle(c_STRPTR):
    @property
    def value(self):
        return (c_STRPTR.value.__get__(self) if long(self) != 1 else True)

class c_PenSpec(CStructure):
    _fields_ = [ ('buf', c_BYTE.ArrayOf(32)) ]

################################################################################
#### PyMUI internal base classes and routines
################################################################################

class MAttribute(property):
    """MAttribute(id, isg, ctype, keep=None, doc=None, **kwds) -> instance

    This class generates class properties to define MUI attributes when you wrap
    a MUI class with PyMUI. Just use it as the property Python class.
    
    This property is used by instances of your class to set/get MUI attribute
    as GetAttr() and SetAttrs() do in the insane C world.


    Arguments documentation:

    - id: [long] the MUI id (MUIA_xxxx values) to wrap
    - isg: [str] a 3-characters string to indicate if the attribute is available
    at initialisation of your class (__init__), can be set or get. Only 4 characters
    are recognized : 'i', 's', 'g' or '.' (dot).
    Use the dot when the corresponding flags is not avaible, in the same way as
    documented in the library/mui.h file. Order doesn't matter, just presence or not.
    - ctype: [PyMUICType class] a PyMUICType class used to handle the MUI attribute value.
    - keep: [bool or None] use it to force or not the object tracking scheme
    (incref a Python object related the input value given during the init or set of
    the attribute). None to let the atribute type decide what to do. True or False
    to force to track or not track something related to the input


    Optional keywords:

    - 'preSet': a callable with prototype (PyMUIObject instance, MAttribute instance, value).
    Called before setting the value to the MUI attribute of the given object.
    This callable shall return the value to really use for setting.
    - 'postSet': a callable with same prototype as preSet. Called after the MUI set is done.
    No return.
    - 'preGet': a callable with prototype (PyMUIObject instance, MAttribute instance).
    Called before getting the value to the MUI attribute of the given object.
    No return.
    - 'postSet': a callable with same prototype as preSet (and not preGet!).
    Called after the MUI get is done with the get value.
    This callable shall return the value really to really return to the user.

    Other keywords are directly given to the property class __init__ constructor.
    """
    
    def __init__(self, id, isg, ctype, keep=None, **kwds):
        assert issubclass(ctype, PyMUICType)
        
        self.__isg = isg
        self.__id = id
        self.__ctype = ctype

        if 'i' in isg:
            def _init(obj, v):
                v = v if isinstance(v, ctype) else ctype(v)
                if (keep is None and v._iskept) or keep is True:
                    obj._keep_dict[id] = v._keep()
                return long(v)
        else:
            def _init(*args):
                raise AttributeError("attribute %08x can't be used at init" % self.__id)

        if 's' in isg:
            def _setter(obj, v, nn=False):
                v = (v if isinstance(v, ctype) else ctype(v))
                if (keep is None and v._iskept) or keep is True:
                    obj._keep_dict[id] = v._keep()
                if nn:
                    obj._nnset(id, v)
                else:
                    obj._set(id, v)
        else:
            _setter = None

        if 'g' in isg:
            def _getter(obj):
                return ctype.FromLong(obj._get(id))
        else:
            _getter = None

        preSet = kwds.pop('preSet', None)
        postSet = kwds.pop('postSet', None)
        if preSet and postSet:
            def setter(obj, v, nn=False):
                _setter(obj, preSet(obj, self, v), nn)
                postSet(obj, self, v)
            def init(obj, v):
                x = _init(obj, preSet(obj, self, v))
                postSet(obj, self, v)
                return x
        elif preSet:
            def setter(obj, v, nn=False):
                _setter(obj, preSet(obj, self, v), nn)
            def init(obj, v):
                return _init(obj, preSet(obj, self, v))
        elif postSet:
            def setter(obj, v, nn=False):
                _setter(obj, v, nn)
                postSet(obj, self, v)
            def init(obj, v):
                x = _init(obj, v)
                postSet(obj, self, v)
                return x
        else:
            setter = _setter
            init = _init

        self.init = init

        preGet = kwds.pop('preGet', None)
        postGet = kwds.pop('postGet', None)
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

        self.setter = setter
        property.__init__(self, fget=getter, fset=setter, **kwds)

    @property
    def id(self):
        "MUI id of the MUI attribute"
        return self.__id

    @property
    def isg(self):
        "MUI ISG flags of the MUI attribute"
        return self.__isg
    
    @property
    def ctype(self):
        "PyMUICType class of the MUI attribute"
        return self.__ctype

#===============================================================================

class MMethod(property):
    def __init__(self, id, fields=None, rettype=c_ULONG,
                 varargs=False, doc=None, **kwds):
        self.__id = id
        self.__rettp = rettype
        if rettype is None:
            self.__retconv = lambda x: None
        else:
            self.__retconv = rettype.FromLong
        
        if fields:
            self.__msgtype = type('c_MUIP_%x' % id, (CStructure,), {'_fields_': [ ('MethodID', c_ULONG) ] + fields})
            buftp = (_ct.c_ulong * (len(fields)+1))

            if not varargs:
                def cb(obj, *args, **kwds):
                    msg = self.__msgtype()
                    msg.MethodID = id # MethodID

                    if len(args) > len(fields):
                        raise SyntaxError("Too many arguments given")

                    args = list(args)
                    for i, field in enumerate(fields):
                        nm, tp = field
                        if args:
                            if nm in kwds:
                                raise SyntaxError("field '%s' is given as positional and keyword argument" % nm)
                            o = args.pop(0)
                            if not isinstance(o, tp):
                                o = field[1](o)
                            setattr(msg, nm, o)
                        else:
                            if nm not in kwds:
                                raise SyntaxError("required field '%s' missing" % nm)
                            o = kwds[nm]
                            if not isinstance(o, tp):
                                o = field[1](o)
                            setattr(msg, nm, o)

                    if kwds:
                        raise SyntaxError("Too many arguments given")

                    return self.__retconv(obj._do(msg))
            else:
                def cb(obj, *args):
                    msg = buftp()
                    msg[0] = id # MethodID

                    args = list(args)
                    keep = []
                    for i, field in enumerate(fields):
                        o = args.pop(0)
                        if not isinstance(o, field[1]):
                            o = field[1](o)
                        keep.append(o)
                        msg[i+1] = long(o)
                    return self.__retconv(obj._do(msg, args))
        else:
            self.__msgtype = type('c_MUIP_%x' % id, (CStructure,), {'_fields_': [ ('MethodID', c_ULONG) ]})

            if not varargs:
                def cb(obj):
                    return self.__retconv(obj._do(_ct.c_ulong(id)))
            else:
                def cb(obj):
                    return self.__retconv(obj._do(_ct.c_ulong(id)))

        self.__cb = cb
        self.__alias = None
        property.__init__(self, fget=lambda obj: functools.partial(self.__cb, obj), doc=doc)

    def __call__(self, obj, *args):
        return self.__cb(obj, *args)

    def alias(self, f):
        @functools.wraps(f)
        def wrapper(obj, *args, **kwds):
            return f(obj, self, *args, **kwds)
        return wrapper

    @property
    def id(self):
        return self.__id

    @property
    def msgtype(self):
        return self.__msgtype

#===============================================================================

class Event(object):
    def __init__(self, source):
        self.Source = source

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
        

class AttributeNotify:
    def __init__(self, trigvalue, cb, args):
        self.cb = cb
        self.args = args
        self.trigvalue = long(trigvalue)

    def __call__(self, e):
        return self.cb(e, *self.args)

#===============================================================================

class MUIMetaClass(type):
    def __new__(metacl, name, bases, dct):
        clid = dct.pop('CLASSID', None)
        if not clid:
            clid = [ base._mclassid for base in bases if hasattr(base, '_mclassid') ]
            if not len(clid):
                raise TypeError("No valid MUI class name found")
            clid = clid[0]

        dct['_mclassid'] = clid
        dct['isMCC'] = bool(dct.pop('MCC', False))

        if dct['isMCC']:
            if not any(hasattr(base, '__pymui_overloaded__') for base in bases):
                dct['__pymui_overloaded__'] = {}
            
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

    def __init__(cl, name, bases, dct):
        type.__init__(cl, name, bases, dct)

        # register MUI overloaded methods
        d = dct.get('__pymui_overloaded__')
        if d is not None:
            for v in dct.itervalues():
                if hasattr(v, '_pymui_mid_'):
                    meth = v._pymui_mid_
                    if not isinstance(meth, MMethod):
                        meth = cl._getMM(v._pymui_mid_)
                    d[meth.id] = functools.partial(getattr(cl, v.__name__), tp=meth.msgtype)


# decorator to register a class method to overload a MUI method
def muimethod(mid):
    def wrapper(func):
        @functools.wraps(func)
        def convertor(self, msg, tp):
            # Becarefull here: the constructed Msg object from tp,
            # is only valid during the call of the function and accessible
            # by msg getattr function.
            return func(self, msg._setup(tp.FromLong))
        convertor._pymui_mid_ = mid
        return convertor
    return wrapper

#===============================================================================

class BOOPSIMixin:
    @classmethod
    def _getMA(cl, o):
        if isinstance(o, str):
            return cl._getMAByName(o)
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
        if isinstance(o, str):
            return cl._getMMByName(o)
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

def _postSet_Child(self, attr, o):
        if o is None:
            self._cdel(attr.id)
        else:
            self._cadd(o, attr.id)

class rootclass(PyMUIObject, BOOPSIMixin):
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
        #self._notify_cbdict = {}

        # Extra parameters overwrite local ones.
        kwds.update(kwds.pop('pymui_extra', {}))
        
        # A 'struct TagItem' array
        init_tags = (c_TagItem * (len(kwds)+1))()

        # Convert keywords into (attr, value) tuples
        for i, k in enumerate(kwds.keys()):
            attr = self._getMAByName(k)
            init_tags[i].ti_Tag = attr.id
            init_tags[i].ti_Data = attr.init(self, kwds[k])

        overloaded = getattr(self, '__pymui_overloaded__', {})

        self._create(self._mclassid, _ct.addressof(init_tags),
                     self.__class__.isMCC, overloaded)

    def AddChild(self, o):
        if not self._cin(o):
            self._add(o)
            self._cadd(o) # incref the child object to not lost it during next GC

    def RemChild(self, o):
        if self._cin(o):
            self._rem(o)
            self._crem(o)

#===============================================================================

class c_NotifyHook(c_Hook): _argtypes_ = (c_MUIObject, c_APTR._PointerType())

class Notify(rootclass):
    CLASSID = MUIC_Notify

    ApplicationObject = MAttribute(MUIA_ApplicationObject , '..g', c_MUIObject)
    AppMessage        = MAttribute(MUIA_AppMessage        , '..g', c_APTR)
    HelpLine          = MAttribute(MUIA_HelpLine          , 'isg', c_LONG)
    HelpNode          = MAttribute(MUIA_HelpNode          , 'isg', c_STRPTR)
    NoNotify          = MAttribute(MUIA_NoNotify          , '.s.', c_BOOL)
    NoNotifyMethod    = MAttribute(MUIA_NoNotifyMethod    , '.s.', c_ULONG)
    ObjectID          = MAttribute(MUIA_ObjectID          , 'isg', c_ULONG)
    Parent            = MAttribute(MUIA_Parent            , '..g', c_MUIObject)
    Revision          = MAttribute(MUIA_Revision          , '..g', c_LONG)
    # forbidden: MUIA_UserData (intern usage)
    Version           = MAttribute(MUIA_Version           , '..g', c_LONG)

    CallHook = MMethod(MUIM_CallHook, [ ('hook', c_NotifyHook) ], varargs=True)

    def NNSet(self, attr, v):
        self._getMA(attr).setter(self, v, True)

    def _notify_cb(self, a, v, nv):
        attr = self._getMAByID(a)
        v = attr.ctype.FromLong(v)
        lv = long(v)
        e = AttributeEvent(self, v, nv)
        for o in self._notify_cbdict[a]:
            if o.trigvalue == MUIV_EveryTime or o.trigvalue == lv:
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
        self.ApplicationObject.value.Quit()


#===============================================================================

class Family(Notify):
    CLASSID = MUIC_Family
    
    Child = MAttribute(MUIA_Family_Child, 'i..', c_MUIObject)
    List  = MAttribute(MUIA_Family_List , '..g', c_pMinList)

    Insert   = MMethod(MUIM_Family_Insert,   [ ('obj', c_MUIObject), ('pred', c_MUIObject) ])
    Remove   = MMethod(MUIM_Family_Remove,   [ ('obj', c_MUIObject) ])
    Sort     = MMethod(MUIM_Family_Sort,     [ ('objs', c_MUIObject._PointerType()) ])
    Transfer = MMethod(MUIM_Family_Transfer, [ ('family', c_MUIObject) ])

    def __init__(self, **kwds):
        child = kwds.pop('Child', None)
        super(Family, self).__init__(**kwds)
        if child:
            self.AddTail(child)

    def AddHead(self, o):
        if isinstance(o, c_MUIObject): o = o.value
        assert isinstance(o, Family)
        x = self._do1(MUIM_Family_AddHead, o._object)
        self._cadd(o)
        return x

    def AddTail(self, o):
        if isinstance(o, c_MUIObject): o = o.value
        assert isinstance(o, Family)
        x = self._do1(MUIM_Family_AddTail, o._object)
        self._cadd(o)
        return x

    @Insert.alias
    def Insert(self, meth, o, p):
        if isinstance(o, c_MUIObject): o = o.value
        if isinstance(p, c_MUIObject): p = p.value
        isinstance(o, Family) and isinstance(p, Family)
        assert self._cin(p)
        x = meth(self, o, p)
        self._cadd(o)
        return x

    @Remove.alias
    def Remove(self, meth, o):
        if isinstance(o, c_MUIObject): o = o.value
        assert self._cin(o)
        x = meth(self, o)
        self._crem(o)
        return x

    @Sort.alias
    def Sort(self, *args):
        a = c_MUIObject.ArrayOf(len(args)+1)() # transitive object, not needed to be keep
        a[:] = args
        return meth(self, a[0])

    @Transfer.alias
    def Transfer(self, meth, f):
        if isinstance(f, c_MUIObject): f = f.value
        assert isinstance(f, Family)
        x = meth(self, f)
        for o in self._children:
            f._cadd(o)
        self._cclear()
        return x

#===============================================================================

class Menustrip(Family):
    CLASSID = MUIC_Menustrip
    
    Enabled = MAttribute(MUIA_Menustrip_Enabled, 'isg', c_BOOL)

    InitChange = MMethod(MUIM_Menustrip_InitChange)
    ExitChange = MMethod(MUIM_Menustrip_ExitChange)
    Popup      = MMethod(MUIM_Menustrip_Popup, [ ('parent', c_MUIObject),
                                                 ('flags', c_ULONG),
                                                 ('x', c_LONG),
                                                 ('y', c_LONG) ])

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
        # XXX: safe to not keep parent?
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
        self.Notify('Trigger', callback=lambda e, *args: callback(*args), args=args)

#===============================================================================

class Application(Notify): # TODO: unfinished
    CLASSID = MUIC_Application

    Active         = MAttribute(MUIA_Application_Active,         'isg', c_BOOL)
    Author         = MAttribute(MUIA_Application_Author,         'i.g', c_STRPTR)
    Base           = MAttribute(MUIA_Application_Base,           'i.g', c_STRPTR)
    Broker         = MAttribute(MUIA_Application_Broker,         '..g', c_APTR)
    BrokerHook     = MAttribute(MUIA_Application_BrokerHook,     'isg', c_Hook)
    BrokerPort     = MAttribute(MUIA_Application_BrokerPort,     '..g', c_APTR)
    BrokerPri      = MAttribute(MUIA_Application_BrokerPri,      'i.g', c_LONG)
    Commands       = MAttribute(MUIA_Application_Commands,       'isg', c_APTR)
    Copyright      = MAttribute(MUIA_Application_Copyright,      'i.g', c_STRPTR)
    Description    = MAttribute(MUIA_Application_Description,    'i.g', c_STRPTR)
    DiskObject     = MAttribute(MUIA_Application_DiskObject,     'isg', c_APTR)
    DoubleStart    = MAttribute(MUIA_Application_DoubleStart,    '..g', c_BOOL)
    DropObject     = MAttribute(MUIA_Application_DropObject,     'is.', c_MUIObject, postSet=_postSet_Child)
    ForceQuit      = MAttribute(MUIA_Application_ForceQuit,      '..g', c_BOOL)
    HelpFile       = MAttribute(MUIA_Application_HelpFile,       'isg', c_STRPTR)
    Iconified      = MAttribute(MUIA_Application_Iconified,      '.sg', c_BOOL)
    MenuAction     = MAttribute(MUIA_Application_MenuAction,     '..g', c_ULONG)
    MenuHelp       = MAttribute(MUIA_Application_MenuHelp,       '..g', c_ULONG)
    Menustrip      = MAttribute(MUIA_Application_Menustrip,      'i..', c_MUIObject, postSet=_postSet_Child)
    RexxHook       = MAttribute(MUIA_Application_RexxHook,       'isg', c_Hook)
    RexxMsg        = MAttribute(MUIA_Application_RexxMsg,        '..g', c_APTR)
    RexxString     = MAttribute(MUIA_Application_RexxString,     '.s.', c_STRPTR)
    SingleTask     = MAttribute(MUIA_Application_SingleTask,     'i..', c_BOOL)
    Sleep          = MAttribute(MUIA_Application_Sleep,          '.s.', c_BOOL)
    Title          = MAttribute(MUIA_Application_Title,          'i.g', c_STRPTR)
    UseCommodities = MAttribute(MUIA_Application_UseCommodities, 'i..', c_BOOL)
    UsedClasses    = MAttribute(MUIA_Application_UsedClasses,    'isg', c_pSTRPTR)
    UseRexx        = MAttribute(MUIA_Application_UseRexx,        'i..', c_BOOL)
    Version        = MAttribute(MUIA_Application_Version,        'i.g', c_STRPTR)
    Window         = MAttribute(MUIA_Application_Window,         'i..', c_MUIObject)
    WindowList     = MAttribute(MUIA_Application_WindowList,     '..g', c_pList)

    AboutMUI         = MMethod(MUIM_Application_AboutMUI,         [ ('refwindow', c_MUIObject) ])
    ##AddInputHandler
    ##BuildSettingsPanel
    CheckRefresh     = MMethod(MUIM_Application_CheckRefresh)
    ##DefaultConfigItem
    InputBuffered    = MMethod(MUIM_Application_InputBuffered)
    Load             = MMethod(MUIM_Application_Load,             [ ('name', c_STRPTR) ])
    NewInput         = MMethod(MUIM_Application_NewInput,         [ ('signal', c_ULONG._PointerType()) ])
    OpenConfigWindow = MMethod(MUIM_Application_OpenConfigWindow, [ ('flags', c_ULONG),
                                                                    ('classid', c_STRPTR) ])
    PushMethod       = MMethod(MUIM_Application_PushMethod,       [ ('dest', c_MUIObject),
                                                                    ('count', c_LONG) ], varargs=True)
    ##RemInputHandler
    ReturnID         = MMethod(MUIM_Application_ReturnID,         [ ('retid', c_ULONG) ])
    Save             = MMethod(MUIM_Application_Save,             [ ('name', c_STRPTR) ])

    ShowHelp         = MMethod(MUIM_Application_ShowHelp,         [ ('window', c_MUIObject),
                                                                    ('name',   c_STRPTR),
                                                                    ('node',   c_STRPTR),
                                                                    ('line',   c_LONG) ])
    
    def __init__(self, MainWindow=None, **kwds):
        super(Application, self).__init__(**kwds)

        # Add Window PyMUIObject passed as argument
        if MainWindow is not None:
            self.AddChild(MainWindow)
            MainWindow.Notify('Open', False, lambda e: MainWindow.KillApp())

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

class Window(Notify): # TODO: unfinished
    CLASSID = MUIC_Window
    
    def __checkForApp(self, attr, o):
        if not self.ApplicationObject.value:
            raise AttributeError("Window not linked to an application yet")
        return o

    Activate                = MAttribute(MUIA_Window_Activate                , 'isg', c_BOOL)
    ActiveObject            = MAttribute(MUIA_Window_ActiveObject            , '.sg', c_MUIObject) # XXX: what append if the object is not a child?
    AltHeight               = MAttribute(MUIA_Window_AltHeight               , 'i.g', c_LONG)
    AltLeftEdge             = MAttribute(MUIA_Window_AltLeftEdge             , 'i.g', c_LONG)
    AltTopEdge              = MAttribute(MUIA_Window_AltTopEdge              , 'i.g', c_LONG)
    AltWidth                = MAttribute(MUIA_Window_AltWidth                , 'i.g', c_LONG)
    AppWindow               = MAttribute(MUIA_Window_AppWindow               , 'i..', c_BOOL)
    Backdrop                = MAttribute(MUIA_Window_Backdrop                , 'i..', c_BOOL)
    Borderless              = MAttribute(MUIA_Window_Borderless              , 'i..', c_BOOL)
    CloseGadget             = MAttribute(MUIA_Window_CloseGadget             , 'i..', c_BOOL)
    CloseRequest            = MAttribute(MUIA_Window_CloseRequest            , '..g', c_BOOL)
    DefaultObject           = MAttribute(MUIA_Window_DefaultObject           , 'isg', c_MUIObject) # XXX: what append if the object is not a child?
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
    Menustrip               = MAttribute(MUIA_Window_Menustrip               , 'i.g', c_MUIObject, postSet=_postSet_Child)
    MouseObject             = MAttribute(MUIA_Window_MouseObject             , '..g', c_MUIObject)
    NeedsMouseObject        = MAttribute(MUIA_Window_NeedsMouseObject        , 'i..', c_BOOL)
    NoMenus                 = MAttribute(MUIA_Window_NoMenus                 , 'is.', c_BOOL)
    Open                    = MAttribute(MUIA_Window_Open                    , '.sg', c_BOOL, preSet=__checkForApp)
    PublicScreen            = MAttribute(MUIA_Window_PublicScreen            , 'isg', c_STRPTR)
    RefWindow               = MAttribute(MUIA_Window_RefWindow               , 'is.', c_MUIObject)
    RootObject              = MAttribute(MUIA_Window_RootObject              , 'isg', c_MUIObject, postSet=_postSet_Child)
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
        if i == -1:
            for i in xrange(1<<10):
                if i not in cl.__idset:
                    cl.__idset.add(i)
                    return i
            raise RuntimeError("No more availables IDs")
        elif isinstance(i, str):
            i = sum(ord(c) << (24-n*8) for n, c in enumerate(i[:4]))
            if i in cl.__idset:
                raise RuntimeError("ID %u already taken" % i)

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

    Application = MAttribute(MUIA_Aboutmui_Application, 'i..', c_MUIObject)

    def __init__(self, app, **kwds):
        super(AboutMUI, self).__init__(Application=app, RefWindow=kwds.pop('RefWindow', None), **kwds)
        # We don't call app.AddChild() because this object do it itself during its OM_NEW
        
#===============================================================================

class c_MinMax(CStructure):
    _fields_ = [ ('MinWidth', c_WORD),
                 ('MinHeight', c_WORD),
                 ('MaxWidth', c_WORD),
                 ('MaxHeight', c_WORD),
                 ('DefWidth', c_WORD),
                 ('DefHeight', c_WORD) ]

class c_IntuiMessage(CStructure):
    _fields_ = [ ('ExecMessage', c_Message),
                 ('Class', c_ULONG),
                 ('Code', c_UWORD),
                 ('Qualifier', c_UWORD),
                 ('IAddress', c_APTR),
                 ('MouseX', c_WORD),
                 ('MouseY', c_WORD),
                 ('Seconds', c_ULONG),
                 ('Micros', c_ULONG),
                 ('IDCMPWindow', c_APTR),
                 ('SpecialLink', c_APTR) ]

class c_EventHandlerNode(CStructure):
    _fields_ = [ ('ehn_Node', c_MinNode),
                 ('ehn_Reserved', c_BYTE),
                 ('ehn_Priority', c_BYTE),
                 ('ehn_Flags', c_UWORD),
                 ('ehn_Object', c_MUIObject),
                 ('ehn_Class', c_APTR),
                 ('ehn_Events', c_ULONG) ]

class Area(Notify): # TODO: unfinished
    CLASSID = MUIC_Area

    Background         = MAttribute(MUIA_Background         , 'is.', c_STRPTR)
    BottomEdge         = MAttribute(MUIA_BottomEdge         , '..g', c_LONG)
    ContextMenu        = MAttribute(MUIA_ContextMenu        , 'isg', c_MUIObject, postSet=_postSet_Child)
    ContextMenuTrigger = MAttribute(MUIA_ContextMenuTrigger , '..g', c_MUIObject)
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
    WindowObject       = MAttribute(MUIA_WindowObject       , '..g', c_MUIObject)

    AskMinMax   = MMethod(MUIM_AskMinMax,   [ ('MinMaxInfo', c_MinMax._PointerType()) ])
    Cleanup     = MMethod(MUIM_Cleanup)
    DragQuery   = MMethod(MUIM_DragQuery,   [ ('obj', c_MUIObject) ])
    Draw        = MMethod(MUIM_Draw,        [ ('flags', c_ULONG) ])
    HandleEvent = MMethod(MUIM_HandleEvent, [ ('imsg', c_IntuiMessage._PointerType()),
                                              ('muikey', c_LONG),
                                              ('ehn', c_EventHandlerNode._PointerType()) ])
    Setup       = MMethod(MUIM_Setup,       [ ('RenderInfo', c_APTR) ])

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

    def AddClipping(self):
        """AddClipping() -> None

        Call MUI_AddClipping() for the full area.

        This function shall be called during MUIM_Draw method call.
        And method RemoveClipping shall be called before leaving the MUIM_Draw method.
        """

        self.__cliphandle =_muimaster._AddClipping(self)

    def RemoveClipping(self):
        """RemoveClipping(self) -> None

        Call MUI_RemoveClipping(). Must be called after a call to AddClipping and before
        the end of the MUIM_Draw method.
        """

        _muimaster._RemoveClipping(self, self.__cliphandle)

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
    Spec            = MAttribute(MUIA_Image_Spec            , 'i..', c_STRPTR)
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

    Alpha          = MAttribute(MUIA_Bitmap_Alpha,          'isg', c_ULONG)
    Bitmap         = MAttribute(MUIA_Bitmap_Bitmap,         'isg', c_APTR) # struct BitMap *
    Height         = MAttribute(MUIA_Bitmap_Height,         'isg', c_LONG)
    MappingTable   = MAttribute(MUIA_Bitmap_MappingTable,   'isg', c_UBYTE._PointerType())
    Precision      = MAttribute(MUIA_Bitmap_Precision,      'isg', c_LONG)
    RemappedBitmap = MAttribute(MUIA_Bitmap_RemappedBitmap, '..g', c_APTR) # struct BitMap *
    SourceColors   = MAttribute(MUIA_Bitmap_SourceColors,   'isg', c_ULONG._PointerType())
    Transparent    = MAttribute(MUIA_Bitmap_Transparent,    'isg', c_LONG)
    UseFriend      = MAttribute(MUIA_Bitmap_UseFriend,      'i..', c_BOOL)
    Width          = MAttribute(MUIA_Bitmap_Width,          'isg', c_LONG)

#===============================================================================

class Bodychunk(Bitmap):
    CLASSID = MUIC_Bodychunk

    Body        = MAttribute(MUIA_Bodychunk_Body,        'isg', c_UBYTE._PointerType())
    Compression = MAttribute(MUIA_Bodychunk_Compression, 'isg', c_UBYTE)
    Depth       = MAttribute(MUIA_Bodychunk_Depth,       'isg', c_LONG)
    Masking     = MAttribute(MUIA_Bodychunk_Masking,     'isg', c_UBYTE)

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
    def KeyButton(cl, label, key=None, **kwds):
        kwds.update(Contents=label,
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
    
    Gadget = MAttribute(MUIA_Gadget_Gadget, '..g', c_APTR) # struct Gadget *

#===============================================================================

class String(Area):
    CLASSID = MUIC_String

    Accept         = MAttribute(MUIA_String_Accept,         'isg', c_STRPTR)
    Acknowledge    = MAttribute(MUIA_String_Acknowledge,    '..g', c_STRPTR)
    AdvanceOnCR    = MAttribute(MUIA_String_AdvanceOnCR,    'isg', c_BOOL)
    AttachedList   = MAttribute(MUIA_String_AttachedList,   'isg', c_MUIObject, postSet=_postSet_Child)
    BufferPos      = MAttribute(MUIA_String_BufferPos,      '.sg', c_LONG)
    Contents       = MAttribute(MUIA_String_Contents,       'isg', c_STRPTR)
    DisplayPos     = MAttribute(MUIA_String_DisplayPos,     '.sg', c_LONG)
    EditHook       = MAttribute(MUIA_String_EditHook,       'isg', c_Hook)
    Format         = MAttribute(MUIA_String_Format,         'i.g', c_LONG)
    Integer        = MAttribute(MUIA_String_Integer,        'isg', c_ULONG)
    LonelyEditHook = MAttribute(MUIA_String_LonelyEditHook, 'isg', c_BOOL)
    MaxLen         = MAttribute(MUIA_String_MaxLen,         'i.g', c_LONG)
    Reject         = MAttribute(MUIA_String_Reject,         'isg', c_STRPTR)
    Secret         = MAttribute(MUIA_String_Secret,         'i.g', c_BOOL)

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

    Current  = MAttribute(MUIA_Gauge_Current,  'isg', c_LONG)
    Divide   = MAttribute(MUIA_Gauge_Divide,   'isg', c_ULONG)
    Horiz    = MAttribute(MUIA_Gauge_Horiz,    'i..', c_BOOL)
    InfoRate = MAttribute(MUIA_Gauge_InfoRate, 'isg', c_LONG)
    InfoText = MAttribute(MUIA_Gauge_InfoText, 'isg', c_STRPTR)
    Max      = MAttribute(MUIA_Gauge_Max,      'isg', c_LONG)

#===============================================================================

class Scale(Area):
    CLASSID = MUIC_Scale

    Horiz = MAttribute(MUIA_Scale_Horiz, 'isg', c_BOOL)
    
#===============================================================================

class Colorfield(Area):
    CLASSID = MUIC_Colorfield

    Blue  = MAttribute(MUIA_Colorfield_Blue,  'isg', c_ULONG)
    Green = MAttribute(MUIA_Colorfield_Green, 'isg', c_ULONG)
    Pen   = MAttribute(MUIA_Colorfield_Pen,   '..g', c_ULONG)
    Red   = MAttribute(MUIA_Colorfield_Red,   'isg', c_ULONG)
    RGB   = MAttribute(MUIA_Colorfield_RGB,   'isg', c_ULONG._PointerType())

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

    Decrease     = MMethod(MUIM_Numeric_Decrease,     [ ('amount', c_LONG) ])
    Increase     = MMethod(MUIM_Numeric_Increase,     [ ('amount', c_LONG) ])
    ScaleToValue = MMethod(MUIM_Numeric_ScaleToValue, [ ('scalemin', c_LONG), ('scalemax', c_LONG), ('scale', c_LONG) ])
    SetDefault   = MMethod(MUIM_Numeric_SetDefault)
    Stringify    = MMethod(MUIM_Numeric_Stringify,    [ ('value', c_LONG) ])
    ValueToScale = MMethod(MUIM_Numeric_ValueToScale, [ ('scalemin', c_LONG), ('scalemax', c_LONG) ])

#===============================================================================

class Knob(Numeric):
    CLASSID = MUIC_Knob

#===============================================================================

class Levelmeter(Numeric):
    CLASSID = MUIC_Levelmeter

    Label = MAttribute(MUIA_Levelmeter_Label, 'isg', c_STRPTR)

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

    Pen       = MAttribute(MUIA_Pendisplay_Pen,       '..g', c_ULONG)
    Reference = MAttribute(MUIA_Pendisplay_Reference, 'isg', c_MUIObject)
    RGBcolor  = MAttribute(MUIA_Pendisplay_RGBcolor,  'isg', c_APTR) # struct MUI_RGBcolor *
    Spec      = MAttribute(MUIA_Pendisplay_Spec,      'isg', c_APTR) # struct MUI_PenSpec *

    SetColormap = MMethod(MUIM_Pendisplay_SetColormap, [ ('colormap', c_LONG) ])
    SetMUIPen   = MMethod(MUIM_Pendisplay_SetMUIPen,   [ ('muipen', c_LONG) ])
    SetRGB      = MMethod(MUIM_Pendisplay_SetRGB,      [ ('red', c_ULONG), ('green', c_ULONG), ('blue', c_ULONG) ])

#===============================================================================

class Poppen(Pendisplay):
    CLASSID = MUIC_Poppen

#===============================================================================

class Group(Area): # TODO: unfinished
    CLASSID = MUIC_Group

    ActivePage   = MAttribute(MUIA_Group_ActivePage   , 'isg', c_LONG)
    Child        = MAttribute(MUIA_Group_Child        , 'i..', c_MUIObject)
    ChildList    = MAttribute(MUIA_Group_ChildList    , '..g', c_pList)
    Columns      = MAttribute(MUIA_Group_Columns      , 'is.', c_LONG)
    Horiz        = MAttribute(MUIA_Group_Horiz        , 'i..', c_BOOL)
    HorizSpacing = MAttribute(MUIA_Group_HorizSpacing , 'isg', c_LONG)
    LayoutHook   = MAttribute(MUIA_Group_LayoutHook   , 'i..', c_Hook)
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
        
        x = kwds.pop('GroupTitle', None)
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

class c_List_ConstructHook(c_Hook): _argtypes_ = (None, long)
class c_List_DestructHook(c_Hook): _argtypes_ = (None, long)
class c_List_DisplayHook(c_Hook): _argtypes_ = (c_pSTRPTR, long)

class List(Group): # TODO: unfinished
    CLASSID = MUIC_List

    Active           = MAttribute(MUIA_List_Active,         'isg', c_LONG)
    AdjustHeight     = MAttribute(MUIA_List_AdjustHeight,   'i..', c_BOOL)
    AdjustWidth      = MAttribute(MUIA_List_AdjustWidth,    'i..', c_BOOL)
    AgainClick       = MAttribute(MUIA_List_AgainClick,     'i.g', c_BOOL)
    AutoVisible      = MAttribute(MUIA_List_AutoVisible,    'isg', c_BOOL)
    ClickColumn      = MAttribute(MUIA_List_ClickColumn,    '..g', c_LONG)
    CompareHook      = MAttribute(MUIA_List_CompareHook,    'is.', c_Hook)
    ConstructHook    = MAttribute(MUIA_List_ConstructHook,  'is.', c_List_ConstructHook)
    DefClickColumn   = MAttribute(MUIA_List_DefClickColumn, 'isg', c_LONG)
    DestructHook     = MAttribute(MUIA_List_DestructHook,   'is.', c_List_DestructHook)
    DisplayHook      = MAttribute(MUIA_List_DisplayHook,    'is.', c_List_DisplayHook)
    DoubleClick      = MAttribute(MUIA_List_DoubleClick,    'i.g', c_BOOL)
    DragSortable     = MAttribute(MUIA_List_DragSortable,   'isg', c_BOOL)
    DragType         = MAttribute(MUIA_List_DragType,       'isg', c_LONG)
    DropMark         = MAttribute(MUIA_List_DropMark,       '..g', c_LONG)
    Entries          = MAttribute(MUIA_List_Entries,        '..g', c_LONG)
    First            = MAttribute(MUIA_List_First,          '..g', c_LONG)
    Format           = MAttribute(MUIA_List_Format,         'isg', c_STRPTR)
    Input            = MAttribute(MUIA_List_Input,          'i..', c_BOOL)
    InsertPosition   = MAttribute(MUIA_List_InsertPosition, '..g', c_LONG)
    MinLineHeight    = MAttribute(MUIA_List_MinLineHeight,  'i..', c_LONG)
    MultiSelect      = MAttribute(MUIA_List_MultiSelect,    'i..', c_LONG)
    MultiTestHook    = MAttribute(MUIA_List_MultiTestHook,  'is.', c_Hook)
    # Pool           = MAttribute(MUIA_List_Pool,           'i.g', c_APTR)
    # PoolPuddleSize = MAttribute(MUIA_List_PoolPuddleSize, 'i..', c_ULONG)
    # PoolThreshSize = MAttribute(MUIA_List_PoolThreshSize, 'i..', c_ULONG)
    Quiet            = MAttribute(MUIA_List_Quiet,          '.s.', c_BOOL)
    ScrollerPos      = MAttribute(MUIA_List_ScrollerPos,    'i..', c_BOOL)
    SelectChange     = MAttribute(MUIA_List_SelectChange,   '..g', c_BOOL)
    ShowDropMarks    = MAttribute(MUIA_List_ShowDropMarks,  'isg', c_BOOL)
    SourceArray      = MAttribute(MUIA_List_SourceArray,    'i..', c_APTR)
    Title            = MAttribute(MUIA_List_Title,          'isg', c_ListTitle)
    TitleClick       = MAttribute(MUIA_List_TitleClick,     '..g', c_LONG)
    Visible          = MAttribute(MUIA_List_Visible,        '..g', c_LONG)

    Clear              = MMethod(MUIM_List_Clear)
    CreateImage        = MMethod(MUIM_List_CreateImage,  [ ('obj', c_MUIObject), ('flags', c_ULONG) ], retype=c_APTR)
    DeleteImage        = MMethod(MUIM_List_DeleteImage,  [ ('listimg', c_APTR) ])
    Compare            = MMethod(MUIM_List_Compare,      [ ('entry1', c_APTR), ('entry2', c_APTR) ], rettype=c_LONG)
    Construct          = MMethod(MUIM_List_Construct,    [ ('entry', c_APTR), ('pool', c_APTR) ], rettype=c_APTR)
    Destruct           = MMethod(MUIM_List_Destruct,     [ ('entry', c_APTR), ('pool', c_APTR) ])
    Display            = MMethod(MUIM_List_Display,      [ ('entry', c_APTR), ('array', c_pSTRPTR) ])
    Insert             = MMethod(MUIM_List_Insert,       [ ('entries', c_APTR), ('count', c_LONG), ('pos', c_LONG) ])
    InsertSingle       = MMethod(MUIM_List_InsertSingle, [ ('entry', c_APTR), ('pos', c_LONG) ])
    Jump               = MMethod(MUIM_List_Jump,         [ ('pos', c_LONG) ])
    Sort               = MMethod(MUIM_List_Sort)
    GetEntry           = MMethod(MUIM_List_GetEntry,     [ ('pos', c_LONG), ('entry', c_APTR._PointerType()) ])

    @Insert.alias
    def Insert(self, meth, objs, pos):
        n = len(objs)
        return meth(c_APTR.ArrayOf(n)(*objs), n, pos)

    @InsertSingle.alias
    def InsertSingleString(self, meth, s, pos=MUIV_List_Insert_Bottom):
        return meth(self, c_STRPTR(s), pos)

    cols = property(fget=lambda self: self.Format.value.count(',')+1)

#===============================================================================

class Floattext(List):
    CLASSID = MUIC_Floattext

    Justify   = MAttribute(MUIA_Floattext_Justify,   'isg', c_BOOL)
    SkipChars = MAttribute(MUIA_Floattext_SkipChars, 'is.', c_STRPTR)
    TabSize   = MAttribute(MUIA_Floattext_TabSize,   'is.', c_LONG)
    Text      = MAttribute(MUIA_Floattext_Text,      'isg', c_STRPTR)
    
#===============================================================================

class Volumelist(List):
    CLASSID = MUIC_Volumelist

    ExampleMode = MAttribute(MUIA_Volumelist_ExampleMode, 'i..', c_BOOL)

#===============================================================================

class Dirlist(List):
    CLASSID = MUIC_Dirlist

    AcceptPattern = MAttribute(MUIA_Dirlist_AcceptPattern, 'is.', c_STRPTR)
    Directory     = MAttribute(MUIA_Dirlist_Directory,     'isg', c_STRPTR)
    DrawersOnly   = MAttribute(MUIA_Dirlist_DrawersOnly,   'is.', c_BOOL)
    ExAllType     = MAttribute(MUIA_Dirlist_ExAllType,     'i.g', c_ULONG)
    FilesOnly     = MAttribute(MUIA_Dirlist_FilesOnly,     'is.', c_BOOL)
    FilterDrawers = MAttribute(MUIA_Dirlist_FilterDrawers, 'is.', c_BOOL)
    FilterHook    = MAttribute(MUIA_Dirlist_FilterHook,    'is.', c_Hook)
    MultiSelDirs  = MAttribute(MUIA_Dirlist_MultiSelDirs,  'is.', c_BOOL)
    NumBytes      = MAttribute(MUIA_Dirlist_NumBytes,      '..g', c_LONG)
    NumDrawers    = MAttribute(MUIA_Dirlist_NumDrawers,    '..g', c_LONG)
    NumFiles      = MAttribute(MUIA_Dirlist_NumFiles,      '..g', c_LONG)
    Path          = MAttribute(MUIA_Dirlist_Path,          '..g', c_STRPTR)
    RejectIcons   = MAttribute(MUIA_Dirlist_RejectIcons,   'is.', c_BOOL)
    RejectPattern = MAttribute(MUIA_Dirlist_RejectPattern, 'is.', c_STRPTR)
    SortDirs      = MAttribute(MUIA_Dirlist_SortDirs,      'is.', c_LONG)
    SortHighLow   = MAttribute(MUIA_Dirlist_SortHighLow,   'is.', c_BOOL)
    SortType      = MAttribute(MUIA_Dirlist_SortType,      'is.', c_LONG)
    Status        = MAttribute(MUIA_Dirlist_Status,        '..g', c_LONG)
    
    ReRead = MMethod(MUIM_Dirlist_ReRead)

#===============================================================================

class Selectgroup(Group):
    CLASSID = MUIC_Selectgroup

#===============================================================================

class Argstring(Group):
    CLASSID = MUIC_Argstring

    Contents = MAttribute(MUIA_Argstring_Contents, 'isg', c_STRPTR)
    Template = MAttribute(MUIA_Argstring_Template, 'isg', c_STRPTR)

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

    Frame  = MAttribute(MUIA_Register_Frame,  'i.g', c_BOOL)
    Titles = MAttribute(MUIA_Register_Titles, 'i.g', c_pSTRPTR)

#===============================================================================

class Backgroundadjust(Area):
    CLASSID = MUIC_Backgroundadjust

#===============================================================================

class Penadjust(Backgroundadjust):
    CLASSID = MUIC_Penadjust

    PSIMode = MAttribute(MUIA_Penadjust_PSIMode, 'i..', c_BOOL)

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

    Type = MAttribute(MUIA_Scrollbar_Type, 'i..', c_LONG)

#===============================================================================

class Listview(Group):
    CLASSID = MUIC_Listview

    AgainClick     = MAttribute(MUIA_Listview_AgainClick,     'i.g', c_BOOL)
    ClickColumn    = MAttribute(MUIA_Listview_ClickColumn,    '..g', c_LONG)
    DefClickColumn = MAttribute(MUIA_Listview_DefClickColumn, 'isg', c_LONG)
    DoubleClick    = MAttribute(MUIA_Listview_DoubleClick,    'i.g', c_BOOL)
    DragType       = MAttribute(MUIA_Listview_DragType,       'isg', c_LONG)
    Input          = MAttribute(MUIA_Listview_Input,          'i..', c_BOOL)
    List           = MAttribute(MUIA_Listview_List,           'i.g', c_MUIObject, postSet=_postSet_Child)
    MultiSelect    = MAttribute(MUIA_Listview_MultiSelect,    'i..', c_LONG)
    ScollerPos     = MAttribute(MUIA_Listview_ScrollerPos,    'i..', c_BOOL)
    SelectChange   = MAttribute(MUIA_Listview_SelectChange,   '..g', c_BOOL)

#===============================================================================

class Radio(Group):
    CLASSID = MUIC_Radio

    Active = MAttribute(MUIA_Radio_Active,   'isg', c_LONG)
    Entries = MAttribute(MUIA_Radio_Entries, 'i..', c_pSTRPTR)

    def __init__(self, Entries, **kwds):
        super(Radio, self).__init__(Entries=Entries, **kwds)

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
    RGB    = MAttribute(MUIA_Coloradjust_RGB    , 'isg', c_ULONG.ArrayOf(3))

#===============================================================================

class c_PaletteEntry(CStructure):
    _fields_ = [ ('mpe_ID', c_LONG),
                 ('mpe_Red', c_ULONG),
                 ('mpe_Green', c_ULONG),
                 ('mpe_Blue', c_ULONG),
                 ('mpe_Group', c_LONG) ]

class Palette(Group):
    CLASSID = MUIC_Palette

    Entries   = MAttribute(MUIA_Palette_Entries,   'i.g', c_PaletteEntry._PointerType())
    Groupable = MAttribute(MUIA_Palette_Groupable, 'isg', c_BOOL)
    Names     = MAttribute(MUIA_Palette_Names,     'isg', c_pSTRPTR)

#===============================================================================

class Popstring(Group):
    CLASSID = MUIC_Popstring

    Button    = MAttribute(MUIA_Popstring_Button   , 'i.g', c_MUIObject, postSet=_postSet_Child)
    CloseHook = MAttribute(MUIA_Popstring_CloseHook, 'isg', c_Hook)
    OpenHook  = MAttribute(MUIA_Popstring_OpenHook , 'isg', c_Hook)
    String    = MAttribute(MUIA_Popstring_String   , 'i.g', c_MUIObject, postSet=_postSet_Child)
    Toggle    = MAttribute(MUIA_Popstring_Toggle   , 'isg', c_BOOL)

    Close = MMethod(MUIM_Popstring_Close, [ ('result', c_LONG) ])
    Open  = MMethod(MUIM_Popstring_Open)

#===============================================================================

class Pubscreenadjust(Group):
    CLASSID = MUIC_Pubscreenadjust

#===============================================================================

class Pubscreenpanel(Group):
    CLASSID = MUIC_Pubscreenpanel

#===============================================================================

class Pubscreenlist(Group):
    CLASSID = MUIC_Pubscreenlist

    Selection = MAttribute(MUIA_Pubscreenlist_Selection, '..g', c_STRPTR)
    
#===============================================================================

class Popobject(Popstring):
    CLASSID = MUIC_Popobject

    Follow     = MAttribute(MUIA_Popobject_Follow,      'isg', c_BOOL)
    Light      = MAttribute(MUIA_Popobject_Light,       'isg', c_BOOL)
    Object     = MAttribute(MUIA_Popobject_Object,      'i.g', c_MUIObject, postSet=_postSet_Child)
    ObjStrHook = MAttribute(MUIA_Popobject_ObjStrHook , 'isg', c_Hook)
    StrObjHook = MAttribute(MUIA_Popobject_StrObjHook,  'isg', c_Hook)
    Volatile   = MAttribute(MUIA_Popobject_Volatile,    'isg', c_BOOL)
    WindowHook = MAttribute(MUIA_Popobject_WindowHook,  'isg', c_Hook)

#===============================================================================

class Poplist(Popobject):
    CLASSID = MUIC_Poplist

    Array = MAttribute(MUIA_Poplist_Array, 'i..', c_pSTRPTR)

    def __init__(self, Array, **kwds):
        super(Cycle, self).__init__(Array=Array, **kwds)

#===============================================================================

class Popscreen(Popobject):
    CLASSID = MUIC_Popscreen

#===============================================================================

_ASL_TB = TAG_USER + 0x80000
ASLFR_DrawersOnly = _ASL_TB + 47
ASLFR_TitleText   = _ASL_TB + 1

class Popasl(Popstring):
    CLASSID = MUIC_Popasl

    Active    = MAttribute(MUIA_Popasl_Active,    '..g', c_BOOL)
    StartHook = MAttribute(MUIA_Popasl_StartHook, 'isg', c_Hook)
    StopHook  = MAttribute(MUIA_Popasl_StopHook,  'isg', c_Hook)
    Type      = MAttribute(MUIA_Popasl_Type,      'i.g', c_ULONG)

    ASLDrawersOnly = MAttribute(ASLFR_DrawersOnly, 'i..', c_BOOL)
    ASLTitle       = MAttribute(ASLFR_TitleText,   'i..', c_STRPTR)


    __type_map = {'FileRequest':        0,
                  'FontRequest':        1,
                  'ScreenModeRequest':  2}

    def __init__(self, Type, **kwds):
        Type = self.__type_map.get(Type, Type)
        Popstring.__init__(self, Type=Type, **kwds)

#===============================================================================

# XXX: this class isn't very usefull on Python
class Semaphore(rootclass):
    CLASSID = MUIC_Semaphore

    Attempt       = MMethod(MUIM_Semaphore_Attempt)
    AttemptShared = MMethod(MUIM_Semaphore_AttemptShared)
    Obtain        = MMethod(MUIM_Semaphore_Obtain)
    ObtainShared  = MMethod(MUIM_Semaphore_ObtainShared)
    Release       = MMethod(MUIM_Semaphore_Release)

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

    AllowMouseEvents = MAttribute(MUIA_Keyadjust_AllowMouseEvents, 'isg', c_BOOL)
    Key              = MAttribute(MUIA_Keyadjust_Key, 'isg', c_STRPTR)

#===============================================================================

class Imagebrowser(Group):
    CLASSID = MUIC_Imagebrowser

#===============================================================================

class Colorring(Group):
    CLASSID = MUIC_Colorring

#===============================================================================

# XXX: Needed?
class Process(Semaphore):
    CLASSID = MUIC_Process
    # TODO

#===============================================================================

class Aboutpage(Mccprefs):
    CLASSID = MUIC_Aboutpage

################################################################################
#################################  END OF FILE  ################################
################################################################################
