###############################################################################
# Copyright (c) 2009-2010 Guillaume Roguez
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

import pymui

MAttribute = pymui.MAttribute
MMethod = pymui.MMethod

MUIC_NList = "NList.mcc"

### Attributes ###

MUIA_NList_TypeSelect               = 0x9d510030 # GM  is.  LONG
MUIA_NList_Prop_DeltaFactor         = 0x9d510031 # GM  ..gn LONG
MUIA_NList_Horiz_DeltaFactor        = 0x9d510032 # GM  ..gn LONG

MUIA_NList_Horiz_First              = 0x9d510033 # GM  .sgn LONG
MUIA_NList_Horiz_Visible            = 0x9d510034 # GM  ..gn LONG
MUIA_NList_Horiz_Entries            = 0x9d510035 # GM  ..gn LONG

MUIA_NList_Prop_First               = 0x9d510036 # GM  .sgn LONG
MUIA_NList_Prop_Visible             = 0x9d510037 # GM  ..gn LONG
MUIA_NList_Prop_Entries             = 0x9d510038 # GM  ..gn LONG

MUIA_NList_TitlePen                 = 0x9d510039 # GM  isg  LONG
MUIA_NList_ListPen                  = 0x9d51003a # GM  isg  LONG
MUIA_NList_SelectPen                = 0x9d51003b # GM  isg  LONG
MUIA_NList_CursorPen                = 0x9d51003c # GM  isg  LONG
MUIA_NList_UnselCurPen              = 0x9d51003d # GM  isg  LONG

MUIA_NList_ListBackground           = 0x9d51003e # GM  isg  LONG
MUIA_NList_TitleBackground          = 0x9d51003f # GM  isg  LONG
MUIA_NList_SelectBackground         = 0x9d510040 # GM  isg  LONG
MUIA_NList_CursorBackground         = 0x9d510041 # GM  isg  LONG
MUIA_NList_UnselCurBackground       = 0x9d510042 # GM  isg  LONG

MUIA_NList_MultiClick               = 0x9d510043 # GM  ..gn LONG

MUIA_NList_DefaultObjectOnClick     = 0x9d510044 # GM  is.  BOOL

MUIA_NList_ClickColumn              = 0x9d510045 # GM  ..g  LONG
MUIA_NList_DefClickColumn           = 0x9d510046 # GM  isg  LONG
MUIA_NList_DoubleClick              = 0x9d510047 # GM  ..gn LONG
MUIA_NList_DragType                 = 0x9d510048 # GM  isg  LONG
MUIA_NList_Input                    = 0x9d510049 # GM  isg  BOOL
MUIA_NList_MultiSelect              = 0x9d51004a # GM  is.  LONG
MUIA_NList_SelectChange             = 0x9d51004b # GM  ...n BOOL

MUIA_NList_Active                   = 0x9d51004c # GM  isgn LONG
MUIA_NList_AdjustHeight             = 0x9d51004d # GM  i..  BOOL
MUIA_NList_AdjustWidth              = 0x9d51004e # GM  i..  BOOL
MUIA_NList_AutoVisible              = 0x9d51004f # GM  isg  BOOL
MUIA_NList_CompareHook              = 0x9d510050 # GM  is.  struct Hook *
MUIA_NList_ConstructHook            = 0x9d510051 # GM  is.  struct Hook *
MUIA_NList_DestructHook             = 0x9d510052 # GM  is.  struct Hook *
MUIA_NList_DisplayHook              = 0x9d510053 # GM  is.  struct Hook *
MUIA_NList_DragSortable             = 0x9d510054 # GM  isg  BOOL
MUIA_NList_DropMark                 = 0x9d510055 # GM  ..g  LONG
MUIA_NList_Entries                  = 0x9d510056 # GM  ..gn LONG
MUIA_NList_First                    = 0x9d510057 # GM  isgn LONG
MUIA_NList_Format                   = 0x9d510058 # GM  isg  STRPTR
MUIA_NList_InsertPosition           = 0x9d510059 # GM  ..gn LONG
MUIA_NList_MinLineHeight            = 0x9d51005a # GM  is.  LONG
MUIA_NList_MultiTestHook            = 0x9d51005b # GM  is.  struct Hook *
MUIA_NList_Pool                     = 0x9d51005c # GM  i..  APTR
MUIA_NList_PoolPuddleSize           = 0x9d51005d # GM  i..  ULONG
MUIA_NList_PoolThreshSize           = 0x9d51005e # GM  i..  ULONG
MUIA_NList_Quiet                    = 0x9d51005f # GM  .s.  BOOL
MUIA_NList_ShowDropMarks            = 0x9d510060 # GM  isg  BOOL
MUIA_NList_SourceArray              = 0x9d510061 # GM  i..  APTR *
MUIA_NList_Title                    = 0x9d510062 # GM  isg  char *
MUIA_NList_Visible                  = 0x9d510063 # GM  ..g  LONG
MUIA_NList_CopyEntryToClipHook      = 0x9d510064 # GM  is.  struct Hook *
MUIA_NList_KeepActive               = 0x9d510065 # GM  .s.  Obj *
MUIA_NList_MakeActive               = 0x9d510066 # GM  .s.  Obj *
MUIA_NList_SourceString             = 0x9d510067 # GM  i..  char *
MUIA_NList_CopyColumnToClipHook     = 0x9d510068 # GM  is.  struct Hook *
MUIA_NList_ListCompatibility        = 0x9d510069 # GM  ...  OBSOLETE
MUIA_NList_AutoCopyToClip           = 0x9d51006A # GM  is.  BOOL
MUIA_NList_TabSize                  = 0x9d51006B # GM  isg  ULONG
MUIA_NList_SkipChars                = 0x9d51006C # GM  isg  char *
MUIA_NList_DisplayRecall            = 0x9d51006D # GM  .g.  BOOL
MUIA_NList_PrivateData              = 0x9d51006E # GM  isg  APTR
MUIA_NList_EntryValueDependent      = 0x9d51006F # GM  isg  BOOL

