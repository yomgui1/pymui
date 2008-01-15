##
## @file _core.py
## @author ROGUEZ "Yomgui" Guillaume
##

## TODO
##
# General:
# * adding twice or more a child causes endless loop at dispose().
# => Add a checking in AddChild() method.

#### Designing a class ####
#
## Attributes:
#


from UserDict import DictMixin
from itertools import chain
import weakref
from pyamiga._core import *
from pyamiga._exec import List, Node
import pyamiga.intuition as _intui

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

CT_LONG = int
CT_ULONG = long

EveryTime = TriggerValue = 0x49893131
NotTriggerValue = 0x49893133

isiterable = lambda x: hasattr(x, '__iter__')

class InputEventStruct(Struct):
    def __init__(self, address):
        Struct.__init__(self, address, 0, "InputEvent")

class MenuItemStruct(Struct):
    def __init__(self, address):
        Struct.__init__(self, address, 0, "MenuItem")

class PyMuiInputHandlerNodeStruct(Struct):
    def __init__(self, address):
        Struct.__init__(self, address, 0, "MUI_InputHandlerNode")

class MetaLimitedString(type):
    def __new__(metacl, name, bases, dct):
        limit = dct.pop('limit', 0)
        cl = type.__new__(metacl, name, bases, dct)
        cl.__limit = limit
        return cl

    def __setLimit(cl, limit):
        assert limit >= 0
        cl.__limit = limit

    limit = property(fget=lambda cl: cl.__limit,
                     fset=__setLimit)

class LimitedStringBase(str):
    def __init__(self, *args, **kwds):
        str.__init__(self, *args, **kwds)
        if len(self) > self.__class__.limit:
            raise ValueError("String too long (limited to %lu)" % self.__class__.limit)

LimitedStringFactory = lambda n, x: MetaLimitedString(n, (LimitedStringBase,), {'limit': x})

class MetaCArray(type):
    def __new__(metacl, name, bases, dct):
        limit = dct.pop('type', 0)
        cl = type.__new__(metacl, name, bases, dct)
        cl.__type = type
        return cl

    def __setLimit(cl, limit):
        assert limit >= 0
        type.__limit = limit

    type = property(fget=lambda cl: cl.__type)

CArrayFactory = lambda n, x: MetaCArray(n, (CPointer,), {'type': x})

PyMuiObjectArray = CArrayFactory('PyMuiObjectArray', PyMuiObject)

##############################################################################
### ERRORS
##############################################################################

class PyMuiKeyError(KeyError):
    name = 'Key'

    def __init__(self, cl, key):
        KeyError.__init__(self)
        self.cl = cl

        if isinstance(key, basestring):
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

class PyMuiError(Exception):
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

##############################################################################
### Basic classes
##############################################################################

class PyMuiObjectIterator:
    def __init__(self, node):
        assert isinstance(node, Node)
        self.node = node
        
    def __iter__(self):
        return self

    def next(self):
        if self.node:
            addr, self.node = _intui.NextObject(self.node)
            if addr:
                return PyMuiObject(addr)
        raise StopIteration

class PyMuiObjectList(List):
    def __contains__(self, o):
        for x in self:
            if x == o:
                return True

    def __iter__(self):
        return PyMuiObjectIterator(self.head)
    
class PyMuiObjectMinList(PyMuiObjectList):
    def __init__(self, address):
        List.__init__(self, address, True)

