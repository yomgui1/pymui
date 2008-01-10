from pymui import *

app = Application()

mainwin = Window(app,
    Title="Rebootator for AmigaOS 4.0",
    LeftEdge=-2,
    TopEdge=-2,
    Width=320,
    Height=64)
 
win = Aboutmui(app)
win.Notify('CloseRequest', True, win.Set, 'Open', False)
win.Open = True      

g = VGroup(mainwin)

# just a simple text gadget
root = Text(g, "\033cHello! I'm a very good program!\nClose me now...",
            Draggable=True,
            Frame=MUIV_Frame_String)

g2 = HGroup(g)    
SimpleButton(g2, "Close")
SimpleButton(g2, "Me")
SimpleButton(g2, "Now!")

# Creates our mwin window with our text gadget inside

mainwin.Open = True
mainwin.Notify('CloseRequest', True, app.ReturnID, -1)

# Go!

app.Mainloop()



