###
## \file _core.py
## \author ROGUEZ "Yomgui" Guillaume
##

import sys, functools

try:
    DEBUG = sys.argv[1] == '-v'
except:
    DEBUG = False

def debug(x, *args):
    if DEBUG:
        print x % args

try:
    assert __name__ != "__main__"
    from _muimaster import *
except: # For testing => use stubs
    class PyBOOPSIObject(object):
        def _create(self, i, sid=None, a={}):
            debug("Stubs: %s._create(%s, %s, %s)", self.__class__.__name__, i, sid, repr(a))
        def _set(self, i, v):
            debug("Stubs: %s._set(0x%x, %s)", self.__class__.__name__, i, repr(v))
        def _get(self, i, fmt):
            debug("Stubs: %s._get(0x%x, '%s')", self.__class__.__name__, i, fmt)
        def _do(self, i, *args):
            debug("Stubs: %s._do(0x%x, %s)", self.__class__.__name__, i, tuple(args))
        def _do1(self, i, arg):
            debug("Stubs: %s._do(0x%x, %s)", self.__class__.__name__, i, repr(arg))
        def _add(self, o, l=False):
            debug("Stubs: %s._add(%s, %s)", self.__class__.__name__, repr(o), bool(l))
        def _rem(self, o, l=False):
            debug("Stubs: %s._add(%s, %s)", self.__class__.__name__, repr(o), bool(l))
        
    class PyMUIObject(PyBOOPSIObject):
        def __init__(self, **kwds):
            self.__children = []
        def _nnset(self, *args):
            pass
        def _notify(self, *args):
            pass
        def __del_children(self):
            self._children = []
        _children = property(fget=lambda self: self.__children, fdel=__del_children)
    
from defines import *
import weakref

MUI_EventHandlerRC_Eat = (1<<0)

class AttributeInfo:
    def __init__(self, value, args):
        if type(value) not in (int, long):
            raise TypeError("Value argument shall be int or long")
        self._value = value
        self._name, self._format, isg = args
        if isg not in ('i..', '.s.' , '..g', 'is.', 'i.g', '.sg', 'isg'):
            raise ValueError("Not recognized ISG value: '%s'" % isg)
        self._isg = isg.lower()

    value = property(fget=lambda self: self._value)
    name = property(fget=lambda self: self._name)
    format = property(fget=lambda self: self._format)
    mode = property(fget=lambda self: self._isg)
    isinit = property(fget=lambda self: 'i' in self._isg)
    isset = property(fget=lambda self: 's' in self._isg)
    isget = property(fget=lambda self: 'g' in self._isg)

import array

class ArrayOf(object):
    def __init__(self, itemtype, size=0):
        self.pointer_base = str(itemtype)[0]
        self.size = size

    def set(self, obj):
        return array.array(self.pointer_base, obj).tostring()


##
## MetaMCC takes some predefined class attributes and use it to fill the class dict
## with usefull dict for raw functions.
##

class MetaMCC(type):
    def __new__(metacl, name, bases, dct):
        clid = dct.pop('CLASSID', None)
        if not clid:
            clid = [base._classid for base in bases if hasattr(base, '_classid')]
            if not len(clid):
                raise TypeError("No valid MUI class name found")
            clid = clid[0]

        dct['_'+name+'__muiclassid'] = clid
        dct['_'+name+'__id_meths'] = dct.pop('METHODS', {})

        kw = {}
        attrs = {}
        for k,v in dct.pop('ATTRIBUTES', {}).iteritems():
            x = AttributeInfo(k, v)
            
            # filter for doublons
            if x.name in kw:
                raise RuntimeError("Attribute %s already given" % x.name)
            if x.value in attrs:
                raise RuntimeError("Attribute %x already given" % x.value)
            
            attrs[x.value] = x # dict (attribute id, AttributeInfo)
            kw[x.name] = x # dict (attribute name, AttributeInfo) - for speed

            # Generate property objects when 's' or 'g' in format
            if x.name not in dct:
                d = {}
                if x.isget:
                    d['fget'] = eval("lambda self: self.Get('%s')" % x.name)
                if x.isset:
                    d['fset'] = dct.get('Set'+x.name, None)
                    if d['fset'] is None:
                        d['fset'] = eval("lambda self, value: self.Set('%s', value)" % x.name)
                if d:
                    dct[x.name] = property(**d)
            
        dct['_id_attrs'] = attrs
        dct['_id_kw'] = kw
        
        return type.__new__(metacl, name, bases, dct)


