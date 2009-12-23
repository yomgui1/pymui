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

from pymui import Area, c_ULONG, c_APTR, c_STRPTR, MAttribute

MUIC_Guigfx = "Guigfx.mcc"
NEWIMAGE_TAGBASE = 0xfec20000
MUIA_Guigfx_Picture          = (NEWIMAGE_TAGBASE+0) # [ISG] APTR
MUIA_Guigfx_FileName         = (NEWIMAGE_TAGBASE+1) # [IS ] STRPTR
MUIA_Guigfx_BitmapInfo       = (NEWIMAGE_TAGBASE+2) # [IS ] struct MUIP_Guigfx_BitMapInfo*
MUIA_Guigfx_ImageInfo        = (NEWIMAGE_TAGBASE+3) # [IS ] struct MUIP_Guigfx_ImageInfo*
MUIA_Guigfx_Transparency     = (NEWIMAGE_TAGBASE+4) # [ISG] ULONG
MUIA_Guigfx_TransparentColor = (NEWIMAGE_TAGBASE+5) # [ISG] ULONG
MUIA_Guigfx_Quality          = (NEWIMAGE_TAGBASE+6) # [ISG] ULONG
MUIA_Guigfx_ScaleMode        = (NEWIMAGE_TAGBASE+7) # [ISG] ULONG
MUIA_Guigfx_ShowRect         = (NEWIMAGE_TAGBASE+8) # [ISG] struct Rect32*

# Quality settings
MUIV_Guigfx_Quality_Low    = 0
MUIV_Guigfx_Quality_Medium = 1
MUIV_Guigfx_Quality_High   = 2
MUIV_Guigfx_Quality_Best   = 3


# Scaling flags
NISMB_SCALEUP            = 0      # allow image to grow
NISMB_SCALEDOWN          = 1      # allow image to shrink
NISMB_KEEPASPECT_PICTURE = 2      # keep picture's aspect ratio
NISMB_KEEPASPECT_SCREEN  = 3      # take screen's aspect ratio into account

NISMF_NONE               = 0
NISMF_SCALEUP            = (1<<NISMB_SCALEUP)
NISMF_SCALEDOWN          = (1<<NISMB_SCALEDOWN)
NISMF_KEEPASPECT_PICTURE = (1<<NISMB_KEEPASPECT_PICTURE)
NISMF_KEEPASPECT_SCREEN  = (1<<NISMB_KEEPASPECT_SCREEN)

# combinations
NISMF_SCALEFREE  = (NISMF_SCALEUP | NISMF_SCALEDOWN)
NISMF_KEEPASPECT = (NISMF_KEEPASPECT_PICTURE | NISMF_KEEPASPECT_SCREEN)
NISMF_SCALEMASK  = 0x0f  # all scaling bits


# transparency flags
NITRB_MASK = 0           # use mask plane if present in picture
NITRB_RGB  = 1           # use RGB value as mask
                         # (see MUIA_Guigfx_TransparentColor)

NITRF_MASK = (1<<NITRB_MASK)
NITRF_RGB  = (1<<NITRB_RGB)


# additional info for passing bitmaps to Guigfx.mcc
NEWIMAGE_BITMAPINFO_VERSION = 1

# additional info for passing intuition images to Guigfx.mcc
NEWIMAGE_IMAGEINFO_VERSION = 1

MUIV_Guigfx_WBPalette      = (-1)   # Workbench's palette (icons!)
MUIV_Guigfx_GreyPalette    = (-3)   # Greyscale palette
MUIV_Guigfx_CurrentPalette = (-5)   # Current screen's palette.
                                    # Probably not very useful in applications

class Guigfx(Area):
    CLASSID = MUIC_Guigfx

    Picture          = MAttribute(MUIA_Guigfx_Picture          , 'isg', c_APTR)
    FileName         = MAttribute(MUIA_Guigfx_FileName         , 'is.', c_STRPTR)
    BitmapInfo       = MAttribute(MUIA_Guigfx_BitmapInfo       , 'is.', c_APTR)
    ImageInfo        = MAttribute(MUIA_Guigfx_ImageInfo        , 'is.', c_APTR)
    Transparency     = MAttribute(MUIA_Guigfx_Transparency     , 'isg', c_ULONG)
    TransparentColor = MAttribute(MUIA_Guigfx_TransparentColor , 'isg', c_ULONG)
    Quality          = MAttribute(MUIA_Guigfx_Quality          , 'isg', c_ULONG)
    ScaleMode        = MAttribute(MUIA_Guigfx_ScaleMode        , 'isg', c_ULONG)
    ShowRect         = MAttribute(MUIA_Guigfx_ShowRect         , 'isg', c_APTR)
