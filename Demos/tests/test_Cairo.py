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
import cairo, math

class MyMCC(Rectangle):
    _MCC_ = True
    done = False

    @muimethod(MUIM_AskMinMax)
    def MCC_AskMinMax(self, msg):
        msg.DoSuper()
        minmax = msg.MinMaxInfo.contents
        minmax.MinWidth = minmax.MinWidth.value + 320
        minmax.MinHeight = minmax.MinHeight.value + 240

    @muimethod(MUIM_Draw)
    def MCC_Draw(self, msg):
        msg.DoSuper()

        if msg.flags.value & MADF_DRAWOBJECT:
            self.draw(self.MWidth, self.MHeight)

    def draw(self, w, h):
        cr = self.cairo_context
        cr.get_target().set_device_offset(.5,.5)
        cr.rectangle(0,0,w-1,h-1)
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.fill()

        cr.set_antialias(cairo.ANTIALIAS_NONE)
        cr.set_line_width(1)
        cr.set_source_rgb(1,0,0)
        cr.rectangle(0,0,w-1,h-1)
        cr.stroke()

        cr.set_antialias(cairo.ANTIALIAS_DEFAULT)
        cr.set_font_size(24)
        for i in range(9):
            cr.set_source_rgb(i/8.,1.-i/8.,0)
            cr.move_to(32+i*16, 32+i*24)
            cr.text_path("Hello World")
            cr.fill()
            cr.stroke()


o = MyMCC(InnerSpacing=0, FillArea=False)

g = VGroup()
bt = SimpleButton("Draw")
bt.Notify('Pressed', lambda e: o.Redraw(), when=False)
g.AddChild(o)
g.AddChild(bt)
win = Window('Test', RootObject=g, CloseOnReq=True)
app = Application(win)

win.OpenWindow()
app.Run()

