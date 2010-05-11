###############################################################################
# Copyright (c) 2009-2010 Guillaume Roguez
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
    
    NList          = MAttribute(MUIA_NListview_NList,           'i.g', pymui.c_MUIObject, postSet=pymui.postset_child)
    VertScrollBar  = MAttribute(MUIA_NListview_Vert_ScrollBar,  'isg', pymui.c_LONG)
    HorizScrollBar = MAttribute(MUIA_NListview_Horiz_ScrollBar, 'isg', pymui.c_LONG)
    VSBWidth       = MAttribute(MUIA_NListview_VSB_Width,       '..g', pymui.c_LONG)
    HSBHeight      = MAttribute(MUIA_NListview_HSB_Height,      '..g', pymui.c_LONG)