class BoopsiWrapping:
    @classmethod
    def _check_attr(cl, attr, mode):
        """_check_attr(attr) -> dict

        Take a MUI attribute, check if this one is permitted and return a dictionnary
        with raw information to give to low level _muimaster functions.
        attr is a integer (i.e. MUIA_xxx) or a string declared in the ATTRIBUTE field of the class.
        """
        if isinstance(attr, basestring):
            inf = cl._id_kw.get(attr)
        else:
            inf = cl._id_attrs.get(attr)
            
        if inf != None:
            if [True for c in mode if c in inf.mode]:
                return inf
            raise SyntaxError("Attribute %s can't be used for this action" % inf.name)

        # try the superclass
        try:
            # beurk!
            return cl.__bases__[0]._check_attr(attr, mode)
        except AttributeError:
            raise ValueError("Attribute %s is not supported" % repr(attr))

    def _keep(self, k, v, f='i'):
        # Udpate the keep dict content
        if k in self._keep_dict and v is None:
            ov = self._keep_dict.pop(k)
            debug("%s._keep(0x%x): del %s", self.__class__.__name__, k, repr(ov))
            return ov
        elif f in 'szupM': # None is permitted when format = 'z':
            ov = self._keep_dict.get(k)
            self._keep_dict[k] = v
            debug("%s._keep(0x%x): keep %s (old: %s)", self.__class__.__name__, k, repr(v), repr(ov))
            return ov
        
    def Get(self, attr):
        inf = self._check_attr(attr, 'g')
        return self._get(inf.value, inf.format)

    def Set(self, attr, value):
        inf = self._check_attr(attr, 's')
        if isinstance(inf.format, str):
            self._set(inf.value, value)
            return self._keep(inf.value, value, inf.format)
        else:
            self._set(inf.value, value, inf.format)
            return self._keep(inf.value, value, 'p')

    def DoMethod(self, attr, *args):
        """DoMethod(attr, *args) -> int

        WARNING: this method doesn't keep reference on object given in args!
        User shall take care of this or the system may crash...
        """
        #inf = self._check_attr(attr, 's')
        return self._do(attr, args)


class Notify(PyMUIObject, BoopsiWrapping):
    __metaclass__ = MetaMCC

    CLASSID = MUIC_Notify
    ATTRIBUTES = {
        MUIA_ApplicationObject: ('ApplicationObject' , 'M', '..g'),
        # not supported: MUIA_AppMessage
        MUIA_HelpLine:          ('HelpLine'          , 'i', 'isg'),
        MUIA_HelpNode:          ('HelpNode'          , 's', 'isg'),
        MUIA_NoNotify:          ('NoNotify'          , 'b', '.s.'),
        MUIA_NoNotifyMethod:    ('NoNotifyMethod'    , 'I', '.s.'),
        MUIA_ObjectID:          ('ObjectID'          , 'I', 'isg'),
        MUIA_Parent:            ('Parent'            , 'M', '..g'),
        MUIA_Revision:          ('Revision'          , 'i', '..g'),
        # forbidden: MUIA_UserData
        MUIA_Version:           ('Version'           , 'i', '..g'),
        }

    def __init__(self, **kwds):
        super(Notify, self).__init__()

        self._keep_dict = {}
        self._notify_cbdict = {} 
        
        if kwds.pop('MCC', False):
            superid = self.__class__.__bases__[0].__muiclassid
        else:
            superid = None

        attrs = [(self._check_attr(k, 'i'), v) for k, v in kwds.iteritems()]
        self._create(self.__muiclassid, superid, ((inf.value,v) for inf, v in attrs))
        
        for inf, v in attrs:
            if isinstance(inf.format, basestring):
                self._keep(inf.value, v, inf.format)
        
    def _notify_cb(self, id, value):
        for cb, args in self._notify_cbdict[id]:
            def convertArgs(a, v):
                if isinstance(a, weakref.ref):
                    if a() is None:
                        raise RuntimeError("Notify(%x): some arguments have been destroyed" % id)  
                    else:
                        a = a()
                if a == MUIV_TriggerValue:
                    return v
                elif a == MUIV_NotTriggerValue:
                    return not v
                return a

            if cb(*tuple(convertArgs(a, value) for a in args)) == MUI_EventHandlerRC_Eat:
                return

    def Notify(self, attr, trigvalue, callback, *args):
        attr = self._check_attr(attr, 'sg').value
        l = self._notify_cbdict.get(attr, [])
        weak_args = []
        for a in args:
            try:
                weak_args.append(weakref.ref(a))
            except TypeError:
                weak_args.append(a)
        l.append((callback, weak_args))
        self._notify_cbdict.setdefault(attr, l)
        self._notify(attr, trigvalue)

    def NNSet(self, attr, value):
        inf = self._check_attr(attr, 's')
        self._nnset(inf.value, value)
        self._keep(inf.value, value, inf.format)


