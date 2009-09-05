# Oriented Object way

from pymui import *

class MainWindow(Window):
    def __init__(self):
        super(MainWindow, self).__init__('HelloWorld - OrientObject version - PyMUI demo test',
                                         LeftEdge=MUIV_Window_LeftEdge_Moused,
                                         TopEdge=MUIV_Window_TopEdge_Moused,
                                         Width=320, Height=64)
 
        buttons = [ Text.Button("Close"),
                    Text.Button("Me"),
                    Text.Button("Now!") ]

        butGroup = Group.HGroup()
        butGroup.AddChild(buttons)

        text = Text(Contents=MUIX_C + "Hello! I'm a very good program!\nClose me now...",
                    Draggable=True,
                    Frame=MUIV_Frame_String)

        mainGroup = Group.VGroup()
        mainGroup.AddChild( (text, butGroup) )
        self.RootObject = mainGroup
        

class HelloWorld(Application):
    def __init__(self):
        super(HelloWorld, self).__init__()
        win = MainWindow()
        win.Notify('CloseRequest', True, self.Quit)
        self.AddWindow(win)
        win.Open()

# Go !

app = HelloWorld()
app.Run()

