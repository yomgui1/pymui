###
## \file _core.py
## \author ROGUEZ "Yomgui" Guillaume
##

try:
    assert __name__ != "__main__"
    from _muimaster import *
except: # For testing => use stubs
    class PyBOOPSIObject(object):
        def _set(self, i, v):
            print "Stubs: %s._set(0x%x, %s)" % (self.__class__.__name__, i, repr(v))
        def _get(self, i, fmt):
            print "Stubs: %s._get(0x%x, '%s')" % (self.__class__.__name__, i, fmt)
        def _do(self, i, *args):
            print "Stubs: %s._do(0x%x, %s)" % (self.__class__.__name__, i, tuple(args))
        def _do1(self, i, arg):
            print "Stubs: %s._do(0x%x, %s)" % (self.__class__.__name__, i, repr(arg))
        def _add(self, o, l=False):
            print "Stubs: %s._add(%s, %s)" % (self.__class__.__name__, repr(o), bool(l))
        def _rem(self, o, l=False):
            print "Stubs: %s._add(%s, %s)" % (self.__class__.__name__, repr(o), bool(l))
        
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

    def _keep(self, k, v, f):
        # Udpate the keep dict content
        if k in self._keep_dict and v is None:
            ov = self._keep_dict.pop(k)
            print "%s._keep(0x%x): del %s" % (self.__class__.__name__, k, repr(ov))
            return ov
        elif f in 'szupM': # None is permitted when format = 'z':
            ov = self._keep_dict.get(k)
            self._keep_dict[k] = v
            print "%s._keep(0x%x): keep %s (old: %s)" % (self.__class__.__name__, k, repr(v), repr(ov))
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

    def __new__(cl, **kwds):
        if 'attributes' in kwds:
            attrs = [(cl._check_attr(k, 'i'), v) for k,v in kwds.pop('attributes')]
        else:
            attrs = []
        attrs += [(cl._check_attr(k, 'i'), v) for k,v in kwds.iteritems()]
        self = PyMUIObject.__new__(cl, cl._classid, ((inf.value,v) for inf,v in attrs))
        self._keep_dict = {}
        for inf,v in attrs:
                self._keep(inf.value, v, inf.format[0])
        return self

    def __init__(self, *args, **kwds):
        super(Notify, self).__init__(*args, **kwds)
        self._notify_cbdict = {}
        
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
        attr = self._check_attr(attr, 's').value
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
        super(Application, self).__init__(*args, **kwds)
        self._win = []

        # Add Window PyMUIObject passed as argument
        x = kwds.get('Window')
        if x:
            self._win.append(x)
            # unneeded to let a ref in self._keep as it's already in self._win
            inf = self._id_kw['Window']
            self._keep(inf.value, None, inf.format[0])

    def Run(self):
        mainloop(self)

    def Quit(self):
        self._do1(MUIM_Application_ReturnID, MUIV_Application_ReturnID_Quit)

    def AddWindow(self, win):
        if win in self._win:
            raise RuntimeError("Window already attached.")
        self._add(win)
        self._win.append(win)


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
    
    __current_id = 0

    def __new__(cl, Id=-1, **kwds):
        if Id == -1:
            cl.__current_id += 1
            Id = cl.__current_id
        kwds['ID'] = Id
        killapp = kwds.pop('killapp', False)
        self = Notify.__new__(cl, **kwds)
        if killapp:
            self.Notify(MUIA_Window_CloseRequest, MUIV_EveryTime, self.KillApp)
        return self

    def KillApp(self):
        app = self.Get(MUIA_ApplicationObject)
        if app is None:
            raise RuntimeError("No application set for this %s object" % self.__class__.__name__)
        self.app.Quit()

    def Open(self):
        self._set(MUIA_Window_Open, True)

    def Close(self):
        self._set(MUIA_Window_Open, False)


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
        MUIA_DoubleBuffer:       ('DoubleBuffer',       'b', 'isg'),
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
        return cl(Weight=x)

    @classmethod
    def VSpace(cl, x):
        return cl(Weight=x)

    @classmethod
    def HCenter(cl, o):
        g = Group.HGroup(Spacing=0)
        g.AddChild((cl.HSpace(0), o, cl.HSpace(0)))
        return g

    @ classmethod
    def VCenter(cl, o):
        g = Group.VGroup(Spacing=0)
        return g.AddChild((cl.VSpace(0), o, cl.VSpace(0)))
    

