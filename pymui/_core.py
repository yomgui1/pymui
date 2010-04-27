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

import _muimaster
from _muimaster import *

from defines import *
from types import *
import ctypes as _ct
from ctypes import addressof, string_at

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

class c_Object(_ct.py_object, PyMUICSimpleType):
    def __new__(cl, x=None):
        o = _ct.py_object.__new__(cl)
        if x is not None:
            assert isinstance(x, PyBOOPSIObject)
            o.value = x
        return o

    def __long__(self):
        return self.value._object

    def FromLong(self, v):
        self.value = _muimaster._ptr2pyboopsi(v)

class c_MUIObject(_ct.py_object, PyMUICSimpleType):
    def __new__(cl, x=None):
        o = _ct.py_object.__new__(cl)
        if x is not None:
            assert isinstance(x, PyMUIObject)
            o.value = x
        return o

    def __long__(self):
        return self.value._object

    def FromLong(self, v):
        self.value = _muimaster._ptr2pymui(v)


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
            def _init(obj, x):
                x = (x if isinstance(x, ctype) else ctype(x))
                return c_ULONG.from_address(addressof(x)).value
        else:
            def _init(*args):
                raise AttributeError("attribute %08x can't be used at init" % self.__id)

        if 's' in isg:
            def _setter(obj, x, nn=False):
                x = c_ULONG.from_address(addressof(x if isinstance(x, ctype) else ctype(x))).value
                if nn:
                    obj._nnset(id, x)
                else:
                    obj._set(id, x)
        else:
            _setter = None

        if 'g' in isg:
            def _getter(obj):
                return ctype(obj._get(id))
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
            self.__msgtype = type('c_MUIP_%x' % id, (c_STRUCTURE,), {'_fields_': [ ('MethodID', c_ULONG) ] + fields})
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
            self.__msgtype = type('c_MUIP_%x' % id, (c_STRUCTURE,), {'_fields_': [ ('MethodID', c_ULONG) ]})

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

class BOOPSIMetaClass(type):
    def __new__(metacl, name, bases, dct):
        clid = dct.pop('CLASSID', None)
        if not clid:
            clid = [ base._bclassid for base in bases if hasattr(base, '_bclassid') ]
            if not len(clid):
                raise TypeError("No valid BOOPSI class name found")
            clid = clid[0]

        dct['_bclassid'] = clid

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
        

class MUIMetaClass(BOOPSIMetaClass):
    def __new__(metacl, name, bases, dct):
        dct['isMCC'] = bool(dct.pop('MCC', False))

        if dct['isMCC']:
            if not any(hasattr(base, '__pymui_overloaded__') for base in bases):
                dct['__pymui_overloaded__'] = {}

        return BOOPSIMetaClass.__new__(metacl, name, bases, dct)

    def __init__(cl, name, bases, dct):
        BOOPSIMetaClass.__init__(cl, name, bases, dct)

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
    """muimethod(MethodID) -> function

    MCC class method decorator to declare the decorated method to be called
    by BOOPSI when the given MethodID is used by a DoMethod() call.

    The given MethodID argument can be a interger or an instance of MAttribute.

    Note: an MCC class shall define 'MCC' class attribute to True to be used
    as an MCC with overloading methods and not as normal class.
    """
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


def postset_child(self, attr, o):
    o._loosed()

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

    def AddChild(self, o):
        self._addchild(o)

    def RemChild(self, o):
        self._remchild(o)

    def Dispose(self):
        self._dispose()


################################################################################
#### Official Public Classes
################################################################################

#===============================================================================

class BOOPSIRootClass(PyBOOPSIObject, BOOPSIMixin):
    """rootclass for all BOOPSI sub-classes.

    ATTENTION: You can't create instance of this class!
    """

    __metaclass__ = BOOPSIMetaClass
    CLASSID = "rootclass"

    # filter out parameters for the class C interface
    def __new__(cl, *args, **kwds):
        return PyBOOPSIObject.__new__(cl)

    def __init__(self, **kwds):
        PyBOOPSIObject.__init__(self)

#===============================================================================

class c_NotifyHook(c_Hook): _argtypes_ = (c_MUIObject, c_APTR.PointerType())