MUIA_NList_StackCheck               = 0x9d510097 # GM  i..  BOOL
MUIA_NList_WordSelectChars          = 0x9d510098 # GM  isg  char *
MUIA_NList_EntryClick               = 0x9d510099 # GM  ..gn LONG
MUIA_NList_DragColOnly              = 0x9d51009A # GM  isg  LONG
MUIA_NList_TitleClick               = 0x9d51009B # GM  isgn LONG
MUIA_NList_DropType                 = 0x9d51009C # GM  ..g  LONG
MUIA_NList_ForcePen                 = 0x9d51009D # GM  isg  LONG
MUIA_NList_SourceInsert             = 0x9d51009E # GM  i..  struct MUIP_NList_InsertWrap *
MUIA_NList_TitleSeparator           = 0x9d51009F # GM  isg  BOOL

MUIA_NList_SortType2                = 0x9d5100ED # GM  isgn LONG
MUIA_NList_TitleClick2              = 0x9d5100EE # GM  isgn LONG
MUIA_NList_TitleMark2               = 0x9d5100EF # GM  isg  LONG
MUIA_NList_MultiClickAlone          = 0x9d5100F0 # GM  ..gn LONG
MUIA_NList_TitleMark                = 0x9d5100F1 # GM  isg  LONG
MUIA_NList_DragSortInsert           = 0x9d5100F2 # GM  ..gn LONG
MUIA_NList_MinColSortable           = 0x9d5100F3 # GM  isg  LONG
MUIA_NList_Imports                  = 0x9d5100F4 # GM  isg  LONG
MUIA_NList_Exports                  = 0x9d5100F5 # GM  isg  LONG
MUIA_NList_Columns                  = 0x9d5100F6 # GM  isgn BYTE *
MUIA_NList_LineHeight               = 0x9d5100F7 # GM  ..gn LONG
MUIA_NList_ButtonClick              = 0x9d5100F8 # GM  ..gn LONG
MUIA_NList_CopyEntryToClipHook2     = 0x9d5100F9 # GM  is.  struct Hook *
MUIA_NList_CopyColumnToClipHook2    = 0x9d5100FA # GM  is.  struct Hook *
MUIA_NList_CompareHook2             = 0x9d5100FB # GM  is.  struct Hook *
MUIA_NList_ConstructHook2           = 0x9d5100FC # GM  is.  struct Hook *
MUIA_NList_DestructHook2            = 0x9d5100FD # GM  is.  struct Hook *
MUIA_NList_DisplayHook2             = 0x9d5100FE # GM  is.  struct Hook *
MUIA_NList_SortType                 = 0x9d5100FF # GM  isgn LONG


MUIA_NLIMG_EntryCurrent             = MUIA_NList_First   # LONG (special for nlist custom image object)
MUIA_NLIMG_EntryHeight              = MUIA_NList_Visible # LONG (special for nlist custom image object)

