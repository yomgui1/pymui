###
## \file _core.py
## \author ROGUEZ "Yomgui" Guillaume
##

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
    import _muimaster as _m
    from _muimaster import *
except:
    from simu import *


EveryTime = TriggerValue = 0x49893131
NotTriggerValue = 0x49893133

isiterable = lambda x: hasattr(x, '__iter__')

class InputEventStruct(CStructure):
    def __init__(self, address):
        CStructure.__init__(self, address, 0, "InputEvent")

class MenuItemStruct(CStructure):
    def __init__(self, address):
        CStructure.__init__(self, address, 0, "MenuItem")

class PyMuiInputHandlerNodeStruct(CStructure):
    def __init__(self, address):
        CStructure.__init__(self, address, 0, "MUI_InputHandlerNode")

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

## Convertors used to transfert value between Python and MUI

class MetaConvertor(type):
    """MetaConvertor

    Metaclass for Convertor subclasses classes.
    This metaclass records Convertor subclasses created with ConvertorFactory function.

    See documentation of ConvertorFactory() to create new Convertors.
    
    To obtain a suitable convertor for a given type, call Convertor(type),
    where type is your type object. Raise a KeyError if no convertors have been found
    for this type.
    """
    
    __convs = {} # Convertors depository

    def __new__(metacl, name, bases, dct):
        debug("MetaConvertor.__new__ called:", name)
        
        if name == 'Convertor':
            return type.__new__(metacl, name, bases, dct)
        
        # Check for type attribute
        t = dct['type']
        if not isinstance(t, type):
            raise TypeError("'type' argument should be a type, not %s" % type(t).__name__)

        # Check for format attribute
        f = dct['format']
        if not isinstance(f, str):
            raise TypeError("'format' argument should be a string, not %s" % type(f).__name__)
        if not f:
            raise TypeError("'format' argument should be non empty")

        # Generate a key for recording and check if doesn't exist
        if t in metacl.__convs:
            raise RuntimeError("type %s has already a registered convertor: '%s'" % (t.__name__,
                                                                                     metacl.__convs[k].__name__))

        # Create the ney Convertor class and record it
        conv = type.__new__(metacl, name+'_Convertor', bases, dct)
        metacl.__convs[t] = conv
        return conv

    @staticmethod
    def GetConvertor(x):
        if not isinstance(x, type):
            raise TypeError("%s object is not a type object" % type(x).__name__)
        debug("Searching for a convertor for %s type..." % x.__name__)
        if isinstance(x, Convertor):
            return c            
        if x in MetaConvertor.__convs:
            return MetaConvertor.__convs[x]
        else:
            for k in MetaConvertor.__convs:
                if issubclass(x, k):
                    return MetaConvertor.__convs[k]
        raise KeyError("Cannot find a suitable Convertor class for type %s" % x.__name__)

class Convertor(object):
    __metaclass__ = MetaConvertor
    
    def __new__(cl, obj):
        debug("Convertor.__new__ called:", obj)
        assert not isinstance(obj, Convertor)
        # Create a new object of cl.type type, without calling the __init__ method
        return cl.type.__new__(cl.type, obj)

ConvertorFactory = lambda n, t, f: MetaConvertor(n, (Convertor, ), {'type': t, 'format': f})

# Registring some Convertors
BOOLConvertor = ConvertorFactory('BOOL', bool, 'b')
LONGConvertor = ConvertorFactory('LONG', int, 'i')
ULONGConvertor = ConvertorFactory('ULONG', int, 'I')
APTRConvertor = ConvertorFactory('APTR', CPointer, 'i')
STRPTRConvertor = ConvertorFactory('STRPTR', str, 's')

# PyMuiObjectConvertor()
#   Existance of this class is to convert the representation of a C MUI Object pointer
#   into its corresponding PyMuiObject.
#   Mechanism is implemented directly in C in the new method of PyMuiObject type.
#   But this class is mandatory because when Python will call this new method,
#   it will return the same object, subtype of PyMuiObject and not PyMuiObjectConvertor.
#   As the type argument (PyMuiObjectConvertor so) is not the type or subtype of the
#   returned object, no __init__ method is called. Exactly what we want.
PyMuiObjectConvertor = ConvertorFactory('PyMuiObject', PyMuiObject)

