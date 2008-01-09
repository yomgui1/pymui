from UserDict import DictMixin
from itertools import chain
import weakref
from pyamiga._core import Struct
import pyamiga.intuition as _intuition

debugme = False

if debugme:
    import sys
    def debug(msg='', *a):
        print msg,
        for x in a:
            print x,
        print
else:
    def debug(msg='', *a):
        pass

try:
    from _muimaster import *
    import _muimaster as _m
except:
    from simu import *

CT_POINTER = _m.CPointer
CT_LONG = int
CT_ULONG = long

EveryTime = TriggerValue = 0x49893131
NotTriggerValue = 0x49893133

class PyMuiObject(_m.MUIObject):
    pass

class InputEventStruct(Struct):
    def __init__(self, address):
        Struct.__init__(self, address, 0, "InputEvent")
        

##############################################################################
### ERRORS
##############################################################################
    
class PyMuiKeyError(KeyError):
    name = 'Key'
    def __init__(self, cl, key):
        super(PyMuiKeyError, self).__init__()
        self.cl = cl
        
        if isinstance(self.key, basestring):
            self.key = key
        else:
            self.key = hex(key)
            
    def __str__(self):
        return "%s %s doesn't exist for PyMUI class %s." % (self.name, self.key, self.cl.__name__)


class PyMuiAttributeError(PyMuiKeyError):
    name = 'Attribute'


class PyMuiMethodError(PyMuiKeyError):
    name = 'Method'


class PyDisposedObjectError(AttributeError):
    pass


class _PyDisposedObject(object):
    reprStr = "Python wrapper for DISPOSED %s object! (The MUI object no longer exists.)"
    attrStr = "The MUI part of the %s object has been deleted, attribute access no longer allowed."

    def __repr__(self):
        if not hasattr(self, "_name"):
            self._name = "[unknown]"
        return self.reprStr % self._name
    
    def __getattr__(self, *args):
        if not hasattr(self, "_name"):
            self._name = "[unknown]"
        raise PyDisposedObjectError(self.attrStr % self._name)

    def __nonzero__(self):
        return 0


class PyMuiContainerMixer:
    def __init__(self, unique=False):
        self.__unique = unique
        self.__children = []
        
    def AddChild(self, child):
        assert isinstance(child, PyMuiObject) and child
        assert child not in self.__children

        if self._AddChild(child):
            if self.__unique and self.__children:
                self.__children[0] = child # XXX usage of weakref, duplicate with 'k' flag ?
            else:
                self.__children.append(child)
            return True
        return False

    def RemChild(self, child):
        assert isinstance(child, PyMuiObject) and child
        assert child in self.__children
        self.__children.remove(child)
        return self._RemChild(child)

    def _AddChild(self, child):
        raise NotImplemented('Class using PyMuiContainerMixer without implementing _AddChild method')


class PyMuiChildMixer:
    def __init__(self, parent):
        "Should be called after Create (or super __init__)"
        
        self.PyParent = parent
        parent.AddChild(self)

    def __GetPyParent(self):
        return self.__parent

    def __SetPyParent(self, parent):
        assert isinstance(parent, PyMuiObject) and parent
        self._CheckParent(parent)
        self.__parent = parent

    def _CheckParent(self, parent):
        pass

    PyParent = property(fget=__GetPyParent, fset=__SetPyParent)
    

class PyMuiContainerAndChildMixer(PyMuiContainerMixer, PyMuiChildMixer):
    def __init__(self, parent, **kwds):
        "Should be called after Create (or super __init__)"
        
        PyMuiContainerMixer.__init__(self, **kwds)
        PyMuiChildMixer.__init__(self, parent)


##############################################################################
### Attributes and methods tools
##############################################################################

class PyMuiID:
    """PyMuiID(id) -> instance

    id: [integer value] ID value

    Note for subclasses: attribute '_name' should be defined as a class name
    """
    def __init__(self, id):
        self.__id = long(id)
        
    def __long__(self):
        return self.__id

    def __int__(self):
        return int(self.__id)

    def __repr__(self):
        return "<%s: 0x%x>" % (self._name, self.__id)

    id = property(fget=lambda self: self.__id,
                  doc="Returns the id of %s." % self._name)


