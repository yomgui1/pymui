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

import pymui

MAttribute = pymui.MAttribute
MMethod = pymui.MMethod

MUIC_Listtree = "Listtree.mcc"

### Methods ###

MUIM_Listtree_Close       = 0x8002001f
MUIM_Listtree_Exchange    = 0x80020008
MUIM_Listtree_FindName    = 0x8002003c
MUIM_Listtree_GetEntry    = 0x8002002b
MUIM_Listtree_GetNr       = 0x8002000e
MUIM_Listtree_Insert      = 0x80020011
MUIM_Listtree_Move        = 0x80020009
MUIM_Listtree_Open        = 0x8002001e
MUIM_Listtree_Remove      = 0x80020012
MUIM_Listtree_Rename      = 0x8002000c
MUIM_Listtree_SetDropMark = 0x8002004c
MUIM_Listtree_Sort        = 0x80020029
MUIM_Listtree_TestPos     = 0x8002004b

#### Attributes ###

MUIA_Listtree_Active            = 0x80020020
MUIA_Listtree_CloseHook         = 0x80020033
MUIA_Listtree_ConstructHook     = 0x80020016
MUIA_Listtree_DestructHook      = 0x80020017
MUIA_Listtree_DisplayHook       = 0x80020018
MUIA_Listtree_DoubleClick       = 0x8002000d
MUIA_Listtree_DragDropSort      = 0x80020031
MUIA_Listtree_DuplicateNodeName = 0x8002003d
MUIA_Listtree_EmptyNodes        = 0x80020030
MUIA_Listtree_Format            = 0x80020014
MUIA_Listtree_MultiSelect       = 0x800200c3
MUIA_Listtree_NList             = 0x800200c4
MUIA_Listtree_OpenHook          = 0x80020032
MUIA_Listtree_Quiet             = 0x8002000a
MUIA_Listtree_SortHook          = 0x80020010
MUIA_Listtree_Title             = 0x80020015
MUIA_Listtree_TreeColumn        = 0x80020013

### Special methods values ###

MUIV_Listtree_Close_ListNode_Root   = 0
MUIV_Listtree_Close_ListNode_Parent = -1
MUIV_Listtree_Close_ListNode_Active = -2

MUIV_Listtree_Close_TreeNode_Head   = 0
MUIV_Listtree_Close_TreeNode_Tail   = -1
MUIV_Listtree_Close_TreeNode_Active = -2
MUIV_Listtree_Close_TreeNode_All    = -3

MUIV_Listtree_Exchange_ListNode1_Root   = 0
MUIV_Listtree_Exchange_ListNode1_Active = -2

MUIV_Listtree_Exchange_TreeNode1_Head   = 0
MUIV_Listtree_Exchange_TreeNode1_Tail   = -1
MUIV_Listtree_Exchange_TreeNode1_Active = -2

MUIV_Listtree_Exchange_ListNode2_Root   = 0
MUIV_Listtree_Exchange_ListNode2_Active = -2

MUIV_Listtree_Exchange_TreeNode2_Head   = 0
MUIV_Listtree_Exchange_TreeNode2_Tail   = -1
MUIV_Listtree_Exchange_TreeNode2_Active = -2
MUIV_Listtree_Exchange_TreeNode2_Up     = -5
MUIV_Listtree_Exchange_TreeNode2_Down   = -6

MUIV_Listtree_FindName_ListNode_Root   = 0
MUIV_Listtree_FindName_ListNode_Active = -2

MUIV_Listtree_GetEntry_ListNode_Root   = 0
MUIV_Listtree_GetEntry_ListNode_Active = -2

MUIV_Listtree_GetEntry_Position_Head     = 0
MUIV_Listtree_GetEntry_Position_Tail     = -1
MUIV_Listtree_GetEntry_Position_Active   = -2
MUIV_Listtree_GetEntry_Position_Next     = -3
MUIV_Listtree_GetEntry_Position_Previous = -4
MUIV_Listtree_GetEntry_Position_Parent   = -5

MUIV_Listtree_GetNr_TreeNode_Active = -2

MUIV_Listtree_Insert_ListNode_Root   = 0
MUIV_Listtree_Insert_ListNode_Active = -2

MUIV_Listtree_Insert_PrevNode_Head   = 0
MUIV_Listtree_Insert_PrevNode_Tail   = -1
MUIV_Listtree_Insert_PrevNode_Active = -2
MUIV_Listtree_Insert_PrevNode_Sorted = -4

