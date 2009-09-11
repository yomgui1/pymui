# Oriented Object way

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

class MainWindow(Window):
    def __init__(self):
        super(MainWindow, self).__init__('HelloWorld - OrientObject version - PyMUI demo test',
                                         LeftEdge=MUIV_Window_LeftEdge_Moused,
                                         TopEdge=MUIV_Window_TopEdge_Moused,
                                         Width=320, Height=64)
 
        buttons = [ Text.Button("Close"),
                    Text.Button("Me"),
                    Text.Button("Now!") ]

        butGroup = Group.HGroup()
        butGroup.AddChild(buttons)

        text = Text(Contents=MUIX_C + "Hello! I'm a very good program!\nClose me now...",
                    Draggable=True,
                    Frame=MUIV_Frame_String)

        mainGroup = Group.VGroup()
        mainGroup.AddChild( (text, butGroup) )
        self.RootObject = mainGroup
        

class HelloWorld(Application):
    def __init__(self):
        super(HelloWorld, self).__init__()
        win = MainWindow()
        win.Notify('CloseRequest', True, self.Quit)
        self.AddWindow(win)
        win.Open()

# Go !

app = HelloWorld()
app.Run()

