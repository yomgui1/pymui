# Raw way to use PyMUI

from pymui import *

button = Text(attributes=((MUIA_Text_Contents, MUIX_C + "Ok"),
                          (MUIA_Background,    MUII_ButtonBack),
                          (MUIA_InputMode,     MUIV_InputMode_RelVerify),
                          (MUIA_Frame,         MUIV_Frame_Button),
                          (MUIA_Font,          MUIV_Font_Button),
                          ))

win = Window(attributes=((MUIA_Window_Title,      "HelloWorld window"),
                         (MUIA_Window_LeftEdge,   MUIV_Window_LeftEdge_Moused),
                         (MUIA_Window_TopEdge,    MUIV_Window_TopEdge_Moused),
                         (MUIA_Window_RootObject, button),
                         ))

app = Application()
app.AddWindow(win)

win.Notify(MUIA_Window_CloseRequest, MUIV_EveryTime, app.Quit)
win.Open()

app.Run()