# CArray factory

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

class CArrayIterator:
    def __init__(self, address, type):
        self.array = CPointer(address)
        self.conv = Convertor.GetConvertor(type)
        
    def __iter__(self):
        return self

    def next(self):
        if self.ptr:
            self.ptr = self.ptr.advance()
            if self.ptr:
                return self.create(self.ptr)
        raise StopIteration


CArrayFactory = lambda n, x: MetaCArray(n, (CPointer,), {'type': x})
PyMuiObjectArray = CArrayFactory('PyMuiObjectArray', PyMuiObject)

# Limited string class factory

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

# C List of C Object converted to PyMuiObject

class PyMuiObjectIterator:
    def __init__(self, node):
        self.n = int(node)
        
    def __iter__(self):
        return self

    def next(self):
        if self.n:
            x, self.n = _intui.NextObject(self.n)
            if x:
                return PyMuiObjectConvertor(x)
        raise StopIteration

class PyMuiObjectList(List):
    def __contains__(self, o):
        for x in self:
            if x == o:
                return True

    def __iter__(self):
        return PyMuiObjectIterator(self.head)
    
class PyMuiObjectMinList(PyMuiObjectList):
    def __init__(self, x):
        List.__init__(self, x, True)

# Mixer for PyMuiObject that can contain some other PyMuiObject.

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
### Classes to handle MUI attributes and methods
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

    def __init__(self, id, c_args=(), c_ret=int):
        PyMuiID.__init__(self, id)

        if not isinstance(c_args, tuple):
            raise TypeError("c_args should be a tuple instance, not '%s'" % type(c_args).__name__)

        self.__c_ret = MetaConvertor.GetConvertor(c_ret)
        self.__c_args = tuple(MetaConvertor.GetConvertor(x) for x in c_args)

    def bind(self, obj):
        o = weakref.ref(obj)
        def func(*args):
            o()._do(self.id, args)
        return func

    c_ret = property(fget=lambda self: self.__c_ret,
                     doc="Returns the C convertor of the method returns value:")
    c_args = property(fget=lambda self: self.__c_args,
                      doc="Returns a tuple of the C convertors of method arguments.")

