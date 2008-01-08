from UserDict import DictMixin
from itertools import chain
import weakref

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

CT_Pointer = _m.CPointer
CT_Bool = bool
CT_Long = int
CT_ULong = long
CT_String = str
CT_MUIObject = _m.MUIObject

MUIV_Window_LeftEdge_Moused = -2
MUIV_Window_TopEdge_Moused  = -2

class MUIMethod:
    def __init__(self, id, t_args=(), t_ret=CT_Long):
        if not isinstance(t_args, tuple):
            raise TypeError("t_args should be a tuple instance, not '%s'" % type(t_args).__name__)
        self.__id = long(id)
        self.__t_ret = t_ret
        self.__t_args = t_args

    def __long__(self):
        return self.__id

    def __int__(self):
        return int(self.__id)

    def bind(self, obj):
        o = weakref.ref(obj)
        def func(*args):
            o()._do(self.id, args)
        return func
    
    id = property(fget=lambda self: self.__id,
                  doc="Returns the id of method.")
    t_ret = property(fget=lambda self: self.__t_ret,
                     doc="Returns the C type of method returns value:")
    t_args = property(fget=lambda self: self.__t_args,
                      doc="Returns a tuple of the C types of method arguments.")


class MUIAttribute:
    def __init__(self, id, isg, type, keep=None):
        assert issubclass(type, (CT_Pointer, CT_Bool, CT_Long, CT_ULong, CT_String))
        isg = isg.lower()  
        if filter(lambda x: x not in 'isgk', isg):
            raise ValueError("isg argument should be a string formed with letters i, s, g or k.")
        self.__id = long(id)
        self.__fl = tuple(x in isg for x in 'isgk')
        self.__tp = type

    def __long__(self):
        return self.__id

    def __int__(self):
        return int(self.__id)

    def __repr__(self):
        return "<Attribute: 0x%x>" % self.__id

    def init(self, obj, value):
        if not self.__fl[0]:
            raise RuntimeError("attribute 0x%x cannot be set at init" % self.id)
        if not issubclass(type(value), self.__tp):
            raise TypeError("Value for attribute 0x%x should of type %s, not %s"
                            % (self.__id, self.__tp.__name__, type(value).__name__))
        obj._init(self.__id, value, self.__fl[3])

    def set(self, obj, value):
        if not self.__fl[1]:
            raise RuntimeError("attribute 0x%x cannot be set" % self.id)
        if not issubclass(type(value), self.__tp):
            raise TypeError("Value for attribute 0x%x should of type %s, not %s"
                            % (self.__id, self.__tp.__name__, type(value).__name__))
        obj._set(self.__id, value, self.__fl[3])
        
    def get(self, obj):
        if not self.__fl[2]:
            raise RuntimeError("attribute %s cannot be get" % self.id)
        return obj._get(self.__tp, self.__id)
    
    id = property(fget=lambda self: self.__id,
                  doc="Returns the id of attribute.")
    type = property(fget=lambda self: self.__tp,
                    doc="Returns the type of attribute.")
    CanInit = property(fget=lambda self: self.__fl[0],
                       doc="Returns True is the attribute can be set at initialisation.")
    CanSet = property(fget=lambda self: self.__fl[1],
                      doc="Returns True is the attribute can be set after initialisation.")
    CanGet = property(fget=lambda self: self.__fl[2],
                      doc="Returns True is the attribute can be get.")
    Keep = property(fget=lambda self: self.__fl[3])
    
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


class MethodsDict(InheritedDict):
    def __init__(self, methods, tagbase=0, *a, **k):
        d = {}
        for t in methods:
            d[t[0].upper()] = MUIMethod(tagbase + t[1], *t[2:])
        super(MethodsDict, self).__init__(d, *a, **k)

    def __getitem__(self, k):
        return super(MethodsDict, self).__getitem__(k.upper())


class AttributesDict(InheritedDict):
    def __init__(self, attributes, tagbase=0, *a, **k):
        d = {}
        for t in attributes:
            d[t[0].upper()] = MUIAttribute(tagbase + t[1], *t[2:])
        super(AttributesDict, self).__init__(d, *a, **k)

    def __getitem__(self, k):
        return super(AttributesDict, self).__getitem__(k.upper())


class MetaPyMCC(type):
    def __new__(meta, name, bases, dct): 
        header = dct.pop('header', name)
        meths = dct.pop('methods', ())
        attrs = dct.pop('attributes', ())

        debug()
        debug('name  :', name)
        debug('bases :', bases)

        dct['__clid'] = dct.pop('classid', name+'.mcc')
        tb = dct.pop('tagbase', 0)

        mdbases = filter(None, (getattr(b, '__mui_meths', None) for b in bases))
        md = dct['__mui_meths'] = MethodsDict(meths, tagbase=tb, bases=mdbases)
        del mdbases

        adbases = filter(None, (getattr(b, '__mui_attrs', None) for b in bases))
        ad = dct['__mui_attrs'] = AttributesDict(attrs, tagbase=tb, bases=adbases)
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


EveryTime = TriggerValue = 0x49893131
NotTriggerValue = 0x49893133

