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

from pymui import Group, MAttribute, c_ULONG, c_LONG, c_BOOL

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

    ChildNumber       = MAttribute(MUIA_LayGroup_ChildNumber       , '..g', c_ULONG)
    MaxHeight         = MAttribute(MUIA_LayGroup_MaxHeight         , 'i..', c_LONG)
    MaxWidth          = MAttribute(MUIA_LayGroup_MaxWidth          , 'i..', c_LONG)
    HorizSpacing      = MAttribute(MUIA_LayGroup_HorizSpacing      , 'isg', c_LONG)
    VertSpacing       = MAttribute(MUIA_LayGroup_VertSpacing       , 'isg', c_LONG)
    Spacing           = MAttribute(MUIA_LayGroup_Spacing           , 'is.', c_LONG)
    LeftOffset        = MAttribute(MUIA_LayGroup_LeftOffset        , 'isg', c_LONG)
    TopOffset         = MAttribute(MUIA_LayGroup_TopOffset         , 'isg', c_LONG)
    AskLayout         = MAttribute(MUIA_LayGroup_AskLayout         , 'i..', c_BOOL)
    NumberOfColumns   = MAttribute(MUIA_LayGroup_NumberOfColumns   , '..g', c_ULONG)
    NumberOfRows      = MAttribute(MUIA_LayGroup_NumberOfRows      , '..g', c_ULONG)
    InheritBackground = MAttribute(MUIA_LayGroup_InheritBackground , 'i..', c_BOOL)