class PyMuiAttribute(PyMuiID):
    _name = 'Attribute'

    def __init__(self, id, isg, conv):
        PyMuiID.__init__(self, id)

        conv = MetaConvertor.GetConvertor(conv)

        isg = isg.lower()
        if filter(lambda x: x not in 'isgk', isg):
            raise ValueError("isg argument should be a string formed with letters i, s, g or k.")

        self.__fl = tuple(x in isg for x in 'isgk')
        self.__conv = conv

    def init(self, obj, value):
        if not self.__fl[0]:
            raise RuntimeError("attribute 0x%x cannot be set at init" % self.id)
        if not isinstance(value, self.type):
            raise TypeError("Value for attribute 0x%x should be of type %s, not %s"
                            % (self.id, self.type.__name__, type(value).__name__))
        obj._init(self.id, value, self.Keep)

    def set(self, obj, value):
        if not self.__fl[1]:
            raise RuntimeError("attribute 0x%x cannot be set" % self.id)
        if not isinstance(value, self.type):
            raise TypeError("Value for attribute 0x%x should be of type %s, not %s"
                            % (self.id, self.type.__name__, type(value).__name__))
        obj._set(self.id, value, self.Keep)

    def get(self, obj):
        if not self.__fl[2]:
            raise RuntimeError("attribute %s cannot be get" % self.id)
        return self.__conv(obj._get(self.id, self.__conv.format))

    type = property(fget=lambda self: self.__conv.type,
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
    __ids = []
    __idscnt = -1
    
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
        type.__init__(cl, name, bases, dct)
        
        debug("\nMethods list for class", name)
        for n, m in dct['__mui_meths'].iteritems():
            debug("  0x%08x: %s" % (m.id, n))

        debug("\nAttributes list for class", name)
        for n, a in dct['__mui_attrs'].iteritems():
            debug("  0x%08x: %-20s (i=%-5s, s=%-5s, g=%-5s)" % (a.id, n, a.CanInit, a.CanSet, a.CanGet))

    mui_methods = property(fget=lambda cl: getattr(cl, '__mui_meths'))
    mui_attributes = property(fget=lambda cl: getattr(cl, '__mui_attrs'))

    @classmethod
    def NewId(cl):
        while True:
            cl.__idscnt += 1
            if cl.__idscnt not in cl.__ids:
                return cl.__idscnt

    @classmethod
    def RecordId(cl, id):
        if cl.__idscnt in cl.__ids:
            raise PyMuiError("ObjectID %u already given" % id)
        cl.__ids.append(id)

class Notify(PyMuiObject):
    __metaclass__ = MetaPyMCC

    CLASSID = MUIC_Notify
    HEADER = None

    METHODS = (
        # (Name, ID [, (<args types>, ) [, <return type>]])

        # Better implemented in Python:
        # CallHook, FindUData, GetUData, SetUData, SetUDataOnce,
        # KillNotify, KillNotifyObj, MultiSet, NoNotifySet, Notify,
        # Set, SetAsString

        # Not documented, so not supported :-P
        # GetConfigItem

        ('Export',      0x80420f1c, (PyMuiObject,)),
        ('Import',      0x8042d012, (PyMuiObject,)),
        ('WriteLong',   0x80428d86, (long, CPointer)),
        ('WriteString', 0x80424bf4, (str, CPointer)),
        )

    ATTRIBUTES = (
        # (Name, ID, <ISGK string>, function)

        ('ApplicationObject', 0x8042d3ee, 'g',        PyMuiObject),
        ('AppMessage',        0x80421955, 'g',        CPointer),
        ('HelpLine',          0x8042a825, 'isg',      int),
        ('HelpNode',          0x80420b85, 'isgk',     str),
        ('NoNotify',          0x804237f9, 's',        bool),
        ('ObjectID',          0x8042d76e, 'isg',      long),
        ('Parent',            0x8042e35f, 'g',        PyMuiObject),
        ('Revision',          0x80427eaa, 'g',        int),
        ('UserData',          0x80420313, 'isg',      long),
        ('Version',           0x80422301, 'g',        int),
        )
    
    def __new__(cl, *args, **kwds):
        # Creating an empty PyMuiObject
        return PyMuiObject.__new__(cl)
    
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

    def HasOption(self, key):
        return key in self.__tags

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

    def PreCreate(self, **kwds):
        self.__tags = PyMuiAttrOptionDict(self, kwds)
        self.__nd = {} # notifications dictionary

    def Create(self, **kwds):
        super(Notify, self).__init__(**kwds)

        tags = self.__tags
        del self.__tags

        # Auto ID generation if not set
        if 'ObjectID' not in tags:
            tags['ObjectID'] = self.__class__.NewId()
        else:
            self.__class__.RecordId(tags['ObjectID'])

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
            raise RuntimeError("Notification raised on attribute %x without Python notifications set!" % id)

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

    def _OnBoopsiMethod(self, id, msg):
        n = hex(id)
        try:
            m = self.GetMethod(id)
        except:
            pass
        else:
            for k, v in self.__class__.mui_methods.iteritems():
                if v.id == m.id:
                    n = k
                    break
        print "MUI wants call method %s, data @ %s" % (n, hex(msg))

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
        # Use AddChild: ('Child', 0x8042c696, 'ik', PyMuiObject),
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
        ('Exclude',       0x80420bc6, 'isg',  int),
        ('Shortcut',      0x80422030, 'isgk', str),
        ('Title',         0x804218be, 'isgk', str),
        ('Toggle',        0x80424d5c, 'isg',  bool),
        ('Trigger',       0x80426f32, 'g',    CPointer), # XXX : real type?
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
        #('AddInputHandler',  0x8042f099, (PyMuiInputHandlerNodeStruct, )),
        ('CheckRefresh',     0x80424d68),
        #('InputBuffered',   0x80427e59),
        ('Load',             0x8042f90d, (str, )),
        #('NewInput',        0x80423ba6, (, )),
        ('OpenConfigWindow', 0x804299ba, (long, )),
        #('PushMethod',      0x80429ef8, (, )),
        #('RemInputHandler',  0x8042e7af, (PyMuiInputHandlerNodeStruct, )),
        ('ReturnID',         0x804276ef, (long, )),
        ('Save',             0x804227ef, (str, )),
        ('SetConfigItem',    0x80424a80, (long, CPointer)),
        ('ShowHelp',         0x80426479, (PyMuiObject, str, str, int)),
        )
    ATTRIBUTES = (    
        ('Active',         0x804260ab, 'isg',  bool),
        ('Author',         0x80424842, 'igk',  str),
        ('Base',           0x8042e07a, 'igk',  str),
        ('Broker',         0x8042dbce, 'g',    CPointer),
        ('BrokerHook',     0x80428f4b, 'isgk', CPointer),
        ('BrokerPort',     0x8042e0ad, 'g',    CPointer),
        ('BrokerPri',      0x8042c8d0, 'ig',   int),
        ('Commands',       0x80428648, 'isgk', CPointer),
        ('Copyright',      0x8042ef4d, 'igk',  str),
        ('Description',    0x80421fc6, 'igk',  str),
        ('DiskObject',     0x804235cb, 'isgk', CPointer),
        ('DoubleStart',    0x80423bc6, 'g',    bool),
        ('DropObject',     0x80421266, 'isk',  PyMuiObject),
        ('ForceQuit',      0x804257df, 'g',    bool),
        ('HelpFile',       0x804293f4, 'isgk', str),
        ('Iconified',      0x8042a07f, 'sg',   bool),
        ('MenuAction',     0x80428961, 'g',    long),
        ('MenuHelp',       0x8042540b, 'g',    long),
        ('Menustrip',      0x804252d9, 'ik',   PyMuiObject),
        ('RexxHook',       0x80427c42, 'isgk', CPointer),
        ('RexxMsg',        0x8042fd88, 'g',    CPointer),
        ('RexxString',     0x8042d711, 's',    str),
        ('SingleTask',     0x8042a2c8, 'i',    bool),
        ('Sleep',          0x80425711, 's',    bool),
        ('Title',          0x804281b8, 'igk',  LimitedStringConvertor(30)),
        ('UseCommodities', 0x80425ee5, 'i',    bool),
        ('UseRexx',        0x80422387, 'i',    bool),
        ('Version',        0x8042b33f, 'igk',  str),
        ('WindowList',     0x80429abe, 'g',    PyMuiObjectList),
        )

    def __init__(self, window=None, **kwds):
        super(Application, self).__init__(**kwds)
        ContainerMixer.__init__(self)
        if window:
            self.AddChild(window)

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

        ('LeftEdge',        0x80426c65, 'ig',   int),
        ('TopEdge',         0x80427c66, 'ig',   int),
        ('Width',           0x8042dcae, 'ig',   int),
        ('Height',          0x80425846, 'ig',   int),

        ('AltLeftEdge',     0x80422d65, 'ig',   int),
        ('AltTopEdge',      0x8042e99b, 'ig',   int),
        ('AltWidth',        0x804260f4, 'ig',   int),
        ('AltHeight',       0x8042cce3, 'ig',   int),

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
        ('ID',                      0x804201bd, 'isg',  long),
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

        ('MenuAction',      0x80427521, 'isg',  long),
        ('Menustrip',       0x8042855e, 'ig',   CPointer),

        ('PublicScreen',    0x804278e4, 'isgk', str),
        ('Screen',          0x8042df4f, 'isgk', _intui.Screen),
        ('ScreenTitle',     0x804234b0, 'isgk', str),
        )

    def __init__(self, title='', **kwds):
        if title:
            kwds['Title'] = title
        self.PreCreate(**kwds)

        if not self.HasOption('RootObject'):
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

    def _IsChild(self, child):
        return self == child.WindowObject

