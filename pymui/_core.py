###
## \file _core.py
## \author ROGUEZ "Yomgui" Guillaume
##

import sys
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
        def _create(self, i, a={}):
            debug("Stubs: %s._create(%s, %s)", self.__class__.__name__, i, repr(a))
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
        def _nnset(self, *args):
            pass
        def _notify(self, *args):
            pass
    
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

        dct['_classid'] = clid
        dct['_id_meths'] = dct.pop('METHODS', {})

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
            if mode in inf.mode:
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
        self._set(inf.value, value)
        return self._keep(inf.value, value, inf.format[0])

    def DoMethod(self, attr, *args):
        """DoMethod(attr, *args) -> int

        WARNING: this method doesn't keep reference on object given in args!
        User shall take care of this or the system may crash...
        """
        inf = self._check_attr(attr, 's')
        return self._do(inf.value, args)


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
        
        if 'attributes' in kwds:
            attrs = [(self._check_attr(k, 'i'), v) for k,v in kwds.pop('attributes')]
        else:
            attrs = []
        attrs += [(self._check_attr(k, 'i'), v) for k,v in kwds.iteritems()]
        
        self._create(self._classid, ((inf.value,v) for inf,v in attrs))
        
        for inf,v in attrs:
            self._keep(inf.value, v, inf.format[0])
        
    def _notify_cb(self, id, value):
        for cb, args in self._notify_cbdict[id]:
            def convertArgs(a, v):
                if a == MUIV_TriggerValue:
                    return v
                elif a == MUIV_NotTriggerValue:
                    return not v
                return a
     
            newargs = tuple(convertArgs(a(), value) for a in args if a() != None)
            if len(newargs) != len(args):
                raise RuntimeError("Notify(%x): some arguments have been destroyed" % id)

            if cb(*newargs) == MUI_EventHandlerRC_Eat:
                return

    def Notify(self, attr, trigvalue, callback, *args):
        attr = self._check_attr(attr, 'g').value
        l = self._notify_cbdict.get(attr, [])
        l.append((callback, map(weakref.ref, args)))
        self._notify_cbdict.setdefault(attr, l)
        self._notify(attr, trigvalue)

    def NNSet(self, attr, value):
        inf = self._check_attr(attr, 's')
        self._nnset(inf.value, value)
        self._keep(inf.value, value, inf.format[0])


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

    def __init__(self, *args, **kwds):
        win = kwds.pop('Window', None)
        super(Application, self).__init__(*args, **kwds) 

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
        win._app = self


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

    def __init__(self, Title=None, ID=-1, **kwds):
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

        if 'RootObject' not in kwds:
            kwds['RootObject'] = Rectangle.HVSpace()

        if not Title is None:
            kwds['Title'] = Title

        if 'RightEdge' in kwds:
            kwds['LeftEdge'] = -1000 - kwds.pop('RightEdge')

        if 'BottomEdge' in kwds:
            kwds['TopEdge'] = -1000 - kwds.pop('BottomEdge')

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

    def Open(self):
        if self._app: # _app set during the AddWindow
            self._set(MUIA_Window_Open, True)

    def Close(self):
        if self._app: # _app set during the AddWindow
            self._set(MUIA_Window_Open, False)


class AboutMUI(Window):
    CLASSID = MUIC_Aboutmui
    ATTRIBUTES = { MUIA_Aboutmui_Application: ('Application', 'M', 'i..') }

    def __init__(self, Application, RefWindow=None, **kwds):
        Window.__init__(self, Application=Application, RefWindow=RefWindow, **kwds)
        self._app = Application
        Application._children.append(self)