class PyMuiMethod(PyMuiID):
    _name = 'Method'
    
    def __init__(self, id, t_args=(), t_ret=CT_LONG):
        PyMuiID.__init__(self, id)
        
        if not isinstance(t_args, tuple):
            raise TypeError("t_args should be a tuple instance, not '%s'" % type(t_args).__name__)

        self.__t_ret = t_ret
        self.__t_args = t_args

    def bind(self, obj):
        o = weakref.ref(obj)
        def func(*args):
            o()._do(self.id, args)
        return func
    
    t_ret = property(fget=lambda self: self.__t_ret,
                     doc="Returns the C type of method returns value:")
    t_args = property(fget=lambda self: self.__t_args,
                      doc="Returns a tuple of the C types of method arguments.")


class PyMuiAttribute(PyMuiID):
     _name = 'Attribute'
     
    def __init__(self, id, isg, type):
        PyMuiID.__init__(self, id)
        
        assert issubclass(type, (CT_Pointer, bool, CT_LONG, CT_ULONG, str))
        
        isg = isg.lower()
        if filter(lambda x: x not in 'isgk', isg):
            raise ValueError("isg argument should be a string formed with letters i, s, g or k.")
        
        self.__fl = tuple(x in 'isgk' for x in isg)
        self.__tp = type

    def init(self, obj, value):
        if not self.__fl[0]:
            raise RuntimeError("attribute 0x%x cannot be set at init" % self.id)
        if not issubclass(type(value), self.__tp):
            raise TypeError("Value for attribute 0x%x should be of type %s, not %s"
                            % (self.id, self.__tp.__name__, type(value).__name__))
        obj._init(self.id, value, self.Keep)

    def set(self, obj, value):
        if not self.__fl[1]:
            raise RuntimeError("attribute 0x%x cannot be set" % self.id)
        if not issubclass(type(value), self.__tp):
            raise TypeError("Value for attribute 0x%x should be of type %s, not %s"
                            % (self.id, self.__tp.__name__, type(value).__name__))
        obj._set(self.id, value, self.Keep)
        
    def get(self, obj):
        if not self.__fl[2]:
            raise RuntimeError("attribute %s cannot be get" % self.id)
        if issubclass(self.__tp, Struct):
            return self.__tp(obj._get(CT_POINTER, self.id))
        return obj._get(self.__tp, self.id)
    
    type = property(fget=lambda self: self.__tp,
                    doc="Returns the type of attribute.")
    CanInit = property(fget=lambda self: self.__fl[0],
                       doc="Returns True if the attribute can be set at initialisation.")
    CanSet = property(fget=lambda self: self.__fl[1],
                      doc="Returns True if the attribute can be set after initialisation.")
    CanGet = property(fget=lambda self: self.__fl[2],
                      doc="Returns True if the attribute can be get.")
    Keep = property(fget=lambda self: self.__fl[3],
                    doc="Returns True if set() should keep track that the value is used by MUI.")


class PyMuiAttrOptionDict(object, DictMixin):
    def __init__(self, obj):
        self.__mcl = obj.__class__
        self.__d = {}

    def __getitem__(self, key):
        return self.__d[self.__mcl.GetAttribute(key)]
    
    def __setitem__(self, key, value):
        self.__d[self.__mcl.GetAttribute(key)] = value

    def keys(self):
        return self.__d.keys()

    def iteritems(self):
        return self.__d.iteritems()