### Special attribute values ###

MUIV_NList_TypeSelect_Line = 0
MUIV_NList_TypeSelect_Char = 1

MUIV_NList_Font        = -20
MUIV_NList_Font_Little = -21
MUIV_NList_Font_Fixed  = -22

MUIV_NList_ConstructHook_String = -1
MUIV_NList_DestructHook_String  = -1

MUIV_NList_Active_Off      = -1
MUIV_NList_Active_Top      = -2
MUIV_NList_Active_Bottom   = -3
MUIV_NList_Active_Up       = -4
MUIV_NList_Active_Down     = -5
MUIV_NList_Active_PageUp   = -6
MUIV_NList_Active_PageDown = -7

MUIV_NList_First_Top             = -2
MUIV_NList_First_Bottom          = -3
MUIV_NList_First_Up              = -4
MUIV_NList_First_Down            = -5
MUIV_NList_First_PageUp          = -6
MUIV_NList_First_PageDown        = -7
MUIV_NList_First_Up2             = -8
MUIV_NList_First_Down2           = -9
MUIV_NList_First_Up4             = -10
MUIV_NList_First_Down4           = -11

MUIV_NList_Horiz_First_Start     = -2
MUIV_NList_Horiz_First_End       = -3
MUIV_NList_Horiz_First_Left      = -4
MUIV_NList_Horiz_First_Right     = -5
MUIV_NList_Horiz_First_PageLeft  = -6
MUIV_NList_Horiz_First_PageRight = -7
MUIV_NList_Horiz_First_Left2     = -8
MUIV_NList_Horiz_First_Right2    = -9
MUIV_NList_Horiz_First_Left4     = -10
MUIV_NList_Horiz_First_Right4    = -11

MUIV_NList_MultiSelect_None       = 0
MUIV_NList_MultiSelect_Default    = 1
MUIV_NList_MultiSelect_Shifted    = 2
MUIV_NList_MultiSelect_Always     = 3

MUIV_NList_Insert_Top            = 0
MUIV_NList_Insert_Active         = -1
MUIV_NList_Insert_Sorted         = -2
MUIV_NList_Insert_Bottom         = -3

MUIV_NList_Remove_First          = 0
MUIV_NList_Remove_Active         = -1
MUIV_NList_Remove_Last           = -2
MUIV_NList_Remove_Selected       = -3

MUIV_NList_Select_Off             = 0
MUIV_NList_Select_On              = 1
MUIV_NList_Select_Toggle          = 2
MUIV_NList_Select_Ask             = 3

MUIV_NList_GetEntry_Active       = -1
MUIV_NList_GetEntryInfo_Line     = -2

MUIV_NList_Select_Active         = -1
MUIV_NList_Select_All            = -2

MUIV_NList_Redraw_Active         = -1
MUIV_NList_Redraw_All            = -2
MUIV_NList_Redraw_Title          = -3
MUIV_NList_Redraw_VisibleCols    = -5

MUIV_NList_Move_Top              = 0
MUIV_NList_Move_Active           = -1
MUIV_NList_Move_Bottom           = -2
MUIV_NList_Move_Next             = -3 # only valid for second parameter (and not with Move_Selected)
MUIV_NList_Move_Previous         = -4 # only valid for second parameter (and not with Move_Selected)
MUIV_NList_Move_Selected         = -5 # only valid for first parameter

MUIV_NList_Exchange_Top          = 0
MUIV_NList_Exchange_Active       = -1
MUIV_NList_Exchange_Bottom       = -2
MUIV_NList_Exchange_Next         = -3 # only valid for second parameter
MUIV_NList_Exchange_Previous     = -4 # only valid for second parameter

MUIV_NList_Jump_Top              = 0
MUIV_NList_Jump_Active           = -1
MUIV_NList_Jump_Bottom           = -2
MUIV_NList_Jump_Up               = -4
MUIV_NList_Jump_Down             = -3

MUIV_NList_NextSelected_Start    = -1
MUIV_NList_NextSelected_End      = -1

MUIV_NList_PrevSelected_Start    = -1
MUIV_NList_PrevSelected_End      = -1

MUIV_NList_DragType_None          = 0
MUIV_NList_DragType_Default       = 1
MUIV_NList_DragType_Immediate     = 2
MUIV_NList_DragType_Borders       = 3
MUIV_NList_DragType_Qualifier     = 4