class Family(Notify):
    CLASSID = MUIC_Family
    ATTRIBUTES = {
        MUIA_Family_Child: ('Child', 'M', 'i..'),
        MUIA_Family_List:  ('List', 'p', '..g'),
        }

    def __init__(self, **kwds):
        child = kwds.pop('Child', None)
        super(Family, self).__init__(**kwds)
        if child:
            self._children.append(child)

    def AddHead(self, o):
        assert isinstance(o, PyMUIObject)
        assert o not in self._children
        self._do1(MUIM_Family_AddHead, o)
        self._children.append(o)

    def AddTail(self, o):
        assert isinstance(o, PyMUIObject)
        assert o not in self._children  
        self._do1(MUIM_Family_AddTail, o)
        self._children.append(o)

    def Insert(self, o, p):
        assert isinstance(o, PyMUIObject)
        assert o not in self._children and p in self._children
        self._do(MUIM_Family_Insert, (o, p))
        self._children.append(o)

    def Remove(self, o):
        assert o in self._children
        self._do1(MUIM_Family_Remove, o)
        self._children.remove(o) 

    def Sort(self, *args):
        assert len(True for o in args if o in self._children) > 0
        self._do1(MUIM_Family_Sort, array('L', [o._mo for o in args] + [0]))

    def Transfer(self, f):
        assert isinstance(f, Family)
        self._do1(MUIM_Family_Transfer, f)
        f._children = self._children
        del self._children


class Menustrip(Family):
    CLASSID = MUIC_Menustrip
    ATTRIBUTES = { MUIA_Menustrip_Enabled: ('Enabled', 'b', 'isg') }

    def __init__(self, items=None, **kwds):
        super(Menustrip, self).__init__(**kwds)
        if not items: return
        if hasattr(items, '__iter__'):
            for x in items:
                self.AddTail(x)
        else:
            self.AddTail(items)

    def InitChange(self):
        self._do(MUIM_Menustrip_InitChange)
 
    def ExitChange(self):
        self._do(MUIM_Menustrip_ExitChange)

    def Popup(self, parent, x, y, flags=0):
        assert isinstance(parent, Family)
        self._do(MUIM_Menustrip_Popup, (parent, int(flags), int(x), int(y)))


class Menu(Family):
    CLASSID = MUIC_Menu
    ATTRIBUTES = {
        MUIA_Menu_Enabled: ('Enabled', 'b', 'isg'),
        MUIA_Menu_Title:   ('Title',   's', 'isg'),
        }

    def __init__(self, Title, **kwds):
        super(Menu, self).__init__(Title=Title, **kwds)
 

class Menuitem(Family):
    CLASSID = MUIC_Menuitem
    ATTRIBUTES = {
        MUIA_Menuitem_Checked:       ('Checked',       'b', 'isg'),
        MUIA_Menuitem_Checkit:       ('Checkit',       'b', 'isg'),
        MUIA_Menuitem_CommandString: ('CommandString', 'b', 'isg'),
        MUIA_Menuitem_CopyStrings:   ('CopyStrings',   'b', 'i..'),
        MUIA_Menuitem_Enabled:       ('Enabled',       'b', 'isg'),
        MUIA_Menuitem_Exclude:       ('Exclude',       'i', 'isg'),
        MUIA_Menuitem_Shortcut:      ('Shortcut',      's', 'isg'),
        MUIA_Menuitem_Title:         ('Title',         's', 'isg'),
        MUIA_Menuitem_Toggle:        ('Toggle',        'b', 'isg'),
        MUIA_Menuitem_Trigger:       ('Trigger',       'p', '..g'),
        }

    def __init__(self, Title, Shortcut=None, **kwds):
        if Shortcut:
            kwds['Shortcut'] = Shortcut
            if len(Shortcut) > 1:
                kwds['CommandString'] = True
            else:
                kwds['CommandString'] = False
        super(Menuitem, self).__init__(Title=Title, **kwds)

    def action(self, callback, *args):
        self.Notify('Trigger', MUIV_EveryTime, callback, *args)
 

class Application(Notify):
    CLASSID = MUIC_Application
    ATTRIBUTES = {
        MUIA_Application_Active:         ('Active',         'b', 'isg'),
        MUIA_Application_Author:         ('Author',         's', 'i.g'),
        MUIA_Application_Base:           ('Base',           's', 'i.g'),
        MUIA_Application_Broker:         ('Broker',         'p', '..g'),
        MUIA_Application_BrokerHook:     ('BrokerHook',     'p', 'isg'),
        MUIA_Application_BrokerPort:     ('BrokerPort',     'p', '..g'),
        MUIA_Application_BrokerPri:      ('BrokerPri',      'l', 'i.g'),
        MUIA_Application_Commands:       ('Commands',       'p', 'isg'),
        MUIA_Application_Copyright:      ('Copyright',      's', 'i.g'),
        MUIA_Application_Description:    ('Description',    's', 'i.g'),
        MUIA_Application_DiskObject:     ('DiskObject',     'p', 'isg'),
        MUIA_Application_DoubleStart:    ('DoubleStart',    'b', '..g'),
        MUIA_Application_DropObject:     ('DropObject',     'M', 'is.'),
        MUIA_Application_ForceQuit:      ('ForceQuit',      'b', '..g'),
        MUIA_Application_HelpFile:       ('HelpFile',       's', 'isg'),
        MUIA_Application_Iconified:      ('Iconified',      'b', '.sg'),
        MUIA_Application_MenuAction:     ('MenuAction',     'I', '..g'),
        MUIA_Application_MenuHelp:       ('MenuHelp',       'I', '..g'),
        MUIA_Application_Menustrip:      ('Menustrip',      'M', 'i..'),
        MUIA_Application_RexxHook:       ('RexxHook',       'p', 'isg'),
        MUIA_Application_RexxMsg:        ('RexxMsg',        'p', '..g'),
        MUIA_Application_RexxString:     ('RexxString',     's', '.s.'),
        MUIA_Application_SingleTask:     ('SingleTask',     'b', 'i..'),
        MUIA_Application_Sleep:          ('Sleep',          'b', '.s.'),
        MUIA_Application_Title:          ('Title',          's', 'i.g'),
        MUIA_Application_UseCommodities: ('UseCommodities', 'b', 'i..'),
        MUIA_Application_UsedClasses:    ('UsedClasses',    'p', 'isg'),
        MUIA_Application_UseRexx:        ('UseRexx',        'b', 'i..'),
        MUIA_Application_Version:        ('Version',        's', 'i.g'),
        MUIA_Application_Window:         ('Window',         'M', 'i..'),
        MUIA_Application_WindowList:     ('WindowList',     'p', '..g'),
        }

    def __init__(self, **kwds):
        win = kwds.pop('Window', None)
        super(Application, self).__init__(**kwds)

        # Add Window PyMUIObject passed as argument
        if win:
            self.AddWindow(win)

    def Run(self):
        mainloop(self)

    def Quit(self):
        self._do1(MUIM_Application_ReturnID, MUIV_Application_ReturnID_Quit)

    def AddWindow(self, win):
        if win in self._children:
            raise RuntimeError("Window already attached.")
        self._add(win)
        self._children.append(win)
        win.SetApp(self)