MUIV_Listtree_Move_OldListNode_Root   = 0
MUIV_Listtree_Move_OldListNode_Active = -2

MUIV_Listtree_Move_OldTreeNode_Head   = 0
MUIV_Listtree_Move_OldTreeNode_Tail   = -1
MUIV_Listtree_Move_OldTreeNode_Active = -2

MUIV_Listtree_Move_NewListNode_Root   = 0
MUIV_Listtree_Move_NewListNode_Active = -2

MUIV_Listtree_Move_NewTreeNode_Head   = 0
MUIV_Listtree_Move_NewTreeNode_Tail   = -1
MUIV_Listtree_Move_NewTreeNode_Active = -2
MUIV_Listtree_Move_NewTreeNode_Sorted = -4

MUIV_Listtree_Open_ListNode_Root   = 0
MUIV_Listtree_Open_ListNode_Parent = -1
MUIV_Listtree_Open_ListNode_Active = -2
MUIV_Listtree_Open_TreeNode_Head   = 0
MUIV_Listtree_Open_TreeNode_Tail   = -1
MUIV_Listtree_Open_TreeNode_Active = -2
MUIV_Listtree_Open_TreeNode_All    = -3

MUIV_Listtree_Remove_ListNode_Root   = 0
MUIV_Listtree_Remove_ListNode_Active = -2
MUIV_Listtree_Remove_TreeNode_Head   = 0
MUIV_Listtree_Remove_TreeNode_Tail   = -1
MUIV_Listtree_Remove_TreeNode_Active = -2
MUIV_Listtree_Remove_TreeNode_All    = -3

MUIV_Listtree_Rename_TreeNode_Active = -2

MUIV_Listtree_SetDropMark_Entry_None = -1

MUIV_Listtree_SetDropMark_Values_None   = 0
MUIV_Listtree_SetDropMark_Values_Above  = 1
MUIV_Listtree_SetDropMark_Values_Below  = 2
MUIV_Listtree_SetDropMark_Values_Onto   = 3
MUIV_Listtree_SetDropMark_Values_Sorted = 4

MUIV_Listtree_Sort_ListNode_Root   = 0
MUIV_Listtree_Sort_ListNode_Active = -2

MUIV_Listtree_TestPos_Result_Flags_None   = 0
MUIV_Listtree_TestPos_Result_Flags_Above  = 1
MUIV_Listtree_TestPos_Result_Flags_Below  = 2
MUIV_Listtree_TestPos_Result_Flags_Onto   = 3
MUIV_Listtree_TestPos_Result_Flags_Sorted = 4

### Special method flags ###

MUIV_Listtree_Close_Flags_Nr      = (1<<15)
MUIV_Listtree_Close_Flags_Visible = (1<<14)

MUIV_Listtree_FindName_Flags_SameLevel = (1<<15)
MUIV_Listtree_FindName_Flags_Visible   = (1<<14)

MUIV_Listtree_GetEntry_Flags_SameLevel = (1<<15)
MUIV_Listtree_GetEntry_Flags_Visible   = (1<<14)

MUIV_Listtree_GetNr_Flags_ListEmpty  = (1<<12)
MUIV_Listtree_GetNr_Flags_CountList  = (1<<13)
MUIV_Listtree_GetNr_Flags_CountLevel = (1<<14)
MUIV_Listtree_GetNr_Flags_CountAll   = (1<<15)

MUIV_Listtree_Insert_Flags_Nr       = (1<<15)
MUIV_Listtree_Insert_Flags_Visible  = (1<<14)
MUIV_Listtree_Insert_Flags_Active   = (1<<13)
MUIV_Listtree_Insert_Flags_NextNode = (1<<12)

MUIV_Listtree_Move_Flags_Nr      = (1<<15)
MUIV_Listtree_Move_Flags_Visible = (1<<14)

MUIV_Listtree_Open_Flags_Nr      = (1<<15)
MUIV_Listtree_Open_Flags_Visible = (1<<14)

MUIV_Listtree_Remove_Flags_Nr      = (1<<15)
MUIV_Listtree_Remove_Flags_Visible = (1<<14)

MUIV_Listtree_Rename_Flags_User      = (1<<8)
MUIV_Listtree_Rename_Flags_NoRefresh = (1<<9)