class ContainerMixer:
    def __init__(self):
        self.__children = set()

    def _AddChild(self, child):
        raise NotImplementedError("Class %s doesn't implement method _AddChild" % self.__class__.__name__)

    def _RemChild(self, child):
        raise NotImplementedError("Class %s doesn't implement method _RemChild" % self.__class__.__name__)

    def _IsChild(self, child):
        raise NotImplementedError("Class %s doesn't implement method _IsChild" % self.__class__.__name__)

    def __contains__(self, child):
        if child in self.__children:
            return True
        if self._IsChild(child):
            self.__children.add(child)
            return True
        return False

    def CheckChild(self, child):
        assert isinstance(child, PyMuiObject)
        self._CheckChild(child)
        if hasattr(child, 'CheckParent'):
            child.CheckParent(self)

    def AddChild(self, child):
        if isiterable(child):
            for o in child:
                if o in self:
                    raise PyMuiError("object %s already child of %s\n" % (o, self))
                self.CheckChild(o)
                if not self._AddChild(o):
                    return False
                self.__children.add(o)
            return True
        elif not child:
            raise TypeError('null child')
        elif child in self:
            raise PyMuiError("object %s already child of %s\n" % (child, self))
        else:
            self.CheckChild(child)
            if self._AddChild(child):
                self.__children.add(child)
                return True
            return False

    def RemChild(self, child):
        if isiterable(child):
            for o in child:
                if o not in self:
                    raise PyMuiError("object %s is not a child of %s\n" % (o, self))
                self.CheckChild(o)
                if not self._RemChild(o):
                    return False
                self.__children.remove(o)
            return True
        elif not child:
            raise TypeError('null child')
        elif child in self:
            raise PyMuiError("object %s is not a child of %s\n" % (child, self))
        else:
            self.CheckChild(o)   
            if self._RemChild(child):
                self.__children.remove(child)
                return True
            return False

    children = property(fget=lambda self: iter(self.__children),
                        doc="Iterable on a list of children")

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

    def __hex__(self):
        return hex(self.__id)

    def __repr__(self):
        return "<%s: 0x%x>" % (self._name, self.__id)

    id = property(fget=lambda self: self.__id,
                  doc="Returns the id.")

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

        assert issubclass(type, (Struct, CPointer, bool, CT_LONG, CT_ULONG, str))

        isg = isg.lower()
        if filter(lambda x: x not in 'isgk', isg):
            raise ValueError("isg argument should be a string formed with letters i, s, g or k.")

        self.__fl = tuple(x in isg for x in 'isgk')
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
            return self.__tp(obj._get(CPointer, self.id))
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
    def __init__(self, obj, options):
        self.__mcl = obj.__class__
        self.__d = {}
        self.update(options)

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
        if bases:
            header = getattr(bases[0], '__header', name)
        else:
            header = name
        header = dct.pop('HEADER', header)

        meths = dct.pop('METHODS', ())
        attrs = dct.pop('ATTRIBUTES', ())

        if bases:
            tb = getattr(bases[0], '__tb', 0)
        else:
            tb = 0
        tb = dct.pop('TAGBASE', tb)

        dct['__header'] = header
        dct['__tb'] = tb

        # Finding the right MUI ClassID name
        clid = name+'.mcc'
        if bases:
            clid = getattr(bases[0], '__clid', clid)
        dct['__clid'] = dct.pop('CLASSID', clid)

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

    CLASSID = MUIC_Notify
    HEADER = None

    METHODS = (
        # (Name, ID [, (<args types>, ) [, <returns type>]])

        # Better implemented in Python:
        # CallHook, FindUData, GetUData, SetUData, SetUDataOnce,
        # KillNotify, KillNotifyObj, MultiSet, NoNotifySet, Notify,
        # Set, SetAsString

        # Not documented, so not supported :-P
        # GetConfigItem

        ('Export',      0x80420f1c, (PyMuiObject,)),
        ('Import',      0x8042d012, (PyMuiObject,)),
        ('WriteLong',   0x80428d86, (CT_ULONG, CPointer)),
        ('WriteString', 0x80424bf4, (str, CPointer)),
        )

    ATTRIBUTES = (
        # (Name, ID, <ISGK string>, type)

        ('ApplicationObject', 0x8042d3ee, 'g',        PyMuiObject),
        ('AppMessage',        0x80421955, 'g',        CPointer),
        ('HelpLine',          0x8042a825, 'isg',      CT_LONG),
        ('HelpNode',          0x80420b85, 'isgk',     str),
        ('NoNotify',          0x804237f9, 's',        bool),
        ('ObjectID',          0x8042d76e, 'isg',      CT_ULONG),
        ('Parent',            0x8042e35f, 'g',        PyMuiObject),
        ('Revision',          0x80427eaa, 'g',        CT_LONG),
        ('UserData',          0x80420313, 'isg',      CT_ULONG),
        ('Version',           0x80422301, 'g',        CT_LONG),
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
        if isinstance(name, basestring):
            if name in cl.mui_attributes:
                return cl.mui_attributes[name]
        else:
            n = long(name)
            for a in cl.mui_attributes.itervalues():
                if a.id == n: return a
        raise PyMuiAttributeError(cl, name)

    @classmethod
    def GetAttributeID(cl, name):
        return cl.GetAttribute(name).id

    @classmethod
    def HasAttribute(cl, name):
        if isinstance(name, basestring):
            if name in cl.mui_attributes:
                return True
        else:
            n = long(name)
            for a in cl.mui_attributes.itervalues():
                if a.id == n: return True
            return False

    @classmethod
    def GetMethod(cl, name):
        if isinstance(name, basestring):
            if name in cl.mui_methods:
                return cl.mui_methods[name]
        else:
            n = long(name)
            for m in cl.mui_methods.itervalues():
                if m.id == n: return m
        raise PyMuiMethodError(cl, name)

    @classmethod
    def GetMethodID(cl, name):
        return cl.GetMethod(name).id

    @classmethod
    def HasMethod(cl, name):
        if isinstance(name, basestring):
            if name in cl.mui_methods:
                return True
        else:
            n = long(name)
            for m in cl.mui_methods.itervalues():
                if m.id == n: return True
            return False

    def GetOption(self, key, default=None):
        try:
            return self.__tags[key]
        except KeyError:
            return default

    def SetOption(self, key, value):
        self.__tags[key] = value

    def SetOptions(self, **kwds):
        for k, v in kwds.iteritems():
            self.__tags[k] = v

    def PreCreate(self, tags=None, **kwds):
        if not isinstance(tags, PyMuiAttrOptionDict):
            self.__tags = PyMuiAttrOptionDict(self, tags)
        else:
            self.__tags = tags
        self.__tags.update(kwds)
        self.__nd = {} # notifications dictionary

    def Create(self, **kwds):
        super(Notify, self).__init__(**kwds)

        tags = self.__tags
        del self.__tags

        # set defaults
        if 'ObjectID' not in tags:
            tags['ObjectID'] = _m.newid()

        # initialize object tags
        for attr, value in tags.iteritems():
            attr.init(self, value)

        # create the MUI object
        return self._create(getattr(self, '__clid'), dict(tags))

    def Dispose(self):
        if not self._dispose():
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

    def _OnBoopsiMethod(self, id, msg):
        print "MUI wants call method %s , data @ %s" % (hex(id), hex(msg))

    def Set(self, attr, value):
        self.GetAttribute(attr).set(self, value)

    def AddMember(self, obj):
        return self._do(OM_ADDMEMBER, (obj,))

    def RemMember(self, obj):
        return self._do(OM_REMMEMBER, (obj,))

#=============================================================================
# Family
#-----------------------------------------------------------------------------

class Family(Notify):
    CLASSID = MUIC_Family
    HEADER = None

    METHODS = (
        ('AddHead',  0x8042e200, (PyMuiObject, )),
        ('AddTail',  0x8042d752, (PyMuiObject, )),
        ('Insert',   0x80424d34, (PyMuiObject, PyMuiObject)),
        ('Remove',   0x8042f8a9, (PyMuiObject, )),
        ('Sort',     0x80421c49, (PyMuiObject, CPointer)),
        ('Transfer', 0x8042c14a, (PyMuiObject, PyMuiObjectArray)),
        )

    ATTRIBUTES = (    
        #('Child', 0x8042c696, 'ik', PyMuiObject),
        ('List',   0x80424b9e, 'g',  PyMuiObjectMinList),
        )

#=============================================================================
# Menustrip
#-----------------------------------------------------------------------------

class Menustrip(Family):
    CLASSID = MUIC_Menustrip
    HEADER = None

    ATTRIBUTES = (    
        ('Enabled', 0x8042815b, 'isg', bool),
        )

#=============================================================================
# Menu
#-----------------------------------------------------------------------------

class Menu(Family):
    CLASSID = MUIC_Menu
    HEADER = None

    ATTRIBUTES = (    
        ('Enabled', 0x8042ed48, 'isg',  bool),
        ('Title',   0x8042a0e3, 'isgk', str),
        )

#=============================================================================
# Menuitem
#-----------------------------------------------------------------------------

MUIV_Menuitem_Shortcut_Check = -1

class Menuitem(Family):
    CLASSID = MUIC_Menuitem
    HEADER = None

    ATTRIBUTES = (    
        ('Checked',       0x8042562a, 'isg',  bool),
        ('Checkit',       0x80425ace, 'isg',  bool),
        ('CommandString', 0x8042b9cc, 'isg',  bool),
        ('Enabled',       0x8042ae0f, 'isg',  bool),
        ('Exclude',       0x80420bc6, 'isg',  CT_LONG),
        ('Shortcut',      0x80422030, 'isgk', str),
        ('Title',         0x804218be, 'isgk', str),
        ('Toggle',        0x80424d5c, 'isg',  bool),
        ('Trigger',       0x80426f32, 'g',    MenuItemStruct),
        )

#=============================================================================
# Application
#-----------------------------------------------------------------------------

class Application(Notify, ContainerMixer):
    """Application(...) -> instance

    Python wrapper on MUI Application class.
    """
    
    CLASSID = MUIC_Application
    HEADER = None

    METHODS = (
        ('AboutMUI',         0x8042d21d, (PyMuiObject, )),
        ('AddInputHandler',  0x8042f099, (PyMuiInputHandlerNodeStruct, )),
        ('CheckRefresh',     0x80424d68),
        #('InputBuffered',   0x80427e59),
        ('Load',             0x8042f90d, (str, )),
        #('NewInput',        0x80423ba6, (, )),
        ('OpenConfigWindow', 0x804299ba, (CT_ULONG, )),
        #('PushMethod',      0x80429ef8, (, )),
        ('RemInputHandler',  0x8042e7af, (PyMuiInputHandlerNodeStruct, )),
        ('ReturnID',         0x804276ef, (CT_ULONG, )),
        ('Save',             0x804227ef, (str, )),
        ('SetConfigItem',    0x80424a80, (CT_ULONG, CPointer)),
        ('ShowHelp',         0x80426479, (PyMuiObject, str, str, CT_LONG)),
        )
    ATTRIBUTES = (    
        ('Active',         0x804260ab, 'isg',  bool),
        ('Author',         0x80424842, 'igk',  str),
        ('Base',           0x8042e07a, 'igk',  str),
        ('Broker',         0x8042dbce, 'g',    CPointer),
        ('BrokerHook',     0x80428f4b, 'isgk', CPointer),
        ('BrokerPort',     0x8042e0ad, 'g',    CPointer),
        ('BrokerPri',      0x8042c8d0, 'ig',   CT_LONG),
        ('Commands',       0x80428648, 'isgk', CPointer),
        ('Copyright',      0x8042ef4d, 'igk',  str),
        ('Description',    0x80421fc6, 'igk',  str),
        ('DiskObject',     0x804235cb, 'isgk', CPointer),
        ('DoubleStart',    0x80423bc6, 'g',    bool),
        ('DropObject',     0x80421266, 'isk',  PyMuiObject),
        ('ForceQuit',      0x804257df, 'g',    bool),
        ('HelpFile',       0x804293f4, 'isgk', str),
        ('Iconified',      0x8042a07f, 'sg',   bool),
        ('MenuAction',     0x80428961, 'g',    CT_ULONG),
        ('MenuHelp',       0x8042540b, 'g',    CT_ULONG),
        ('Menustrip',      0x804252d9, 'ik',   PyMuiObject),
        ('RexxHook',       0x80427c42, 'isgk', CPointer),
        ('RexxMsg',        0x8042fd88, 'g',    CPointer),
        ('RexxString',     0x8042d711, 's',    str),
        ('SingleTask',     0x8042a2c8, 'i',    bool),
        ('Sleep',          0x80425711, 's',    bool),
        ('Title',          0x804281b8, 'igk',  LimitedStringFactory('AppTitleStr', 30)),
        ('UseCommodities', 0x80425ee5, 'i',    bool),
        ('UseRexx',        0x80422387, 'i',    bool),
        ('Version',        0x8042b33f, 'igk',  str),
        #('window',         0x8042bfe0, 'i',    PyMuiObject),
        ('WindowList',     0x80429abe, 'g',    PyMuiObjectList),
        )

    def __init__(self, Window=None, *args, **kwds):
        super(Application, self).__init__(*args, **kwds)
        ContainerMixer.__init__(self)
        self.AddChild(Window)

    def Init(self):
        pass

    def Term(self):
        pass

    def Run(self):
        self.Init()
        try:
            _m.mainloop(self)
        finally:
            self.Term()

    def CheckParent(self, parent):
        raise SyntaxError("Application instance cannot be a child of anything")

    #
    ## Children handling functions requested by the ContainerMixer class
    #

    def _CheckChild(self, child):
        if not isinstance(child, Window):
            raise TypeError("Application accept only Window instances as children")

    def _AddChild(self, child):
        return self.AddMember(child)

    def _RemChild(self, child):
        return self.RemMember(child)

    def _IsChild(self, child):
        return child in self.WindowList

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

class Window(Notify, ContainerMixer):
    """Window(title='', root=None, ...) -> instance

    Python class wrapper for MUI Window object.

    title: default window title. Empty string by default.
    root:  content of PyMui object. If None uses DefaultObject tags.

    others arguments: see the Notify.
    """

    CLASSID = MUIC_Window
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
        ('MouseObject',     0x8042bf9b, 'g',    CPointer),

        ('MenuAction',      0x80427521, 'isg',  CT_ULONG),
        ('Menustrip',       0x8042855e, 'ig',   CPointer),

        ('PublicScreen',    0x804278e4, 'isgk', str),
        ('Screen',          0x8042df4f, 'isgk', _intui.Screen),
        ('ScreenTitle',     0x804234b0, 'isgk', str),
        )

    def __init__(self, title='', **kwds):
        if title:
            kwds['Title'] = title
        self.PreCreate(**kwds)

        root = PyMuiObject()
        root._create(MUIC_Rectangle)

        self.SetOption('RootObject', root)

        self.Create(**kwds)
        ContainerMixer.__init__(self)      

    def CheckParent(self, parent):
        if not isinstance(parent, (Application, Window)):
            raise TypeError("parent object should be instance of Application"
                            "or Window, not %s." % parent.__class__.__name__)

    def _CheckChild(self, child):
        if not isinstance(child, Area):
            raise TypeError("parent object should be instance of Area"
                            ", not %s." % parent.__class__.__name__)

    def _AddChild(self, child):
        self.RootObject = child
        if self.RootObject is child:
            child.IsSubWindow = True
            child.RefWindow = self
            return True

    def _RemChild(self, child):
        raise RuntimeError("You can't remove the root object of a window. Use AddChild().")