class Window(Notify):
    CLASSID = MUIC_Window
    ATTRIBUTES = {
        MUIA_Window_Activate:                ('Activate',                'b', 'isg'),
        MUIA_Window_ActiveObject:            ('ActiveObject',            'M', '.sg'),
        MUIA_Window_AltHeight:               ('AltHeight',               'i', 'i.g'),
        MUIA_Window_AltLeftEdge:             ('AltLeftEdge',             'i', 'i.g'),
        MUIA_Window_AltTopEdge:              ('AltTopEdge',              'i', 'i.g'),
        MUIA_Window_AltWidth:                ('AltWidth',                'i', 'i.g'),
        MUIA_Window_AppWindow:               ('AppWindow',               'b', 'i..'),
        MUIA_Window_Backdrop:                ('Backdrop',                'b', 'i..'),
        MUIA_Window_Borderless:              ('Borderless',              'b', 'i..'),
        MUIA_Window_CloseGadget:             ('CloseGadget',             'b', 'i..'),
        MUIA_Window_CloseRequest:            ('CloseRequest',            'b', '..g'),
        MUIA_Window_DefaultObject:           ('DefaultObject',           'M', 'isg'),
        MUIA_Window_DepthGadget:             ('DepthGadget',             'b', 'i..'),
        MUIA_Window_DisableKeys:             ('DisableKeys',             'I', 'isg'),
        MUIA_Window_DragBar:                 ('DragBar',                 'b', 'i..'),
        MUIA_Window_FancyDrawing:            ('FancyDrawing',            'b', 'isg'),
        MUIA_Window_Height:                  ('Height',                  'i', 'i.g'),
        MUIA_Window_ID:                      ('ID',                      'I', 'isg'),
        MUIA_Window_InputEvent:              ('InputEvent',              'p', '..g'),
        MUIA_Window_IsSubWindow:             ('IsSubWindow',             'b', 'isg'),
        MUIA_Window_LeftEdge:                ('LeftEdge',                'i', 'i.g'),
        MUIA_Window_MenuAction:              ('MenuAction',              'I', 'isg'),
        MUIA_Window_Menustrip:               ('Menustrip',               'M', 'i.g'),
        MUIA_Window_MouseObject:             ('MouseObject',             'M', '..g'),
        MUIA_Window_NeedsMouseObject:        ('NeedsMouseObject',        'b', 'i..'),
        MUIA_Window_NoMenus:                 ('NoMenus',                 'b', 'is.'),
        MUIA_Window_Open:                    ('Open',                    'b', '.sg'),
        MUIA_Window_PublicScreen:            ('PublicScreen',            's', 'isg'),
        MUIA_Window_RefWindow:               ('RefWindow',               'M', 'is.'),
        MUIA_Window_RootObject:              ('RootObject',              'M', 'isg'),
        MUIA_Window_Screen:                  ('Screen',                  'p', 'isg'),
        MUIA_Window_ScreenTitle:             ('ScreenTitle',             's', 'isg'),
        MUIA_Window_SizeGadget:              ('SizeGadget',              'b', 'i..'),
        MUIA_Window_SizeRight:               ('SizeRight',               'b', 'i..'),
        MUIA_Window_Sleep:                   ('Sleep',                   'b', '.sg'),
        MUIA_Window_Title:                   ('Title',                   's', 'isg'),
        MUIA_Window_TopEdge:                 ('TopEdge',                 'i', 'i.g'),
        MUIA_Window_UseBottomBorderScroller: ('UseBottomBorderScroller', 'b', 'isg'),
        MUIA_Window_UseLeftBorderScroller:   ('UseLeftBorderScroller',   'b', 'isg'),
        MUIA_Window_UseRightBorderScroller:  ('UseRightBorderScroller',  'b', 'isg'),
        MUIA_Window_Width:                   ('Width',                   'i', 'i.g'),
        MUIA_Window_Window:                  ('Window',                  'p', '..g'),
        }

    __window_ids = []

    __attr_map = { 'LeftEdge': { 'centered': MUIV_Window_LeftEdge_Centered,
                                 'moused': MUIV_Window_LeftEdge_Moused },
                   'TopEdge' : { 'centered': MUIV_Window_TopEdge_Centered,
                                 'moused': MUIV_Window_TopEdge_Moused },
                   'Height':   { 'default': MUIV_Window_Height_Default,
                                 'scaled':  MUIV_Window_Height_Scaled },
                   'Width':    { 'default': MUIV_Window_Width_Default,
                                 'scaled': MUIV_Window_Width_Scaled },
                   }

    def __init__(self, Title=None, ID=-1, **kwds):
        self.__app = None

        # Auto Window ID handling
        if ID == -1:
            for x in xrange(1<<8):
                if x not in self.__window_ids:
                    ID = x
                    break
            if ID == -1:
                raise RuntimeError("No more available ID")
        else:
            if isinstance(ID, str):
                ID = sum(ord(x) << (24-i*8) for i, x in enumerate(ID[:4]))
            elif not isinstance(ID, (int, long)):
                raise ValueError("ID shall be a int or long, not", type(ID).__name__)

        self.__window_ids.append(ID)

        # A root object is mandatory to create the window
        # Use a dummy rectangle if nothing given
        if 'RootObject' not in kwds:
            kwds['RootObject'] = Rectangle()

        if Title is not None:
            kwds['Title'] = Title

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

        super(Window, self).__init__(ID=ID, **kwds)
        self._children.append(kwds['RootObject'])

    def SetRootObject(self, o):
        self.Set(MUIA_Window_RootObject, o)
        self._children[0] = o

    def KillApp(self):
        app = self.Get(MUIA_ApplicationObject)
        if app is None:
            raise RuntimeError("No application set for this %s object" % self.__class__.__name__)
        app.Quit()

    def SetApp(self, app):
        """This function is called by Application.AddWindow method.
        It permits to safely call Open/Close Window methods.
        """
        if self.__app: return
        self.__app = app
        self.__Open = functools.partial(self._set, MUIA_Window_Open, True)
        self.__Close = functools.partial(self._set, MUIA_Window_Open, False)

    def __Open(self):
        raise RuntimeError("Can't open the Window object, not linked to an application yet.\n"
                           "Please, see Window.SetApp method.")

    def __Close(self):
        raise RuntimeError("Can't close the Window object, not linked to an application yet.\n"
                           "Please, see Window.SetApp method.")
 
    def Open(self):
        self.__Open() # raise error if object not linked to an application (SetApp)

    def Close(self):
        self.__Close() # raise error if object not linked to an application (SetApp)


