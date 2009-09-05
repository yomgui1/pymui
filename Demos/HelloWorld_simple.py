# Minimal way :-)

from pymui import *

w = Window(Title="HelloWorld window", RootObject=Text.Button("Ok"))
w.Notify('CloseRequest', MUIV_EveryTime, w.KillApp)
app = Application(Window=w)
w.Open()   
app.Run()
