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

from pymui.defines import TAG_USER
from pymui import *

MUIC_Textinput       = "Textinput.mcc"
MUIC_Textinputscroll = "Textinputscroll.mcc"

MCC_TI_TAGBASE = TAG_USER | ((1307 << 16) + 0x712)
MCC_TI_ID = lambda x: MCC_TI_TAGBASE + x

MCC_Textinput_Version  = 29
MCC_Textinput_Revision = 1

MUIM_Textinput_ExternalEdit = MCC_TI_ID(1)        # V1
MUIM_Textinput_SaveToFile = MCC_TI_ID(5)          # V1
MUIM_Textinput_LoadFromFile = MCC_TI_ID(6)        # V1
MUIM_Textinput_DoRevert = MCC_TI_ID(8)            # V1
MUIM_Textinput_DoDelLine = MCC_TI_ID(9)           # V1
MUIM_Textinput_DoMarkStart = MCC_TI_ID(10)        # V1
MUIM_Textinput_DoMarkAll = MCC_TI_ID(11)          # V1
MUIM_Textinput_DoCut = MCC_TI_ID(12)              # V1
MUIM_Textinput_DoCopy = MCC_TI_ID(13)             # V1
MUIM_Textinput_DoPaste = MCC_TI_ID(14)            # V1
MUIM_Textinput_AppendText = MCC_TI_ID(15)         # V1
MUIM_Textinput_DoToggleWordwrap = MCC_TI_ID(19)   # V1
MUIM_Textinput_Acknowledge = MCC_TI_ID(20)        # V1
MUIM_Textinput_TranslateEvent = MCC_TI_ID(21)     # V1
MUIM_Textinput_InsertText = MCC_TI_ID(22)         # V1
MUIM_Textinput_DoLeft = MCC_TI_ID(23)             # V1
MUIM_Textinput_DoRight = MCC_TI_ID(24)            # V1
MUIM_Textinput_DoUp = MCC_TI_ID(25)               # V1
MUIM_Textinput_DoDown = MCC_TI_ID(26)             # V1
MUIM_Textinput_DoLineStart = MCC_TI_ID(27)        # V1
MUIM_Textinput_DoLineEnd = MCC_TI_ID(28)          # V1
MUIM_Textinput_DoTop = MCC_TI_ID(29)              # V1
MUIM_Textinput_DoBottom = MCC_TI_ID(30)           # V1
MUIM_Textinput_DoPageUp = MCC_TI_ID(31)           # V1
MUIM_Textinput_DoPageDown = MCC_TI_ID(32)         # V1
MUIM_Textinput_DoPopup = MCC_TI_ID(33)            # V1
MUIM_Textinput_DoPrevWord = MCC_TI_ID(34)         # V1
MUIM_Textinput_DoNextWord = MCC_TI_ID(35)         # V1
MUIM_Textinput_DoDel = MCC_TI_ID(36)              # V1
MUIM_Textinput_DoDelEOL = MCC_TI_ID(37)           # V1
MUIM_Textinput_DoBS = MCC_TI_ID(38)               # V1
MUIM_Textinput_DoBSSOL = MCC_TI_ID(39)            # V1
MUIM_Textinput_DoubleClick = MCC_TI_ID(42)        # V1
MUIM_Textinput_DoBSWord = MCC_TI_ID(43)           # V1
MUIM_Textinput_DoDelWord = MCC_TI_ID(44)          # V1
MUIM_Textinput_DoInsertFile = MCC_TI_ID(45)       # V1
MUIM_Textinput_InsertFromFile = MCC_TI_ID(46)     # V1
MUIM_Textinput_HandleChar = MCC_TI_ID(47)         # V14
MUIM_Textinput_HandleURL = MCC_TI_ID(48)          # V16
MUIM_Textinput_DoToggleCase = MCC_TI_ID(51)       # V21
MUIM_Textinput_DoToggleCaseEOW = MCC_TI_ID(52)    # V21
MUIM_Textinput_DoIncrementDec = MCC_TI_ID(53)     # V21
MUIM_Textinput_DoDecrementDec = MCC_TI_ID(54)     # V21
MUIM_Textinput_DoUndo = MCC_TI_ID(56)             # V21
MUIM_Textinput_DoRedo = MCC_TI_ID(57)             # V21
MUIM_Textinput_DoTab = MCC_TI_ID(58)              # V22
MUIM_Textinput_DoNextGadget = MCC_TI_ID(59)       # V22
MUIM_Textinput_DoSetBookmark1 = MCC_TI_ID(60)     # V22
MUIM_Textinput_DoSetBookmark2 = MCC_TI_ID(61)     # V22
MUIM_Textinput_DoSetBookmark3 = MCC_TI_ID(62)     # V22
MUIM_Textinput_DoGotoBookmark1 = MCC_TI_ID(63)    # V22
MUIM_Textinput_DoGotoBookmark2 = MCC_TI_ID(64)    # V22
MUIM_Textinput_DoGotoBookmark3 = MCC_TI_ID(65)    # V22
MUIM_Textinput_DoCutLine = MCC_TI_ID(66)          # V22
MUIM_Textinput_DoCopyCut = MCC_TI_ID(67)          # V29