#=============================================================================
# Aboutmui
#-----------------------------------------------------------------------------

class Aboutmui(Window):
    CLASSID = MUIC_Aboutmui
    HEADER = None

    def __init__(self, app=None, *kwds):
        super(Aboutmui, self).__init__(*kwds)
        if app:
           app.AddChild(self)

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
        ('Background',  0x8042545b, 'is',   int),
        ('BottomEdge',  0x8042e552, 'g',    int),
        ('Frame',       0x8042ac64, 'i',    int),
        ('FrameTitle',  0x8042d1c7, 'i',    str),
        ('InputMode',   0x8042fb04, 'i',    int),
        ('Draggable',   0x80420b6e, 'isg',  bool),
        ('WindowObject', 0x8042669e, 'g',   PyMuiObject),
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
# Balance
#-----------------------------------------------------------------------------

class Balance(Area):
    CLASSID = MUIC_Balance
    HEADER = None

#=============================================================================
# Image
#-----------------------------------------------------------------------------

class Image(Area):
    CLASSID = MUIC_Image
    HEADER = None

    ATTRIBUTES = (
        ('FontMatch',       0x8042815d, 'i', bool),
        ('FontMatchHeight', 0x80429f26, 'i', bool),
        ('FontMatchWidth',  0x804239bf, 'i', bool),
        ('FreeHoriz',       0x8042da84, 'i', bool),
        ('FreeVert',        0x8042ea28, 'i', bool),
        #('OldImage',        0x80424f3d, 'i', CPointer),
        ('Spec',            0x804233d5, 'i', str),
        ('State',           0x8042a3ad, 'is', int),
        )

