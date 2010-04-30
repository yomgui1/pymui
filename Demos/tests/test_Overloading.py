from pymui import *

dragobject = SimpleButton('Test')
dragobject.Draggable = True

class MyMCC(Rectangle):
    _MCC_ = True

    @muimethod(Rectangle.AskMinMax)
    def MCC_AskMinMax(self, msg):
        # Let MUI super fill data
        msg.DoSuper()

        # Print information
        minmax = msg.MinMaxInfo.contents
        for field in minmax._fields_:
            print field[0]+':', getattr(minmax, field[0]).value

        # Set our data
        minmax.DefWidth = 320
        minmax.DefHeight = 240

    @muimethod(MUIM_DragQuery)
    def MCC_DragQuery(self, msg):
        return (MUIV_DragQuery_Accept if msg.obj.value is dragobject else MUIV_DragQuery_Refuse)

assert hasattr(MyMCC, '__pymui_overloaded__')
assert MUIM_AskMinMax in MyMCC.__pymui_overloaded__

o = MyMCC(Dropable=True)

win = Window('Test', RootObject=VGroup(Child=(o, dragobject)), CloseOnReq=True)
app = Application(win)

win.OpenWindow()
app.Run()

