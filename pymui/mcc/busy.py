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

from pymui import Area

MUIC_Busy            = "Busy.mcc"

MUIM_Busy_Move       = 0x80020001

MUIA_Busy_ShowHideIH = 0x800200a9
MUIA_Busy_Speed      = 0x80020049

MUIV_Busy_Speed_Off  = 0
MUIV_Busy_Speed_User = -1

class Busy(Area):
    CLASSID = MUIC_Busy
    ATTRIBUTES = {
        MUIA_Busy_ShowHideIH: ('ShowHideIH', 'b', 'i..'),
        MUIA_Busy_Speed:      ('Speed',      'i', 'isg'),
        }

    def __init__(self, Speed=MUIV_Busy_Speed_User, **kwds):
        super(Busy, self).__init__(Speed=Speed, **kwds)