class Notify(PyMUIObject, BOOPSIMixin):
    """rootclass for all MUI sub-classes.
    """
    
    __metaclass__ = MUIMetaClass
    CLASSID = MUIC_Notify

    ApplicationObject = MAttribute(MUIA_ApplicationObject, '..g', c_MUIObject)
    AppMessage        = MAttribute(MUIA_AppMessage,        '..g', c_APTR)
    HelpLine          = MAttribute(MUIA_HelpLine,          'isg', c_LONG)
    HelpNode          = MAttribute(MUIA_HelpNode,          'isg', c_STRPTR)
    NoNotify          = MAttribute(MUIA_NoNotify,          '.s.', c_BOOL)
    NoNotifyMethod    = MAttribute(MUIA_NoNotifyMethod,    '.s.', c_ULONG)
    ObjectID          = MAttribute(MUIA_ObjectID,          'isg', c_ULONG)
    Parent            = MAttribute(MUIA_Parent,            '..g', c_MUIObject)
    Revision          = MAttribute(MUIA_Revision,          '..g', c_LONG)
    UserData          = MAttribute(MUIA_UserData,          'isg', c_ULONG)
    Version           = MAttribute(MUIA_Version,           '..g', c_LONG)

    CallHook = MMethod(MUIM_CallHook, [ ('hook', c_NotifyHook) ], varargs=True)

    # filter out parameters for the class C interface
    def __new__(cl, *args, **kwds):
        return PyMUIObject.__new__(cl, kwds.pop('_address', 0))

    def __init__(self, **kwds):
        self.precreate(**kwds)
        self.create(**kwds)
        self.postcreate(**kwds)
        
    def precreate(self, **kwds):
        PyMUIObject.__init__(self)
        
    def postcreate(self, **kwds): pass

    def create(self, **kwds):
        if self._object: return
        
        extra = kwds.pop('muiargs', [])

        # convert given keywords as long
        muiargs = [(self._getMAByName(k).id, v) for k,v in kwds] + extra
        
        self._create(self._bclassid, muiargs)
        
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
    DropObject     = MAttribute(MUIA_Application_DropObject,     'is.', c_MUIObject, postSet=postset_child)
    ForceQuit      = MAttribute(MUIA_Application_ForceQuit,      '..g', c_BOOL)
    HelpFile       = MAttribute(MUIA_Application_HelpFile,       'isg', c_STRPTR)
    Iconified      = MAttribute(MUIA_Application_Iconified,      '.sg', c_BOOL)
    MenuAction     = MAttribute(MUIA_Application_MenuAction,     '..g', c_ULONG)
    MenuHelp       = MAttribute(MUIA_Application_MenuHelp,       '..g', c_ULONG)
    Menustrip      = MAttribute(MUIA_Application_Menustrip,      'i..', c_MUIObject, postSet=postset_child)
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
    Window         = MAttribute(MUIA_Application_Window,         'i..', c_MUIObject, postSet=postset_child)
    WindowList     = MAttribute(MUIA_Application_WindowList,     '..g', c_pList)

    AboutMUI         = MMethod(MUIM_Application_AboutMUI,         [ ('refwindow', c_MUIObject) ])
    ##AddInputHandler
    ##BuildSettingsPanel
    CheckRefresh     = MMethod(MUIM_Application_CheckRefresh)
    ##DefaultConfigItem
    InputBuffered    = MMethod(MUIM_Application_InputBuffered)
    Load             = MMethod(MUIM_Application_Load,             [ ('name', c_STRPTR) ])
    #NewInput         = MMethod(MUIM_Application_NewInput,         [ ('signal', c_ULONG.PointerType()) ])
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

    def __init__(self, mainwin=None, **kwds):
        super(Application, self).__init__(**kwds)

        if mainwin:
            self.AddChild(mainwin)
            mainwin.Notify(MUIA_Window_Open, False, lambda e: e.Source.KillApp())

    def AddChild(self, win):
        assert isinstance(win, Window)
        super(Application, self).AddChild(win)

    def RemChild(self, win):
        assert isinstance(win, Window)
        super(Application, self).RemChild(win)
        win.Open = False
        # win may be not owned anymore, let user decide to dispose it

    def Run(self):
        _muimaster.mainloop(self)

    def Quit(self):
        self.ReturnID(MUIV_Application_ReturnID_Quit)

    @AboutMUI.alias
    def AboutMUI(self, meth, refwin=None):
        meth(self, refwin)


################################################################################
#################################  END OF FILE  ################################
################################################################################
