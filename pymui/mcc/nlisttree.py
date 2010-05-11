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

from pymui.mcc.nlist import *

MUIC_NListtree = "NListtree.mcc"

#### Attributes ###

MUIA_NListtree_Active           = 0xfec81201  # *** [.SGN]
MUIA_NListtree_ActiveList       = 0xfec81202  # *** [..GN]
MUIA_NListtree_CloseHook        = 0xfec81203  # *** [IS..]
MUIA_NListtree_ConstructHook    = 0xfec81204  # *** [IS..]
MUIA_NListtree_DestructHook     = 0xfec81205  # *** [IS..]
MUIA_NListtree_DisplayHook      = 0xfec81206  # *** [IS..]
MUIA_NListtree_DoubleClick      = 0xfec81207  # *** [ISGN]
MUIA_NListtree_DragDropSort     = 0xfec81208  # *** [IS..]
MUIA_NListtree_DupNodeName      = 0xfec81209  # *** [IS..]
MUIA_NListtree_EmptyNodes       = 0xfec8120a  # *** [IS..]
MUIA_NListtree_Format           = 0xfec8120b  # *** [IS..]
MUIA_NListtree_OpenHook         = 0xfec8120c  # *** [IS..]
MUIA_NListtree_Quiet            = 0xfec8120d  # *** [.S..]
MUIA_NListtree_CompareHook      = 0xfec8120e  # *** [IS..]
MUIA_NListtree_Title            = 0xfec8120f  # *** [IS..]
MUIA_NListtree_TreeColumn       = 0xfec81210  # *** [ISG.]
MUIA_NListtree_AutoVisible      = 0xfec81211  # *** [ISG.]
MUIA_NListtree_FindNameHook     = 0xfec81212  # *** [IS..]
MUIA_NListtree_MultiSelect      = 0xfec81213  # *** [I...]
MUIA_NListtree_MultiTestHook    = 0xfec81214  # *** [IS..]
MUIA_NListtree_CopyToClipHook   = 0xfec81217  # *** [IS..]
MUIA_NListtree_DropType         = 0xfec81218  # *** [..G.]
MUIA_NListtree_DropTarget       = 0xfec81219  # *** [..G.]
MUIA_NListtree_DropTargetPos    = 0xfec8121a  # *** [..G.]
MUIA_NListtree_FindUserDataHook = 0xfec8121b  # *** [IS..]
MUIA_NListtree_ShowTree         = 0xfec8121c  # *** [ISG.]

### Special attribute values ###

MUIV_NListtree_Active_Off                          = 0
MUIV_NListtree_Active_Parent                       = -2
MUIV_NListtree_Active_First                        = -3
MUIV_NListtree_Active_FirstVisible                 = -4
MUIV_NListtree_Active_LastVisible                  = -5

MUIV_NListtree_ActiveList_Off                      = 0

MUIV_NListtree_AutoVisible_Off                     = 0
MUIV_NListtree_AutoVisible_Normal                  = 1
MUIV_NListtree_AutoVisible_FirstOpen               = 2
MUIV_NListtree_AutoVisible_Expand                  = 3

MUIV_NListtree_CompareHook_Head                    = 0
MUIV_NListtree_CompareHook_Tail                    = -1
MUIV_NListtree_CompareHook_LeavesTop               = -2
MUIV_NListtree_CompareHook_LeavesMixed             = -3
MUIV_NListtree_CompareHook_LeavesBottom            = -4

MUIV_NListtree_ConstructHook_String                = -1
MUIV_NListtree_ConstructHook_Flag_AutoCreate       = 1<<15

MUIV_NListtree_CopyToClipHook_Default              = 0

MUIV_NListtree_DestructHook_String                 = -1

MUIV_NListtree_DisplayHook_Default                 = -1

MUIV_NListtree_DoubleClick_Off                     = -1
MUIV_NListtree_DoubleClick_All                     = -2
MUIV_NListtree_DoubleClick_Tree                    = -3
MUIV_NListtree_DoubleClick_NoTrigger               = -4

MUIV_NListtree_DropType_None                       = 0
MUIV_NListtree_DropType_Above                      = 1
MUIV_NListtree_DropType_Below                      = 2
MUIV_NListtree_DropType_Onto                       = 3
MUIV_NListtree_DropType_Sorted                     = 4

