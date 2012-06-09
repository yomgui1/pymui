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

from pymui import Area, c_ULONG, MAttribute, MMethod, c_PenSpec

MUIC_Lamp  = "Lamp.mcc"

# attributes

MUIA_Lamp_Type                  = 0x85b90001 # [ISG]  ULONG
MUIA_Lamp_Color                 = 0x85b90002 # [ISG]  ULONG *
MUIA_Lamp_ColorType             = 0x85b90003 # [..G]  ULONG
MUIA_Lamp_Red                   = 0x85b90004 # [ISG]  ULONG
MUIA_Lamp_Green                 = 0x85b90005 # [ISG]  ULONG
MUIA_Lamp_Blue                  = 0x85b90006 # [ISG]  ULONG
MUIA_Lamp_PenSpec               = 0x85b90007 # [ISG]  struct MUI_PenSpec *


# methods
MUIM_Lamp_SetRGB                = 0x85b90008


# special values
MUIV_Lamp_Type_Tiny             = 0
MUIV_Lamp_Type_Small            = 1
MUIV_Lamp_Type_Medium           = 2
MUIV_Lamp_Type_Big              = 3
MUIV_Lamp_Type_Huge             = 4

MUIV_Lamp_ColorType_UserDefined = 0
MUIV_Lamp_ColorType_Color       = 1
MUIV_Lamp_ColorType_PenSpec     = 2

MUIV_Lamp_Color_Off             = 0
MUIV_Lamp_Color_Ok              = 1
MUIV_Lamp_Color_Warning         = 2
MUIV_Lamp_Color_Error           = 3
MUIV_Lamp_Color_FatalError      = 4
MUIV_Lamp_Color_Processing      = 5
MUIV_Lamp_Color_LookingUp       = 6
MUIV_Lamp_Color_Connecting      = 7
MUIV_Lamp_Color_SendingData     = 8
MUIV_Lamp_Color_ReceivingData   = 9
MUIV_Lamp_Color_LoadingData     = 10
MUIV_Lamp_Color_SavingData      = 11

class Lamp(Area):
    CLASSID = MUIC_Lamp

    def __preset_color(self, attr, v):
        if isinstance(v, (int, long)):
            return c_ULONG.FromLong(v)
        return v

    Type = MAttribute(MUIA_Lamp_Type           , 'isg', c_ULONG)
    Color = MAttribute(MUIA_Lamp_Color         , 'isg', c_ULONG.PointerType(), preSet=__preset_color)
    ColorType = MAttribute(MUIA_Lamp_ColorType , '..g', c_ULONG)
    Red = MAttribute(MUIA_Lamp_Red             , 'isg', c_ULONG)
    Green = MAttribute(MUIA_Lamp_Green         , 'isg', c_ULONG)
    Blue = MAttribute(MUIA_Lamp_Blue           , 'isg', c_ULONG)
    PenSpec = MAttribute(MUIA_Lamp_PenSpec     , 'isg', c_PenSpec)

    SetRGB = MMethod(MUIM_Lamp_SetRGB, [ ('red', c_ULONG), ('green', c_ULONG), ('blue', c_ULONG) ])

    def __init__(self, Color=MUIV_Lamp_Color_Off, **kwds):
        super(Lamp, self).__init__(Color=Color, **kwds)
