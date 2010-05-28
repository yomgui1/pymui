###############################################################################
# Copyright (c) 2010 Guillaume Roguez
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

__all__ = [ 'MUIC_Rawimage', 'MUIA_Rawimage_Data',
            'RAWIMAGE_FORMAT_RAW_ARGB_ID', 'RAWIMAGE_FORMAT_BZ2_ARGB_ID',
            'mkRawimageData', 'Rawimage' ]

MUIC_Rawimage = "Rawimage.mcc"

MUIA_Rawimage_Data = 0xfed10014 # [IS.] struct MUI_RawimageData * v20.1 (06.01.2007)

RAWIMAGE_FORMAT_RAW_ARGB_ID = 0
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
    obj.ri_Data[:] = [ ord(x) for x in data ]
    return obj

class Rawimage(Area):
    CLASSID = MUIC_Rawimage

    Picture = MAttribute(MUIA_Rawimage_Data, 'is.', c_APTR, keep=True)

    def __init__(self, Picture=None, **kw):
        if Picture:
            kw['Picture'] = Picture
        super(Rawimage, self).__init__(**kw)