MUIV_NList_CopyToClip_Active     = -1
MUIV_NList_CopyToClip_Selected   = -2
MUIV_NList_CopyToClip_All        = -3
MUIV_NList_CopyToClip_Entries    = -4
MUIV_NList_CopyToClip_Entry      = -5
MUIV_NList_CopyToClip_Strings    = -6
MUIV_NList_CopyToClip_String     = -7

MUIV_NList_CopyTo_Active         = -1
MUIV_NList_CopyTo_Selected       = -2
MUIV_NList_CopyTo_All            = -3
MUIV_NList_CopyTo_Entries        = -4
MUIV_NList_CopyTo_Entry          = -5

MUIV_NLCT_Success                 = 0
MUIV_NLCT_OpenErr                 = 1
MUIV_NLCT_WriteErr                = 2
MUIV_NLCT_Failed                  = 3

MUIV_NList_ForcePen_On            = 1
MUIV_NList_ForcePen_Off           = 0
MUIV_NList_ForcePen_Default       = -1

MUIV_NList_DropType_Mask          = 0x00FF
MUIV_NList_DropType_None          = 0
MUIV_NList_DropType_Above         = 1
MUIV_NList_DropType_Below         = 2
MUIV_NList_DropType_Onto          = 3

MUIV_NList_DoMethod_Active       = -1
MUIV_NList_DoMethod_Selected     = -2
MUIV_NList_DoMethod_All          = -3

MUIV_NList_DoMethod_Entry        = -1
MUIV_NList_DoMethod_Self         = -2
MUIV_NList_DoMethod_App          = -3

MUIV_NList_EntryValue             = pymui.MUIV_TriggerValue + 0x100
MUIV_NList_EntryPosValue          = pymui.MUIV_TriggerValue + 0x102
MUIV_NList_SelfValue              = pymui.MUIV_TriggerValue + 0x104
MUIV_NList_AppValue               = pymui.MUIV_TriggerValue + 0x106

MUIV_NList_ColWidth_All          = -1
MUIV_NList_ColWidth_Default      = -1
MUIV_NList_ColWidth_Get          = -2

MUIV_NList_ContextMenu_Default    = 0x9d510031
MUIV_NList_ContextMenu_TopOnly    = 0x9d510033
MUIV_NList_ContextMenu_BarOnly    = 0x9d510035
MUIV_NList_ContextMenu_Bar_Top    = 0x9d510037
MUIV_NList_ContextMenu_Always     = 0x9d510039
MUIV_NList_ContextMenu_Never      = 0x9d51003b

MUIV_NList_Menu_DefWidth_This     = 0x9d51003d
MUIV_NList_Menu_DefWidth_All      = 0x9d51003f
MUIV_NList_Menu_DefOrder_This     = 0x9d510041
MUIV_NList_Menu_DefOrder_All      = 0x9d510043
MUIV_NList_Menu_Default_This      = MUIV_NList_Menu_DefWidth_This
MUIV_NList_Menu_Default_All       = MUIV_NList_Menu_DefWidth_All

MUIV_NList_SortType_None          = 0xF0000000
MUIV_NList_SortTypeAdd_None       = 0x00000000
MUIV_NList_SortTypeAdd_2Values    = 0x80000000
MUIV_NList_SortTypeAdd_4Values    = 0x40000000
MUIV_NList_SortTypeAdd_Mask       = 0xC0000000
MUIV_NList_SortTypeValue_Mask     = 0x3FFFFFFF

MUIV_NList_Sort3_SortType_Both    = 0x00000000
MUIV_NList_Sort3_SortType_1       = 0x00000001
MUIV_NList_Sort3_SortType_2       = 0x00000002

MUIV_NList_Quiet_None             = 0
MUIV_NList_Quiet_Full             = -1
MUIV_NList_Quiet_Visual           = -2

MUIV_NList_Imports_Active         = 1 << 0
MUIV_NList_Imports_Selected       = 1 << 1
MUIV_NList_Imports_First          = 1 << 2
MUIV_NList_Imports_ColWidth       = 1 << 3
MUIV_NList_Imports_ColOrder       = 1 << 4
MUIV_NList_Imports_TitleMark      = 1 << 7
MUIV_NList_Imports_Cols           = 0x000000F8
MUIV_NList_Imports_All            = 0x0000FFFF