class AboutMUI(Window):
    CLASSID = MUIC_Aboutmui
    ATTRIBUTES = { MUIA_Aboutmui_Application: ('Application', 'M', 'i..') }

    def __init__(self, app, **kwds):
        Window.__init__(self, Application=app, RefWindow=kwds.pop('RefWindow', None), **kwds)

        # We don't call app.AddWindow() because this object do it itself at OM_NEW
        app._children.append(self)
        self.SetApp(app)


class Convertor_ImageSpec:
    @staticmethod
    def get(value):
        if value <= MUII_LASTPAT:
            return value
        else:
            return None

    @staticmethod 
    def set(value):
        return value


class Area(Notify):
    CLASSID = MUIC_Area
    ATTRIBUTES = {
        MUIA_Background:         ('Background',         Convertor_ImageSpec, 'is.'),
        MUIA_BottomEdge:         ('BottomEdge',         'i', '..g'),
        MUIA_ContextMenu:        ('ContextMenu',        'M', 'isg'),
        MUIA_ContextMenuTrigger: ('ContextMenuTrigger', 'M', '..g'),
        MUIA_ControlChar:        ('ControlChar',        'c', 'isg'),
        MUIA_CycleChain:         ('CycleChain',         'i', 'isg'),
        MUIA_Disabled:           ('Disabled',           'b', 'isg'),
        MUIA_DoubleBuffer:       ('DoubleBuffer',           'b', 'isg'),
        MUIA_Draggable:          ('Draggable',          'b', 'isg'),
        MUIA_Dropable:           ('Dropable',           'b', 'isg'),
        MUIA_FillArea:           ('FillArea',           'b', 'is.'),
        MUIA_FixHeight:          ('FixHeight',          'i', 'i..'),
        MUIA_FixHeightTxt:       ('FixHeightTxt',       's', 'i..'),
        MUIA_FixWidth:           ('FixWidth',           'i', 'i..'),
        MUIA_FixWidthTxt:        ('FixWidthTxt',        's', 'i..'),
        MUIA_Font:               ('Font',               'p', 'i.g'),
        MUIA_Frame:              ('Frame',              'i', 'i..'),
        MUIA_FrameDynamic:       ('FrameDynamic',       'b', 'isg'),
        MUIA_FramePhantomHoriz:  ('FramePhantomHoriz',  'b', 'i..'),
        MUIA_FrameTitle:         ('FrameTitle',         's', 'i..'),
        MUIA_FrameVisible:       ('FrameVisible',       'b', 'isg'),
        MUIA_Height:             ('Height',             'i', '..g'),
        MUIA_HorizDisappear:     ('HorizDisappear',     'i', 'isg'),
        MUIA_HorizWeight:        ('HorizWeight',        'i', 'isg'),
        MUIA_InnerBottom:        ('InnerBottom',        'i', 'i.g'),
        MUIA_InnerLeft:          ('InnerLeft',          'i', 'i.g'),
        MUIA_InnerRight:         ('InnerRight',         'i', 'i.g'),
        MUIA_InnerTop:           ('InnerTop',           'i', 'i.g'),
        MUIA_InputMode:          ('InputMode',          'i', 'i..'),
        MUIA_LeftEdge:           ('LeftEdge',           'i', '..g'),
        MUIA_MaxHeight:          ('MaxHeight',          'i', 'i..'),
        MUIA_MaxWidth:           ('MaxWidth',           'i', 'i..'),
        MUIA_Pressed:            ('Pressed',            'b', '..g'),
        MUIA_RightEdge:          ('RightEdge',          'i', '..g'),
        MUIA_Selected:           ('Selected',           'b', 'isg'),
        MUIA_ShortHelp:          ('ShortHelp',          's', 'isg'),
        MUIA_ShowMe:             ('ShowMe',             'b', 'isg'),
        MUIA_ShowSelState:       ('ShowSelState',       'b', 'i..'),
        MUIA_Timer:              ('Timer',              'i', '..g'),
        MUIA_TopEdge:            ('TopEdge',            'i', '..g'),
        MUIA_VertDisappear:      ('VertDisappear',      'i', 'isg'),
        MUIA_VertWeight:         ('VertWeight',         'i', 'isg'),
        MUIA_Weight:             ('Weight',             'i', 'i..'),
        MUIA_Width:              ('Width',              'i', '..g'),
        MUIA_Window:             ('Window',             'p', '..g'),
        MUIA_WindowObject:       ('WindowObject',       'M', '..g'),
        }

    def __init__(self, **kwds):
        v = kwds.pop('InnerSpacing', None)
        if v:
            kwds['InnerLeft'], kwds['InnerRight'], kwds['InnerTop'], kwds['InnerBottom'], 
        super(Area, self).__init__(**kwds)


