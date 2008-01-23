from pymui import *
from math import sin, cos, pi
from time import sleep

def rot(a, r):
    a *= pi/180
    return int(r*cos(a)), int(r*sin(a))

app = Application()

mainwin = Window(
    Title="HelloWorld - PyMUI demo test",
    LeftEdge=-2,
    TopEdge=-2,
    Width=320,
    Height=64)
app.AddChild(mainwin)

g = VGroup()

# just a simple text gadget
root = Text(open(__file__).read(),
            Draggable=True,
            Frame=MUIV_Frame_String)

g2 = HGroup()

g2.AddChild(SimpleButton("Close"))
g2.AddChild(SimpleButton("Me"))
g2.AddChild(SimpleButton("Now!"))

g.AddChild(root)  
g.AddChild(g2)

mainwin.AddChild(g)
mainwin.Notify('CloseRequest', True, app.ReturnID, MUIV_Application_ReturnID_Quit)
mainwin.Open = True

# Go!
sigs = 0
win_ptr = mainwin.Window   
a = 0
r = 128
ox, oy = rot(a, r)
while True:
    sigs, res = app.NewInput(sigs)
    if res == MUIV_Application_ReturnID_Quit:
        break

    x, y = rot(a, r)
    a += 1
    if a == 360: a = 0
    win_ptr.Move(x - ox, y - oy)
    ox = x
    oy = y

    sleep(0.01)
