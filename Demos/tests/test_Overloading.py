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
import ctypes

dragobject = SimpleButton('Test')
dragobject.Draggable = True

class MyMCC(Rectangle):
    _MCC_ = True

    @muimethod(Rectangle.AskMinMax)
    def MCC_AskMinMax(self, msg):
        # Let MUI super fill data
        msg.DoSuper()

        # Print information
        minmax = msg.MinMaxInfo.contents
        for field in minmax._fields_:
            print field[0]+':', getattr(minmax, field[0]).value

        # Set our data
        minmax.DefWidth = 320
        minmax.DefHeight = 240

    @muimethod(MUIM_DragQuery)
    def MCC_DragQuery(self, msg):
        return (MUIV_DragQuery_Accept if msg.obj.value is dragobject else MUIV_DragQuery_Refuse)

assert hasattr(MyMCC, '_pymui_overloaded_')
assert MUIM_AskMinMax in MyMCC._pymui_overloaded_

o = MyMCC(Dropable=True)

win = Window('Test', RootObject=VGroup(Child=(o, dragobject)), CloseOnReq=True)
app = Application(win)

win.OpenWindow()
app.Run()