MUIV_NList_Exports_Active         = 1 << 0
MUIV_NList_Exports_Selected       = 1 << 1
MUIV_NList_Exports_First          = 1 << 2
MUIV_NList_Exports_ColWidth       = 1 << 3
MUIV_NList_Exports_ColOrder       = 1 << 4
MUIV_NList_Exports_TitleMark      = 1 << 7
MUIV_NList_Exports_Cols           = 0x000000F8
MUIV_NList_Exports_All            = 0x0000FFFF

MUIV_NList_TitleMark_ColMask      = 0x000000FF
MUIV_NList_TitleMark_TypeMask     = 0xF0000000
MUIV_NList_TitleMark_None         = 0xF0000000
MUIV_NList_TitleMark_Down         = 0x00000000
MUIV_NList_TitleMark_Up           = 0x80000000
MUIV_NList_TitleMark_Box          = 0x40000000
MUIV_NList_TitleMark_Circle       = 0xC0000000

MUIV_NList_TitleMark2_ColMask     = 0x000000FF
MUIV_NList_TitleMark2_TypeMask    = 0xF0000000
MUIV_NList_TitleMark2_None        = 0xF0000000
MUIV_NList_TitleMark2_Down        = 0x00000000
MUIV_NList_TitleMark2_Up          = 0x80000000
MUIV_NList_TitleMark2_Box         = 0x40000000
MUIV_NList_TitleMark2_Circle      = 0xC0000000

MUIV_NList_SetColumnCol_Default   = -1

MUIV_NList_GetPos_Start           = -1
MUIV_NList_GetPos_End             = -1

MUIV_NList_SelectChange_Flag_Multi = 1 << 0

MUIV_NList_UseImage_All           = -1

### Structures & Flags ###

MUI_NLPR_ABOVE  = 1<<0
MUI_NLPR_BELOW  = 1<<1
MUI_NLPR_LEFT   = 1<<2
MUI_NLPR_RIGHT  = 1<<3
MUI_NLPR_BAR    = 1<<4  # if between two columns you'll get the left
                        # column number of both, and that flag
MUI_NLPR_TITLE  = 1<<5  # if clicked on title, only column, xoffset and yoffset (and MUI_NLPR_BAR)
                        # are valid (you'll get MUI_NLPR_ABOVE too)
MUI_NLPR_ONTOP  = 1<<6  # it is on title/half of first visible entry

NOWRAP          = 0x00
WRAPCOL0        = 0x01
WRAPCOL1        = 0x02
WRAPCOL2        = 0x04
WRAPCOL3        = 0x08
WRAPCOL4        = 0x10
WRAPCOL5        = 0x20
WRAPCOL6        = 0x40
WRAPPED         = 0x80

DISPLAY_ARRAY_MAX = 64

ALIGN_LEFT      = 0x0000
ALIGN_CENTER    = 0x0100
ALIGN_RIGHT     = 0x0200
ALIGN_JUSTIFY   = 0x0400

### Methods ###

MUIM_NList_Clear              = 0x9d510070 # GM
MUIM_NList_ColToColumn        = 0x9d51008f # GM
MUIM_NList_ColWidth           = 0x9d51008c # GM
MUIM_NList_ColumnToCol        = 0x9d510091 # GM
MUIM_NList_Compare            = 0x9d5100A3 # GM $$$Sensei
MUIM_NList_Construct          = 0x9d5100A1 # GM $$$Sensei
MUIM_NList_ContextMenuBuild   = 0x9d51008d # GM
MUIM_NList_CopyTo             = 0x9d510087 # GM
MUIM_NList_CopyToClip         = 0x9d51007f # GM
MUIM_NList_CreateImage        = 0x9d510071 # GM
MUIM_NList_DeleteImage        = 0x9d510072 # GM
MUIM_NList_Destruct           = 0x9d5100A2 # GM $$$Sensei
MUIM_NList_Display            = 0x9d5100A4 # GM $$$Sensei
MUIM_NList_DoMethod           = 0x9d51008b # GM
MUIM_NList_DropDraw           = 0x9d510089 # GM
MUIM_NList_DropEntryDrawErase = 0x9d51008e # GM
MUIM_NList_DropType           = 0x9d510088 # GM
MUIM_NList_Exchange           = 0x9d510073 # GM
MUIM_NList_GetEntry           = 0x9d510074 # GM
MUIM_NList_GetEntryInfo       = 0x9d510084 # GM
MUIM_NList_GetPos             = 0x9d510096 # GM
MUIM_NList_GetSelectInfo      = 0x9d510086 # GM
MUIM_NList_Insert             = 0x9d510075 # GM
MUIM_NList_InsertSingle       = 0x9d510076 # GM
MUIM_NList_InsertSingleWrap   = 0x9d510083 # GM
MUIM_NList_InsertWrap         = 0x9d510082 # GM
MUIM_NList_Jump               = 0x9d510077 # GM
MUIM_NList_Move               = 0x9d510078 # GM
MUIM_NList_NextSelected       = 0x9d510079 # GM
MUIM_NList_PrevSelected       = 0x9d510093 # GM
MUIM_NList_Redraw             = 0x9d51007a # GM
MUIM_NList_RedrawEntry        = 0x9d51008a # GM
MUIM_NList_Remove             = 0x9d51007b # GM
MUIM_NList_ReplaceSingle      = 0x9d510081 # GM
MUIM_NList_Select             = 0x9d51007c # GM
MUIM_NList_SelectChange       = 0x9d5100A0 # GM
MUIM_NList_SetColumnCol       = 0x9d510094 # GM
MUIM_NList_Sort               = 0x9d51007d # GM
MUIM_NList_Sort2              = 0x9d510092 # GM
MUIM_NList_Sort3              = 0x9d510095 # GM
MUIM_NList_TestPos            = 0x9d51007e # GM
MUIM_NList_UseImage           = 0x9d510080 # GM

