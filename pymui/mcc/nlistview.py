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

import pymui

MAttribute = pymui.MAttribute

MUIC_NListview = "NListview.mcc"

MUIA_NListview_NList                = 0x9d510020 # GM  i.g Object *
MUIA_NListview_Vert_ScrollBar       = 0x9d510021 # GM  isg LONG
MUIA_NListview_Horiz_ScrollBar      = 0x9d510022 # GM  isg LONG
MUIA_NListview_VSB_Width            = 0x9d510023 # GM  ..g LONG
MUIA_NListview_HSB_Height           = 0x9d510024 # GM  ..g LONG

MUIV_Listview_ScrollerPos_Default = 0
MUIV_Listview_ScrollerPos_Left    = 1
MUIV_Listview_ScrollerPos_Right   = 2
MUIV_Listview_ScrollerPos_None    = 3

MUIV_NListview_VSB_Always      = 1
MUIV_NListview_VSB_Auto        = 2
MUIV_NListview_VSB_FullAuto    = 3
MUIV_NListview_VSB_None        = 4
MUIV_NListview_VSB_Default     = 5
MUIV_NListview_VSB_Left        = 6

MUIV_NListview_HSB_Always      = 1
MUIV_NListview_HSB_Auto        = 2
MUIV_NListview_HSB_FullAuto    = 3
MUIV_NListview_HSB_None        = 4
MUIV_NListview_HSB_Default     = 5

MUIV_NListview_VSB_On          = 0x0030
MUIV_NListview_VSB_Off         = 0x0010

MUIV_NListview_HSB_On          = 0x0300
MUIV_NListview_HSB_Off         = 0x0100

### Class ###

class NListview(pymui.Group):
    CLASSID = MUIC_NListview
    
    NList          = MAttribute(MUIA_NListview_NList,           'i.g', pymui.c_pMUIObject, postSet=pymui.postset_child, keep=True)
    VertScrollBar  = MAttribute(MUIA_NListview_Vert_ScrollBar,  'isg', pymui.c_LONG)
    HorizScrollBar = MAttribute(MUIA_NListview_Horiz_ScrollBar, 'isg', pymui.c_LONG)
    VSBWidth       = MAttribute(MUIA_NListview_VSB_Width,       '..g', pymui.c_LONG)
    HSBHeight      = MAttribute(MUIA_NListview_HSB_Height,      '..g', pymui.c_LONG)

