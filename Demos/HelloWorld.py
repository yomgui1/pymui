# Raw way to use PyMUI

###############################################################################
# Copyright (c) 2009 Guillaume Roguez
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

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