MUIV_NListtree_FindNameHook_CaseSensitive          = 0
MUIV_NListtree_FindNameHook_CaseInsensitive        = -1
MUIV_NListtree_FindNameHook_PartCaseSensitive      = -2
MUIV_NListtree_FindNameHook_PartCaseInsensitive    = -3
MUIV_NListtree_FindNameHook_PointerCompare         = -4

MUIV_NListtree_FindUserDataHook_CaseSensitive      = 0
MUIV_NListtree_FindUserDataHook_CaseInsensitive    = -1
MUIV_NListtree_FindUserDataHook_Part               = -2
MUIV_NListtree_FindUserDataHook_PartCaseInsensitive= -3
MUIV_NListtree_FindUserDataHook_PointerCompare     = -4

MUIV_NListtree_MultiSelect_None                    = 0
MUIV_NListtree_MultiSelect_Default                 = 1
MUIV_NListtree_MultiSelect_Shifted                 = 2
MUIV_NListtree_MultiSelect_Always                  = 3

MUIV_NListtree_ShowTree_Toggle                     = -1

### Structures & Flags ###

class c_NListtree_TreeNode(pymui.PyMUICStructureType):
    _fields_ = [ ('tn_Node',  pymui.c_MinNode), # To make it a node
                 ('tn_Name',  pymui.c_STRPTR),  # Simple name field
                 ('tn_Flags', pymui.c_UWORD),   # Used for the flags below
                 ('tn_User',  pymui.c_APTR),    # Free for user data

                 # Privates fields follow, so this type shall not be used
                 # to defines fields in stuctures.
                 # For this purpose, use c_pNListtree_TreeNode
                 ]

c_pNListtree_TreeNode = c_NListtree_TreeNode.PointerType()

TNF_OPEN     = (1<<0)
TNF_LIST     = (1<<1)
TNF_FROZEN   = (1<<2)
TNF_NOSIGN   = (1<<3)
TNF_SELECTED = (1<<4)

class c_TestPosResult(pymui.PyMUICStructureType):
    _fields_ = [ ('tpr_TreeNode',  c_pNListtree_TreeNode),
                 ('tpr_Type',      pymui.c_UWORD),
                 ('tpr_ListEntry', pymui.c_LONG),
                 ('tpr_ListFlags', pymui.c_UWORD),
                 ('tpr_Column',    pymui.c_WORD),
                 ]
    
### Methods ###

MUIM_NListtree_Open         = 0xfec81101
MUIM_NListtree_Close        = 0xfec81102
MUIM_NListtree_Insert       = 0xfec81103
MUIM_NListtree_Remove       = 0xfec81104
MUIM_NListtree_Exchange     = 0xfec81105
MUIM_NListtree_Move         = 0xfec81106
MUIM_NListtree_Rename       = 0xfec81107
MUIM_NListtree_FindName     = 0xfec81108
MUIM_NListtree_GetEntry     = 0xfec81109
MUIM_NListtree_GetNr        = 0xfec8110a
MUIM_NListtree_Sort         = 0xfec8110b
MUIM_NListtree_TestPos      = 0xfec8110c
MUIM_NListtree_Redraw       = 0xfec8110d
MUIM_NListtree_NextSelected = 0xfec81110
MUIM_NListtree_MultiTest    = 0xfec81111
MUIM_NListtree_Select       = 0xfec81112
MUIM_NListtree_Copy         = 0xfec81113
MUIM_NListtree_InsertStruct = 0xfec81114  # *** Insert a struct (like a path) into the list.
MUIM_NListtree_Active       = 0xfec81115  # *** Method which gives the active node/number.
MUIM_NListtree_DoubleClick  = 0xfec81116  # *** Occurs on every double click.
MUIM_NListtree_PrevSelected = 0xfec81118  # *** Like reverse NextSelected.
MUIM_NListtree_CopyToClip   = 0xfec81119  # *** Copy an entry or part to the clipboard.
MUIM_NListtree_FindUserData = 0xfec8111a  # *** Find a node upon user data.
MUIM_NListtree_Clear        = 0xfec8111b  # *** Clear complete tree.
MUIM_NListtree_DropType     = 0xfec8111e  # ***
MUIM_NListtree_DropDraw     = 0xfec8111f  # ***

### Special method values ###

MUIV_NListtree_Close_ListNode_Root                 = 0
MUIV_NListtree_Close_ListNode_Parent               = -1
MUIV_NListtree_Close_ListNode_Active               = -2

