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