#=============================================================================
# Aboutmui
#-----------------------------------------------------------------------------

class Aboutmui(Window):
    CLASSID = MUIC_Aboutmui
    HEADER = None

    ATTRIBUTES = (
        ('Application', 0x80422523, 'i', PyMuiObject),
        )

    def __init__(self, app=None):
        self.PreCreate()
        if app is not None:
            self.SetOption('Application', app)
        self.Create()

    def CheckParent(self, parent):
        if not isinstance(parent, Application):
            raise TypeError("parent object should be an Application object"
                            ", not %s." % parent.__class__.__name__)

    def _CheckChild(self, child):
        raise SyntaxError("Aboutmui instance doesn't accept children")

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
        ('Background',  0x8042545b, 'is',   CT_LONG),
        ('BottomEdge',  0x8042e552, 'g',    CT_LONG),
        ('Frame',       0x8042ac64, 'i',    CT_LONG),
        ('FrameTitle',  0x8042d1c7, 'i',    str),
        ('InputMode',   0x8042fb04, 'i',    CT_LONG),
        ('Draggable',   0x80420b6e, 'isg',  bool),
        )

    def CheckParent(self, parent):
        if not isinstance(parent, (Window, Group)):
            raise TypeError("parent should be Group or Window instance"
                            ", not %s." % parent.__class__.__name__)