MUIV_NListtree_Close_TreeNode_Head                 = 0
MUIV_NListtree_Close_TreeNode_Tail                 = -1
MUIV_NListtree_Close_TreeNode_Active               = -2
MUIV_NListtree_Close_TreeNode_All                  = -3



MUIV_NListtree_Exchange_ListNode1_Root             = 0
MUIV_NListtree_Exchange_ListNode1_Active           = -2

MUIV_NListtree_Exchange_TreeNode1_Head             = 0
MUIV_NListtree_Exchange_TreeNode1_Tail             = -1
MUIV_NListtree_Exchange_TreeNode1_Active           = -2

MUIV_NListtree_Exchange_ListNode2_Root             = 0
MUIV_NListtree_Exchange_ListNode2_Active           = -2

MUIV_NListtree_Exchange_TreeNode2_Head             = 0
MUIV_NListtree_Exchange_TreeNode2_Tail             = -1
MUIV_NListtree_Exchange_TreeNode2_Active           = -2
MUIV_NListtree_Exchange_TreeNode2_Up               = -5
MUIV_NListtree_Exchange_TreeNode2_Down             = -6


MUIV_NListtree_FindName_ListNode_Root              = 0
MUIV_NListtree_FindName_ListNode_Active            = -2

MUIV_NListtree_FindName_Flag_SameLevel             = 1<<15
MUIV_NListtree_FindName_Flag_Visible               = 1<<14
MUIV_NListtree_FindName_Flag_Activate              = 1<<13
MUIV_NListtree_FindName_Flag_Selected              = 1<<11
MUIV_NListtree_FindName_Flag_StartNode             = 1<<10
MUIV_NListtree_FindName_Flag_Reverse               = 1<<9


MUIV_NListtree_FindUserData_ListNode_Root          = 0
MUIV_NListtree_FindUserData_ListNode_Active        = -2

MUIV_NListtree_FindUserData_Flag_SameLevel         = 1<<15
MUIV_NListtree_FindUserData_Flag_Visible           = 1<<14
MUIV_NListtree_FindUserData_Flag_Activate          = 1<<13
MUIV_NListtree_FindUserData_Flag_Selected          = 1<<11
MUIV_NListtree_FindUserData_Flag_StartNode         = 1<<10
MUIV_NListtree_FindUserData_Flag_Reverse           = 1<<9


MUIV_NListtree_GetEntry_ListNode_Root              = 0
MUIV_NListtree_GetEntry_ListNode_Active            = -2
MUIV_NListtree_GetEntry_TreeNode_Active            = -3

MUIV_NListtree_GetEntry_Position_Head              = 0
MUIV_NListtree_GetEntry_Position_Tail              = -1
MUIV_NListtree_GetEntry_Position_Active            = -2
MUIV_NListtree_GetEntry_Position_Next              = -3
MUIV_NListtree_GetEntry_Position_Previous          = -4
MUIV_NListtree_GetEntry_Position_Parent            = -5

MUIV_NListtree_GetEntry_Flag_SameLevel             = 1<<15
MUIV_NListtree_GetEntry_Flag_Visible               = 1<<14


MUIV_NListtree_GetNr_TreeNode_Root                 = 0
MUIV_NListtree_GetNr_TreeNode_Active               = -2

MUIV_NListtree_GetNr_Flag_CountAll                 = 1<<15
MUIV_NListtree_GetNr_Flag_CountLevel               = 1<<14
MUIV_NListtree_GetNr_Flag_CountList                = 1<<13
MUIV_NListtree_GetNr_Flag_ListEmpty                = 1<<12
MUIV_NListtree_GetNr_Flag_Visible                  = 1<<11


MUIV_NListtree_Insert_ListNode_Root                = 0
MUIV_NListtree_Insert_ListNode_Active              = -2
MUIV_NListtree_Insert_ListNode_LastInserted        = -3
MUIV_NListtree_Insert_ListNode_ActiveFallback      = -4

MUIV_NListtree_Insert_PrevNode_Head                = 0
MUIV_NListtree_Insert_PrevNode_Tail                = -1
MUIV_NListtree_Insert_PrevNode_Active              = -2
MUIV_NListtree_Insert_PrevNode_Sorted              = -4

MUIV_NListtree_Insert_Flag_Active                  = 1<<13
MUIV_NListtree_Insert_Flag_NextNode                = 1<<12


MUIV_NListtree_Move_OldListNode_Root               = 0
MUIV_NListtree_Move_OldListNode_Active             = -2

