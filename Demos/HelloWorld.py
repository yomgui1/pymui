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

## Functional usage of PyMUI 
#
# This example just open a window with only a text button gadget inside.
#
# Quit the program by closing the window or send CTRLC signal in the console.
#

# Importing all pymui API
from pymui import *

### Objects creation ###

# A little button
but = SimpleButton('Hello, World!')

# The window (using the previous button as root object)
win = Window('HelloWorld window - functionnal version - PyMUI demo test',
             CloseOnReq = True, # Close the window if window close button is pressed
             LeftEdge   = MUIV_Window_LeftEdge_Moused,
             TopEdge    = MUIV_Window_TopEdge_Moused,
             RootObject = but,
             Width      = 320,
             Height     = 64)

# Creating an Application object
# Adding the previous created window as the main window of the application
# A main window closes the application when the window is closed.
app = Application(win,
                  Title="HelloWorld",
                  Author = "Guillaume ROGUEZ",
                  Description="Simple functional usage of PyMUI",
                  Copyright="(c) 2009-2010, Guillaume ROGUEZ",
                  Base="PyMUI_HelloWorld")

# Open it
win.Open = True

# Run the mainloop
app.Run()