### Class ###

class NList(pymui.Area):
    CLASSID = MUIC_NList

    Active        = MAttribute(MUIA_NList_Active,        'is.', pymui.c_LONG)
    ConstructHook = MAttribute(MUIA_NList_ConstructHook, 'is.', pymui.c_Hook)
    DestructHook  = MAttribute(MUIA_NList_DestructHook,  'is.', pymui.c_Hook)
    DoubleClick   = MAttribute(MUIA_NList_DoubleClick,   '..g', pymui.c_LONG)
    Entries       = MAttribute(MUIA_NList_Entries,       '..g', pymui.c_LONG)
    MinLineHeight = MAttribute(MUIA_NList_MinLineHeight, 'is.', pymui.c_LONG)
    Quiet         = MAttribute(MUIA_NList_Quiet,         '.s.', pymui.c_BOOL)

    Clear        = MMethod(MUIM_NList_Clear, retype=None)
    CreateImage  = MMethod(MUIM_NList_CreateImage,  [ ('obj', pymui.c_pMUIObject),
                                                      ('flags', pymui.c_ULONG) ], pymui.c_APTR)
    DeleteImage  = MMethod(MUIM_NList_DeleteImage,  [ ('obj', pymui.c_APTR) ], retype=None)
    GetEntry     = MMethod(MUIM_NList_GetEntry,     [ ('pos', pymui.c_LONG), ('entry', pymui.c_APTR.PointerType()) ])
    InsertSingle = MMethod(MUIM_NList_InsertSingle, [ ('entry', pymui.c_APTR), ('pos', pymui.c_LONG) ])
    UseImage     = MMethod(MUIM_NList_UseImage,     [ ('obj', pymui.c_pMUIObject),
                                                      ('imgnum', pymui.c_LONG),
                                                      ('flags', pymui.c_ULONG) ], retype=pymui.c_ULONG)

    def __init__(self, **kwds):
        if self._bclassid == MUIC_NList and not self._MCC_:
            kwds.setdefault('ConstructHook', MUIV_NList_ConstructHook_String)
            kwds.setdefault('DestructHook', MUIV_NList_DestructHook_String)
        super(NList, self).__init__(**kwds)

    @CreateImage.alias
    def CreateImage(self, meth, obj, flags=0):
        return meth(self, obj, flags)

    @InsertSingle.alias
    def InsertSingle(self, meth, entry, pos=MUIV_NList_Insert_Bottom):
        return meth(self, entry, pos)

    def InsertSingleString(self, s, pos=MUIV_NList_Insert_Bottom):
        x = pymui.c_STRPTR(s) # keep valid the s object until the return
        return self.InsertSingle(x, pos)

    def GetStringEntry(self, pos=MUIV_NList_GetEntry_Active):
        ptr = pymui.c_APTR()
        if self.GetEntry(pos, ptr) and ptr.value:
            return pymui.c_STRPTR.from_value(ptr.value).contents

    @UseImage.alias
    def UseImage(self, meth, obj, imgnum, flags=0):
        return meth(self, obj, imgnum, flags)