MUIV_NListtree_Move_OldTreeNode_Head               = 0
MUIV_NListtree_Move_OldTreeNode_Tail               = -1
MUIV_NListtree_Move_OldTreeNode_Active             = -2

MUIV_NListtree_Move_NewListNode_Root               = 0
MUIV_NListtree_Move_NewListNode_Active             = -2

MUIV_NListtree_Move_NewTreeNode_Head               = 0
MUIV_NListtree_Move_NewTreeNode_Tail               = -1
MUIV_NListtree_Move_NewTreeNode_Active             = -2
MUIV_NListtree_Move_NewTreeNode_Sorted             = -4

MUIV_NListtree_Move_Flag_KeepStructure             = 1<<13


MUIV_NListtree_Open_ListNode_Root                  = 0
MUIV_NListtree_Open_ListNode_Parent                = -1
MUIV_NListtree_Open_ListNode_Active                = -2
MUIV_NListtree_Open_TreeNode_Head                  = 0
MUIV_NListtree_Open_TreeNode_Tail                  = -1
MUIV_NListtree_Open_TreeNode_Active                = -2
MUIV_NListtree_Open_TreeNode_All                   = -3



MUIV_NListtree_Remove_ListNode_Root                = 0
MUIV_NListtree_Remove_ListNode_Active              = -2
MUIV_NListtree_Remove_TreeNode_Head                = 0
MUIV_NListtree_Remove_TreeNode_Tail                = -1
MUIV_NListtree_Remove_TreeNode_Active              = -2
MUIV_NListtree_Remove_TreeNode_All                 = -3
MUIV_NListtree_Remove_TreeNode_Selected            = -4

MUIV_NListtree_Remove_Flag_NoActive                = 1<<13




MUIV_NListtree_Rename_TreeNode_Active              = -2

MUIV_NListtree_Rename_Flag_User                    = 1<<8
MUIV_NListtree_Rename_Flag_NoRefresh               = 1<<9


MUIV_NListtree_Sort_ListNode_Root                  = 0
MUIV_NListtree_Sort_ListNode_Active                = -2
MUIV_NListtree_Sort_TreeNode_Active                = -3

MUIV_NListtree_Sort_Flag_RecursiveOpen             = 1<<13
MUIV_NListtree_Sort_Flag_RecursiveAll              = 1<<12


MUIV_NListtree_TestPos_Result_None                 = 0
MUIV_NListtree_TestPos_Result_Above                = 1
MUIV_NListtree_TestPos_Result_Below                = 2
MUIV_NListtree_TestPos_Result_Onto                 = 3
MUIV_NListtree_TestPos_Result_Sorted               = 4

MUIV_NListtree_Redraw_Active                       = -1
MUIV_NListtree_Redraw_All                          = -2

MUIV_NListtree_Redraw_Flag_Nr                      = 1<<15

MUIV_NListtree_Select_Active                       = -1
MUIV_NListtree_Select_All                          = -2
MUIV_NListtree_Select_Visible                      = -3

MUIV_NListtree_Select_Off                          = 0
MUIV_NListtree_Select_On                           = 1
MUIV_NListtree_Select_Toggle                       = 2
MUIV_NListtree_Select_Ask                          = 3

MUIV_NListtree_Select_Flag_Force                   = 1<<15


MUIV_NListtree_NextSelected_Start                  = -1
MUIV_NListtree_NextSelected_End                    = -1


MUIV_NListtree_Copy_SourceListNode_Root            = 0
MUIV_NListtree_Copy_SourceListNode_Active          = -2

MUIV_NListtree_Copy_SourceTreeNode_Head            = 0
MUIV_NListtree_Copy_SourceTreeNode_Tail            = -1
MUIV_NListtree_Copy_SourceTreeNode_Active          = -2

MUIV_NListtree_Copy_DestListNode_Root              = 0
MUIV_NListtree_Copy_DestListNode_Active            = -2

MUIV_NListtree_Copy_DestTreeNode_Head              = 0
MUIV_NListtree_Copy_DestTreeNode_Tail              = -1
MUIV_NListtree_Copy_DestTreeNode_Active            = -2
MUIV_NListtree_Copy_DestTreeNode_Sorted            = -4

MUIV_NListtree_Copy_Flag_KeepStructure             = 1<<13


MUIV_NListtree_PrevSelected_Start                  = -1
MUIV_NListtree_PrevSelected_End                    = -1