#=============================================================================
# Rectangle
#-----------------------------------------------------------------------------

class Rectangle(Area):
    CLASSID = MUIC_Rectangle
    HEADER = None
    ATTRIBUTES = (
        ('BarTitle', 0x80426689, 'ig',   str),
        ('HBar',     0x8042c943, 'ig',   bool),
        ('VBar',     0x80422204, 'ig',   bool),
        )

HVSpace = lambda p: Rectangle(p)

#=============================================================================
# Text
#-----------------------------------------------------------------------------

class Text(Area):
    CLASSID = _m.MUIC_Text
    HEADER = None

    ATTRIBUTES = (
        ('Contents', 0x8042f8dc, 'isgk', str),
        ('PreParse', 0x8042566d, 'isgk', str),
        ('HiChar',   0x804218ff, 'i',    CT_LONG),
        )

    def __init__(self, text='', **kwds):
        kwds.setdefault('Contents', text)
        super(Text, self).__init__(**kwds)

SimpleButton = lambda text: Text(text,
                                 Frame=MUIV_Frame_Button,
                                 InputMode=MUIV_InputMode_RelVerify,
                                 PreParse="\033c")

#=============================================================================
# Group
#-----------------------------------------------------------------------------

MUIV_Group_ActivePage_First   =  0
MUIV_Group_ActivePage_Last    = -1
MUIV_Group_ActivePage_Prev    = -2
MUIV_Group_ActivePage_Next    = -3
MUIV_Group_ActivePage_Advance = -4