class InheritedDict(object, DictMixin):
    def __init__(self, dct, bases=()):
        self.__bases = bases
        self.__d = dct

    def __getitem__(self, k):
        if k in self.__d:
            return self.__d[k]

        else:
            for b in self.__bases:
                try:
                    return b[k]
                except:
                    pass

        raise KeyError("key not found: %s" % k)

    def __setitem__(self, *a, **k):
        raise RuntimeError("Inherided Dict are not mutable")

    def __delitem__(self, *a, **k):
        raise RuntimeError("Inherided Dict are not mutable")

    def keys(self):
        s = set(self.__d.keys())
        for b in self.__bases:
            s.update(b.keys())
        return list(s)

    def iteritems(self):
        return chain(self.__d.iteritems(), *chain(b.iteritems() for b in self.__bases))


class PyMuiMethodDict(InheritedDict):
    def __init__(self, methods, tagbase=0, *a, **k):
        d = {}
        for t in methods:
            d[t[0].upper()] = PyMuiMethod(tagbase + t[1], *t[2:])
        super(PyMuiMethodDict, self).__init__(d, *a, **k)

    def __getitem__(self, k):
        return super(PyMuiMethodDict, self).__getitem__(k.upper())


class PyMuiAttributeDict(InheritedDict):
    def __init__(self, attributes, tagbase=0, *a, **k):
        d = {}
        for t in attributes:
            d[t[0].upper()] = PyMuiAttribute(tagbase + t[1], *t[2:])
        super(PyMuiAttributeDict, self).__init__(d, *a, **k)

    def __getitem__(self, k):
        return super(PyMuiAttributeDict, self).__getitem__(k.upper())


##############################################################################
### PyMCC base
##############################################################################
    
class MetaPyMCC(type):
    def __new__(meta, name, bases, dct):
        debug()
        debug('name  :', name)
        debug('bases :', bases)
        
        # Fetch some class customization constants
        header = dct.pop('HEADER', name)
        meths = dct.pop('METHODS', ())
        attrs = dct.pop('ATTRIBUTES', ())
        tb = dct.pop('TAGBASE', 0)

        # Finding the right MUI ClassID name
        dct['__clid'] = dct.pop('classid', name+'.mcc')

        # Methods dict creation
        mdbases = filter(None, (getattr(b, '__mui_meths', None) for b in bases))
        md = dct['__mui_meths'] = PyMuiMethodDict(meths, tagbase=tb, bases=mdbases)
        del mdbases

        # Attributes dict creation
        adbases = filter(None, (getattr(b, '__mui_attrs', None) for b in bases))
        ad = dct['__mui_attrs'] = PyMuiAttributeDict(attrs, tagbase=tb, bases=adbases)
        del adbases
        
        debug('dct   :', sorted(dct.keys()))
        return type.__new__(meta, name, bases, dct)

    def __init__(cl, name, bases, dct):
        debug("\nMethods list for class", name)
        for n, m in dct['__mui_meths'].iteritems():
            debug("  0x%08x: %s" % (m.id, n))

        debug("\nAttributes list for class", name)
        for n, a in dct['__mui_attrs'].iteritems():
            debug("  0x%08x: %-20s (i=%-5s, s=%-5s, g=%-5s)" % (a.id, n, a.CanInit, a.CanSet, a.CanGet))

    mui_methods = property(fget=lambda cl: getattr(cl, '__mui_meths'))
    mui_attributes = property(fget=lambda cl: getattr(cl, '__mui_attrs'))
        
    
