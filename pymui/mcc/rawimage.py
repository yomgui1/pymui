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

from pymui import *
from array import array as _array

__all__ = [ 'MUIC_Rawimage', 'MUIA_Rawimage_Data',
            'RAWIMAGE_FORMAT_RAW_ARGB_ID',
            'RAWIMAGE_FORMAT_RAW_RGB_ID',
            'RAWIMAGE_FORMAT_BZ2_ARGB_ID',
            'mkRawimageData', 'Rawimage' ]

MUIC_Rawimage = "Rawimage.mcc"

MUIA_Rawimage_Data = 0xfed10014 # [IS.] struct MUI_RawimageData * v20.1 (06.01.2007)

RAWIMAGE_FORMAT_RAW_ARGB_ID = 0
RAWIMAGE_FORMAT_RAW_RGB_ID  = 1
RAWIMAGE_FORMAT_BZ2_ARGB_ID = MAKE_ID('B','Z','2','\0')

def mkRawimageData(w, h, data, f=RAWIMAGE_FORMAT_RAW_ARGB_ID):
    size = len(data)
    obj = type('_rawimg_%u' % size,
               (PyMUICStructureType,),
               {'_fields_': [ ('ri_Width',  c_ULONG),
                              ('ri_Height', c_ULONG),
                              ('ri_Format', c_ULONG),
                              ('ri_Size',   c_ULONG),
                              ('ri_Data',   c_UBYTE.ArrayType(size)) ]})()
    obj.ri_Width   = w
    obj.ri_Height  = h
    obj.ri_Format  = f
    obj.ri_Size    = size
    obj.ri_Data[:] = _array('B', data)
    return obj

class Rawimage(Area):
    CLASSID = MUIC_Rawimage

    Picture = MAttribute(MUIA_Rawimage_Data, 'isg', c_APTR, keep=True)

    def __init__(self, Picture=None, **kw):
        if Picture:
            kw['Picture'] = Picture
        super(Rawimage, self).__init__(**kw)