#=============================================================================
# Bitmap
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Bodychunk
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Text
#-----------------------------------------------------------------------------

class Text(Area):
    CLASSID = _m.MUIC_Text
    HEADER = None

    ATTRIBUTES = (
        ('Contents', 0x8042f8dc, 'isgk', str),
        ('PreParse', 0x8042566d, 'isgk', str), # XXX: k ?
        ('HiChar',   0x804218ff, 'i',    int),
        ('SetMax',   0x80424d0a, 'i',    bool),
        ('SetMin',   0x80424e10, 'i',    bool),
        ('SetVMax',  0x80420d8b, 'i',    bool),
        )

    def __init__(self, text='', **kwds):
        kwds.setdefault('Contents', text)
        c = kwds.get('HiChar', None)
        if c and isinstance(HiChar, basestring):
            if len(c) == 1:
                kwds['HiChar'] = ord(HiChar[0])
            else:
                raise TypeError("HiChar expected a character, but string of length %u found" % len(c))
        super(Text, self).__init__(**kwds)

SimpleButton = lambda text: Text(text,
                                 Frame=MUIV_Frame_Button,
                                 InputMode=MUIV_InputMode_RelVerify,
                                 PreParse="\033c")

#=============================================================================
# Gadget
#-----------------------------------------------------------------------------

class Gadget(Area):
    CLASSID = _m.MUIC_Gadget
    HEADER = None

    ATTRIBUTES = (
        ('Gadget', 0x8042ec1a, 'g', CPointer),
        )

#=============================================================================
# String
#-----------------------------------------------------------------------------

MUIV_String_Format_Left   = 0
MUIV_String_Format_Center = 1
MUIV_String_Format_Right  = 2

class String(Gadget):
    CLASSID = _m.MUIC_String
    HEADER = None

    ATTRIBUTES = (
        ('Accept',         0x8042e3e1, 'isgk', str),
        ('Acknowledge',    0x8042026c, 'g',    str),
        ('AdvanceOnCR',    0x804226de, 'isg',  bool),
        ('AttachedList',   0x80420fd2, 'isgk', PyMuiObject),
        ('BufferPos',      0x80428b6c, 'sg',   int),
        ('Contents',       0x80428ffd, 'isgk', str),
        ('DisplayPos',     0x8042ccbf, 'sg',   int),
        #Not supported: ('EditHook',       0x80424c33, 'isg',  CPointer),
        ('Format',         0x80427484, 'ig',   int),
        ('Integer',        0x80426e8a, 'isg',  long),
        ('LonelyEditHook', 0x80421569, 'isg',  bool),
        ('MaxLen',         0x80424984, 'ig',   int),
        ('Reject',         0x8042179c, 'isgk', str),
        ('Secret',         0x80428769, 'ig',   bool),
        )

#=============================================================================
# Boopsi
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Prop
#-----------------------------------------------------------------------------