class Notify(PyMuiObject):
    __metaclass__ = MetaPyMCC
    
    CLASSID = _m.MUIC_Notify
    HEADER = None
    
    METHODS = (
        # (Name, ID [, (<args types>, ) [, <returns type>]])
        
        ('Export', 0x80420f1c, (CT_POINTER,)),
        )
    
    ATTRIBUTES = (
        # (Name, ID, <ISGK string>, type)
        
        ('ApplicationObject',   0x8042d3ee, 'g',        PyMuiObject),
        ('AppMessage',          0x80421955, 'g',        CT_POINTER),
        ('HelpLine',            0x8042a825, 'isg',      CT_LONG),
        ('HelpNode',            0x80420b85, 'isg',      str),
        ('NoNotify',            0x804237f9, 's',        bool),
        ('ObjectID',            0x8042d76e, 'isg',      CT_ULONG),
        ('Parent',              0x8042e35f, 'g',        PyMuiObject),
        ('Revision',            0x80427eaa, 'g',        CT_LONG),
        ('UserData',            0x80420313, 'isg',      CT_ULONG),
        ('Version',             0x80422301, 'g',        CT_LONG),
        )
    
    def __init__(self, **kwds):
        self.PreCreate(**kwds)
        self.Create(**kwds)
        
    def __getattr__(self, k):
        # uses the normal getattr way in first
        # then the MUI attributes search.
        try:
            return super(Notify, self).__getattribute__(k)
        except AttributeError:
            try:
                return self.GetAttribute(k).get(self)
            except PyMuiAttributeError:
                return self.GetMethod(k).bind(self)

    def __setattr__(self, k, v):
        try:
            self.GetAttribute(k).set(self, v)
        except PyMuiAttributeError:
            super(Notify, self).__setattr__(k, v)

    @classmethod
    def GetAttribute(cl, name):
        if isinstance(name, basestring) and name in cl.mui_attributes:
            return cl.mui_attributes[name]
        else:
            for a in cl.mui_attributes.itervalues():
                if a.id == name: return a
        raise PyMuiAttributeError(cl, name)

    @classmethod
    def GetAttributeID(cl, name):
        return cl.GetAttribute(name).id

    @classmethod
    def HasAttribute(cl, name):
        if isinstance(name, basestring) and name in cl.mui_attributes:
            return True
        else:
            for a in cl.mui_attributes.itervalues():
                if a.id == name: return True
            return False

    @classmethod
    def GetMethod(cl, name):
        if isinstance(name, basestring) and name in cl.mui_methods:
            return cl.mui_methods[name]
        else:
            for m in cl.mui_methods.itervalues():
                if m.id == name: return m
        raise PyMuiMethodError(cl, name)
    
    @classmethod
    def GetMethodID(cl, name):
        return cl.GetMethod(name).id

    @classmethod
    def HasMethod(cl, name):
        if isinstance(name, basestring) and name in cl.mui_methods:
            return True
        else:
            for m in cl.mui_methods.itervalues():
                if m.id == name: return True
            return False

    def GetOption(self, key):
        return self.__tags[key]

    def SetOption(self, key, value):
        self.__tags[key] = value

    def SetOptions(self, **kwds):
        for k, v in kwds.iteritems():
            self.__tags[k] = v

    def PreCreate(self, tags=None, **kwds):
        self.__tags = tags or PyMuiAttrOptionDict(self)
        assert isinstance(self.__tags, PyMuiAttrOptionDict)
        self.__tags.update(kwds)
        self.__nd = {} # notifications dictionary

    def Create(self, **kwds):
        super(Notify, self).__init__(**kwds)

        tags = self.__tags
        del self.__tags
        
        # set defaults
        if 'ObjectID' in not tags:
            tags['ObjectID'] = _m.newid()

        # initialize object tags
        for attr, value in tags.iteritems():
            attr.init(self, value)

        # create the MUI object
        self._create(getattr(self, '__clid'), tags)

    def Dispose(self):
        if !self._dispose():
            self.__class__ = _PyDisposedObject
            return False
        return True

    def Notify(self, attr, value, callback, *args):
        """Notify(attr, value, callback, *args) -> bool
        
        Call this function to create a new Notification event
        on the calling instance object.
        If an MUI attribute is changing to the given value,
        the 'callback' is called with given arguments 'args')

        attr: attribute to notify. Can be an Attribute instance,
            an integer ID or a string.
            If a string is used, the attribute ID is retrived by
            searching the given string in the MUI attributes dictionary
            of the class. The searching is case insensitive.
            Then, if not founded, the string is searched as a global and
            the ID used is the returns of long() on this variable found.

        value: can be any CT_xxx type value, depends on attribute ID.
        Can also be the special attribute 'mui.EveryTime'.
        """

        attr = self.GetAttribute(attr)
        if not isinstance(value, attr.type):
            raise ValueError("value should be of type %s, not %s" % (attr.type, type(value)))
        self.AddNotification(attr, callback, args)
        self._notify(attr.id, value)

    def AddNotification(self, attr, callback, args):
        if not hasattr(callback, '__call__'):
            raise ValueError("callback should be a callable.")
        if attr.id not in self.__nd:
            nl = self.__nd[attr.id] = []
        else:
            nl = self.__nd[attr.id]
        nl.append((callback, args))

    def RemNotification(self, attr, callback, args):
        if attr.id not in self.__nd:
            raise ValueError("Attribute %x hasn't got any notifications on instance %s." % self)

        nl = self.__nd[attr.id]
        for t in nl:
            if t[0] is callback:
                nl.remove(t)
                return
            
        raise ValueError("No notification recorded for attribute %x and callback %s" % (attr.id, callback))

    def _OnAttrChanged(self, id, value):
        if id not in self.__nd:
            raise RuntimeError("Notification raised on attribute %x without Python notifications set." % id)

        for callback, args in self.__nd[id]:
            _a = []
            for x in args:
                if x == TriggerValue:
                    _a.append(value)
                elif x == NotTriggerValue:
                    _a.append(~value)
                else:
                    _a.append(x)
                
            callback(*_a)

    def _GetAttrType(self, attr):
        return self.GetAttribute(attr).type