MUIA_Textinput_Multiline = MCC_TI_ID(100)             # V1 i.g BOOL
MUIA_Textinput_MaxLen = MCC_TI_ID(101)                # V1 i.g ULONG
MUIA_Textinput_MaxLines = MCC_TI_ID(102)              # V1 i.g ULONG
MUIA_Textinput_AutoExpand = MCC_TI_ID(103)            # V1 isg BOOL
MUIA_Textinput_Contents = MCC_TI_ID(104)              # V1 isg STRPTR
MUIA_Textinput_Blinkrate = MCC_TI_ID(108)             # V1 isg ULONG
MUIA_Textinput_Cursorstyle = MCC_TI_ID(109)           # V1 isg ULONG
MUIA_Textinput_AdvanceOnCR = MCC_TI_ID(110)           # V1 isg BOOL
MUIA_Textinput_TmpExtension = MCC_TI_ID(111)          # V1 isg STRPTR
MUIA_Textinput_Quiet = MCC_TI_ID(112)                 # V1 .sg BOOL
MUIA_Textinput_Acknowledge = MCC_TI_ID(113)           # V1 ..g STRPTR
MUIA_Textinput_Integer = MCC_TI_ID(114)               # V1 isg ULONG
MUIA_Textinput_MinVersion = MCC_TI_ID(115)            # V1 i.. ULONG
MUIA_Textinput_DefaultPopup = MCC_TI_ID(117)          # V1 i.. BOOL
MUIA_Textinput_WordWrap = MCC_TI_ID(118)              # V1 isg ULONG
MUIA_Textinput_IsNumeric = MCC_TI_ID(119)             # V1 isg BOOL
MUIA_Textinput_MinVal = MCC_TI_ID(120)                # V1 isg ULONG
MUIA_Textinput_MaxVal = MCC_TI_ID(121)                # V1 isg ULONG
MUIA_Textinput_AcceptChars = MCC_TI_ID(122)           # V1 isg STRPTR
MUIA_Textinput_RejectChars = MCC_TI_ID(123)           # V1 isg STRPTR
MUIA_Textinput_Changed = MCC_TI_ID(124)               # V1 .sg BOOL
MUIA_Textinput_AttachedList = MCC_TI_ID(125)          # V1 isg Object
MUIA_Textinput_RemainActive = MCC_TI_ID(126)          # V1 isg BOOL
MUIA_Textinput_CursorPos = MCC_TI_ID(127)             # V1 .sg ULONG
MUIA_Textinput_Secret = MCC_TI_ID(128)                # V1 isg BOOL
MUIA_Textinput_Lines = MCC_TI_ID(129)                 # V1 ..g ULONG
MUIA_Textinput_Editable = MCC_TI_ID(130)              # V1 isg BOOL
MUIA_Textinputscroll_UseWinBorder = MCC_TI_ID(131)    # V1 i.. BOOL
MUIA_Textinput_IsOld = MCC_TI_ID(132)                 # V1 isg BOOL
MUIA_Textinput_MarkStart = MCC_TI_ID(133)             # V13 isg ULONG
MUIA_Textinput_MarkEnd = MCC_TI_ID(134)               # V13 isg ULONG
MUIA_Textinputscroll_VertScrollerOnly = MCC_TI_ID(135)# V14 i.. BOOL
MUIA_Textinput_NoInput = MCC_TI_ID(136)               # V15 i.g BOOL
MUIA_Textinput_SetMin = MCC_TI_ID(137)                # V15 isg BOOL
MUIA_Textinput_SetMax = MCC_TI_ID(138)                # V15 isg BOOL
MUIA_Textinput_SetVMax = MCC_TI_ID(139)               # V15 isg BOOL
MUIA_Textinput_Styles = MCC_TI_ID(140)                # V15 isg ULONG
MUIA_Textinput_PreParse = MCC_TI_ID(141)              # V18 isg STRPTR
MUIA_Textinput_Format = MCC_TI_ID(142)                # V19 i.g ULONG
MUIA_Textinput_SetVMin = MCC_TI_ID(143)               # V20 isg BOOL
MUIA_Textinput_HandleURLHook = MCC_TI_ID(144)         # V22 isg struct Hook *
MUIA_Textinput_Tabs = MCC_TI_ID(145)                  # V22 i** ULONG
MUIA_Textinput_TabLen = MCC_TI_ID(146)                # V22 i** ULONG
MUIA_Textinput_Bookmark1 = MCC_TI_ID(147)             # V22 isg ULONG
MUIA_Textinput_Bookmark2 = MCC_TI_ID(148)             # V22 isg ULONG
MUIA_Textinput_Bookmark3 = MCC_TI_ID(149)             # V22 isg ULONG
MUIA_Textinput_CursorSize = MCC_TI_ID(150)            # V22 isg ULONG
MUIA_Textinput_TopLine = MCC_TI_ID(151)               # V22 isg ULONG
MUIA_Textinput_Font = MCC_TI_ID(152)                  # V23 isg ULONG
MUIA_Textinput_SuggestParse = MCC_TI_ID(153)          # V24 isg ULONG
MUIA_Textinput_ProhibitParse = MCC_TI_ID(154)         # V24 isg ULONG
MUIA_Textinput_NoCopy = MCC_TI_ID(155)                # V26 isg ULONG
MUIA_Textinput_MinimumWidth = MCC_TI_ID(156)          # V26 i.g ULONG
MUIA_Textinput_ResetMarkOnCursor = MCC_TI_ID(157)     # V29 isg BOOL
MUIA_Textinput_NoExtraSpacing = MCC_TI_ID(158)        # V29 isg BOOL
MUIA_Textinputscroll_VertBar = MCC_TI_ID(159)         # V29 i   APTR
MUIA_Textinputscroll_HorizBar = MCC_TI_ID(160)        # V29 i   APTR

