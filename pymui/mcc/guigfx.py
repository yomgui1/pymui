from pymui import Area

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
    ATTRIBUTES = {
        MUIA_Guigfx_Picture:            ('Picture',          'p', 'isg'),
        MUIA_Guigfx_FileName:           ('FileName',         's', 'is.'),
        MUIA_Guigfx_BitmapInfo:         ('BitmapInfo',       'p', 'is.'),
        MUIA_Guigfx_ImageInfo:          ('ImageInfo',        'p', 'is.'),
        MUIA_Guigfx_Transparency:       ('Transparency',     'I', 'isg'),
        MUIA_Guigfx_TransparentColor:   ('TransparentColor', 'I', 'isg'),
        MUIA_Guigfx_Quality:            ('Quality',          'I', 'isg'),
        MUIA_Guigfx_ScaleMode:          ('ScaleMode',        'I', 'isg'),
        MUIA_Guigfx_ShowRect:           ('ShowRect',         'p', 'isg'),
        }