#=============================================================================
# Application
#-----------------------------------------------------------------------------

class Application(Notify, PyMuiContainerMixer):
    CLASSID = _m.MUIC_Application
    HEADER = None
    
    METHODS = (
        ('AboutMUI', 0x8042d21d, (PyMuiObject, )),
        ('ReturnID', 0x804276ef, (CT_ULONG, )),
        )
    ATTRIBUTES = (    
        ('Window', 0x8042bfe0, 'ik', PyMuiObject),
        )

    def __init__(self, *args, **kwds):
        super(Application, self).__init__(*args, **kwds)
        PyMuiContainerMixer.__init__()
        _m._initapp(self)

    def Mainloop(self):
        _m.mainloop()
        
    def _AddChild(self, child):
        assert isinstance(child, Window)
        self._do(OM_ADDMEMBER, (child, ))
        return child.ApplicationObject is self

#=============================================================================
# Window
#-----------------------------------------------------------------------------

MUIV_Window_ActiveObject_None    = 0
MUIV_Window_ActiveObject_Next    = -1
MUIV_Window_ActiveObject_Prev    = -2
MUIV_Window_AltHeight_MinMax     = lambda p: 0 - p
MUIV_Window_AltHeight_Visible    = lambda p: -100 - p
MUIV_Window_AltHeight_Screen     = lambda p: -200 - p
MUIV_Window_AltHeight_Scaled     = -1000
MUIV_Window_AltLeftEdge_Centered = -1
MUIV_Window_AltLeftEdge_Moused   = -2
MUIV_Window_AltLeftEdge_NoChange = -1000
MUIV_Window_AltTopEdge_Centered  = -1
MUIV_Window_AltTopEdge_Moused    = -2
MUIV_Window_AltTopEdge_Delta     = lambda p: -3 - p
MUIV_Window_AltTopEdge_NoChange  = -1000
MUIV_Window_AltWidth_MinMax      = lambda p: 0 - p
MUIV_Window_AltWidth_Visible     = lambda p: -100 - p
MUIV_Window_AltWidth_Screen      = lambda p: -200 - p
MUIV_Window_AltWidth_Scaled      = -1000
MUIV_Window_Height_MinMax        = lambda p: 0 - p
MUIV_Window_Height_Visible       = lambda p: -100 - p
MUIV_Window_Height_Screen        = lambda p: -200 - p
MUIV_Window_Height_Scaled        = -1000
MUIV_Window_Height_Default       = -1001
MUIV_Window_LeftEdge_Centered    = -1
MUIV_Window_LeftEdge_Moused      = -2
MUIV_Window_TopEdge_Centered     = -1
MUIV_Window_TopEdge_Moused       = -2
MUIV_Window_TopEdge_Delta        = lambda p: -3 - p
MUIV_Window_Width_MinMax         = lambda p: 0 - p
MUIV_Window_Width_Visible        = lambda p: -100 - p
MUIV_Window_Width_Screen         = lambda p: -200 - p
MUIV_Window_Width_Scaled         = -1000
MUIV_Window_Width_Default        = -1001

