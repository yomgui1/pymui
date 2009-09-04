# Oriented Object way

from pymui import *

class MainWindow(Window):
    def __new__(self, **kwds):
        super(MainWindow, self).__new__(Title='HelloWorld - OrientObject version - PyMUI demo test',
                                        LeftEdge=MUIV_Window_LeftEdge_Moused,
                                        TopEdge=MUIV_Window_LeftEdge_Mouse,
                                        Width=320,
                                        Height=64, **kwds)

        buttons = [ Text.Button("Close"),
                    Text.Button("Me"),
                    Text.Button("Now!") ]

        butGroup = Group.HGroup()
        butGroup.AddChild(buttons)

        text = Text(Content=MUIX_C + "Hello! I'm a very good program!\nClose me now...",
                    Draggable=True,
                    Frame=MUIV_Frame_String)

        mainGroup = VGroup()
        mainGroup.AddChild( (text, butGroup) )
        
        self.RootObject = mainGroup

class HelloWorld(Application):
    def __init__(self):
        win = MainWindow(killapp=True)
        self.AddWindow(win)
        win.Open = True

# Go !

app = HelloWorld()
app.Run()
