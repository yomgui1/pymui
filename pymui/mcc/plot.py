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

from pymui import *

c_pDOUBLE = c_DOUBLE.PointerType()

MUIC_Plot = "Plot.mcc"

MUIA_Plot_Color            = 0xFED2000C  # [...s.] (ULONG)   v1.3 (24.06.2008)
MUIA_Plot_GridOffsetX      = 0xFED20010  # [ISG..] (DOUBLE*) v1.4 (26.06.2008)   // not implemented yet
MUIA_Plot_GridOffsetY      = 0xFED20011  # [ISG..] (DOUBLE*) v1.4 (26.06.2008)   // not implemented yet
MUIA_Plot_Hidden           = 0xFED20013  # [...s.] (LONG)    v1.5 (01.09.2008)
MUIA_Plot_MaxX             = 0xFED20002  # [ISG..] (DOUBLE*) v1.1 (17.06.2008)
MUIA_Plot_MaxXAuto         = 0xFED20017  # [ISG..] (BOOL)    v1.7 (08.11.2008)
MUIA_Plot_MaxY             = 0xFED20004  # [ISG..] (DOUBLE*) v1.1 (17.06.2008)
MUIA_Plot_MaxYAuto         = 0xFED20019  # [ISG..] (BOOL)    v1.7 (08.11.2008)
MUIA_Plot_MinX             = 0xFED20001  # [ISG..] (DOUBLE*) v1.1 (17.06.2008)
MUIA_Plot_MinXAuto         = 0xFED20016  # [ISG..] (BOOL)    v1.7 (08.11.2008)
MUIA_Plot_MinY             = 0xFED20003  # [ISG..] (DOUBLE*) v1.1 (17.06.2008)
MUIA_Plot_MinYAuto         = 0xFED20018  # [ISG..] (BOOL)    v1.7 (08.11.2008)
MUIA_Plot_Name             = 0xFED20012  # [...s.] (STRPTR)  v1.5 (01.09.2008)
MUIA_Plot_PrimaryGridX     = 0xFED2000E  # [ISG..] (DOUBLE*) v1.4 (26.06.2008)
MUIA_Plot_PrimaryGridY     = 0xFED2000F  # [ISG..] (DOUBLE*) v1.4 (26.06.2008)
MUIA_Plot_Quiet            = 0xFED2000D  # [..S..] (BOOL)    v1.3 (24.06.2008)
MUIA_Plot_Transparency     = 0xFED20015  # [...s.] (DOUBLE*) v1.6 (10.10.2008)   // not implemented yet
MUIA_Plot_Units            = 0xFED20014  # [ISG..] (ULONG)   v1.6 (10.10.2008)   // not implemented yet

MUIM_Plot_BindXValues      = 0xFED2000A  # v1.2 (20.06.2008)
MUIM_Plot_Clear            = 0xFED20005  # v1.1 (17.06.2008)
MUIM_Plot_ExportODS        = 0xFED2001A  # v1.7 (11.11.2008)
MUIM_Plot_Insert           = 0xFED20006  # v1.1 (17.06.2008)
MUIM_Plot_Move             = 0xFED20007  # v1.1 (17.06.2008)
MUIM_Plot_Remove           = 0xFED20008  # v1.1 (17.06.2008)
MUIM_Plot_SetAttr          = 0xFED20009  # v1.2 (20.06.2008)
MUIM_Plot_UnbindXValues    = 0xFED2000B  # v1.2 (20.06.2008)

#***** Values for data type (MUIM_Plot_Insert).

MUIV_Plot_DataType_Double           =   1

#***** Special values for insert position (MUIM_Plot_Insert).

MUIV_Plot_Insert_Top                =   0
MUIV_Plot_Insert_Bottom             =  -1

#***** Special values for move position (MUIM_Plot_Move).

MUIV_Plot_Move_Top                  =   0
MUIV_Plot_Move_Bottom               =  -1
MUIV_Plot_Move_Up                   =  -2
MUIV_Plot_Move_Down                 =  -3

#***** Special values for remove position (MUIM_Plot_Remove).

