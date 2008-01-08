from mui import *
from pygima._exec import ColdReboot

# just a simple text gadget
root = Text("\033cHello! I'm a very good program!\nClose me now...",
            Draggable=True,
            Frame=MUIV_Frame_Button,
            InputMode=MUIV_InputMode_RelVerify)

# Creates our mwin window with our text gadget inside
win  = Window(  Title="Rebootator for AmigaOS 4.0",
                LeftEdge=-2,
                TopEdge=-2,
                Width=320,
                Height=64,
                RootObject=root)

# Only one window can be added at init
app  = Application(win)

win.Open = True
win.Notify('CloseRequest', True, app.ReturnID, -1)

# Go!

app.Mainloop()
