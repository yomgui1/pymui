from pymui import *

app = Application()

mainwin = Window(
    Title="HelloWorld - PyMUI demo test",
    LeftEdge=-2,
    TopEdge=-2,
    Width=320,
    Height=64)

win = Aboutmui(app)
win.Notify('CloseRequest', True, win.Set, 'Open', False)

app.AddChild(mainwin)

g = VGroup()

# just a simple text gadget
root = Text("\033cHello! I'm a very good program!\nClose me now...",
            Draggable=True,
            Frame=MUIV_Frame_String)

g2 = HGroup()

g2.AddChild(SimpleButton("Close"))
g2.AddChild(SimpleButton("Me"))
g2.AddChild(SimpleButton("Now!"))

g.AddChild(root)  
g.AddChild(g2)

mainwin.AddChild(g)
mainwin.Open = True
mainwin.Notify('CloseRequest', True, app.ReturnID, -1)

win.Open = True    

# Go!

app.Run()

