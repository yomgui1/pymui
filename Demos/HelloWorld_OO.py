###############################################################################
# Copyright (c) 2009-2010 Guillaume Roguez
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

## Oriented Object usage of PyMUI 
#
# This example just open a window with only a text button gadget inside.
#
# Quit the program by closing the window or send CTRLC signal in the console.
#

# Importing all pymui API
from pymui import *

# Our window class
class MainWindow(Window):
    def __init__(self):
        super(MainWindow, self).__init__('HelloWorld - OO version - PyMUI demo test',
                                         CloseOnReq = True, # Close the window if window close button is pressed
                                         LeftEdge=MUIV_Window_LeftEdge_Moused,
                                         TopEdge=MUIV_Window_TopEdge_Moused,
                                         Width=320, Height=64)
        self.RootObject = SimpleButton('Hello, World!')
        
# Our Application class
class HelloWorld(Application):
    def __init__(self):
        win = MainWindow()
        
        super(MainWindow, self).__init__(MainWindow=win,
                                         Title="HelloWorld_OO",
                                         Author = "Guillaume ROGUEZ",
                                         Description="OO usage of PyMUI",
                                         Copyright="(c) 2009-2010, Guillaume ROGUEZ",
                                         Base="PyMUI_HelloWorld")

        # Open the window
        win.OpenWindow() # act like 'win.Open = True'

# Go !
app = HelloWorld()
app.Run()