class Dtpic(Area):
    CLASSID = MUIC_Dtpic
    ATTRIBUTES = { MUIA_Dtpic_Name: ('Name', 's', 'isg') }

    def __init__(self, Name='', **kwds):
        super(Dtpic, self).__init__(Name=Name, **kwds)


class Rectangle(Area):
    CLASSID = MUIC_Rectangle
    ATTRIBUTES = {
        MUIA_Rectangle_BarTitle: ('BarTitle', 's', 'i.g'),
        MUIA_Rectangle_HBar:     ('HBar',     'b', 'i.g'),
        MUIA_Rectangle_VBar:     ('VBar',     'b', 'i.g'),
        }

    # Factory class methods

    @classmethod
    def HVSpace(cl):
        return cl()

    @classmethod
    def HSpace(cl, x):
        return cl(VertWeight=x)

    @classmethod
    def VSpace(cl, x):
        return cl(HorizWeight=x)

    @classmethod
    def HCenter(cl, o):
        g = Group.HGroup(Spacing=0)
        g.AddChild((cl.HSpace(0), o, cl.HSpace(0)))
        return g

    @classmethod
    def VCenter(cl, o):
        g = Group.VGroup(Spacing=0)
        return g.AddChild((cl.VSpace(0), o, cl.VSpace(0)))

HVSpace = Rectangle.HVSpace
HSpace = Rectangle.HSpace
VSpace = Rectangle.VSpace
HCenter = Rectangle.HCenter
VCenter = Rectangle.VCenter


class Balance(Area):
    CLASSID = MUIC_Balance
    ATTRIBUTES = { MUIA_Balance_Quiet: ('Quiet', 'i', 'i..') }