class Area(Notify):
    CLASSID = MUIC_Area
    ATTRIBUTES = {
        MUIA_Background:         ('Background',         'i', 'is.'),
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


class Dtpic(Area):
    CLASSID = MUIC_Dtpic
    ATTRIBUTES = { MUIA_Dtpic_Name: ('Name', 's', 'isg') }

    def __init__(self, Name, **kwds):
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
        return cl()

    @classmethod
    def VSpace(cl, x):
        return cl()

    @classmethod
    def HCenter(cl, o):
        g = Group.HGroup(Spacing=0)
        g.AddChild((cl.HSpace(0), o, cl.HSpace(0)))
        return g

    @ classmethod
    def VCenter(cl, o):
        g = Group.VGroup(Spacing=0)
        return g.AddChild((cl.VSpace(0), o, cl.VSpace(0)))


class Text(Area):
    CLASSID = MUIC_Text
    ATTRIBUTES = {
        MUIA_Text_Contents:    ('Contents',       's', 'isg'),
        MUIA_Text_ControlChar: ('ControlChar',    'c', 'isg'),
        MUIA_Text_Copy:        ('MUIA_Text_Copy', 'b', 'isg'),
        MUIA_Text_HiChar:      ('HiChar',         'c', 'isg'),
        MUIA_Text_PreParse:    ('PreParse',       's', 'i..'),
        MUIA_Text_SetMin:      ('SetMin',         'b', 'i..'),
        MUIA_Text_SetVMax:     ('SetVMax',        'b', 'is.'),
        MUIA_Text_Shorten:     ('Shorten',        'I', 'isg'),
        MUIA_Text_Shortened:   ('Shortened',      'b', '..g'),
        }

    def __init__(self, Contents='', **kwds):
        super(Text, self).__init__(Contents=Contents, **kwds)

    # Factory class methods

    @classmethod
    def Button(cl, x, key=None):
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


class Gadget(Area):
    CLASSID = MUIC_Gadget

    ATTRIBUTES = {
        MUIA_Gadget_Gadget: ('Gadget',   'p', '..g'),
    }


class String(Gadget):
    CLASSID = MUIC_String

    ATTRIBUTES = {
        MUIA_String_Accept:         ('Accept',   's', 'isg'),
        MUIA_String_Acknowledge:    ('Acknowledge',   's', '..g'),
        MUIA_String_AdvanceOnCR:    ('AdvanceOnCR',   'p', 'isg'),
        MUIA_String_AttachedList:   ('AttachedList',   'M', 'isg'),
        MUIA_String_BufferPos:      ('BufferPos',   'i', '.sg'),
        MUIA_String_Contents:       ('Contents',   's', 'isg'),
        MUIA_String_DisplayPos:     ('DisplayPos',   'i', '.sg'),
        MUIA_String_EditHook:       ('EditHook',   'p', 'isg'),
        MUIA_String_Format:         ('Format',   'i', 'i.g'),
        MUIA_String_Integer:        ('Integer',   'I', 'isg'),
        MUIA_String_LonelyEditHook: ('LonelyEditHook',   'p', 'isg'),
        MUIA_String_MaxLen:         ('MaxLen',   'i', 'i.g'),
        MUIA_String_Reject:         ('Reject',   's', 'isg'),
        MUIA_String_Secret:         ('Secret',   'b', 'i.g'),
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
            self.AddChild(*tuple(child))

    def __add_child(self, child, lock):
        if child not in self._children:
            self._add(child, lock)
            self._children.append(child)

    def __rem_child(self, child, lock):
        if child in self._children:
            self._rem(child, lock)
            self._children.remove(child)
            
    def AddChild(self, child, *children, **kwds):
        lock = kwds.get('lock', False)
        self.__add_child(child, lock)
        for o in children:
            self.__add_child(o, lock)

    def RemChild(self, child, *children, **kwds):
        lock = kwds.get('lock', False)
        self.__rem_child(child, lock)
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


class Coloradjust(Group):
    CLASSID = MUIC_Coloradjust
    ATTRIBUTES = {
        MUIA_Coloradjust_Blue:   ('Blue',   'I', 'isg'),
        MUIA_Coloradjust_Green:  ('Green',  'I', 'isg'),
        MUIA_Coloradjust_ModeID: ('ModeID', 'I', 'isg'),
        MUIA_Coloradjust_Red:    ('Red',    'I', 'isg'),
        MUIA_Coloradjust_RGB:    ('RGB',    'p', 'isg'),
    }


#################################################################################


if __name__ == "__main__":
    # Unit testing section

    # instance
    print "\n=> a = Notify(HelpNode='An object') <="
    a = Notify(HelpNode='An object')
    print a

    print "\n=> b = Text(attributes=((MUIA_Text_Contents, 'test'), )) <="
    b = Text(attributes=((MUIA_Text_Contents, 'test'), ))
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