MUIV_Plot_Remove_Top                =   0
MUIV_Plot_Remove_Bottom             =  -1

#***** Graphic elements identifiers for MUIM_Plot_SetAttr.

MUIV_Plot_BorderLeft                =  -1
MUIV_Plot_BorderTop                 =  -2
MUIV_Plot_BorderRight               =  -3
MUIV_Plot_BorderBottom              =  -4
MUIV_Plot_PrimaryGridX              =  -5
MUIV_Plot_PrimaryGridY              =  -6
MUIV_Plot_SecondaryGridX            =  -7
MUIV_Plot_SecodnaryGridY            =  -8
MUIV_Plot_AxisX                	    =  -9
MUIV_Plot_AxisY                     =  -10
MUIV_Plot_DescX                	    =  -11
MUIV_Plot_DescY                     =  -12

# point types
MUIV_Graph_PointType_None           =   0     # not implemented yet
MUIV_Graph_PointType_Dot	        =   1     # not implemented yet
MUIV_Graph_PointType_EmptySquare    =   2     # not implemented yet
MUIV_Graph_PointType_FilledSquare   =   3     # not implemented yet

# line types
MUIV_Graph_LineType_None            =   0     # not implemented yet
MUIV_Graph_LineType_Solid           =   1     # not implemented yet


class Plot(Area):
    CLASSID = MUIC_Plot

    GridOffsetX  = MAttribute(MUIA_Plot_GridOffsetX,  'isg', c_pDOUBLE)
    GridOffsetY  = MAttribute(MUIA_Plot_GridOffsetY,  'isg', c_pDOUBLE)
    MaxX         = MAttribute(MUIA_Plot_MaxX,         'isg', c_pDOUBLE)
    MaxXAuto     = MAttribute(MUIA_Plot_MaxXAuto,     'isg', c_BOOL)
    MaxY         = MAttribute(MUIA_Plot_MaxY,         'isg', c_pDOUBLE)
    MaxYAuto     = MAttribute(MUIA_Plot_MaxYAuto,     'isg', c_BOOL)
    MinX         = MAttribute(MUIA_Plot_MinX,         'isg', c_pDOUBLE)
    MinXAuto     = MAttribute(MUIA_Plot_MinXAuto,     'isg', c_BOOL)
    MinY         = MAttribute(MUIA_Plot_MinY,         'isg', c_pDOUBLE)
    MinYAuto     = MAttribute(MUIA_Plot_MinYAuto,     'isg', c_BOOL)
    PrimaryGridX = MAttribute(MUIA_Plot_PrimaryGridX, 'isg', c_pDOUBLE)
    PrimaryGridY = MAttribute(MUIA_Plot_PrimaryGridY, 'isg', c_pDOUBLE)
    Quiet        = MAttribute(MUIA_Plot_Quiet,        '.s.', c_BOOL)
    Units        = MAttribute(MUIA_Plot_Units,        'isg', c_ULONG)

    BindXValues   = MMethod(MUIM_Plot_BindXValues, [ ('YDataset', c_LONG), ('XDataset', c_LONG) ])
    Clear         = MMethod(MUIM_Plot_Clear)
    ExportODS     = MMethod(MUIM_Plot_ExportODS, [ ('Name', c_LONG), ('Compression', c_LONG) ])
    Insert        = MMethod(MUIM_Plot_Insert, [ ('Data', c_APTR), ('Type', c_ULONG), ('Length', c_ULONG), ('InsertPos', c_ULONG) ])
    Move          = MMethod(MUIM_Plot_Move, [ ('FromPosition', c_ULONG), ('ToPosition', c_ULONG) ])
    Remove        = MMethod(MUIM_Plot_Remove, [ ('Position', c_ULONG) ])
    SetAttr       = MMethod(MUIM_Plot_SetAttr, [ ('Target', c_LONG), ('Attr', c_ULONG), ('Value', c_ULONG) ], rettype=c_BOOL)
    UnbindXValues = MMethod(MUIM_Plot_UnbindXValues, [ ('YDataset', c_LONG) ])