class Window(Notify, PyMuiContainerAndChildMixer):
    """Window(parent, title=None, root=None, ...) -> instance

    Python class wrapper for MUI Window object.

    parent:     an Application or Window instance.
    title:      default window title. Empty string by default.
    rootobject: content of PyMui object. If None uses DefaultObject tags.

    others arguments: see the Notify.
    
    If an application is given for parent, the window is attached during initialisation
    of the instance object. If it's a window, the created window is considered as a
    sub-window of this parent.
    """
    
    CLASSID = _m.MUIC_Window
    HEADER = None
    
    ATTRIBUTES = (
        ('RootObject',      0x8042cba5, 'isgk', PyMuiObject),
        ('DefaultObject',   0x804294d7, 'isgk', PyMuiObject),

        ('IsSubWindow',     0x8042b5aa, 'isg',  bool),
        ('RefWindow',       0x804201f4, 'isk',  PyMuiObject),

        ('LeftEdge',        0x80426c65, 'ig',   CT_LONG),
        ('TopEdge',         0x80427c66, 'ig',   CT_LONG),
        ('Width',           0x8042dcae, 'ig',   CT_LONG),
        ('Height',          0x80425846, 'ig',   CT_LONG),
        
        ('AltLeftEdge',     0x80422d65, 'ig',   CT_LONG),
        ('AltTopEdge',      0x8042e99b, 'ig',   CT_LONG),
        ('AltWidth',        0x804260f4, 'ig',   CT_LONG),
        ('AltHeight',       0x8042cce3, 'ig',   CT_LONG),
        
        ('AppWindow',       0x804280cf, 'i',    bool),
        ('Backdrop',        0x8042c0bb, 'i',    bool),
        ('Borderless',      0x80429b79, 'i',    bool),
        ('CloseGadget',     0x8042a110, 'i',    bool),
        ('DepthGadget',     0x80421923, 'i',    bool),
        ('DragBar',         0x8042045d, 'i',    bool),
        ('NeedsMouseObject',0x8042372a, 'i',    bool),
        ('SizeGadget',      0x8042e33d, 'i',    bool),
        ('SizeRight',       0x80424780, 'i',    bool),

        ('Activate',        0x80428d2f, 'isg',  bool),
        ('NoMenus',         0x80429df5, 'is',   bool),
        
        ('FancyDrawing',            0x8042bd0e, 'isg',  bool),
        ('ID',                      0x804201bd, 'isg',  CT_ULONG),
        ('Title',                   0x8042ad3d, 'isgk', str),
        ('UseBottomBorderScroller', 0x80424e79, 'isg',  bool),
        ('UseLeftBorderScroller',   0x8042433e, 'isg',  bool),
        ('UseRightBorderScroller',  0x8042c05e, 'isg',  bool),
      
        ('Sleep',           0x8042e7db, 'sg',   bool),
        ('Open',            0x80428aa0, 'sg',   bool),
        ('CloseRequest',    0x8042e86e, 'g',    bool),
        ('InputEvent',      0x804247d8, 'g',    InputEventStruct),

        ('ActiveObject',    0x80427925, 'sg',   PyMuiObject),
        ('MouseObject',     0x8042bf9b, 'g',    CT_POINTER),

        ('MenuAction',      0x80427521, 'isg',  CT_ULONG),
        ('Menustrip',       0x8042855e, 'ig',   CT_POINTER),
        
        ('PublicScreen',    0x804278e4, 'isgk', str),
        ('Screen',          0x8042df4f, 'isgk', _intuition.Screen),
        ('ScreenTitle',     0x804234b0, 'isgk', str),
        )

    def __init__(self, parent, title='', root=None, **kwds):
        self.PreCreate(**kwds)
        root = root or self.GetOption('RootObject')
        if root: self.SetOption('RootObject', root)
        self.SetOptions(Title=title)

        if isinstance(parent, Window):
            self.SetOptions(IsSubWindow=True, RefWindow=parent)

        self.Create(**kwds)
        PyMuiContainerAndChildMixer.__init__(self, parent, unique=True)

    def _CheckParent(self, parent):
        if not isinstance(parent, (Application, Window)):
            raise TypeError("parent object should be instance of Application"
                            "or Window, not %s." % parent.__class__.__name__)

    def _AddChild(self, child):
        self.RootObject = child
        return self.RootObject is child

    def _RemChild(self, child):
        raise RuntimeError("You can't remove the root object of a window.")