MUIV_Listtree_Sort_Flags_Nr      = (1<<15)
MUIV_Listtree_Sort_Flags_Visible = (1<<14)

### Special attributes values ###

MUIV_Listtree_Active_Off = 0

MUIV_Listtree_ConstructHook_String = -1

MUIV_Listtree_DestructHook_String  = -1

MUIV_Listtree_DisplayHook_Default = -1

MUIV_Listtree_DoubleClick_Off  = -1
MUIV_Listtree_DoubleClick_All  = -2
MUIV_Listtree_DoubleClick_Tree = -3

MUIV_Listtree_SortHook_Head         = 0
MUIV_Listtree_SortHook_Tail         = -1
MUIV_Listtree_SortHook_LeavesTop    = -2
MUIV_Listtree_SortHook_LeavesMixed  = -3
MUIV_Listtree_SortHook_LeavesBottom = -4

### Structures, Flags & Values ###

class c_Listtree_TreeNode(pymui.PyMUICStructureType):
    _pack_   = 2
    _fields_ = [ ('tn_Private1', pymui.c_LONG),
                 ('tn_Private2', pymui.c_LONG),
                 ('tn_Name',  pymui.c_STRPTR),
                 ('tn_Flags', pymui.c_UWORD),
                 ('tn_User',  pymui.c_APTR) ]

    def SetUserData(self, v):
        self.tn_User = int(v)

    def GetUserData(self):
        return self.tn_User.value

c_pListtree_TreeNode = c_Listtree_TreeNode.PointerType()

class c_Listtree_TestPosResult(pymui.PyMUICStructureType):
    _pack_   = 2
    _fields_ = [ ('tpr_TreeNode',  c_pListtree_TreeNode),
                 ('tpr_Flags',     pymui.c_UWORD),
                 ('tpr_ListEntry', pymui.c_LONG),
                 ('tpr_ListFlags', pymui.c_UWORD) ]

TNF_OPEN     = (1<<0)
TNF_LIST     = (1<<1)
TNF_FROZEN   = (1<<2)
TNF_NOSIGN   = (1<<3)

### Hooks ###

class c_ListTree_CloseHook(pymui.c_Hook): _argtypes_ = (None, c_pListtree_TreeNode)
class c_ListTree_ConstructHook(pymui.c_Hook): _argtypes_ = (None, pymui.c_APTR)
class c_ListTree_DestructHook(pymui.c_Hook): _argtypes_ = (None, pymui.c_APTR)
class c_ListTree_DisplayHook(pymui.c_Hook): _argtypes_ = (pymui.c_pSTRPTR, c_pListtree_TreeNode)
class c_ListTree_OpenHook(pymui.c_Hook): _argtypes_ = (None, c_pListtree_TreeNode)
class c_ListTree_SortHook(pymui.c_Hook): _argtypes_ = (c_pListtree_TreeNode, c_pListtree_TreeNode)

### Class ###

