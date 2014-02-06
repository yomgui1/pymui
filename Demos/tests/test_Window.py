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

from pymui import *

t1 = 'MainWindow'
win = Window(t1, CloseOnReq=True)

assert isinstance(win.Title, c_STRPTR)
assert win.Title.contents == t1

def onclose(evt, win):
    print "Received 'CloseRequest' from Window:", evt.Source
    win.KillApp()

app = Application(Window=win)

win2 = Window('Another one', CloseOnReq=True)

try:
    win2.OpenWindow()
    win2.Open = True
except AttributeError:
    pass
else:
    raise AssertionError("OpenWindow() success on non attached window")

app.AddChild(win2)

win.OpenWindow()
win2.OpenWindow()

app.Run()
