from mui import *
import arexx

class MPlayer:
    def __init__(self):
        self.port = arexx.port("Python")
        self.portname = "MPLAYER.1"
        self.length = -1
        #print self.port.send(self.portname, "help", 0)[2]

    def Pause(self):
        self.port.send(self.portname, "pause", 0)

    def Seek(self, percent):
        self.port.send(self.portname, "seek abs_percent %u" % percent, 0)

    def GetLength(self):
        return self.port.send(self.portname, "query length", 0)[2]

    def GetPosition(self):
        if self.length == -1:
            self.length = self.GetLength()
        return self.port.send(self.portname, "query position", 0)[2] * 100 / self.length

mp = MPlayer()

maingroup = VGroup()

pn = Text("\033c\033bMPlayer-GUI: Python Power'ed"); maingroup.add(pn)

gr = HGroup(); maingroup.add(gr)
open = SimpleButton('Load'); gr.add(open)
pause = ToggleButton('Pause'); gr.add(pause)
quit = SimpleButton('Quit'); gr.add(quit)

slider = Slider(); maingroup.add(slider)

win = Window(Title="MPlayer GUI", RootObject=maingroup)

app = Application(Title="MPlayer GUI",
                  Version="$VER: MPlayer-GUI 45.635 (04.11.07)",
                  Author="Yomgui",
                  Description="MUI_Python demo for Alchimie7",
                  Base="MPLAYERGUI",
                  Window=win)

#
# Notifications place
#

quit.Notify('Pressed', False, app, 'ReturnID', MUIV_Application_ReturnID_Quit)
win.Notify('CloseRequest', True, app.Quit)

pause.Notify('Selected', MUIV_EveryTime, mp.Pause)
slider.Notify('Value', MUIV_EveryTime, mp.Seek, MUIV_TriggerValue)

win.Open = True

app.Mainloop()