class Listtree(pymui.List):
    CLASSID = MUIC_Listtree
    
    Active            = MAttribute(MUIA_Listtree_Active,            '.sg', c_pListtree_TreeNode)
    CloseHook         = MAttribute(MUIA_Listtree_CloseHook,         'is.', c_ListTree_CloseHook.PointerType(), keep=True)
    ConstructHook     = MAttribute(MUIA_Listtree_ConstructHook,     'is.', c_ListTree_ConstructHook.PointerType(), keep=True)
    DestructHook      = MAttribute(MUIA_Listtree_DestructHook,      'is.', c_ListTree_DestructHook.PointerType(), keep=True)
    DisplayHook       = MAttribute(MUIA_Listtree_DisplayHook,       'is.', c_ListTree_DisplayHook.PointerType(), keep=True)
    DoubleClick       = MAttribute(MUIA_Listtree_DoubleClick,       'isg', pymui.c_ULONG)
    DragDropSort      = MAttribute(MUIA_Listtree_DragDropSort,      'is.', pymui.c_BOOL)
    DuplicateNodeName = MAttribute(MUIA_Listtree_DuplicateNodeName, 'is.', pymui.c_BOOL)
    EmptyNodes        = MAttribute(MUIA_Listtree_EmptyNodes,        'is.', pymui.c_BOOL)
    Format            = MAttribute(MUIA_Listtree_Format,            'is.', pymui.c_STRPTR)
    MultiSelect       = MAttribute(MUIA_Listtree_MultiSelect,       'i..', pymui.c_ULONG)
    NList             = MAttribute(MUIA_Listtree_NList,             'i..', pymui.c_pMUIObject)
    OpenHook          = MAttribute(MUIA_Listtree_OpenHook,          'is.', c_ListTree_OpenHook.PointerType(), keep=True)
    Quiet             = MAttribute(MUIA_Listtree_Quiet,             '.s.', pymui.c_BOOL)
    SortHook          = MAttribute(MUIA_Listtree_SortHook,          'is.', c_ListTree_SortHook.PointerType(), keep=True)
    Title             = MAttribute(MUIA_Listtree_Title,             'is.', pymui.c_BOOL)
    TreeColumn        = MAttribute(MUIA_Listtree_TreeColumn,        'is.', pymui.c_ULONG)

    Close    = MMethod(MUIM_Listtree_Close, [ ('ListNode', c_pListtree_TreeNode),
                                              ('TreeNode', c_pListtree_TreeNode),
                                              ('Flags',    pymui.c_ULONG) ], None)
    Exchange = MMethod(MUIM_Listtree_Exchange, [ ('ListLode1', c_pListtree_TreeNode),
                                                 ('TreeLode1', c_pListtree_TreeNode),
                                                 ('ListLode2', c_pListtree_TreeNode),
                                                 ('TreeLode2', c_pListtree_TreeNode),
                                                 ('Flags',    pymui.c_ULONG) ], None)
    FindName = MMethod(MUIM_Listtree_FindName, [ ('ListNode', c_pListtree_TreeNode),
                                                 ('Name', pymui.c_STRPTR),
                                                 ('listnode2', c_pListtree_TreeNode),
                                                 ('treenode2', c_pListtree_TreeNode),
                                                 ('Flags',    pymui.c_ULONG) ], c_Listtree_TreeNode)
    GetEntry = MMethod(MUIM_Listtree_GetEntry, [ ('Node',     c_pListtree_TreeNode),
                                                 ('Position', pymui.c_LONG),
                                                 ('Flags',    pymui.c_ULONG) ], c_Listtree_TreeNode)
    GetNr    = MMethod(MUIM_Listtree_GetNr, [ ('TreeNode', c_pListtree_TreeNode),
                                              ('Flags',    pymui.c_ULONG) ])
    Insert   = MMethod(MUIM_Listtree_Insert, [ ('Name',     pymui.c_STRPTR),
                                               ('User',     pymui.c_APTR),
                                               ('ListNode', c_pListtree_TreeNode),
                                               ('PrevNode', c_pListtree_TreeNode),
                                               ('Flags',    pymui.c_ULONG) ], c_Listtree_TreeNode)
    Move     = MMethod(MUIM_Listtree_Move, [ ('OldListNode', c_pListtree_TreeNode),
                                             ('OldTreeNode', c_pListtree_TreeNode),
                                             ('NewListNode', c_pListtree_TreeNode),
                                             ('NewTreeNode', c_pListtree_TreeNode),
                                             ('Flags',    pymui.c_ULONG) ], None)
    Open     = MMethod(MUIM_Listtree_Open, [ ('ListNode', c_pListtree_TreeNode),
                                             ('TreeNode', c_pListtree_TreeNode),
                                             ('Flags',    pymui.c_ULONG) ], None)
    Remove   = MMethod(MUIM_Listtree_Remove, [ ('ListNode', c_pListtree_TreeNode),
                                               ('TreeNode', c_pListtree_TreeNode),
                                               ('Flags',    pymui.c_ULONG) ], None)
    Rename   = MMethod(MUIM_Listtree_Rename, [ ('TreeNode', c_pListtree_TreeNode),
                                               ('NewName',  pymui.c_STRPTR),
                                               ('Flags',    pymui.c_ULONG) ], c_Listtree_TreeNode)
    SetDropMark = MMethod(MUIM_Listtree_SetDropMark, [ ('Entry',  pymui.c_LONG),
                                                       ('Values', pymui.c_ULONG) ], None)
    Sort     = MMethod(MUIM_Listtree_Sort, [ ('ListNode', c_pListtree_TreeNode),
                                             ('Flags',    pymui.c_ULONG) ], None)
    TestPos  = MMethod(MUIM_Listtree_TestPos, [ ('X', pymui.c_LONG),
                                                ('Y', pymui.c_LONG),
                                                ('Result', pymui.c_APTR) ], None)

    def __init__(self, **kwds):
        #ovl = getattr(self, '_pymui_overloaded_', {})
        #if pymui.MUIM_List_Construct not in ovl and pymui.MUIM_List_Destruct not in ovl:
        #    kwds.setdefault('ConstructHook', MUIV_Listtree_ConstructHook_String)
        #    kwds.setdefault('DestructHook', MUIV_Listtree_DestructHook_String)
        super(Listtree, self).__init__(**kwds)

    def __asnode(self, x):
        return (x if isinstance(x, c_Listtree_TreeNode) else c_Listtree_TreeNode.from_value(x))

    def InsertString(self, meth, name,
                     lnode=MUIV_Listtree_Insert_ListNode_Root,
                     pnode=MUIV_Listtree_Insert_PrevNode_Tail,
                     flags=0):
        """This method should be used to replace Insert
        if you use MUIV_Listtree_ConstructHook_String
        as ConstructHook attribute value.
        """
        return self.Insert(name, self.__asnode(lnode), self.__asnode(pnode), flags, long(name))

    @Close.alias
    def Close(self, meth,
             lnode=MUIV_Listtree_Close_ListNode_Active,
             tnode=MUIV_Listtree_Close_TreeNode_All,
             flags=0):
        meth(self, self.__asnode(lnode), self.__asnode(tnode), flags)

    @Exchange.alias
    def Exchange(self, meth,
                 listnode1, treenode1,
                 listnode2, treenode2,
                 flags=0):
        return meth(self,
                    self.__asnode(listnode1),
                    self.__asnode(treenode1),
                    self.__asnode(listnode2),
                    self.__asnode(treenode2), flags)

    @FindName.alias
    def FindName(self, meth, name,
                 lnode=MUIV_Listtree_FindName_ListNode_Active,
                 flags=0):
        item = meth(self, self.__asnode(lnode), name, flags)
        return (item if long(item) else None)

    @GetEntry.alias
    def GetEntry(self, meth,
                 node=MUIV_Listtree_GetEntry_ListNode_Active,
                 position=MUIV_Listtree_GetEntry_Position_Active,
                 flags=0):
        item = meth(self, self.__asnode(node), position, flags)
        return (item if long(item) else None)

    @GetNr.alias
    def GetNr(self, meth,
              tnode=MUIV_Listtree_GetNr_TreeNode_Active,
              flags=0):
        item = meth(self, self.__asnode(tnode), flags)
        return (item if long(item) else None)

    @Insert.alias
    def Insert(self, meth, name,
               lnode=MUIV_Listtree_Insert_ListNode_Root,
               pnode=MUIV_Listtree_Insert_PrevNode_Tail,
               flags=0, user=0):
        item = meth(self, name, user, self.__asnode(lnode), self.__asnode(pnode), flags)
        return (item if long(item) else None)

    @Move.alias
    def Move(self, meth,
             oldlistnode, oldtreenode,
             newlistnode, newtreenode,
             flags=0):
        meth(self,
             self.__asnode(oldlistnode),
             self.__asnode(oldtreenode),
             self.__asnode(newlistnode),
             self.__asnode(newtreenode), flags)

    @Open.alias
    def Open(self, meth,
             lnode=MUIV_Listtree_Open_ListNode_Active,
             tnode=MUIV_Listtree_Open_TreeNode_All,
             flags=0):
        meth(self, self.__asnode(lnode), self.__asnode(tnode), flags)

    @Remove.alias
    def Remove(self, meth,
               lnode=MUIV_Listtree_Remove_ListNode_Active,
               tnode=MUIV_Listtree_Remove_TreeNode_All,
               flags=0):
        meth(self, self.__asnode(lnode), self.__asnode(tnode), flags)

    @Rename.alias
    def Rename(self, meth, newname,
               tnode=MUIV_Listtree_Rename_TreeNode_Active,
               flags=0):
        meth(self, self.__asnode(tnode), newname, flags)

    @Sort.alias
    def Sort(self, meth,
             lnode=MUIV_Listtree_Sort_ListNode_Active,
             flags=0):
        meth(self, self.__asnode(lnode), flags)

del MAttribute, MMethod
