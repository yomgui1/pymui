# Minimal way :-)

from pymui import *
Application(Window(Title="HelloWorld window", Open=True, RootObject=Text.Button("Ok"), killapp=True)).Run()
