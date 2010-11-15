import os
from pymui import *

simplelist = List(Background='ListBack', FixWidth=400)

# Called by selectdir() and when the string object is changed to fill the list
def path_changed(pathname, list_obj):
    if os.path.isfile(pathname):
       pathname = os.path.dirname(pathname)
    if os.path.exists(pathname):
        list_obj.Clear()
        for v in os.listdir(pathname):
            list_obj.InsertSingleString(v, MUIV_List_Insert_Bottom)

# Called when the user press the PopDrawer button
def selectdir(o, l):
    path = GetFilename(o.WindowObject.contents, 'Select a location')[0]
    if path is not None:
        o.Contents = path
        path_changed(path, l)

# A string gadget to indicated a pathname
path = String(Frame='String')
path.Notify(MUIA_String_Acknowledge, lambda e: path_changed(e.value.value, simplelist))

# A button to open a lister where user can select a pathname
bt = Image(Frame='ImageButton',
           Background='ButtonBack',
           InputMode='RelVerify',
           Spec=MUII_PopDrawer)
bt.Notify('Selected', lambda e: selectdir(path, simplelist), when=False)

# The GUI now...
top = VGroup()
top.AddChild(simplelist)

g = HGroup(Child=(path, bt))
top.AddChild(g)

win = Window('PyMUI Test - Simple List Test', RootObject=top, CloseOnReq=True)
app = Application(Window=win,
                  Base="PyMUITest_SimpleList",
                  Author="Guillaume ROGUEZ",
                  Copyright="Guillaume ROGUEZ - MIT license")

win.OpenWindow()
app.Run()

