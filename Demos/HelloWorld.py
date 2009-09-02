from pymui import *

# One day shall be like this:
#
# Application(Window(Title="HelloWorld window", Open=True, RootObject=SimpleButton("Ok"), KillApp=True)).Run()
#


button = Text(attributes=((MUIA_Text_Contents, "Ok"),
                          (MUIA_Background,    MUII_ButtonBack),
                          (MUIA_InputMode,     MUIV_InputMode_RelVerify),
                          (MUIA_Frame,         MUIV_Frame_Button),
                          (MUIA_Font,          MUIV_Font_Button),
                          ))

mainwin = Window(attributes=((MUIA_Window_Title,      "HelloWorld window"),
                             (MUIA_Window_LeftEdge,   MUIV_Window_LeftEdge_Moused),
                             (MUIA_Window_TopEdge,    MUIV_Window_TopEdge_Moused),
                             (MUIA_Window_RootObject, button),
                             ))

app = Application()
app.AddWindow(mainwin)

mainwin.Open()
app.Run()