MUIV_Prop_UseWinBorder_None   = 0
MUIV_Prop_UseWinBorder_Left   = 1
MUIV_Prop_UseWinBorder_Right  = 2
MUIV_Prop_UseWinBorder_Bottom = 3

class Prop(Gadget):
    CLASSID = _m.MUIC_Prop
    HEADER = None

    METHODS = (
        ('Decrease', 0x80420dd1, (int, )),
        ('Increase', 0x8042cac0, (int, )),
        )

    ATTRIBUTES = (
        ('Entries',      0x8042fbdb, 'isg', int),
        ('First',        0x8042d4b2, 'isg', int),
        ('Horiz',        0x8042f4f3, 'ig',  bool),
        ('Slider',       0x80429c3a, 'isg', bool),
        ('UseWinBorder', 0x8042deee, 'i',   int),
        ('Visible',      0x8042fea6, 'isg', int),
        )

#=============================================================================
# Gauge
#-----------------------------------------------------------------------------

class Gauge(Area):
    CLASSID = _m.MUIC_Gauge
    HEADER = None

    ATTRIBUTES = (
        ('Current',  0x8042f0dd, 'isg',  int),
        ('Divide',   0x8042d8df, 'isg',  bool),
        ('Horiz',    0x804232dd, 'i',    bool),
        ('InfoText', 0x8042bf15, 'isgk', str),
        ('Max',      0x8042bcdb, 'isg',  int),
        )

#=============================================================================
# Scale
#-----------------------------------------------------------------------------

class Scale(Area):
    CLASSID = _m.MUIC_Scale
    HEADER = None

    ATTRIBUTES = (
        ('Horiz', 0x8042919a, 'isg', bool),
        )

#=============================================================================
# Colorfield
#-----------------------------------------------------------------------------

class Colorfield(Area):
    CLASSID = _m.MUIC_Colorfield
    HEADER = None

    ATTRIBUTES = (
        ('Blue',  0x8042d3b0, 'isg', long),
        ('Green', 0x80424466, 'isg', long),
        ('Pen',   0x8042713a, 'g',   long),
        ('Red',   0x804279f6, 'isg', long),
        #Not supported: ('RGB',   0x8042677a, 'isg', CPointer),
        )

#=============================================================================
# List
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Floattext
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Volumelist
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Scrmodelist
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Dirlist
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Numeric
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Knob
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Levelmeter
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Numericbutton
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Slider
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Framedisplay
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Popframe
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Imagedisplay
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Popimage
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Pendisplay
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Poppen
#-----------------------------------------------------------------------------

## TODO

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
        ('ActivePage',   0x80424199, 'isg', int),
        ('ChildList',    0x80424748, 'g',   PyMuiObjectList),

        ('Spacing',      0x8042866d, 'is',  int),
        ('HorizSpacing', 0x8042c651, 'isg', int),
        ('VertSpacing',  0x8042e1bf, 'isg', int),

        ('Columns',      0x8042f416, 'is',  int),
        ('Rows',         0x8042b68f, 'is',  int),

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
        return self == child.Parent

HGroup = lambda *args, **kwds: Group(Horiz=True, *args, **kwds)
VGroup = lambda *args, **kwds: Group(Horiz=False, *args, **kwds)

#=============================================================================
# Mccprefs
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Register
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Penadjust
#-----------------------------------------------------------------------------

class Penadjust(Group):
    CLASSID = MUIC_Penadjust
    HEADER = None

    ATTRIBUTES = (
        ('PSIMode', 0x80421cbb, 'i', bool),
        )

#=============================================================================
# Settingsgroup
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Settings
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Frameadjust
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Imageadjust
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Virtgroup
#-----------------------------------------------------------------------------

class Virtgroup(Group):
    CLASSID = MUIC_Virtgroup
    HEADER = None

    ATTRIBUTES = (
        ('Height', 0x80423038, 'g',   int),
        ('Input',  0x80427f7e, 'i',   bool),
        ('Left',   0x80429371, 'isg', int),
        ('Top',    0x80425200, 'isg', int),
        ('Width',  0x80427c49, 'g',   int),
        )

#=============================================================================
# Scrollgroup
#-----------------------------------------------------------------------------