class Bitmap(Area):
    CLASSID = MUIC_Bitmap
    ATTRIBUTES = {
        MUIA_Bitmap_Alpha:          ('Alpha',           'I', 'isg'),
        MUIA_Bitmap_Bitmap:         ('Bitmap',          'p', 'isg'),
        MUIA_Bitmap_Height:         ('Height',          'i', 'isg'),
        MUIA_Bitmap_MappingTable:   ('MappingTable',    'p', 'isg'),
        MUIA_Bitmap_Precision:      ('Precision',       'i', 'isg'),
        MUIA_Bitmap_RemappedBitmap: ('RemappedBitmap',  'p', '..g'),
        MUIA_Bitmap_SourceColors:   ('SourceColors',    'p', 'isg'),
        MUIA_Bitmap_Transparent:    ('Transparent',     'i', 'isg'),
        MUIA_Bitmap_UseFriend:      ('UseFriend',       'b', 'i..'),
        MUIA_Bitmap_Width:          ('Width',           'i', 'isg'),
        }


class Text(Area):
    CLASSID = MUIC_Text
    ATTRIBUTES = {
        MUIA_Text_Contents:    ('Contents',       's', 'isg'),
        MUIA_Text_ControlChar: ('ControlChar',    'c', 'isg'),
        MUIA_Text_Copy:        ('MUIA_Text_Copy', 'b', 'isg'),
        MUIA_Text_HiChar:      ('HiChar',         'c', 'isg'),
        MUIA_Text_PreParse:    ('PreParse',       's', 'i..'),
        MUIA_Text_SetMax:      ('SetMax',         'b', 'i..'),
        MUIA_Text_SetMin:      ('SetMin',         'b', 'i..'),
        MUIA_Text_SetVMax:     ('SetVMax',        'b', 'is.'),
        MUIA_Text_Shorten:     ('Shorten',        'I', 'isg'),
        MUIA_Text_Shortened:   ('Shortened',      'b', '..g'),
        }

    def __init__(self, Contents='', **kwds):
        super(Text, self).__init__(Contents=Contents, **kwds)

    # Factory class methods

    @classmethod
    def KeyButton(cl, x, key=None):
        kwds = dict(Contents=x,
                    Font=MUIV_Font_Button,
                    Frame=MUIV_Frame_Button,
                    PreParse=MUIX_C,
                    InputMode=MUIV_InputMode_RelVerify,
                    Background=MUII_ButtonBack)
        if key:
            kwds['HiChar'] = key
            kwds['ControlChar'] = key
        return cl(**kwds)

SimpleButton = functools.partial(Text.Button, key=None)
KeyButton = Text.Button


class Gadget(Area):
    CLASSID = MUIC_Gadget
    ATTRIBUTES = {
        MUIA_Gadget_Gadget: ('Gadget',   'p', '..g'),
    }


class String(Gadget):
    CLASSID = MUIC_String
    ATTRIBUTES = {
        MUIA_String_Accept:         ('Accept',          's', 'isg'),
        MUIA_String_Acknowledge:    ('Acknowledge',     's', '..g'),
        MUIA_String_AdvanceOnCR:    ('AdvanceOnCR',     'p', 'isg'),
        MUIA_String_AttachedList:   ('AttachedList',    'M', 'isg'),
        MUIA_String_BufferPos:      ('BufferPos',       'i', '.sg'),
        MUIA_String_Contents:       ('Contents',        's', 'isg'),
        MUIA_String_DisplayPos:     ('DisplayPos',      'i', '.sg'),
        MUIA_String_EditHook:       ('EditHook',        'p', 'isg'),
        MUIA_String_Format:         ('Format',          'i', 'i.g'),
        MUIA_String_Integer:        ('Integer',         'I', 'isg'),
        MUIA_String_LonelyEditHook: ('LonelyEditHook',  'p', 'isg'),
        MUIA_String_MaxLen:         ('MaxLen',          'i', 'i.g'),
        MUIA_String_Reject:         ('Reject',          's', 'isg'),
        MUIA_String_Secret:         ('Secret',          'b', 'i.g'),
    }


class Group(Area):
    CLASSID = MUIC_Group
    ATTRIBUTES = {
        MUIA_Group_ActivePage:   ('ActivePage',   'i', 'isg'),
        MUIA_Group_Child:        ('Child',        'M', 'i..'),
        MUIA_Group_ChildList:    ('ChildList',    'p', '..g'),
        MUIA_Group_Columns:      ('Columns',      'i', 'is.'),
        MUIA_Group_Horiz:        ('Horiz',        'b', 'i..'),
        MUIA_Group_HorizSpacing: ('HorizSpacing', 'i', 'isg'),
        MUIA_Group_LayoutHook:   ('LayoutHook',   'p', 'i..'),
        MUIA_Group_PageMode:     ('PageMode',     'b', 'i..'),
        MUIA_Group_Rows:         ('Rows',         'i', 'is.'),
        MUIA_Group_SameHeight:   ('SameHeight',   'b', 'i..'),
        MUIA_Group_SameSize:     ('SameSize',     'b', 'i..'),
        MUIA_Group_SameWidth:    ('SameWidth',    'b', 'i..'),
        MUIA_Group_Spacing:      ('Spacing',      'i', 'is.'),
        MUIA_Group_VertSpacing:  ('VertSpacing',  'i', 'isg'),
        }

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

    def __add_child(self, child, lock):
        if child not in self._children:
            self._add(child, lock)
            self._children.append(child)

    def __rem_child(self, child, lock):
        if child in self._children:
            self._rem(child, lock)
            self._children.remove(child)
            
    def AddChild(self, *children, **kwds):
        lock = kwds.get('lock', False)
        for o in children:
            self.__add_child(o, lock)

    def RemChild(self, *children, **kwds):
        lock = kwds.get('lock', False)
        for o in children:
            self.__rem_child(o, lock)

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
 

