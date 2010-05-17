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

t1 = 'MainWindow'
win = Window(t1)

assert isinstance(win.Title, c_STRPTR)
assert win.Title.contents == t1

def onclose(evt, win):
    print "Received 'CloseRequest' from Window:", evt.Source
    win.KillApp()

win.Notify('CloseRequest', True, onclose, win)

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