class Group(Area):
    CLASSID = MUIC_Gauge

    ATTRIBUTES = {
        MUIA_Group_ActivePage:   ('ActivePage',   'i', 'isg'),
        MUIA_Group_Child:        ('Child',        'M', 'i..'),
        MUIA_Group_ChildList:    ('ChildList',    'p', '..g'),
        MUIA_Group_Columns:      ('Columns',      'i', 'is.'),
        MUIA_Group_Forward:      ('Forward',      'b', '.s.'),
        MUIA_Group_Horiz:        ('Horiz',        'b', 'i..'),
        MUIA_Group_HorizCenter:  ('HorizCenter',  'i', 'isg'),
        MUIA_Group_HorizSpacing: ('HorizSpacing', 'i', 'isg'),
        MUIA_Group_LayoutHook:   ('LayoutHook',   'p', 'i..'),
        MUIA_Group_PageMode:     ('PageMode',     'b', 'i..'),
        MUIA_Group_Rows:         ('Rows',         'i', 'is.'),
        MUIA_Group_SameHeight:   ('SameHeight',   'b', 'i..'),
        MUIA_Group_SameSize:     ('SameSize',     'b', 'i..'),
        MUIA_Group_SameWidth:    ('SameWidth',    'b', 'i..'),
        MUIA_Group_Spacing:      ('Spacing',      'i', 'is.'),
        MUIA_Group_VertCenter:   ('VertCenter',   'i', 'isg'),
        MUIA_Group_VertSpacing:  ('VertSpacing',  'i', 'isg'),
        }

    def __init__(self, *args, **kwds):
        super(Group, self).__init__(*args, **kwds)
        self._children = []

        # Add RootObject PyMUIObject passed as argument
        x = kwds.get('Child')
        if x:
            self._children.append(x)
            # unneeded to let a ref in self._keep as it's already in self._children
            inf = self._id_kw['Child']
            self._keep(inf.value, None, inf.format[0])

    def _group_add(self, child, lock):
        if child not in self._children:
            self._add(child, lock)
            self._children.append(child)

    def _group_rem(self, child, lock):
        if child in self._children:
            self._rem(child, lock)
            self._children.remove(child)
            
    def AddChild(self, child, lock=False):
        if hasattr(child, '__iter__'):
            for c in child:
                self._group_add(c, lock)
        else:
            self._group_add(child, lock)

    def RemChild(self, child, lock=False):
        if hasattr(child, '__iter__'):
            for c in child:
                self._group_rem(c, lock)
        else:
            self._group_rem(child, lock)

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
    

class Text(Area):
    CLASSID = MUIC_Text

    ATTRIBUTES = {
        MUIA_Text_Contents:    ('Contents',     's', 'isg'),
        MUIA_Text_ControlChar: ('ControlChar',  'c', 'isg'),
        MUIA_Text_Copy:        ('Copy',         'b', 'i..'),
        MUIA_Text_HiChar:      ('HiChar',       'c', 'isg'),
        MUIA_Text_PreParse:    ('PreParse',     's', 'i..'),
        MUIA_Text_SetMin:      ('SetMin',       'b', 'i..'),
        MUIA_Text_SetVMax:     ('SetVMax',      'b', 'is.'),
        MUIA_Text_Shorten:     ('Shorten',      'i', 'isg'),
        MUIA_Text_Shortened:   ('Shortened',    'b', '..g'),
        }

    # Factory class methods

    @classmethod
    def Button(cl, x, key=None):
        kwds = dict(Contents=x,
                    Font=MUIV_Font_Button,
                    PreParse=MUIX_C,
                    InputMode=MUIV_InputMode_RelVerify,
                    Background=MUII_ButtonBack)
        if key:
            kwds['HiChar'] = key
            kwds['ControlChar'] = key
        return cl(**kwds)

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
    w = Window()
    
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
