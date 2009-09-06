from pymui import Group

MUIC_LayGroup = "LayGroup.mcc"
TAGBASE_LAYGROUP = (0x80000000 + (0x2553 << 16))
MUIA_LayGroup_ChildNumber       = (TAGBASE_LAYGROUP + 0x0001) # [..G] ULONG
MUIA_LayGroup_MaxHeight         = (TAGBASE_LAYGROUP + 0x0002) # [I..] WORD
MUIA_LayGroup_MaxWidth          = (TAGBASE_LAYGROUP + 0x0003) # [I..] WORD
MUIA_LayGroup_HorizSpacing      = (TAGBASE_LAYGROUP + 0x0004) # [ISG] WORD
MUIA_LayGroup_VertSpacing       = (TAGBASE_LAYGROUP + 0x0005) # [ISG] WORD
MUIA_LayGroup_Spacing           = (TAGBASE_LAYGROUP + 0x0006) # [IS.] WORD
MUIA_LayGroup_LeftOffset        = (TAGBASE_LAYGROUP + 0x0007) # [ISG] WORD
MUIA_LayGroup_TopOffset         = (TAGBASE_LAYGROUP + 0x0008) # [ISG] WORD
MUIA_LayGroup_AskLayout         = (TAGBASE_LAYGROUP + 0x0009) # [I..] BOOL
MUIA_LayGroup_NumberOfColumns   = (TAGBASE_LAYGROUP + 0x000A) # [..G] ULONG
MUIA_LayGroup_NumberOfRows      = (TAGBASE_LAYGROUP + 0x000B) # [..G] ULONG
MUIA_LayGroup_InheritBackground = (TAGBASE_LAYGROUP + 0x000C) # [I..] BOOL

MUIV_LayGroup_Spacing_Default =  8
MUIV_LayGroup_Spacing_Minimum =  0
MUIV_LayGroup_Spacing_Maximum = 24

# Values for MUIA_LayGroup_LeftOffset
MUIV_LayGroup_LeftOffset_Default =  0
MUIV_LayGroup_LeftOffset_Minimum =  0
MUIV_LayGroup_LeftOffset_Maximum = 32
MUIV_LayGroup_LeftOffset_Center  = -1

# Values for MUIA_LayGroup_TopOffset
MUIV_LayGroup_TopOffset_Default =  0
MUIV_LayGroup_TopOffset_Minimum =  0
MUIV_LayGroup_TopOffset_Maximum = 32
MUIV_LayGroup_TopOffset_Center  = -1

# Values for MUIM_LayGroup_AskLayout
MUIV_LayGroup_MaxHeight_Auto = -1
MUIV_LayGroup_MaxWidth_Auto  = -1

class LayGroup(Group):
    CLASSID = MUIC_LayGroup
    ATTRIBUTES = {
        MUIA_LayGroup_ChildNumber:       ('ChildNumber',       'I', '..g'),
        MUIA_LayGroup_MaxHeight:         ('MaxHeight',         'i', 'i..'),
        MUIA_LayGroup_MaxWidth:          ('MaxWidth',          'i', 'i..'),
        MUIA_LayGroup_HorizSpacing:      ('HorizSpacing',      'i', 'isg'),
        MUIA_LayGroup_VertSpacing:       ('VertSpacing',       'i', 'isg'),
        MUIA_LayGroup_Spacing:           ('Spacing',           'i', 'is.'),
        MUIA_LayGroup_LeftOffset:        ('LeftOffset',        'i', 'isg'),
        MUIA_LayGroup_TopOffset:         ('TopOffset',         'i', 'isg'),
        MUIA_LayGroup_AskLayout:         ('AskLayout',         'b', 'i..'),
        MUIA_LayGroup_NumberOfColumns:   ('NumberOfColumns',   'I', '..g'),
        MUIA_LayGroup_NumberOfRows:      ('NumberOfRows',      'I', '..g'),
        MUIA_LayGroup_InheritBackground: ('InheritBackground', 'b', 'i..'),
        }