class Virtgroup(Group):
    CLASSID = MUIC_Virtgroup
    ATTRIBUTES = {
        MUIA_Virtgroup_Height: ('Height', 'i', '..g'),
        MUIA_Virtgroup_Input:  ('Input',  'b', 'i..'),
        MUIA_Virtgroup_Left:   ('Left',   'i', 'isg'),
        MUIA_Virtgroup_Top:    ('Top',    'i', 'isg'),
        MUIA_Virtgroup_Width:  ('Width',  'i', '..g'),
    }

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

HGroupV = Virtgroup.HVirtgroup
VGroupV = Virtgroup.VVirtgroup
ColGroupV = Virtgroup.ColVirtgroup
RowGroupV = Virtgroup.RowVirtgroup
PageGroupV = Virtgroup.PageGroup


class Coloradjust(Group):
    CLASSID = MUIC_Coloradjust
    ATTRIBUTES = {
        MUIA_Coloradjust_Blue:   ('Blue',   'I', 'isg'),
        MUIA_Coloradjust_Green:  ('Green',  'I', 'isg'),
        MUIA_Coloradjust_ModeID: ('ModeID', 'I', 'isg'),
        MUIA_Coloradjust_Red:    ('Red',    'I', 'isg'),
        MUIA_Coloradjust_RGB:    ('RGB',    ArrayOf('I', 3), 'isg'),
    }


#################################################################################


if __name__ == "__main__":
    # Unit testing section

    # instance
    print "\n=> a = Notify(HelpNode='An object') <="
    a = Notify(HelpNode='An object')
    print a

    print "\n=> b = Text(Contents='test') <="
    b = Text(Contents='test')
    print b

    # Get
    print "\n=> a.Get(MUIA_Version) <="
    print a.Get(MUIA_Version)
    
    print "\n=> a.Get('Version') <="
    print a.Get('Version')

    print "\n=> a.Get(-1) <="
    try:
        print a.Get(-1)
    except ValueError:
        print "[OK]"
    else:
        raise RuntimeError()

    print "\n=> a.Get('') <="
    try:
        print a.Get('')
    except ValueError:
        print "[OK]"
    else:
        raise RuntimeError()

    print "\n=> a.Get('Contents') <="
    try:
        print a.Get('Contents')
    except ValueError:
        print "[OK]"
    else:
        raise RuntimeError()

    # Get - indirect
    print "\n=> b.Get(MUIA_Version) <="
    print b.Get(MUIA_Version)
    
    print "\n=> b.Get('Version') <="
    print b.Get('Version')

    print "\n=> b.Get('Contents') <="
    print b.Get('Contents')

    # Set
    print "\n=> a.Set(MUIA_ObjectID, 42) <="
    a.Set(MUIA_ObjectID, 42)
    
    print "\n=> a.Set('ObjectID', 33) <="
    a.Set('ObjectID', 33)

    print "\n=> a.Set(MUIA_HelpNode, None) <="
    print a.Set(MUIA_HelpNode, None) # shall not work if _muimaster exists

    print "\n=> a.Set('', 0) <="
    try:
        a.Set('', 0)
    except ValueError:
        print "[OK]"
    else:
        raise RuntimeError()

    print "\n=> a.Set(MUIA_Parent, None) <="
    try:
        a.Set(MUIA_Parent, None)
    except SyntaxError:
        print "[OK]"
    else:
        raise RuntimeError()

    # Keep
    print "\n=> a.Set(MUIA_ObjectID, 42) <="
    a.Set(MUIA_ObjectID, 42)

    # Property
    assert type(Window.Open) != property
    assert type(Text.Version) == property
    
    print "\n=> b.Version <="
    print b.Version

    # Del
    print "\n=> del a, b <="
    del a

    # DoMethod
    print "\n=> a = Application() <="
    a = Application()
    print "\n=> a.Quit() <="
    a.Quit()

    # Test factory
    print "\n=> Rectangle.HCenter(b) <="
    print Rectangle.HCenter(b)
    
    print "\n=> Text.Button('Ok') <="
    print Text.Button('Ok')

    # Test Window KillApp methode
    print "\n=> w = Window().KillApp() <="
    w = Window("Test")
    
    print "\n=> w.KillApp() <="
    try:
        w.KillApp()
    except RuntimeError:
        print "[OK]"
    else:
        raise RuntimeError()

    # Following tests need a valid _muimaster module
    if globals().has_key('BUILD_DATE'):
        print "\n=> a.AddWindow(w) <="
        a.AddWindow(w)
    
        print "\n=> w.KillApp() <="
        w.KillApp()
