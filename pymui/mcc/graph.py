###############################################################################
# Copyright (c) 2009 Guillaume Roguez
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

from pymui import Area, c_ULONG, c_BOOL, MAttribute

MUIC_Graph                  = "Graph.mcc"
MUIA_Graph_MaxEntries       = 0xFED10005
MUIA_Graph_Max              = 0xFED10006
MUIA_Graph_DrawBackCurve    = 0xFED10007
MUIA_Graph_SetMax           = 0xFED10008

class Graph(Area):
    CLASSID = MUIC_Graph

    MaxEntries    = MAttribute(MUIA_Graph_MaxEntries    , 'i.g', c_ULONG)
    Max           = MAttribute(MUIA_Graph_Max           , 'isg', c_ULONG)
    DrawBackCurve = MAttribute(MUIA_Graph_DrawBackCurve , 'isg', c_BOOL)
    SetMax        = MAttribute(MUIA_Graph_SetMax        , 'i..', c_BOOL)