class Group(Area, ContainerMixer):
    CLASSID = MUIC_Group
    HEADER = None

    ATTRIBUTES = (
        ('ActivePage',   0x80424199, 'isg', CT_LONG),
        ('ChildList',    0x80424748, 'g',   PyMuiObjectList),

        ('Spacing',      0x8042866d, 'is',  CT_LONG),
        ('HorizSpacing', 0x8042c651, 'isg', CT_LONG),
        ('VertSpacing',  0x8042e1bf, 'isg', CT_LONG),

        ('Columns',      0x8042f416, 'is',  CT_LONG),
        ('Rows',         0x8042b68f, 'is',  CT_LONG),

        ('Horiz',        0x8042536b, 'i',   bool),
        ('SameHeight',   0x8042037e, 'i',   bool),
        ('SameWidth',    0x8042b3ec, 'i',   bool),
        ('SameSize',     0x80420860, 'i',   bool),
        ('PageMode',     0x80421a5f, 'i',   bool),
        ('LayoutHook',   0x8042c3b2, 'i',   CPointer),
        )

    def __init__(self, *args, **kwds):
        Area.__init__(self, *args, **kwds)
        ContainerMixer.__init__(self) 

    def _CheckChild(self, child):
        if not isinstance(child, Area):
            raise TypeError("Group accept only Area instances as children")

    def _AddChild(self, child):
        return self.AddMember(child)

    def _RemChild(self, child):
        return self.RemMember(child)

    def _IsChild(self, child):
        return child.Parent is self

HGroup = lambda *args, **kwds: Group(Horiz=True, *args, **kwds)
VGroup = lambda *args, **kwds: Group(Horiz=False, *args, **kwds)

