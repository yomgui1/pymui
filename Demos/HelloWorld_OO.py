from pymui import *

class MainWindow(Window):
    def __init__(self):
        super(MainWindow, self).__init__(
            'HelloWorld - OrientObject version - PyMUI demo test',
            LeftEdge=-2,
            TopEdge=-2,
            Width=320,
            Height=64)

        buttons = [ SimpleButton("Close"),
                    SimpleButton("Me"),
                    SimpleButton("Now!") ]

        butGroup = HGroup()
        butGroup.AddChild(buttons)

        text = Text("\033cHello! I'm a very good program!\nClose me now...",
                    Draggable=True,
                    Frame=MUIV_Frame_String)

        mainGroup = VGroup()
        mainGroup.AddChild( (text, butGroup) )
        
        self.AddChild(mainGroup)

class HelloWorld(Application):
    def Init(self):
        self.win = MainWindow()
        self.AddChild(self.win)
        
        self.win.Notify('CloseRequest', True, self.ReturnID, -1)
        self.win.Open = True

        about = Aboutmui(self, about)
        self.AddChild(about)
        about.Notify('CloseRequest', True, about.Set, 'Open', False)

# Go !

app = HelloWorld()
app.Run()