MUIV_NListtree_CopyToClip_Active                   = -1

### Hook message structs ###

class c_NListtree_CloseMessage(pymui.PyMUICStructureType):
    _fields_ = [ ('HookID',   pymui.c_ULONG),
                 ('TreeNode', c_pNListtree_TreeNode) ]

class c_NListtree_CloseHook(pymui.c_Hook): _argtypes_ = (None, c_NListtree_CloseMessage)

_c_NListtree_TreeNode_NULL = c_NListtree_TreeNode.FromLong(0)

### Class ###

class NListtree(NList):
    CLASSID = MUIC_NListtree
    
    Active           = MAttribute(MUIA_NListtree_Active,            '.sg', c_pNListtree_TreeNode)
    ActiveList       = MAttribute(MUIA_NListtree_ActiveList,        '..g', c_pNListtree_TreeNode)
    AutoVisible      = MAttribute(MUIA_NListtree_AutoVisible,       'isg', c_pNListtree_TreeNode)
    CloseHook        = MAttribute(MUIA_NListtree_CloseHook,         'is.', c_NListtree_CloseHook, keep=True)
    CompareHook      = MAttribute(MUIA_NListtree_CompareHook,       'is.', pymui.c_Hook, keep=True)
    ConstructHook    = MAttribute(MUIA_NListtree_ConstructHook,     'is.', pymui.c_Hook, keep=True)
    CopyToClipHook   = MAttribute(MUIA_NListtree_CopyToClipHook,    'is.', pymui.c_Hook, keep=True)
    DestructHook     = MAttribute(MUIA_NListtree_DestructHook,      'is.', pymui.c_Hook, keep=True)
    DisplayHook      = MAttribute(MUIA_NListtree_DisplayHook,       'is.', pymui.c_Hook, keep=True)
    DoubleClick      = MAttribute(MUIA_NListtree_DoubleClick,       'isg', pymui.c_ULONG)
    DragDropSort     = MAttribute(MUIA_NListtree_DragDropSort,      'is.', pymui.c_BOOL)
    DropTarget       = MAttribute(MUIA_NListtree_DropTarget,        '..g', pymui.c_ULONG)
    DropTargetPos    = MAttribute(MUIA_NListtree_DropTargetPos,     '..g', pymui.c_ULONG)
    DropType         = MAttribute(MUIA_NListtree_DropType,          '..g', pymui.c_ULONG)
    DupNodeName      = MAttribute(MUIA_NListtree_DupNodeName,       'is.', pymui.c_BOOL)
    EmptyNodes       = MAttribute(MUIA_NListtree_EmptyNodes,        'is.', pymui.c_BOOL)
    FindNameHook     = MAttribute(MUIA_NListtree_FindNameHook,      'is.', pymui.c_Hook, keep=True)
    FindUserDataHook = MAttribute(MUIA_NListtree_FindUserDataHook,  'is.', pymui.c_Hook, keep=True)
    Format           = MAttribute(MUIA_NListtree_Format,            'is.', pymui.c_STRPTR)
    MultiSelect      = MAttribute(MUIA_NListtree_MultiSelect,       'i..', pymui.c_ULONG)
    MultiTestHook    = MAttribute(MUIA_NListtree_MultiTestHook,     'is.', pymui.c_Hook, keep=True)
    OpenHook         = MAttribute(MUIA_NListtree_OpenHook,          'is.', pymui.c_Hook, keep=True)
    Quiet            = MAttribute(MUIA_NListtree_Quiet,             '.s.', pymui.c_BOOL)
    ShowTree         = MAttribute(MUIA_NListtree_ShowTree,          'isg', pymui.c_ULONG)
    Title            = MAttribute(MUIA_NListtree_Title,             'is.', pymui.c_BOOL)
    TreeColumn       = MAttribute(MUIA_NListtree_TreeColumn,        'isg', pymui.c_ULONG)

    Clear    = MMethod(MUIM_NListtree_Clear,  [ ('ListNode', c_pNListtree_TreeNode),
                                                ('Flags',    pymui.c_ULONG) ], retype=None)
    Close    = MMethod(MUIM_NListtree_Close, [ ('ListNode', c_pNListtree_TreeNode),
                                               ('TreeNode', c_pNListtree_TreeNode),
                                               ('Flags',    pymui.c_ULONG) ], retype=None)
    GetEntry = MMethod(MUIM_NListtree_GetEntry, [ ('Node',     c_pNListtree_TreeNode),
                                                  ('Position', pymui.c_LONG),
                                                  ('Flags',    pymui.c_ULONG),
                                                ], c_NListtree_TreeNode)
    Insert   = MMethod(MUIM_NListtree_Insert, [ ('Name',     pymui.c_STRPTR),
                                                ('User',     pymui.c_APTR),
                                                ('ListNode', c_pNListtree_TreeNode),
                                                ('PrevNode', c_pNListtree_TreeNode),
                                                ('Flags',    pymui.c_ULONG) ], c_NListtree_TreeNode)
    Open     = MMethod(MUIM_NListtree_Open, [ ('ListNode', c_pNListtree_TreeNode),
                                              ('TreeNode', c_pNListtree_TreeNode),
                                              ('Flags',    pymui.c_ULONG) ], retype=None)
    Remove   = MMethod(MUIM_NListtree_Remove, [ ('ListNode', c_pNListtree_TreeNode),
                                                ('TreeNode', c_pNListtree_TreeNode),
                                                ('Flags',    pymui.c_ULONG) ])

    @Clear.alias
    def Clear(self, meth):
        meth(self, _c_NListtree_TreeNode_NULL, 0)
        self._ClearAllPyData()

    @GetEntry.alias
    def GetEntry(self, meth,
                 node=MUIV_NListtree_GetEntry_ListNode_Active,
                 position=MUIV_NListtree_GetEntry_Position_Active,
                 flags=0):
        node = (node if isinstance(node, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(node))
        item = meth(self, node, position, flags)
        return (item if long(item) else None)

    @Insert.alias
    def Insert(self, meth, name,
               lnode=MUIV_NListtree_Insert_ListNode_Root,
               pnode=MUIV_NListtree_Insert_PrevNode_Tail,
               flags=0, user=0):
        lnode = (lnode if isinstance(lnode, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(lnode))
        pnode = (pnode if isinstance(pnode, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(pnode))
        item = meth(self, name, user, lnode, pnode, flags)
        return (item if long(item) else None)

    @Open.alias
    def Open(self, meth,
             lnode=MUIV_NListtree_Open_ListNode_Active,
             tnode=MUIV_NListtree_Open_TreeNode_All,
             flags=0):
        lnode = (lnode if isinstance(lnode, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(lnode))
        tnode = (tnode if isinstance(tnode, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(tnode))
        meth(self, lnode, tnode, flags)

    @Close.alias
    def Close(self, meth,
             lnode=MUIV_NListtree_Close_ListNode_Active,
             tnode=MUIV_NListtree_Close_TreeNode_All,
             flags=0):
        lnode = (lnode if isinstance(lnode, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(lnode))
        tnode = (tnode if isinstance(tnode, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(tnode))
        meth(self, lnode, tnode, flags)

    @Remove.alias
    def Remove(self, meth,
               lnode=MUIV_NListtree_Remove_ListNode_Active,
               tnode=MUIV_NListtree_Remove_TreeNode_All,
               flags=0):
        lnode = (lnode if isinstance(lnode, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(lnode))
        tnode = (tnode if isinstance(tnode, c_NListtree_TreeNode) else c_NListtree_TreeNode.FromLong(tnode))
        meth(self, lnode, tnode, flags)

    def __init__(self, *a, **k):
        super(NListtree, self).__init__(*a, **k)
        self.__data = {} # see (Set|Get)PyData methods

    def GetFirstChild(self, item=MUIV_NListtree_GetEntry_ListNode_Root):
        return self.GetEntry(item, MUIV_NListtree_GetEntry_Position_Head)
    
    def GetLastChild(self, item=MUIV_NListtree_GetEntry_ListNode_Root):
        return self.GetEntry(item, MUIV_NListtree_GetEntry_Position_Tail)
    
    def ItemHasChildren(self, item=MUIV_NListtree_GetEntry_ListNode_Root):
        return bool(self.GetFirstChild(item))

    def GetItemParent(self, item=MUIV_NListtree_GetEntry_ListNode_Root):
        return self.GetEntry(item, MUIV_NListtree_GetEntry_Position_Parent)

    def GetRootItem(self):
        # -15 is a private value taken from NListree sources.
        return self.GetEntry(MUIV_NListtree_GetEntry_ListNode_Root, -15)

    def GetItemText(self, item):
        return item.tn_Name.value
