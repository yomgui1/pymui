###############################################################################
#   Copyright(c) 2009-2014 Guillaume Roguez
#
#   This file is part of PyMUI.
#
#   PyMUI is free software: you can redistribute it and/or modify it under
#   the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PyMUI is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with PyMUI. If not, see <http://www.gnu.org/licenses/>.
#
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
        super(HelloWorld, self).__init__(win,
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