class Notify(CT_MUIObject):
    __metaclass__ = MetaPyMCC

    classid = _m.MUIC_Notify
    header = None
    methods = (
        # (Name, ID [, (<args types>, ) [, <returns type>]])
        ('Export', 0x80420f1c, (CT_Pointer,)),
        )

    attributes = (
        # (Name, ID, <ISG string>, type [, noref])
        ('ApplicationObject',   0x8042d3ee, 'g',        CT_MUIObject),
        ('AppMessage',          0x80421955, 'g',        CT_Pointer),
        ('HelpLine',            0x8042a825, 'isg',      CT_Long),
        ('HelpNode',            0x80420b85, 'isg',      CT_String),
        ('NoNotify',            0x804237f9, 's',        CT_Bool),
        ('ObjectID',            0x8042d76e, 'isg',      CT_ULong),
        ('Parent',              0x8042e35f, 'g',        CT_MUIObject),
        ('Revision',            0x80427eaa, 'g',        CT_Long),
        ('UserData',            0x80420313, 'isg',      CT_ULong),
        ('Version',             0x80422301, 'g',        CT_Long),
        )

    def __init__(self, parent, *a, **k):
        self.PreCreate(parent, *a, **k)
        self.Create(parent, *a, **k)

    def __getattr__(self, k):
        # uses the normal getattr way in first
        # then the MUI attributes search.
        try:
            return super(Notify, self).__getattribute__(k)
        except AttributeError:
            try:
                return self.GetAttribute(k).get(self)
            except KeyError:
                return self.GetMethod(k).bind(self)

    def __setattr__(self, k, v):
        try:
            self.GetAttribute(k).set(self, v)
        except KeyError:
            super(Notify, self).__setattr__(k, v)

    @classmethod
    def GetAttribute(cl, name):
        if isinstance(name, basestring):
            return cl.mui_attributes[name]
        else:
            for attr in cl.mui_attributes.itervalues():
                if attr.id == name: return attr
            raise KeyError("attribute %x not found." % name)

    @classmethod
    def GetAttributeID(cl, name):
        return cl.GetAttribute(name).id

    @classmethod
    def GetMethod(cl, name):
        if isinstance(name, basestring):
            return cl.mui_methods[name]
        else:
            for m in cl.mui_methods.itervalues():
                if m.id == name: return m
            raise KeyError("method %x not found." % name)

    @classmethod
    def GetMethodID(cl, name):
        return cl.GetMethod(name).id

    def PreCreate(self, *a, **k):
        super(Notify, self).__init__(*a, **k)
        self.__nd = {} # notifications dictionary

    def Create(self, parent, **kwds):
        # convert tags keys as MUI attribute instances
        tags = kwds.pop('tags', {})
        for k in tuple(tags):
            if not isinstance(k, MUIAttribute):
                tags[self.GetAttribute(k)] = tags[k]
                del tags[k]

        for k, v in kwds.iteritems():
            tags[self.GetAttribute(k)] = v

        # set defaults
        tags.setdefault(Notify.GetAttribute('ObjectID'), _m.newid())

        # initialize values
        for attr, value in tags.iteritems():
            attr.init(self, value)

        # create the MUI object
        self._create(getattr(self, '__clid'), tags)

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


class Application(Notify):
    classid = _m.MUIC_Application
    header = None
    methods = (
        ('AboutMUI', 0x8042d21d, (CT_MUIObject, )),
        ('ReturnID', 0x804276ef, (CT_ULong, )),
        )
    attributes = (    
        ('Window', 0x8042bfe0, 'ik', CT_MUIObject),
        )

    def __init__(self, *a, **k):
        super(Application, self).__init__(parent=None, *a, **k)
        _m._initapp(self)

    def Mainloop(self):
        _m.mainloop()

    def AttachWindow(self, win):
        self._do(OM_ADDMEMBER, (win, ))


class Window(Notify):
    classid = _m.MUIC_Window
    header = None
    attributes = (
        ('RootObject',      0x8042cba5, 'isgk', CT_MUIObject),
        
        ('LeftEdge',        0x80426c65, 'ig', CT_Long),
        ('TopEdge',         0x80427c66, 'ig', CT_Long),
        ('Width',           0x8042dcae, 'ig', CT_Long),
        ('Height',          0x80425846, 'ig', CT_Long),
        ('Title',           0x8042ad3d, 'isg', CT_String), 
 
        ('CloseRequest',    0x8042e86e, 'g', CT_Bool),
        ('Open',            0x80428aa0, 'sg', CT_Bool),
        )

    def __init__(self, parent, *a, **k):
        #assert isinstance(parent, Application)
        super(Window, self).__init__(parent, *a, **k)
        #parent.AttachWindow(self)

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
    classid = _m.MUIC_Area
    header = None

    attributes = (
        ('Background',  0x8042545b, 'is',   CT_Long),
        ('Frame',       0x8042ac64, 'i',    CT_Long),
        ('InputMode',   0x8042fb04, 'i',    CT_Long),
        ('Draggable',   0x80420b6e, 'isg',  CT_Bool),
        )

class Text(Area):
    classid = _m.MUIC_Text
    header = None
    attributes = (
        ('Contents', 0x8042f8dc, 'isgk', CT_String),
        )

    def __init__(self, parent, text=None, *a, **k):
        if text is not None:
            tags = {'Contents': text}
        else:
            tags = {}
        super(Text, self).__init__(parent, tags=tags, *a, **k)

class Group(Area):
    classid = _m.MUIC_Group
    header = None
 

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