MUIV_Textinput_ParseB_URL      = 0
MUIV_Textinput_ParseB_Misspell = 1
MUIV_Textinput_ParseF_URL      = (1<<MUIV_Textinput_ParseB_URL)
MUIV_Textinput_ParseF_Misspell = (1<<MUIV_Textinput_ParseB_Misspell)
MUIV_Textinput_Tabs_Ignore     = 0
MUIV_Textinput_Tabs_Spaces     = 1
MUIV_Textinput_Tabs_Disk       = 2
MUIV_Textinput_Tabs_Tabs       = 3
MUIV_Textinput_NoMark          = 0xFFFFFFFF
MUIV_Textinput_Styles_None     = 0
MUIV_Textinput_Styles_MUI      = 1
MUIV_Textinput_Styles_IRC      = 2
MUIV_Textinput_Styles_Email    = 3
MUIV_Textinput_Styles_HTML     = 4
MUIV_Textinput_Format_Left     = 0
MUIV_Textinput_Format_Center   = 1
MUIV_Textinput_Format_Centre   = 1
MUIV_Textinput_Format_Right    = 2
MUIV_Textinput_Font_Normal     = 0
MUIV_Textinput_Font_Fixed      = 1

class Textinput(String):
    CLASSID = MUIC_Textinput

    MaxLines          = MAttribute(MUIA_Textinput_MaxLines          , 'i.g', c_ULONG)
    AcceptChars       = MAttribute(MUIA_Textinput_AcceptChars       , 'isg', c_STRPTR)
    Acknowledge       = MAttribute(MUIA_Textinput_Acknowledge       , '..g', c_STRPTR)
    AdvanceOnCR       = MAttribute(MUIA_Textinput_AdvanceOnCR       , 'isg', c_BOOL)
    AttachedList      = MAttribute(MUIA_Textinput_AttachedList      , 'isg', c_pObject)
    AutoExpand        = MAttribute(MUIA_Textinput_AutoExpand        , 'isg', c_BOOL)
    Blinkrate         = MAttribute(MUIA_Textinput_Blinkrate         , 'isg', c_ULONG)
    Bookmark1         = MAttribute(MUIA_Textinput_Bookmark1         , 'isg', c_ULONG)
    Bookmark2         = MAttribute(MUIA_Textinput_Bookmark2         , 'isg', c_ULONG)
    Bookmark3         = MAttribute(MUIA_Textinput_Bookmark3         , 'isg', c_ULONG)
    Changed           = MAttribute(MUIA_Textinput_Changed           , '.sg', c_BOOL)
    Contents          = MAttribute(MUIA_Textinput_Contents          , 'isg', c_STRPTR)
    CursorPos         = MAttribute(MUIA_Textinput_CursorPos         , '.sg', c_ULONG)
    CursorSize        = MAttribute(MUIA_Textinput_CursorSize        , 'isg', c_ULONG)
    Cursorstyle       = MAttribute(MUIA_Textinput_Cursorstyle       , 'isg', c_ULONG)
    DefaultPopup      = MAttribute(MUIA_Textinput_DefaultPopup      , 'i..', c_BOOL)
    Editable          = MAttribute(MUIA_Textinput_Editable          , 'isg', c_BOOL)
    Font              = MAttribute(MUIA_Textinput_Font              , 'isg', c_ULONG)
    Format            = MAttribute(MUIA_Textinput_Format            , 'i.g', c_ULONG)
    HandleURLHook     = MAttribute(MUIA_Textinput_HandleURLHook     , 'isg', c_APTR)
    Integer           = MAttribute(MUIA_Textinput_Integer           , 'isg', c_ULONG)
    IsNumeric         = MAttribute(MUIA_Textinput_IsNumeric         , 'isg', c_BOOL)
    IsOld             = MAttribute(MUIA_Textinput_IsOld             , 'isg', c_BOOL)
    Lines             = MAttribute(MUIA_Textinput_Lines             , '..g', c_ULONG)
    MarkEnd           = MAttribute(MUIA_Textinput_MarkEnd           , 'isg', c_ULONG)
    MarkStart         = MAttribute(MUIA_Textinput_MarkStart         , 'isg', c_ULONG)
    MaxLen            = MAttribute(MUIA_Textinput_MaxLen            , 'i.g', c_ULONG)
    MaxVal            = MAttribute(MUIA_Textinput_MaxVal            , 'isg', c_ULONG)
    MinVal            = MAttribute(MUIA_Textinput_MinVal            , 'isg', c_ULONG)
    MinVersion        = MAttribute(MUIA_Textinput_MinVersion        , 'i..', c_ULONG)
    MinimumWidth      = MAttribute(MUIA_Textinput_MinimumWidth      , 'i.g', c_ULONG)
    Multiline         = MAttribute(MUIA_Textinput_Multiline         , 'i.g', c_BOOL)
    NoCopy            = MAttribute(MUIA_Textinput_NoCopy            , 'isg', c_ULONG)
    NoExtraSpacing    = MAttribute(MUIA_Textinput_NoExtraSpacing    , 'isg', c_BOOL)
    NoInput           = MAttribute(MUIA_Textinput_NoInput           , 'i.g', c_BOOL)
    PreParse          = MAttribute(MUIA_Textinput_PreParse          , 'isg', c_STRPTR)
    ProhibitParse     = MAttribute(MUIA_Textinput_ProhibitParse     , 'isg', c_ULONG)
    Quiet             = MAttribute(MUIA_Textinput_Quiet             , '.sg', c_BOOL)
    RejectChars       = MAttribute(MUIA_Textinput_RejectChars       , 'isg', c_STRPTR)
    RemainActive      = MAttribute(MUIA_Textinput_RemainActive      , 'isg', c_BOOL)
    ResetMarkOnCursor = MAttribute(MUIA_Textinput_ResetMarkOnCursor , 'isg', c_BOOL)
    Secret            = MAttribute(MUIA_Textinput_Secret            , 'isg', c_BOOL)
    SetMax            = MAttribute(MUIA_Textinput_SetMax            , 'isg', c_BOOL)
    SetMin            = MAttribute(MUIA_Textinput_SetMin            , 'isg', c_BOOL)
    SetVMax           = MAttribute(MUIA_Textinput_SetVMax           , 'isg', c_BOOL)
    SetVMin           = MAttribute(MUIA_Textinput_SetVMin           , 'isg', c_BOOL)
    Styles            = MAttribute(MUIA_Textinput_Styles            , 'isg', c_ULONG)
    SuggestParse      = MAttribute(MUIA_Textinput_SuggestParse      , 'isg', c_ULONG)
    TabLen            = MAttribute(MUIA_Textinput_TabLen            , 'isg', c_ULONG)
    Tabs              = MAttribute(MUIA_Textinput_Tabs              , 'i..', c_ULONG)
    TmpExtension      = MAttribute(MUIA_Textinput_TmpExtension      , 'isg', c_STRPTR)
    TopLine           = MAttribute(MUIA_Textinput_TopLine           , 'isg', c_ULONG)
    WordWrap          = MAttribute(MUIA_Textinput_WordWrap          , 'isg', c_ULONG)

