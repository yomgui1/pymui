###
## \file _core2.py
## \author ROGUEZ "Yomgui" Guillaume
##

from _muimaster import *
from defines import *

class MetaMCC(type):
    def __new__(metacl, name, bases, dct):
        cl = dct.pop('CLASSID', None)
        if cl:
            dct['__mui_class_id'] = cl
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
        if id not in self._id_meths:
            raise ValueError("This method is forbidden")
        self._keep_do(id, args)
        return self._do(id, args)

    def Get(self, id):
        if id not in self._id_attrs:
            raise ValueError("This attribute is forbidden")
        return self._get(id, self._id_attrs[id]['fmt'])

    def Set(self, id, value):
        if id not in self._id_attrs:
            raise ValueError("This attribute is forbidden")
        self._keep_set(id, value)
        self._set(id, value)

class Notify(PyMUIObject, BoopsiWrapping):
    __metaclass__ = MetaMCC

    CLASSID = MUIC_Notify

    def __new__(cl, **kwds):
        attrs = list(kwds.pop('attributes', []))
        attrs += list((a, v) for a, v in kwds.iteritems())
        return PyMUIObject.__new__(cl, cl.CLASSID, attrs)

    def Notify(self, id, trigvalue, callback):
        self._notify()

    def NNSet(self, id, value):
        self._nnset()

class Application(Notify):
    CLASSID = MUIC_Application

    def __init__(self, *args, **kwds):
        super(Application).__init__(self, *args, **kwds)
        self._windows = []
        
    def Run(self):
        _mainloop(self)

    def AddWindow(self, win):
        if win in self:
            return
        self._do(OM_ADDMEMBER, (win,))
        self._windows.append(win)
        
    def RemWindow(self, win):
        self._windows.remove(win)
        self._do(OM_REMMEMBER, (win,))

class Window(Notify):
    CLASSID = MUIC_Window
    ATTRIBUTES = {
        MUIA_Window_Open: {'prop': 'open', 'fmt': 'i'},
        }

    __current_id = 0

    def __new__(cl, Id=-1, **kwds):
        if Id == -1:
            cl.__current_id += 1
            Id = cl.__current_id
        kwds['Id'] = Id
        return super(Window, cl).__new__(**kwds)

    def Open(self):
        self._set(MUIA_Window_Open, TRUE)

    def Close(self):
        self._set(MUIA_Window_Open, FALSE)

class Area(Notify):
    CLASSID = MUIC_Area

class Text(Area):
    CLASSID = MUIC_Text