class Scrollgroup(Group):
    CLASSID = MUIC_Scrollgroup
    HEADER = None

    ATTRIBUTES = (
        ('Contents',     0x80421261, 'igk', PyMuiObject),
        ('FreeHoriz',    0x804292f3, 'i',   bool),
        ('FreeVert',     0x804224f2, 'i',   bool),
        ('HorizBar',     0x8042b63d, 'g',   PyMuiObject),
        ('UseWinBorder', 0x804284c1, 'i',   bool),
        ('VertBar',      0x8042cdc0, 'g',   PyMuiObject),
        )

#=============================================================================
# Scrollbar
#-----------------------------------------------------------------------------

MUIV_Scrollbar_Type_Default = 0
MUIV_Scrollbar_Type_Bottom  = 1
MUIV_Scrollbar_Type_Top     = 2
MUIV_Scrollbar_Type_Sym     = 3

class Scrollbar(Group):
    CLASSID = MUIC_Scrollbar
    HEADER = None

    ATTRIBUTES = (
        ('Type', 0x8042fb6b, 'i', int),
        )

#=============================================================================
# Listview
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Radio
#-----------------------------------------------------------------------------

class Radio(Group):
    CLASSID = MUIC_Radio
    HEADER = None

    ATTRIBUTES = (
        ('Active', 0x80429b41, 'isg', int),
        #Not supported: ('Entries', 0x8042b6a1, 'i', ),
        )

#=============================================================================
# Cycle
#-----------------------------------------------------------------------------

class Cycle(Group):
    CLASSID = MUIC_Cycle
    HEADER = None

    ATTRIBUTES = (
        ('Active', 0x80421788, 'isg', int),
        #Not supported: ('Entries', 0x80420629, 'i', ),
        )

#=============================================================================
# Coloradjust
#-----------------------------------------------------------------------------

class Coloradjust(Group):
    CLASSID = MUIC_Coloradjust
    HEADER = None

    ATTRIBUTES = (
        ('Blue',   0x8042b8a3, 'isg', long),
        ('Green',  0x804285ab, 'isg', long),
        ('ModeID', 0x8042ec59, 'isg', long),
        ('Red',    0x80420eaa, 'isg', long),
        #Not supported: ('RGB', 0x8042f899, 'isg', ),
        )

#=============================================================================
# Palette
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Popstring
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Popobject
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Poplist
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Popscreen
#-----------------------------------------------------------------------------

class Popscreen(Group):
    CLASSID = MUIC_Popscreen
    HEADER = None

#=============================================================================
# Popasl
#-----------------------------------------------------------------------------

## TODO

#=============================================================================
# Semaphore
#-----------------------------------------------------------------------------

class Semaphore(Notify):
    CLASSID = MUIC_Semaphore
    HEADER = None

    METHODS = (
        ('Attempt',       0x80426ce2),
        ('AttemptShared', 0x80422551),
        ('Obtain',        0x804276f0),
        ('ObtainShared',  0x8042ea02),
        ('Release',       0x80421f2d),
        )

#=============================================================================
# Applist
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Cclist
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Dataspace
#-----------------------------------------------------------------------------

class Dataspace(Semaphore):
    CLASSID = MUIC_Dataspace
    HEADER = None

    METHODS = (
        ('Add',      0x80423366, (str, int, long)),
        ('Clear',    0x8042b6c9),
        ('Find',     0x8042832c, (long, )),
        #Not supported: ('Merge',    0x80423e2b, (PyMuiObject)),
        #Not supported: ('ReadIFF',  0x80420dfb, (CPointer, )),
        ('Remove',   0x8042dce1, (long, )),
        #Not supported: ('WriteIFF', 0x80425e8e, (CPointer, long, long)),
        )

    ATTRIBUTES = (
        #Not supported: ('Pool', 0x80424cf9, 'i', CPointer),
        )

    def Add(self, data, id):
        return self.DoMuiMethod('Add', data, len(data), id)

#=============================================================================
# Configdata
#-----------------------------------------------------------------------------

## MUI PRIVATE

#=============================================================================
# Dtpic
#-----------------------------------------------------------------------------

class Dtpic(Semaphore):
    CLASSID = MUIC_Dtpic
    HEADER = None
