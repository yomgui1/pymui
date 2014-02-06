###############################################################################
#   Copyright(c) 2009-2014 Guillaume Roguez
#
#   This file is part of PyMUI.
#
#   PyMUI is free software: you can redistribute it and/or modify it under
#   the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PyMUI is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with PyMUI. If not, see <http://www.gnu.org/licenses/>.
#
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
