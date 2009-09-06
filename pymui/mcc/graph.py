from pymui import Area

MUIC_Graph                  = "Graph.mcc"
MUIA_Graph_MaxEntries       = 0xFED10005
MUIA_Graph_Max              = 0xFED10006
MUIA_Graph_DrawBackCurve    = 0xFED10007
MUIA_Graph_SetMax           = 0xFED10008

class Graph(Area):
    CLASSID = MUIC_Graph
    ATTRIBUTES = {
        MUIA_Graph_MaxEntries:    ('MaxEntries',    'I', 'i.g'),
        MUIA_Graph_Max:           ('Max',           'I', 'isg'),
        MUIA_Graph_DrawBackCurve: ('DrawBackCurve', 'b', 'isg'),
        MUIA_Graph_SetMax:        ('SetMax',        'b', 'i..'),
        }
