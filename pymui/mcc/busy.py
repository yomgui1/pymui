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

from pymui import Area, c_LONG, c_BOOL, MAttribute, MMethod

MUIC_Busy            = "Busy.mcc"

MUIM_Busy_Move       = 0x80020001

MUIA_Busy_ShowHideIH = 0x800200a9
MUIA_Busy_Speed      = 0x80020049

MUIV_Busy_Speed_Off  = 0
MUIV_Busy_Speed_User = -1

class Busy(Area):
    CLASSID = MUIC_Busy

    ShowHideIH = MAttribute(MUIA_Busy_ShowHideIH , 'i..', c_BOOL)
    Speed      = MAttribute(MUIA_Busy_Speed      , 'isg', c_LONG)

    Move = MMethod(MUIM_Busy_Move)

    def __init__(self, Speed=MUIV_Busy_Speed_User, **kwds):
        super(Busy, self).__init__(Speed=Speed, **kwds)