#=============================================================================
# Aboutmui
#-----------------------------------------------------------------------------

class Aboutmui(Window):
    CLASSID = _m.MUIC_Aboutmui
    HEADER = None

    ATTRIBUTES = (
        ('Application', 0x80422523, 'i', PyMuiObject),
        )

    def __init__(self, parent, **kwds):
        Window.__init__(self, parent, **kwds)

    def _CheckParent(self, parent):
        if not isinstance(parent, Application):
            raise TypeError("parent object should be an Application object"
                            ", not %s." % parent.__class__.__name__)

    def _AddChild(self, child):
        # Aboutmui cannot accept children
        return False
        
#=============================================================================
# Area
#-----------------------------------------------------------------------------

MUIV_Frame_None         = 0
MUIV_Frame_Button       = 1
MUIV_Frame_ImageButton  = 2
MUIV_Frame_Text         = 3
MUIV_Frame_String       = 4
MUIV_Frame_ReadList     = 5
MUIV_Frame_InputList    = 6
MUIV_Frame_Prop         = 7
MUIV_Frame_Gauge        = 8
MUIV_Frame_Group        = 9
MUIV_Frame_PopUp        = 10
MUIV_Frame_Virtual      = 11
MUIV_Frame_Slider       = 12
MUIV_Frame_Count        = 13

MUIV_InputMode_None         = 0
MUIV_InputMode_RelVerify    = 1
MUIV_InputMode_Immediate    = 2
MUIV_InputMode_Toggle       = 3

class Area(Notify):
    CLASSID = _m.MUIC_Area
    HEADER = None
    ATTRIBUTES = (
        #('', , 'isg', ),
        ('Background',  0x8042545b, 'is',   CT_LONG),
        ('Frame',       0x8042ac64, 'i',    CT_LONG),
        ('InputMode',   0x8042fb04, 'i',    CT_LONG),
        ('Draggable',   0x80420b6e, 'isg',  bool),
        )

#=============================================================================
# Text
#-----------------------------------------------------------------------------

class Text(Area):
    classid = _m.MUIC_Text
    header = None
    attributes = (
        ('Contents', 0x8042f8dc, 'isgk', str),
        )

    def __init__(self, text=None, *a, **k):
        if text is not None:
            tags = {'Contents': text}
        else:
            tags = {}
        super(Text, self).__init__(tags=tags, *a, **k)


class Group(Area):
    CLASSID = _m.MUIC_Group
    HEADER = None

if __name__ == '__main__':
    o = Notify()
    print
    print dir(o)
    print 'methods:', ' '.join(o.__class__.mui_methods)
    print 'attributes:', ' '.join(o.__class__.mui_attributes)
    print "Get ObjectID value..."
    v = o.ObjectID
    print "ObjectID =", v
    v = 125L
    print "Set ObjectID to", v
    o.ObjectID = v
    print "Try lowlevel call..."
    v = o._get(long, 0x8042d76e)
    print "ObjectID =", v