class Textinputscroll(Group):
    CLASSID = MUIC_Textinputscroll

    MaxLines          = MAttribute(MUIA_Textinput_MaxLines          , 'i.g', c_ULONG)
    AcceptChars       = MAttribute(MUIA_Textinput_AcceptChars       , 'isg', c_STRPTR)
    Acknowledge       = MAttribute(MUIA_Textinput_Acknowledge       , '..g', c_STRPTR)
    AdvanceOnCR       = MAttribute(MUIA_Textinput_AdvanceOnCR       , 'isg', c_BOOL)
    AttachedList      = MAttribute(MUIA_Textinput_AttachedList      , 'isg', c_pObject)
    AutoExpand        = MAttribute(MUIA_Textinput_AutoExpand        , 'isg', c_BOOL)
    Blinkrate         = MAttribute(MUIA_Textinput_Blinkrate         , 'isg', c_ULONG)
    Bookmark1         = MAttribute(MUIA_Textinput_Bookmark1         , 'isg', c_ULONG)
    Bookmark2         = MAttribute(MUIA_Textinput_Bookmark2         , 'isg', c_ULONG)
    Bookmark3         = MAttribute(MUIA_Textinput_Bookmark3         , 'isg', c_ULONG)
    Changed           = MAttribute(MUIA_Textinput_Changed           , '.sg', c_BOOL)
    Contents          = MAttribute(MUIA_Textinput_Contents          , 'isg', c_STRPTR)
    CursorPos         = MAttribute(MUIA_Textinput_CursorPos         , '.sg', c_ULONG)
    CursorSize        = MAttribute(MUIA_Textinput_CursorSize        , 'isg', c_ULONG)
    Cursorstyle       = MAttribute(MUIA_Textinput_Cursorstyle       , 'isg', c_ULONG)
    DefaultPopup      = MAttribute(MUIA_Textinput_DefaultPopup      , 'i..', c_BOOL)
    Editable          = MAttribute(MUIA_Textinput_Editable          , 'isg', c_BOOL)
    Font              = MAttribute(MUIA_Textinput_Font              , 'isg', c_ULONG)
    Format            = MAttribute(MUIA_Textinput_Format            , 'i.g', c_ULONG)
    HandleURLHook     = MAttribute(MUIA_Textinput_HandleURLHook     , 'isg', c_APTR)
    Integer           = MAttribute(MUIA_Textinput_Integer           , 'isg', c_ULONG)
    IsNumeric         = MAttribute(MUIA_Textinput_IsNumeric         , 'isg', c_BOOL)
    IsOld             = MAttribute(MUIA_Textinput_IsOld             , 'isg', c_BOOL)
    Lines             = MAttribute(MUIA_Textinput_Lines             , '..g', c_ULONG)
    MarkEnd           = MAttribute(MUIA_Textinput_MarkEnd           , 'isg', c_ULONG)
    MarkStart         = MAttribute(MUIA_Textinput_MarkStart         , 'isg', c_ULONG)
    MaxLen            = MAttribute(MUIA_Textinput_MaxLen            , 'i.g', c_ULONG)
    MaxVal            = MAttribute(MUIA_Textinput_MaxVal            , 'isg', c_ULONG)
    MinVal            = MAttribute(MUIA_Textinput_MinVal            , 'isg', c_ULONG)
    MinVersion        = MAttribute(MUIA_Textinput_MinVersion        , 'i..', c_ULONG)
    MinimumWidth      = MAttribute(MUIA_Textinput_MinimumWidth      , 'i.g', c_ULONG)
    Multiline         = MAttribute(MUIA_Textinput_Multiline         , 'i.g', c_BOOL)
    NoCopy            = MAttribute(MUIA_Textinput_NoCopy            , 'isg', c_ULONG)
    NoExtraSpacing    = MAttribute(MUIA_Textinput_NoExtraSpacing    , 'isg', c_BOOL)
    NoInput           = MAttribute(MUIA_Textinput_NoInput           , 'i.g', c_BOOL)
    PreParse          = MAttribute(MUIA_Textinput_PreParse          , 'isg', c_STRPTR)
    ProhibitParse     = MAttribute(MUIA_Textinput_ProhibitParse     , 'isg', c_ULONG)
    Quiet             = MAttribute(MUIA_Textinput_Quiet             , '.sg', c_BOOL)
    RejectChars       = MAttribute(MUIA_Textinput_RejectChars       , 'isg', c_STRPTR)
    RemainActive      = MAttribute(MUIA_Textinput_RemainActive      , 'isg', c_BOOL)
    ResetMarkOnCursor = MAttribute(MUIA_Textinput_ResetMarkOnCursor , 'isg', c_BOOL)
    Secret            = MAttribute(MUIA_Textinput_Secret            , 'isg', c_BOOL)
    SetMax            = MAttribute(MUIA_Textinput_SetMax            , 'isg', c_BOOL)
    SetMin            = MAttribute(MUIA_Textinput_SetMin            , 'isg', c_BOOL)
    SetVMax           = MAttribute(MUIA_Textinput_SetVMax           , 'isg', c_BOOL)
    SetVMin           = MAttribute(MUIA_Textinput_SetVMin           , 'isg', c_BOOL)
    Styles            = MAttribute(MUIA_Textinput_Styles            , 'isg', c_ULONG)
    SuggestParse      = MAttribute(MUIA_Textinput_SuggestParse      , 'isg', c_ULONG)
    TabLen            = MAttribute(MUIA_Textinput_TabLen            , 'isg', c_ULONG)
    Tabs              = MAttribute(MUIA_Textinput_Tabs              , 'i..', c_ULONG)
    TmpExtension      = MAttribute(MUIA_Textinput_TmpExtension      , 'isg', c_STRPTR)
    TopLine           = MAttribute(MUIA_Textinput_TopLine           , 'isg', c_ULONG)
    WordWrap          = MAttribute(MUIA_Textinput_WordWrap          , 'isg', c_ULONG)
    
    UseWinBorder     = MAttribute(MUIA_Textinputscroll_UseWinBorder     , 'i..', c_BOOL)
    VertScrollerOnly = MAttribute(MUIA_Textinputscroll_VertScrollerOnly , 'i..', c_BOOL)
    VertBar          = MAttribute(MUIA_Textinputscroll_VertBar          , 'i..', c_APTR)
    HorizBar         = MAttribute(MUIA_Textinputscroll_HorizBar         , 'i..', c_APTR)
 
