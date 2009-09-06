# Raw way to use PyMUI

from pymui import *

button = Text(MUIX_C + "Ok",
              Background = MUII_ButtonBack,
              InputMode  = MUIV_InputMode_RelVerify,
              Frame      = MUIV_Frame_Button,
              Font       = MUIV_Font_Button)

color = Coloradjust(Red=0x45454545, Green=0xffffffff)
g = Group.VGroup(Child=(button, color))

win = Window("HelloWorld window",
             LeftEdge   = MUIV_Window_LeftEdge_Moused,
             TopEdge    = MUIV_Window_TopEdge_Moused,
             RootObject = g,
             Width      = 320,
             Height     = 240)

app = Application()
app.AddWindow(win)

win.Notify(MUIA_Window_CloseRequest, MUIV_EveryTime, app.Quit)
win.Open()

print color.RGB
color.RGB = (0x31323334, 0x31323334, 0x31323334)
print tuple(hex(x) for x in color.RGB)

app.Run()
del app
