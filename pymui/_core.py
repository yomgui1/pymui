###
## \file _core.py
## \author ROGUEZ "Yomgui" Guillaume
##

from _muimaster import *
from defines import *
import weakref

class MetaMCC(type):
    def __new__(metacl, name, bases, dct):
        cl = dct.get('CLASSID', None)
        if cl:
            methods = dct.pop('METHODS', None)
        dct['_keep_dict'] = {}
        dct['_id_meths'] = {}
        dct['_id_attrs'] = dct.pop('ATTRIBUTES', {})
        dct['_id_dontkeep'] = {}
        return type.__new__(metacl, name, bases, dct)

class BoopsiWrapping:
    def _keep_set(self, id, value):
        if type(value) not in (int, long) and id not in self._id_dontkeep:
            self._keep_dict[id] = value

    def _keep_do(self, id, args):
        self._keep_dict[id] = [arg for i, arg in enumerate(args) if type(arg) not in (int, long) and i not in self._args_dontkeep[id]]
    
    def DoMethod(self, id, *args):
        t = self._id_meths.get(id, None)
        if not t:
            raise ValueError("This method is forbidden")
        self._keep_do(t['id'], args)
        return self._do(t['id'], args)

    def Get(self, id):
        t = self._id_attrs.get(id, None)
        if not t:
            raise ValueError("This attribute is forbidden")
        return self._get(t['id'], t['fmt'])

    def Set(self, id, value):
        t = self._id_attrs.get(id, None)
        if not t:
            raise ValueError("This attribute is forbidden")
        self._keep_set(t['id'], value)
        self._set(t['id'], value)

class Notify(PyMUIObject, BoopsiWrapping):
    __metaclass__ = MetaMCC

    CLASSID = MUIC_Notify

    def __new__(cl, **kwds):
        def convert(a):
            if cl._id_attrs.has_key(a):
                return cl._id_attrs[a]['id']
            return a
        attrs = list((convert(a), v) for a, v in kwds.pop('attributes', []))
        attrs += list((cl._id_attrs[a]['id'], v) for a, v in kwds.iteritems())
        self = PyMUIObject.__new__(cl, cl.CLASSID, attrs)
        self._keep = {}
        for i, v in attrs:
            # to be more efficient
            if type(v) not in (int, long, basestring, bool):
                self._keep[i] = v
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

            if cb(*newargs):
                return

    def Notify(self, id, trigvalue, callback, *args):
        t = self._id_attrs.get(id, None)
        if not t:
            raise ValueError("This attribute is forbidden")
        l = self._notify_cbdict.get(t['id'], [])
        l.append((callback, map(weakref.ref, args)))
        self._notify_cbdict.setdefault(t['id'], l)
        self._notify(t['id'], trigvalue)

    def NNSet(self, id, value):
        self._nnset()

class Application(Notify):
    CLASSID = MUIC_Application

    def __init__(self, *args, **kwds):
        super(Application, self).__init__(*args, **kwds)
        self._win = []

    def Run(self):
        mainloop(self)

    def Quit(self):
        self._do(MUIM_Application_ReturnID, (MUIV_Application_ReturnID_Quit, ))

    def AddWindow(self, win):
        if win in self._win:
            raise RuntimeError("Window already attached.")
        self._do(OM_ADDMEMBER, (win, ))
        self._win.append(win)

class Window(Notify):
    CLASSID = MUIC_Window
    ATTRIBUTES = {
        'Open': {'id': MUIA_Window_Open, 'prop': 'open', 'fmt': 'b'},
        'Id': {'id': MUIA_Window_ID, 'fmt': 'I'},
        'CloseRequest': {'id': MUIA_Window_CloseRequest, 'fmt': 'b'},
        }

    __current_id = 0

    def __new__(cl, Id=-1, **kwds):
        if Id == -1:
            cl.__current_id += 1
            Id = cl.__current_id
        kwds['Id'] = Id
        return Notify.__new__(cl, **kwds)

    def Open(self):
        self._set(MUIA_Window_Open, True)

    def Close(self):
        self._set(MUIA_Window_Open, False)

class Area(Notify):
    CLASSID = MUIC_Area

class Text(Area):
    CLASSID = MUIC_Text
