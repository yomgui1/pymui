/******************************************************************************
Copyright (c) 2009 Guillaume Roguez

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
******************************************************************************/

// Dev Notes:
//
// ** Fundamentables in design **
//
// - Notifications on attributes changes shall not be bypassed
//   or managed in some way by PyMUI, in C or in pure Python.
//   This prevent any rules breaks in the existent or future
//   MUI notification engine. The order of notifications is the
//   'magic' of MUI, not PyMUI.
//
//   But this is limited to the event itself: so the processing to
//   do when the notification event from MUI occures is not limited.
//   to existent MUI methods. This permit to group and manage various
//   actions to do for one MUI attribute change event.
//
// - MUI don't increment Python object reference.
//   It's to classes/UI designers to make sure that a Python object given
//   to MUI during a call to C side function will not be destroyed by
//   any possible GC job during this call and moreover after the call if a
//   reference on the Python object or any contained materials is done by MUI.
//
// - MUI has a limited 'object usage' understanding.
//   There is nothing in BOOPSI to know when an object is used by another one,
//   like Python does with its references counter in each created objects.
//
//   MUI adds only a limited system by using some attributes like MUIA_Parent.
//   But:
//      - it's not generic: MUIA_Parent is limited to Area classes, Window class
//        is parented to Application using another attribute.
//        Adding, removing this references is method dependend (Check Group vs Familly)
//      - it's not mendatory: some classes doesn't have any ref relations possible,
//        like Semaphore or two direct Notify MCC.
//      - no top system reference management.
//
// - MUI don't save the Python context and is not multi-threaded safe.
//   MUI uses Hooks and these ones are not neccessary called in the same task context
//   than the one wher it has been created.
//   Moreover, the Python context is not saved, so PyMUI shall carrefully takes care
//   to have a valid Python interpretor state before calling any Python code.
//

/*
** Top Includes
*/

#include <Python.h>
#include <structmember.h>


/*
** System Includes
*/

#include <clib/debug_protos.h>
#include <cybergraphx/cybergraphics.h>
#include <libraries/asl.h>

#include <proto/alib.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/intuition.h>
#include <proto/utility.h>
#include <proto/muimaster.h>
#include <proto/cybergraphics.h>
#include <proto/layers.h>
#include <proto/graphics.h>

#include <sys/param.h>


extern void dprintf(char*fmt, ...);

#ifndef PYTHON_BASE_NAME
#define PYTHON_BASE_NAME PythonBase
#endif /* !PYTHON_BASE_NAME */


/*
** Private Macros and Definitions
*/

#ifndef MODNAME
#define MODNAME "_muimaster"
#endif

#ifndef INITFUNC
#define INITFUNC init_muimaster
#endif

#ifndef NDEBUG
#define DPRINT(f, x...) ({ dprintf("\033[32m[%4u:%-23s] \033[0m", __LINE__, __FUNCTION__); dprintf(f ,##x); })
#define DRAWPRINT(f, x...) ({ dprintf(f ,##x); })
#else
#define DPRINT(f, x...)
#define DRAWPRINT(f, x...)
#endif

#ifndef MIN
#define MIN(a, b) ({typeof(a)_a=(a);typeof(b)_b=(b);_a>_b?_b:_a;})
#endif

#ifndef MAX
#define MAX(a, b) ({typeof(a)_a=(a);typeof(b)_b=(b);_a<_b?_b:_a;})
#endif

#ifndef DISPATCHER
#define DISPATCHER(Name) \
static ULONG Name##_Dispatcher(void); \
static struct EmulLibEntry GATE ##Name##_Dispatcher = { TRAP_LIB, 0, (void (*)(void)) Name##_Dispatcher }; \
static ULONG Name##_Dispatcher(void) { struct IClass *cl=(struct IClass*)REG_A0; Msg msg=(Msg)REG_A1; Object *obj=(Object*)REG_A2;
#define DISPATCHER_REF(Name) &GATE##Name##_Dispatcher
#define DISPATCHER_END }
#endif

#define INIT_HOOK(h, f) { struct Hook *_h = (struct Hook *)(h); \
    _h->h_Entry = (APTR) HookEntry; \
    _h->h_SubEntry = (APTR) (f); }

#define ADD_TYPE(m, s, t) {Py_INCREF(t); PyModule_AddObject(m, s, (PyObject *)(t));}
#define INSI(m, s, v) if (PyModule_AddIntConstant(m, s, v)) return -1
#define INSS(m, s, v) if (PyModule_AddStringConstant(m, s, v)) return -1
#define INSL(m, s, v) if (PyModule_AddObject(m, s, PyLong_FromUnsignedLong(v))) return -1

#define ADDVAFUNC(name, func, doc...) {name, (PyCFunction) func, METH_VARARGS ,## doc}
#define ADD0FUNC(name, func, doc...) {name, (PyCFunction) func, METH_NOARGS ,## doc}

#define SIMPLE0FUNC(fname, func) static PyObject * fname(PyObject *self){ func(); Py_RETURN_NONE; }
#define SIMPLE0FUNC_bx(fname, func, x) static PyObject * fname(PyObject *self){ return Py_BuildValue(x, func()); }
#define SIMPLE0FUNC_fx(fname, func, x) static PyObject * fname(PyObject *self){ return x(func()); }

#define OBJ_TNAME(o) (((PyObject *)(o))->ob_type->tp_name)
#define OBJ_TNAME_SAFE(o) ({                                            \
            PyObject *_o = (PyObject *)(o);                             \
            NULL != _o ? _o->ob_type->tp_name : "nil"; })

#if defined __GNUC__
    #define ASM
    #define SAVEDS
#else
    #define ASM    __asm
    #define SAVEDS __saveds
#endif

#define CONF_MUI    (1<<0)
#define CONF_ZOMBIE (1<<1)

#define PyCPointer_ASVOIDPTR(o) (((PyCPointer *)(o))->ptr)
#define PyCPointer_Check(op) PyObject_TypeCheck(op, &PyCPointer_Type)
#define PyCPointer_CheckExact(op) ((op)->ob_type == &PyCPointer_Type)

#define PyBOOPSIObject_Check(op) PyObject_TypeCheck(op, &PyBOOPSIObject_Type)
#define PyBOOPSIObject_CheckExact(op) ((op)->ob_type == &PyBOOPSIObject_Type)

#define PyMUIObject_Check(op) PyObject_TypeCheck(op, &PyMUIObject_Type)
#define PyMUIObject_CheckExact(op) ((op)->ob_type == &PyMUIObject_Type)

#define PyMethodMsgObject_CheckExact(op) ((op)->ob_type == &PyMethodMsgObject_Type)

#define PyBOOPSIObject_GET_OBJECT(o) (((PyBOOPSIObject *)(o))->node->n_Object)
#define PyBOOPSIObject_SET_OBJECT(o, x) (((PyBOOPSIObject *)(o))->node->n_Object = (x))
#define PyBOOPSIObject_ISMUI(o) (CONF_MUI == (((PyBOOPSIObject *)(o))->node->n_Flags & CONF_MUI))
#define PyMUIObject_GET_MCC(o) (((PyBOOPSIObject *)(o))->node->n_MCC)

#define _between(a,x,b) ((x)>=(a) && (x)<=(b))
#define _isinobject(x,y) (_between(_mleft(obj),(x),_mright(obj)) && _between(_mtop(obj),(y),_mbottom(obj)))

/* !! Folowing code works only if 'o' is a valid readable memory pointer (use TypeOfMem) !! */
#define PyBOOPSIObject_CheckHash(o) ({ \
    PyBOOPSIObject *_o = (PyBOOPSIObject *)(o); \
    _o->hash == (((ULONG)_o) ^ ((ULONG)_o->node)); })

#define PyBOOPSIObject_IsValid(op) ({ \
    PyBOOPSIObject *_op = (PyBOOPSIObject *)(op); \
    (TypeOfMem(_op) != 0) && PyBOOPSIObject_CheckHash(_op); })

#define ID_BREAK 0xABADDEAD


/*
** Private Types and Structures
*/

typedef struct OverloadedNode_STRUCT {
    struct MinNode  Node;
    ULONG           MethodID;
    PyObject *      Callable;
} OverloadedNode;

typedef struct CreatedObjectNode_STRUCT {
    struct MinNode           n_Node;
    Object *                 n_Object;
    Object *                 n_Parent;
    ULONG                    n_Flags; /* See CONF_xxx below */
    struct MUI_CustomClass * n_MCC;
} CreatedObjectNode;

typedef struct CreatedMCCNode_STRUCT {
    struct MinNode           n_Node;
    struct MUI_CustomClass * n_MCC;
} CreatedMCCNode;

typedef struct PyRasterObject_STRUCT {
    PyObject_HEAD

    struct RastPort *rp;
} PyRasterObject;

typedef struct PyBOOPSIObject_STRUCT {
    PyObject_HEAD

    ULONG               hash;   /* As I use MUI UserData to link a MUI object to a Python object,
                                 * I check this value to be sure that the returned UserData value
                                 * is really a PyMUI object. If this UserData value is a valid memory
                                 * location (checked by TypeOfMem) and if this hash code is correct.
                                 * the UserData represents a PyMUI object.
                                 */
    CreatedObjectNode * node;    /* Allocated structure because the Python object
                                  * may have been deallocated when the BOOPSI garbadge process is run.
                                  */
} PyBOOPSIObject;

typedef struct PyMUIObject_STRUCT {
    PyBOOPSIObject      base;
    PyObject *          children; /* List of children BOOPSI objects attached to this MUI object.
                                   * this list has the special purpose to be used when the MUI object is destroyed.
                                   * At this time children in this list are forced to be destroyed (only at the BOOPSI side,
                                   * letting the Python side with a dead objet).
                                   * This is due to the fact that children members of a MUI object are always deallocated
                                   * automatically by MUI when the parent is deallocated.
                                   * This code doesn't put or remove children byitself, the user is responsible to handle that.
                                   */
    PyObject *          children_dict; /* like children, but inserted in a dict for at given key */
    PyObject *          notify_cbdict;
    PyObject *          overloaded_dict; /* Dict of MethodID:callable items for overloaded MUI methods */
    struct MinList      overloaded;
    PyRasterObject *    raster;          /* cached value, /!\ not always valid */
    ULONG               SuperCalled;
    ULONG               SuperResult;
} PyMUIObject;

typedef struct PyEventHandlerObject_STRUCT {
    PyObject_HEAD         

    PyObject *                    self; /* used to found the Python object in mHandleEvent() */
    struct MUI_EventHandlerNode   handler;
    PyObject *                    window;
    PyObject *                    target;
    PyObject *                    TabletTagsList; /* a dict of tablet tags {Tag: Data} */
    LONG                          muikey; /* copied from MUIP_HandleEvent msg */
    struct IntuiMessage           imsg;   /* copied from MUIP_HandleEvent->imsg */
    struct TabletData             tabletdata; /* copied from MUIP_HandleEvent msg */
    BYTE                          inobject;
    BYTE                          hastablet;
} PyEventHandlerObject;

typedef struct MCCData_STRUCT {
    PyObject *          PythonObject;
    BOOL                Clip;
    APTR                ClipHandle;
} MCCData;

typedef struct CHookObject_STRUCT {
    PyObject_HEAD

    struct Hook * hook;
    struct Hook   _hook;
    PyObject *    callable;
} CHookObject;

typedef struct PyMethodMsgObject_STRUCT {
    PyObject_HEAD

    PyObject *      mmsg_PyMsg;
    struct IClass * mmsg_Class;
    Object *        mmsg_Object;
    Msg             mmsg_Msg;
    BOOL            mmsg_SuperCalled;
    ULONG           mmsg_SuperResult;
} PyMethodMsgObject;


/*
** Private Variables
*/

static struct Library *MUIMasterBase;
static struct Library *CyberGfxBase;
static struct Library *LayersBase;

static struct Hook OnAttrChangedHook;
static PyTypeObject PyRasterObject_Type;
static PyTypeObject PyBOOPSIObject_Type;
static PyTypeObject PyMUIObject_Type;
static PyTypeObject PyEventHandlerObject_Type;
static PyTypeObject CHookObject_Type;
static PyTypeObject PyMethodMsgObject_Type;
static struct MinList gCreatedObjectList;
static struct MinList gCreatedMCCList;
static BOOL gClosingModule = FALSE;
static Object *gApp = NULL; /* Non-NULL if mainloop is running */


/*
** Module DocString
*/

//+ _muimaster__doc__
PyDoc_STRVAR(_muimaster__doc__,
"This module provides access to muimaster.library functionnalities.\n\
Refer to the library manual and corresponding MorphOS manual entries\n\
for more information on calls.");
//-


/*
** Private Functions
*/

static void PyMUIObject_ClearChildren(PyMUIObject *self);

//+ PyMUIObject_Unlink
static void
PyMUIObject_Unlink(PyObject *o)
{
    Object *mo;

    if (!PyMUIObject_Check(o)) return;

    DPRINT("Child: %p-'%s'\n", o, OBJ_TNAME(o));

    if (PyBOOPSIObject_ISMUI(o)) {
        PyMUIObject_ClearChildren((PyMUIObject *)o);

        mo = PyBOOPSIObject_GET_OBJECT(o);
        if (NULL != mo) {
            struct MUI_CustomClass *mcc = PyMUIObject_GET_MCC(o);

            muiUserData(mo) = 0;
            if (NULL != mcc)
                ((MCCData *)INST_DATA(mcc->mcc_Class, mo))->PythonObject = NULL;
        }
    }

    /* because this object is intended to be disposed by MUI */
    PyBOOPSIObject_SET_OBJECT(o, NULL);
    REMOVE(((PyBOOPSIObject *)o)->node); 
}
//-
//+ PyMUIObject_ClearChildren
static void
PyMUIObject_ClearChildren(PyMUIObject *self)
{
    DPRINT("Root: %p-'%s'\n", self, OBJ_TNAME(self));

    /* The MUI object will be destroyed and MUI will dispose children automatically.
     * So we're going to unlink the MUI side of all children Python objects before.
     */

    if (NULL != self->children) {
        PyObject *iter;

        iter = PyObject_GetIter(self->children);
        if (NULL != iter) {
            PyObject *child;

            while (NULL != (child = PyIter_Next(iter))) /* NR */ {
                PyMUIObject_Unlink(child); /* recursive call to PyMUIObject_ClearChildren() */
                Py_DECREF(child);
            }

            Py_DECREF(iter);
        }

        PyErr_Clear();
        Py_CLEAR(self->children);
    }

    if (NULL != self->children_dict) {
        PyObject *key, *child;
        int pos = 0;

        while (PyDict_Next(self->children_dict, &pos, &key, &child))
            PyMUIObject_Unlink(child);

        PyErr_Clear();
        Py_CLEAR(self->children_dict);
    }

    DPRINT("Root: %p '%s' [done]\n", self, OBJ_TNAME(self));
}
//-
//+ Generic_DisposeObject
static VOID
Generic_DisposeObject(PyBOOPSIObject *self)
{
    Object *obj = PyBOOPSIObject_GET_OBJECT(self);

    /* Note #1: possible issue here if the MUI object has been referenced outside of this module.
     * It's to the user to take care of this!
     *
     * Note #2: abitrary Python code may be called during the disposing!
     */

    if (NULL != obj) {
        if (PyBOOPSIObject_ISMUI(self))
            PyMUIObject_ClearChildren((PyMUIObject *)self);

        if (PyBOOPSIObject_ISMUI(self)) {
            DPRINT("Before MUI_DisposeObject(%p) (%p-'%s')\n", obj, self, OBJ_TNAME(self));
            MUI_DisposeObject(obj);
            DPRINT("After MUI_DisposeObject(%p) (%p-'%s')\n", obj, self, OBJ_TNAME(self));
        } else {
            DPRINT("before DisposeObject(%p) (%p-'%s')\n", obj, self, OBJ_TNAME(self));
            DisposeObject(obj);
            DPRINT("after DisposeObject(%p) (%p-'%s')\n", obj, self, OBJ_TNAME(self));
        }

        /* Due to the Note #2 upper, we unlink the BOOPSI side now */
        PyBOOPSIObject_SET_OBJECT(self, NULL);
        REMOVE(self->node);
    }

    free(self->node);
    self->node = NULL;
}
//-
//+ PyBOOPSIObject_GetObject
static inline Object *
PyBOOPSIObject_GetObject(PyObject *pyo)
{
    PyBOOPSIObject *pybo = (APTR)pyo;
    Object *bo = pybo->node->n_Object;

    if (NULL != bo)
        return bo;
    
    PyErr_SetString(PyExc_TypeError, "no BOOPSI object associated");
    return NULL;
}
//-
//+ PyBOOPSIObject_Initialize
static BOOL
PyBOOPSIObject_Initialize(PyObject *self, Object *mo, struct MUI_CustomClass *mcc, ULONG flags)
{
    PyBOOPSIObject *bo = (APTR)self;
    CreatedObjectNode *node;

    /* Using malloc here and not PyMem_Malloc() because we may need to dealloc
     * the structure after Python memory  manager termination.
     */
    node = malloc(sizeof(*node));
    if (NULL== node) {
        PyErr_NoMemory();
        return FALSE;
    }

    memset(node, 0, sizeof(*node));

    if (mcc != NULL)
        flags |= CONF_MUI;

    node->n_Object = mo;
    node->n_MCC = mcc;
    node->n_Flags = flags;

    bo->node = node;

    /* Object hash code */
    bo->hash = ((ULONG)self) ^ ((ULONG)node); /* simple but enough for the purpose */

    return TRUE;
}
//-
//+ PyMethodMsg_New
static PyMethodMsgObject *
PyMethodMsg_New(struct IClass *cl, Object *obj, Msg msg)
{
    PyMethodMsgObject *self;

    self = PyObject_New(PyMethodMsgObject, &PyMethodMsgObject_Type); /* NR */
    if (NULL != self) {
        self->mmsg_PyMsg = NULL;
        self->mmsg_Class = cl;
        self->mmsg_Object = obj;
        self->mmsg_Msg = msg;
        self->mmsg_SuperCalled = FALSE;
    }

    return self;
}
//-
//+ OnAttrChanged
static void
OnAttrChanged(struct Hook *hook, Object *mo, ULONG *args) {
    PyObject *pyo = (PyObject *)args[0];
    ULONG attr = args[1];
    ULONG value = args[2];

    /* Closing application during the module cleanup may lead to call to this function
     * for Open attribute on window, for example
     * We need to detect that and prevent it.
     */
    if (gClosingModule)
        pyo = NULL;

    /* In case of the Python object die before the MUI object */
    if (NULL != pyo) {
        PyObject *res;
        PyGILState_STATE gstate;

        gstate = PyGILState_Ensure();
        Py_INCREF(pyo); /* to prevent that our object was deleted during methods calls */

        DPRINT("{%#lx} Py=%p-%s, MUI=%p, value=(%ld, %lu, %p)\n",
               attr, pyo, OBJ_TNAME_SAFE(pyo), mo, (LONG)value, value, (APTR)value);

        res = PyObject_CallMethod(pyo, "_notify_cb", "III", attr, value, ~value); /* NR */
        DPRINT("PyObject_CallMethod() resulted with value %p (err=%p)\n", res, PyErr_Occurred());

        if (PyErr_Occurred() && (NULL != gApp))
            DoMethod(gApp, MUIM_Application_ReturnID, ID_BREAK);

        Py_XDECREF(res);
        Py_DECREF(pyo);

        PyGILState_Release(gstate);
    }
}
//-
//+ IntuiMsgFunc
static void
IntuiMsgFunc(struct Hook *hook, struct FileRequester *req, struct IntuiMessage *imsg)
{
    if (IDCMP_REFRESHWINDOW == imsg->Class)
        DoMethod(req->fr_UserData, MUIM_Application_CheckRefresh);
}
//-
//+ getfilename
/* Stolen from MUI psi.c demo */
STRPTR
getfilename(Object *win, STRPTR title, STRPTR init_drawer, STRPTR init_pat, BOOL save)
{
    static char buf[MAXPATHLEN];
    struct FileRequester *req;
    struct Window *w = NULL;
    static LONG left=-1,top=-1,width=-1,height=-1;
    Object *app = NULL;
    char *res = NULL;
    static const struct Hook IntuiMsgHook;

    INIT_HOOK(&IntuiMsgHook, IntuiMsgFunc)

    get(win, MUIA_ApplicationObject, &app);
    if (NULL != app) {
        get(win, MUIA_Window_Window, &w);
        if (NULL != win) {
            if (-1 == left) {
                left   = w->LeftEdge + w->BorderLeft + 2;
                top    = w->TopEdge + w->BorderTop + 2;
                width  = MAX(400, w->Width - w->BorderLeft - w->BorderRight - 4);
                height = MAX(400, w->Height - w->BorderTop - w->BorderBottom - 4);
            }

            if (NULL == init_drawer)
                init_drawer = "PROGDIR:";

            if (NULL == init_pat)
                init_pat = "#?";
         
            req = MUI_AllocAslRequestTags(ASL_FileRequest,
                                          ASLFR_Window         , (ULONG)w,
                                          ASLFR_TitleText      , (ULONG)title,
                                          ASLFR_InitialLeftEdge, left,
                                          ASLFR_InitialTopEdge , top,
                                          ASLFR_InitialWidth   , width,
                                          ASLFR_InitialHeight  , height,
                                          ASLFR_InitialDrawer  , (ULONG)init_drawer,
                                          ASLFR_InitialPattern , (ULONG)init_pat,
                                          ASLFR_DoSaveMode     , save,
                                          ASLFR_DoPatterns     , TRUE,
                                          ASLFR_RejectIcons    , TRUE,
                                          ASLFR_UserData       , (ULONG)app,
                                          ASLFR_IntuiMsgFunc   , (ULONG)&IntuiMsgHook,
                                          TAG_DONE);
            if (NULL != req) {
                set(app, MUIA_Application_Sleep, TRUE);
                
                if (MUI_AslRequestTags(req,TAG_DONE)) {
                    if (NULL != *req->fr_File) {
                        res = buf;
                        stccpy(buf, req->fr_Drawer, sizeof(buf));
                        AddPart(buf, req->fr_File, sizeof(buf));
                    }

                    left   = req->fr_LeftEdge;
                    top    = req->fr_TopEdge;
                    width  = req->fr_Width;
                    height = req->fr_Height;
                }
                
                MUI_FreeAslRequest(req);
                set(app, MUIA_Application_Sleep, FALSE);
            } else
                fprintf(stderr, "MUI_AllocAslRequestTags() failed\n");
        } else
            fprintf(stderr, "no Window for win obj %p\n", win);
    } else
        fprintf(stderr, "no app for win obj %p\n", win);

    return res;
}
//-
//+ py2long
static int
py2long(PyObject *obj, LONG *value)
{
    if (obj == Py_None)
        *value = 0;
    else if (PyLong_CheckExact(obj))
        *value = PyLong_AsUnsignedLongMask(obj);
    else if (PyInt_CheckExact(obj))
        *value = PyInt_AsLong(obj);
    else {
        PyObject *x = PyNumber_Long(obj); /* NR */

        if (NULL == x) return 0;
        *value = PyLong_AsUnsignedLongMask(x);
        Py_DECREF(x);
    }

    DPRINT("obj=%p-'%s', value = 0x%08x\n", obj, OBJ_TNAME_SAFE(obj), *value);

    return 1;
}
//-
//+ callpython
static ULONG
callpython(struct Hook *hook, ULONG a2_value, ULONG a1_value)
{
    CHookObject *self = hook->h_Data;
    PyGILState_STATE gstate;
    PyObject *res;
    ULONG result;

    DPRINT("hook: %p, self: %p\n", hook, self);

    if (gClosingModule) {
        dprintf("Warning: PyMUI CHookObject called during PyMUI closing.");
        return 0;
    }

    if ((NULL == self) || (NULL == self->callable)) {
        dprintf("Warning: Bad PyMUI call: NULL hook or callable (CHook=%p)\n", self);
        return 0;
    }

    gstate = PyGILState_Ensure();

    DPRINT("Callable: %p, values: [%x, %x]\n", self->callable, a2_value, a1_value);

    Py_INCREF(self);
    res = PyObject_CallFunction(self->callable, "kk", a2_value, a1_value); /* NR */
    if (NULL != res) {
        if (!py2long(res, &result))
            result = 0;
        Py_DECREF(res);
    }

    Py_DECREF(self);

    if (PyErr_Occurred() && (NULL != gApp))
        DoMethod(gApp, MUIM_Application_ReturnID, ID_BREAK);

    PyGILState_Release(gstate);

    return result;
}
//-


/*******************************************************************************************
** MCC MUI Object
*/

//+ mCheckPython
static ULONG
mCheckPython(struct IClass *cl, Object *obj, Msg msg)
{
    MCCData *data = INST_DATA(cl, obj);
    PyMUIObject *pyo = (PyMUIObject *)data->PythonObject; /* BR */
    BOOL super = FALSE;
    ULONG result = 0;

    if (NULL != pyo->overloaded_dict) {
        OverloadedNode *node;

        ForeachNode(&pyo->overloaded, node) {
            if (node->MethodID == msg->MethodID) {
                PyObject *callable, *o;
                PyMethodMsgObject *msg_obj;

                msg_obj = PyMethodMsg_New(cl, obj, msg); /* NR */
                if (NULL != msg_obj) {
                    callable = node->Callable; /* BR */
                    DPRINT("pyo=%p-%s (MID: 0x%08x, callable: %p, MethodMsg: %p)\n",
                        pyo, OBJ_TNAME(pyo), msg->MethodID, callable, msg_obj);

                    //XXX: really needed ?
                    //ADDHEAD(&pyo->overloaded, REMOVE(node));

                    o = PyObject_CallFunction(callable, "ON", pyo, msg_obj);
                    DPRINT("result: %p-%s\n", o, OBJ_TNAME_SAFE(o));

                    super = msg_obj->mmsg_SuperCalled;
                    result = msg_obj->mmsg_SuperResult;

                    if (NULL != o) {
                        int ok = py2long(o, &result);

                        Py_DECREF(o);
                        if (!ok)
                            goto check_super;

                        return result;
                    }
                }

                break;
            }
        }
    }

check_super:
    if (!super)
        return DoSuperMethodA(cl, obj, msg);
    return result;
}
//-
//+ MCC Dispatcher
DISPATCHER(mcc)
{
    MCCData *data = INST_DATA(cl, obj);
    PyGILState_STATE gstate = 0;
    ULONG result;

    if (gClosingModule && (NULL != data->PythonObject))
        data->PythonObject = NULL;

    if (NULL == data->PythonObject)
        return DoSuperMethodA(cl, obj, msg);

    gstate = PyGILState_Ensure();

    if (PyErr_Occurred())
        goto err;

    switch (msg->MethodID) {
        /* Protect basic BOOPSI methods */
        case OM_NEW:
        case OM_DISPOSE:
        case OM_ADDMEMBER:
        case OM_REMMEMBER:
        case OM_SET:
        case OM_GET:
        case OM_ADDTAIL:
        case OM_REMOVE:
        case OM_NOTIFY:
        case OM_UPDATE:
            result = DoSuperMethodA(cl, obj, msg);
            break;

        default: result = mCheckPython(cl, obj, (APTR)msg);
    }

    if (PyErr_Occurred()) {
err:
        DPRINT("error, gApp=%p, MethodID=%x\n", gApp, msg->MethodID);

        if (NULL != gApp)
            DoMethod(gApp, MUIM_Application_ReturnID, ID_BREAK);

        result = 0;
    }

    PyGILState_Release(gstate);
    return result;
}
DISPATCHER_END
//-


/*******************************************************************************************
** PyBOOPSIObject_Type
*/

//+ boopsi_new
static PyObject *
boopsi_new(PyTypeObject *type, PyObject *args)
{
    PyBOOPSIObject *self;

    self = (APTR)type->tp_alloc(type, 0); /* NR */
    if (NULL != self) {
        ULONG flags;
        Object *mo = NULL;

        if (PyMUIObject_Check(self))
            flags = CONF_MUI;
        else
            flags = 0;

        /* 1st argument may be address of existing object */
        if (PyArg_ParseTuple(args, "|I", &mo)) {
            if (PyBOOPSIObject_Initialize((PyObject *)self, mo, NULL, flags))
                return (PyObject *)self;
        }

        Py_DECREF(self);
    }

    return NULL;
}
//-
//+ boopsi_dealloc
static void
boopsi_dealloc(PyBOOPSIObject *self)
{
    DPRINT("self=%p, node=%p\n", self, self->node);

    Generic_DisposeObject(self);
    ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}
//-
//+ boopsi_repr
static PyObject *
boopsi_repr(PyBOOPSIObject *self)
{
    Object *obj;
    
    obj = PyBOOPSIObject_GET_OBJECT(self);
    if (NULL != obj)
        return PyString_FromFormat("<%s at %p, BOOPSI at %p>", OBJ_TNAME(self), self, obj);
    else
        return PyString_FromFormat("<%s at %p, NULL object>", OBJ_TNAME(self), self);
}
//-
//+ boopsi_richcompare
static PyObject *
boopsi_richcompare(PyObject *v, PyObject *w, int op)
{
    PyObject *ret;
    int cmp;

    if (!PyBOOPSIObject_Check(v) || !PyBOOPSIObject_Check(w) || ((Py_EQ != op) && (Py_NE != op)) ) {
        Py_INCREF(Py_NotImplemented);
	return Py_NotImplemented;
    }

    cmp = PyBOOPSIObject_GET_OBJECT(v) == PyBOOPSIObject_GET_OBJECT(w);
    if (Py_EQ == op)
        ret = cmp?Py_True:Py_False;
    else
        ret = cmp?Py_False:Py_True;

    Py_INCREF(ret);
    return ret;
}
//-
//+ boopsi__create
static PyObject *
boopsi__create(PyBOOPSIObject *self, PyObject *args)
{
    UBYTE *classid;
    Object *obj;
    LONG isMCC = FALSE;
    BOOL isMUI;
    struct MUI_CustomClass *mcc = NULL;
    struct TagItem *tags;
    PyObject *overloaded_dict = NULL;

    /* Protect againts doubles */
    if (NULL != PyBOOPSIObject_GET_OBJECT(self)) {
        PyErr_SetString(PyExc_RuntimeError, "Already created BOOPSI Object");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "s|IiO!:PyBOOPSIObject", &classid, &tags, &isMCC, &PyDict_Type, &overloaded_dict)) /* BR */
        return NULL;

    DPRINT("ClassID: '%s', tags: %p, isMCC: %d\n", classid, tags, isMCC);

    isMUI = PyBOOPSIObject_ISMUI(self);
    if (!isMUI && isMCC) {
        PyErr_SetString(PyExc_TypeError, "MCC feature requested on a non-MUI object");
        return NULL;
    }

    /* Need to create a new MCC or a simple MUI object instance ? */
    if (isMCC) {
        CreatedMCCNode *node = NULL, *next;

        DPRINT("Search for MCC based on: '%s'\n", classid);
        
        ForeachNode(&gCreatedMCCList, next) {
            if ((NULL != next->n_MCC->mcc_Super->cl_ID) && !strcmp(classid, next->n_MCC->mcc_Super->cl_ID)) {
                node = next;
                break;
            }
        }

        if (NULL == node) {
            node = malloc(sizeof(CreatedMCCNode));
            if (NULL == node) {
                PyErr_SetString(PyExc_MemoryError, "Not enough memory to create a new MCC for this object.");
                return NULL;
            }

            mcc = MUI_CreateCustomClass(NULL, classid, NULL, sizeof(MCCData), DISPATCHER_REF(mcc));
            if (NULL == mcc) {
                free(node);
                PyErr_SetString(PyExc_MemoryError, "Not enough memory to create a new MCC for this object.");
                return NULL;
            }

            node->n_MCC = mcc;
            ADDTAIL(&gCreatedMCCList, node);
        } else
            mcc = node->n_MCC;

        DPRINT("MCC: %p (SuperID: '%s')\n", mcc, node->n_MCC->mcc_Super->cl_ID);
        
        if ((NULL != overloaded_dict) && (PyDict_Size(overloaded_dict) > 0)) {
            /* Create an array from 'overloaded' dict entries */
            PyMUIObject *mo = (PyMUIObject *)self;
            PyObject *key, *value;
            int pos = 0;
            OverloadedNode *ovn = NULL;

            while (PyDict_Next(overloaded_dict, &pos, &key, &value)) { /* BR */
                ULONG mid = PyLong_AsUnsignedLongMask(key);

                if (PyErr_Occurred()) {
                    ovn = NULL;
                    break;
                }

                ovn = PyMem_Malloc(sizeof(OverloadedNode));
                if (NULL == ovn) break;

                ovn->MethodID = mid;
                ovn->Callable = value;

                ADDTAIL(&mo->overloaded, ovn);
                DPRINT("Overloaded: method 0x%08x added, callable: %p\n", mid, value);
            }

            if (NULL == ovn) {
                PyErr_SetString(PyExc_MemoryError, "failed to create the overloaded method list");
                return NULL;
            }

            mo->overloaded_dict = overloaded_dict;
            Py_INCREF(overloaded_dict); /* this keep dict values valid */
        }

        DPRINT("Overloaded: %p\n", overloaded_dict);
    }

    if (NULL != tags) {
#if 0
        struct TagItem *tag, *ttags;

        ttags = tags;
        while (NULL != (tag = NextTagItem(&ttags))) {
            DPRINT("Tag: %x, Data %x\n", tag->ti_Tag, tag->ti_Data);
            if (tag->ti_Tag == 0x80420629) {
                STRPTR *s = (APTR)tag->ti_Data;
                DPRINT("First string at %p\n", *s);

                while (NULL != *s) {
                    DPRINT("s=%p\n", *s);
                    s++;
                }
            }
        }
#endif

        if (isMUI) {
            if (NULL != mcc)
                obj = NewObjectA(mcc->mcc_Class, NULL, tags);
            else
                obj = MUI_NewObjectA(classid, tags);
        } else
            obj = NewObjectA(NULL, classid, tags);
    } else if (isMUI) {
        if (NULL != mcc)
            obj = NewObject(mcc->mcc_Class, NULL, TAG_DONE);
        else
            obj = MUI_NewObject(classid, TAG_DONE);
    } else
        obj = NewObject(NULL, classid, TAG_DONE);

    if (NULL != obj) {
        DPRINT("New %s object @ %p (self=%p, node=%p, mcc=%p)\n", classid, obj, self, self->node, mcc);

        ADDTAIL(&gCreatedObjectList, self->node);
        PyBOOPSIObject_SET_OBJECT(self, obj);

        /* Link MUI / Python together */
        if (isMUI) {
            self->node->n_MCC = mcc;
            muiUserData(obj) = (ULONG)self; /* used for _BOOPSI2Python */
            /* XXX: mega-hack! shall be changed for a setattr() asap ! */
            if (NULL != mcc)
                ((MCCData *)INST_DATA(mcc->mcc_Class, obj))->PythonObject = (APTR)self;
        }

        Py_RETURN_NONE;
    }

    return PyErr_Format(PyExc_SystemError, "Failed to create BOOPSI object of class %s", classid);
}
//-
//+ boopsi__get
PyDoc_STRVAR(boopsi__get_doc,
"_get(id) -> unsigned integer \n\
\n\
Call BOOPSI function GetAttr() on linked BOPPSI object with given attribute id.\n\
Returns the stored value of GetAttr().");

static PyObject *
boopsi__get(PyBOOPSIObject *self, PyObject *args)
{
    Object *obj;
    ULONG attr;
    ULONG value;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;
 
    if (!PyArg_ParseTuple(args, "I", &attr)) /* BR */
        return NULL;

    DPRINT("_get(0x%08x): Object=%p (%s)\n", attr, obj, OCLASS(obj)->cl_ID);
    value = 0xdeadbeaf;
    if (!GetAttr(attr, obj, &value))
        return PyErr_Format(PyExc_ValueError, "GetAttr(0x%08x) failed", (int)attr);
    DPRINT("_get(0x%08x): value=(%d, %u, 0x%08lx)\n", attr, (LONG)value, value, value);

    return PyLong_FromUnsignedLong(value);
}
//-
//+ boopsi__set
PyDoc_STRVAR(boopsi__set_doc,
"_set(attr, value) -> None\n\
\n\
Try to set an attribute of the BOOPSI object by calling the BOOPSI function SetAttrs().\n\
Value should be an interger representing pointer on the ULONG value to use with SetAttrs.\n\
Note: No reference kept on the given value object!");

static PyObject *
boopsi__set(PyBOOPSIObject *self, PyObject *args) {
    Object *obj;
    ULONG attr;
    ULONG value;
    PyObject *v_obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "IO", &attr, &v_obj)) /* BR */
        return NULL;

    if (!py2long(v_obj, &value))
        return NULL;

    DPRINT("Attr 0x%lx set to value: %ld %ld %#lx on BOOPSI obj @ %p\n", attr, (LONG)value, value, value, obj);
    set(obj, attr, value);
    DPRINT("done\n");
    
    /* Due to MUI notification system a Python code may have be called here */
    if (PyErr_Occurred())
        return NULL;

    Py_RETURN_NONE;
}
//-
//+ boopsi__new_do
PyDoc_STRVAR(boopsi__new_do_doc,
"_do(msg, *extra_args) -> long\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__new_do(PyBOOPSIObject *self, PyObject *args) {
    Object *obj;
    ULONG result;
    Msg msg;
    int msg_length;
    PyObject *extra_args = NULL;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "s#|O:_do", &msg, &msg_length, &extra_args)) /* BR */
        return NULL;

    DPRINT("DoMethod(obj=%p, msg=%p (%u bytes), 0x%08x)\n", obj, msg, msg_length, msg->MethodID);

    /* Notes: objects given to the object dispatcher should remains alive during the call of the method,
     * even if this call cause some Python code to be executed causing a DECREF of these objects.
     * This is protected by the fact that objects have their ref counter increased until they remains
     * inside the argument tuple of this function.
     * So here there is no need to INCREF argument python objects.
     */

    /* Collect extra arguments (for variable arguments methods) */
    if (NULL != extra_args) {
        PyObject *fast;
        Msg final_msg;
        ULONG final_length;
        int n;

        fast = PySequence_Fast(extra_args, "Method optional arguments should be convertible into tuple or list"); /* NR */
        if (NULL == fast)
            return NULL;

        n = PySequence_Fast_GET_SIZE(fast);
        final_length = msg_length + n * sizeof(ULONG);

        DPRINT("#  Extra Args count: %d, final msg len: %lu bytes\n", n, final_length);

        final_msg = PyMem_Malloc(final_length);
        if (NULL == final_msg) {
            Py_DECREF(fast);
            return PyErr_NoMemory();
        }

        /* copy the user msg base first */
        CopyMem(msg, final_msg, msg_length);

        if (n > 0) {
            PyObject **data = PySequence_Fast_ITEMS(fast);
            ULONG i, *ptr = (ULONG *)(((char *)final_msg) + msg_length);

            for (i=0; i < n; i++, ptr++) {
                if (!py2long(data[i], ptr))
                    break;

                DPRINT("#  args[%u]: %d, %u, 0x%08x\n", i, *ptr, (ULONG)*ptr, *ptr);
            }
        }

        Py_DECREF(fast);

        /* Catch possible exceptions during py2long() calls */
        if (PyErr_Occurred()) {
            PyMem_Free(msg);
            return NULL;
        }

        result = DoMethodA(obj, final_msg);

        PyMem_Free(final_msg);
    } else
        result = DoMethodA(obj, msg);

    DPRINT("DoMethod(obj=%p, 0x%08x) = (%ld, %lu, %lx)\n", obj, msg->MethodID, (LONG)result, result, result);

    /* Methods can call Python ... check against exception here also */
    if (PyErr_Occurred())
        return NULL;

    return PyLong_FromUnsignedLong(result);
}
//-
//+ boopsi__do1
PyDoc_STRVAR(boopsi__do1_doc,
"_do1(method, arg) -> int\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__do1(PyBOOPSIObject *self, PyObject *args) {
    Object *obj;
    ULONG meth;
    LONG value;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "IO&", &meth, py2long, &value)) /* BR */
        return NULL;

    DPRINT("DoMethod(obj=%p, meth=0x%08x, value=0x%08x):\n", obj, meth, value);
    value = DoMethod(obj, meth, value);

    if (PyErr_Occurred())
        return NULL;

    return PyLong_FromUnsignedLong(value);
}
//-
//+ boopsi__add
PyDoc_STRVAR(boopsi__add_doc,
"_add(object) -> int\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__add(PyBOOPSIObject *self, PyObject *args) {
    PyObject *ret, *pychild;
    Object *obj, *child;
    int lock = FALSE;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "O!|i", &PyBOOPSIObject_Type, &pychild, &lock)) /* BR */
        return NULL;

    /* Warning: no reference kept on arg object after return! */
    child = PyBOOPSIObject_GetObject((PyObject *)pychild);
    if (NULL == child)
        return NULL;

    if (lock) {
        DPRINT("Lock\n");    
        DoMethod(obj, MUIM_Group_InitChange);
    }

    DPRINT("OM_ADDMEMBER: parent=%p, obj=%p\n", obj, child);         
    Py_INCREF(pychild);
    ret = PyInt_FromLong(DoMethod(obj, OM_ADDMEMBER, (ULONG)child));
    Py_DECREF(pychild);
    
    if (lock) {
        DPRINT("Unlock\n");        
        DoMethod(obj, MUIM_Group_ExitChange);
    }

    DPRINT("done\n");

    return ret;
}
//-
//+ boopsi__rem
PyDoc_STRVAR(boopsi__rem_doc,
"_rem(object, lock=False) -> int\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__rem(PyBOOPSIObject *self, PyObject *args) {
    PyObject *ret, *pychild;
    Object *obj, *child;
    int lock = FALSE;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "O!|i", &PyBOOPSIObject_Type, &pychild, &lock)) /* BR */
        return NULL;

    child = PyBOOPSIObject_GetObject((PyObject *)pychild);
    if (NULL == child)
        return NULL;

    DPRINT("OM_REMMEMBER: parent=%p, obj=%p\n", obj, child);

    if (lock) {
        DPRINT("lock\n");
        DoMethod(obj, MUIM_Group_InitChange);
    }

    Py_INCREF(pychild);
    ret = PyInt_FromLong(DoMethod(obj, OM_REMMEMBER, (ULONG)child));
    Py_DECREF(pychild);

    if (lock) {
        DPRINT("Unlock\n");
        DoMethod(obj, MUIM_Group_ExitChange);
    }

    DPRINT("done\n");

    return ret;
}
//-
//+ boopsi_nonzero
static int
boopsi_nonzero(PyBOOPSIObject *self)
{
    return NULL != PyBOOPSIObject_GET_OBJECT(self);
}
//-
//+ boopsi_get_object
static PyObject *
boopsi_get_object(PyBOOPSIObject *self)
{
    return PyLong_FromVoidPtr(PyBOOPSIObject_GET_OBJECT(self));
}
//-

static PyGetSetDef boopsi_getseters[] = {
    {"_object", (getter)boopsi_get_object, NULL, "BOOPSI object address", NULL},
    {NULL} /* sentinel */
};

static PyNumberMethods boopsi_as_number = {
    nb_nonzero : (inquiry)boopsi_nonzero,
};

static struct PyMethodDef boopsi_methods[] = {
    {"_create", (PyCFunction) boopsi__create, METH_VARARGS, NULL},
    {"_get",    (PyCFunction) boopsi__get,    METH_VARARGS, boopsi__get_doc},
    {"_set",    (PyCFunction) boopsi__set,    METH_VARARGS, boopsi__set_doc},
    {"_do",     (PyCFunction) boopsi__new_do, METH_VARARGS, boopsi__new_do_doc},
    {"_do1",    (PyCFunction) boopsi__do1,    METH_VARARGS, boopsi__do1_doc},
    {"_add",    (PyCFunction) boopsi__add,    METH_VARARGS, boopsi__add_doc},
    {"_rem",    (PyCFunction) boopsi__rem,    METH_VARARGS, boopsi__rem_doc},

    {NULL, NULL} /* sentinel */
};

static PyTypeObject PyBOOPSIObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.PyBOOPSIObject",
    tp_basicsize    : sizeof(PyBOOPSIObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    tp_doc          : "BOOPSI Objects",
    
    tp_new          : (newfunc)boopsi_new,
    tp_dealloc      : (destructor)boopsi_dealloc,
    
    tp_repr         : (reprfunc)boopsi_repr,
    tp_methods      : boopsi_methods,
    tp_getset       : boopsi_getseters,
    tp_as_number    : &boopsi_as_number,
    tp_richcompare  : (richcmpfunc)boopsi_richcompare,
};

/*******************************************************************************************
** MUIObject_Type
*/

//+ muiobject_new
static PyObject *
muiobject_new(PyTypeObject *type, PyObject *args)
{
    PyMUIObject *self;

    self = (PyMUIObject *)boopsi_new(type, args); /* NR */
    if (NULL != self) {
        NEWLIST(&self->overloaded);

        self->notify_cbdict = PyDict_New(); /* NR */
        if (NULL != self->notify_cbdict) {
            self->children_dict = PyDict_New(); /* NR */
            if (NULL != self->children_dict) {
                self->children = PySet_New(NULL); /* NR */
                if (NULL != self->children) {
                    self->raster = (PyRasterObject *)PyObject_New(PyRasterObject, &PyRasterObject_Type); /* NR */
                    if (NULL != self->raster)
                        return (PyObject *)self;
                }
            }
        }

        Py_DECREF((PyObject *)self);
    }

    return NULL;
}
//-
//+ muiobject_traverse
static int
muiobject_traverse(PyMUIObject *self, visitproc visit, void *arg)
{
    Py_VISIT(self->notify_cbdict);
    Py_VISIT(self->overloaded_dict);
    Py_VISIT(self->raster);
    Py_VISIT(self->children_dict);
    Py_VISIT(self->children);
    
    return 0;
}
//-
//+ muiobject_clear
static int
muiobject_clear(PyMUIObject *self)
{
    DPRINT("Clearing PyMUIObject: %p [%s]\n", self, OBJ_TNAME(self));

    Py_CLEAR(self->notify_cbdict);
    Py_CLEAR(self->overloaded_dict);
    Py_CLEAR(self->raster);

    PyMUIObject_ClearChildren(self);

    /* Safe to clear the children list now */
    Py_CLEAR(self->children_dict);
    Py_CLEAR(self->children);

    return 0;
}
//-
//+ muiobject_dealloc
static void
muiobject_dealloc(PyMUIObject *self)
{
    OverloadedNode *node, *next;

    muiobject_clear(self);

    ForeachNodeSafe(&self->overloaded, node, next)
        PyMem_Free(node);

    boopsi_dealloc((PyBOOPSIObject *)self);
}
//-
//+ muiobject__cclear
static PyObject *
muiobject__cclear(PyMUIObject *self)
{
    PyDict_Clear(self->children_dict);
    PySet_Clear(self->children);

    Py_RETURN_NONE;
}
//-
//+ muiobject__cadd
static PyObject *
muiobject__cadd(PyMUIObject *self, PyObject *args)
{
    PyObject *child, *key=NULL;
    Object *child_obj;

    if (!PyArg_ParseTuple(args, "O!|O", &PyMUIObject_Type, &child, &key))
        return NULL;

    child_obj = PyBOOPSIObject_GET_OBJECT(child);
    if (NULL != child_obj) {
        int result;

        /* Protection against adding itself */
        if (child_obj == PyBOOPSIObject_GET_OBJECT(self)) {
            PyErr_SetString(PyExc_TypeError, "cannot add an object its own children list!");
            return NULL;
        }

        if (NULL != key) {
            result = PyDict_SetItem(self->children_dict, key, child);
        } else
            result = PySet_Add(self->children, child);

        if (result < 0)
            return NULL;

        ((PyBOOPSIObject *)child)->node->n_Parent = PyBOOPSIObject_GET_OBJECT(self);
    }

    Py_RETURN_NONE;
}
//-
//+ muiobject__crem
/* Note: success even if the object is not a children */
static PyObject *
muiobject__crem(PyMUIObject *self, PyObject *args)
{
    PyObject *child, *key=NULL;
    int result;

    if (!PyArg_ParseTuple(args, "O!|O", &PyMUIObject_Type, &child, &key))
        return NULL;

    ((PyBOOPSIObject *)child)->node->n_Parent = NULL;

    if (NULL != key)
        result = PyDict_DelItem(self->children_dict, key);
    else
        result = PySet_Discard(self->children, child);

    if (result < 0)
        return NULL;

    Py_RETURN_NONE;
}
//-
//+ muiobject__cdel
static PyObject *
muiobject__cdel(PyMUIObject *self, PyObject *key)
{
    PyObject *child;

    if (PyDict_Contains(self->children_dict, key)) {
        child = PyDict_GetItem(self->children_dict, key); /* BR */
        ((PyBOOPSIObject *)child)->node->n_Parent = NULL;

        if (PyDict_DelItem(self->children_dict, key) < 0)
            return NULL;
    }

    Py_RETURN_NONE;
}
//-
//+ muiobject__cin
static PyObject *
muiobject__cin(PyMUIObject *self, PyObject *args)
{
    PyObject *child;

    if (!PyArg_ParseTuple(args, "O!", &PyMUIObject_Type, &child))
        return NULL;

    switch (PySet_Contains(self->children, child)) {
        case -1: return NULL;
        case 0: Py_RETURN_FALSE;
        case 1: Py_RETURN_TRUE;
    }

    Py_RETURN_NONE;
}
//-
//+ muiobject__nnset
PyDoc_STRVAR(muiobject__nnset_doc,
"_nnset(attr, value) -> None\n\
\n\
Like BOOPSIObject._set() but without triggering notification on MUI object.");

static PyObject *
muiobject__nnset(PyMUIObject *self, PyObject *args)
{
    Object *obj;
    ULONG attr;
    LONG value;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "IO&", &attr, py2long, &value)) /* BR */
        return NULL;

    DPRINT("Attr 0x%lx set to value: %ld %ld %#lx on MUI obj @ %p\n", attr, (LONG)value, value, value, obj);
    nnset(obj, attr, value);
    DPRINT("done\n");

    Py_RETURN_NONE;
}
//-
//+ muiobject__notify
PyDoc_STRVAR(muiobject__notify_doc,
"_notify(trigattr, trigvalue) -> None\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
muiobject__notify(PyMUIObject *self, PyObject *args)
{
    ULONG trigattr, trigvalue, value;
    Object *mo;

    mo = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == mo)
        return NULL;

    trigvalue = MUIV_EveryTime;
    if (!PyArg_ParseTuple(args, "I|I", &trigattr, &trigvalue)) /* BR */
        return NULL;

    DPRINT("MO: %p, trigattr: %#lx, trigvalue: %ld, %lu, %#lx\n",
           mo, trigattr, (LONG)trigvalue, trigvalue, trigvalue);

    if (MUIV_EveryTime == trigvalue)
        value = MUIV_TriggerValue;
    else
        value = trigvalue;

    DoMethod(mo, MUIM_Notify, trigattr, trigvalue,
             MUIV_Notify_Self, 5,
             MUIM_CallHook, (ULONG)&OnAttrChangedHook, (ULONG)self, trigattr, value);

    DPRINT("done\n");

    Py_RETURN_NONE;
}
//-
//+ muiobject_redraw
PyDoc_STRVAR(muiobject_redraw_doc,
"_redraw(flags) -> None\n\
\n\
Just direct call to MUI_Redraw(flags).");

static PyObject *
muiobject_redraw(PyMUIObject *self, PyObject *args)
{
    Object *obj;
    ULONG flags = MADF_DRAWOBJECT;

    if (!PyArg_ParseTuple(args, "|I", &flags))
        return NULL;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    MUI_Redraw(obj, flags);

    Py_RETURN_NONE;
}
//-
//+ muiobject_get_mleft
static PyObject *
muiobject_get_mleft(PyObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    return PyInt_FromLong(_mleft(obj));
}
//-
//+ muiobject_get_mright
static PyObject *
muiobject_get_mright(PyObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    return PyInt_FromLong(_mright(obj));
}
//-
//+ muiobject_get_mtop
static PyObject *
muiobject_get_mtop(PyObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    return PyInt_FromLong(_mtop(obj));
}
//-
//+ muiobject_get_mbottom
static PyObject *
muiobject_get_mbottom(PyObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    return PyInt_FromLong(_mbottom(obj));
}
//-
//+ muiobject_get_mdim
static PyObject *
muiobject_get_mdim(PyObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    if (0 == closure)
        return PyInt_FromLong(_mwidth(obj));
    else
        return PyInt_FromLong(_mheight(obj));
}
//-
//+ muiobject_get_mbox
static PyObject *
muiobject_get_mbox(PyObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    return Py_BuildValue("HHHH", _mleft(obj), _mtop(obj), _mright(obj), _mbottom(obj));
}
//-
//+ muiobject_get_sdim
static PyObject *
muiobject_get_sdim(PyObject *self, void *closure)
{
    Object *obj;
    struct Screen *scr;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    scr = _screen(obj);
    if (NULL == scr) {
        PyErr_SetString(PyExc_SystemError, "No valid Screen structure found");
        return NULL;
    }

    if (0 == closure)
        return PyInt_FromLong(scr->Width);
    else
        return PyInt_FromLong(scr->Height);
}
//-
//+ muiobject_get_srange
static PyObject *
muiobject_get_srange(PyObject *self, void *closure)
{
    Object *obj;
    struct Screen *scr;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    scr = _screen(obj);
    if (NULL == scr) {
        PyErr_SetString(PyExc_SystemError, "No valid Screen structure found");
        return NULL;
    }

    if (0 == closure)
        return PyInt_FromLong(scr->Width-1);
    else
        return PyInt_FromLong(scr->Height-1);
}
//-
//+ muiobject_get__superid
static PyObject *
muiobject_get__superid(PyObject *self, void *closure)
{
    Object *obj;
    ClassID id;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    id = OCLASS(obj)->cl_Super->cl_ID;
    if (NULL != id)
        return PyString_FromString(id);

    Py_RETURN_NONE;
}
//-
//+ muiobject_get_rp
static PyObject *
muiobject_get_rp(PyMUIObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    self->raster->rp = _rp(obj);
    Py_INCREF((PyObject *)self->raster);

    return (PyObject *)self->raster;
}
//-
//+ muiobject_get__children
static PyObject *
muiobject_get__children(PyMUIObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
    if (NULL == obj)
        return NULL;

    return PyObject_GetIter(self->children);
}
//-

static PyGetSetDef muiobject_getseters[] = {
    {"MLeft",   (getter)muiobject_get_mleft,   NULL, "_mleft(obj)",   NULL},
    {"MRight",  (getter)muiobject_get_mright,  NULL, "_mright(obj)",  NULL},
    {"MTop",    (getter)muiobject_get_mtop,    NULL, "_mtop(obj)",    NULL},
    {"MBottom", (getter)muiobject_get_mbottom, NULL, "_mbottom(obj)", NULL},
    {"MWidth",  (getter)muiobject_get_mdim,    NULL, "_mwidth(obj)",   (APTR) 0},
    {"MHeight", (getter)muiobject_get_mdim,    NULL, "_mheight(obj)",  (APTR)~0},
    {"MBox",    (getter)muiobject_get_mbox,    NULL, "4-Tuple of the bounded box object values", NULL},
    {"SWidth",  (getter)muiobject_get_sdim,    NULL, "Screen Width",   (APTR) 0},
    {"SHeight", (getter)muiobject_get_sdim,    NULL, "Screen Height",  (APTR)~0},
    {"SRangeX", (getter)muiobject_get_srange,  NULL, "Screen X range", (APTR) 0},
    {"SRangeY", (getter)muiobject_get_srange,  NULL, "Screen Y range", (APTR)~0},
    {"_rp",     (getter)muiobject_get_rp,      NULL, "Object RastPort", NULL},
    {"_superid", (getter)muiobject_get__superid, NULL, "MUI SuperID", NULL},
    {"_children", (getter)muiobject_get__children, NULL, "Iterator on object's children", NULL},
    {NULL} /* sentinel */
};

static PyMemberDef muiobject_members[] = {
    {"_notify_cbdict", T_OBJECT, offsetof(PyMUIObject, notify_cbdict), RO, NULL},
    {NULL} /* sentinel */
};

static struct PyMethodDef muiobject_methods[] = {
    {"_cclear", (PyCFunction) muiobject__cclear,  METH_NOARGS, NULL},
    {"_cadd",   (PyCFunction) muiobject__cadd,    METH_VARARGS, NULL},
    {"_crem",   (PyCFunction) muiobject__crem,    METH_VARARGS, NULL},
    {"_cin",    (PyCFunction) muiobject__cin,     METH_VARARGS, NULL},
    {"_cdel",   (PyCFunction) muiobject__cdel,    METH_O, NULL},
    {"_nnset",  (PyCFunction) muiobject__nnset,   METH_VARARGS, muiobject__nnset_doc},
    {"_notify", (PyCFunction) muiobject__notify,  METH_VARARGS, muiobject__notify_doc},
    {"Redraw",  (PyCFunction) muiobject_redraw,   METH_VARARGS, muiobject_redraw_doc},
    {NULL} /* sentinel */
};

static PyTypeObject PyMUIObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_base         : &PyBOOPSIObject_Type,
    tp_name         : "_muimaster.PyMUIObject",
    tp_basicsize    : sizeof(PyMUIObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    tp_doc          : "MUI Objects",

    tp_new          : (newfunc)muiobject_new,
    tp_traverse     : (traverseproc)muiobject_traverse,
    tp_clear        : (inquiry)muiobject_clear,
    tp_dealloc      : (destructor)muiobject_dealloc,
    
    tp_methods      : muiobject_methods,
    tp_members      : muiobject_members,
    tp_getset       : muiobject_getseters,
};

/*******************************************************************************************
** MethodMsg_Type
*/

//+ mmsg__setup
static PyObject *
mmsg__setup(PyMethodMsgObject *self, PyObject *callable)
{
    if (!PyCallable_Check(callable)) {
        PyErr_SetString(PyExc_TypeError, "bad internal call");
        return NULL;
    }

    /* The argument shall be a callable that takes the pointer on the BOOPSI Msg
     * and returns a PyMUICType object set with this message.
     */
    self->mmsg_PyMsg = PyObject_CallFunction(callable, "k", (ULONG)self->mmsg_Msg);
    if (NULL == self->mmsg_PyMsg)
        return NULL;

    Py_INCREF(self);
    return (PyObject *)self;
}
//-
//+ mmsg_dosuper
static PyObject *
mmsg_dosuper(PyMethodMsgObject *self)
{
    struct IClass *cl;
    Object *obj;
    Msg msg;

    msg = self->mmsg_Msg;

    if (self->mmsg_SuperCalled)
        return PyErr_Format(PyExc_RuntimeError, "SuperMethod already called for id 0x%08x", (unsigned int)msg->MethodID);

    cl = self->mmsg_Class;
    obj = self->mmsg_Object;

    DPRINT("cl: %p, obj: %p, msg: %p (MethodID: 0x%08x)\n", cl, obj, msg, msg->MethodID);
    self->mmsg_SuperCalled = TRUE; /* better to set it now */
    self->mmsg_SuperResult = DoSuperMethodA((struct IClass *)cl, obj, msg);

    if (PyErr_Occurred())
        return NULL;

    return PyLong_FromUnsignedLong(self->mmsg_SuperResult);
}
//-
//+ mmsg_getattro
static PyObject *
mmsg_getattro(PyMethodMsgObject *self, PyObject *attr)
{
    PyObject *o;

    o = PyObject_GenericGetAttr((PyObject *)self, attr); /* NR */
    if ((NULL == o) && (NULL != self->mmsg_PyMsg)) {
        PyErr_Clear();
        DPRINT("PyMsg: %p\n", self->mmsg_PyMsg);
        return PyObject_GetAttr(self->mmsg_PyMsg, attr);
    }

    return o;
}
//-

static struct PyMethodDef mmsg_methods[] = {
    {"_setup", (PyCFunction)mmsg__setup, METH_O, "PRIVATE. Don't call it."},
    {"DoSuper", (PyCFunction)mmsg_dosuper, METH_NOARGS, "Call DoSuperMethod() using IClass and Msg in this object."},
    {NULL} /* sentinel */
};

static PyTypeObject PyMethodMsgObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.MethodMsg",
    tp_basicsize    : sizeof(PyMethodMsgObject),
    tp_flags        : Py_TPFLAGS_DEFAULT,
    tp_doc          : "Method Message Objects",

    tp_new          : (newfunc)PyType_GenericNew,
    tp_getattro     : (getattrofunc)mmsg_getattro,
    tp_methods      : mmsg_methods,
};


/*******************************************************************************************
** RasterObject_Type
*/

//+ raster_dealloc
static void
raster_dealloc(PyRasterObject *self)
{
    self->rp = NULL;
    self->ob_type->tp_free((PyObject *)self);
}
//-
//+ raster_blit8
PyDoc_STRVAR(raster_blit8_doc,
"Blit8(buffer, dst_x, dst_y, src_w, src_h, src_x=0, src_y=0)\n\
\n\
Blit given RGB8 buffer on the raster.\n\
\n\
src_x, src_y: top-left corner of source rectangle to blit.\n\
src_w: source rectangle width.\n\
src_h: source rectangle height.\n\
dst_x: destination position on X-axis in the raster.\n\
dst_y: destination position on Y-axis in the raster.");

static PyObject *
raster_blit8(PyRasterObject *self, PyObject *args)
{
    char *buf;
    UWORD src_x=0, src_y=0, dst_x, dst_y, src_w, src_h;
    int buf_size;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "s#HHHH|HH:Blit8", &buf, &buf_size,
                          &dst_x, &dst_y, &src_w, &src_h, &src_x, &src_y)) /* BR */
        return NULL;

    WritePixelArray(buf, src_x, src_y, buf_size/src_h, self->rp, dst_x, dst_y, src_w, src_h, RECTFMT_RGB);

    Py_RETURN_NONE;
}
//-
//+ raster_scaled_blit8
PyDoc_STRVAR(raster_scaled_blit8_doc,
"ScaledBlit8(buffer, src_w, src_h, dst_x, dst_y, dst_w, dst_h)\n\
\n\
Blit given RGB8 buffer on the raster. If src and dst size are different,\n\
performs a scaling before blitting at given raster position.\n\
\n\
src_w: source rectangle width.\n\
src_h: source rectangle height.\n\
dst_x: destination position on X-axis in the raster.\n\
dst_y: destination position on Y-axis in the raster.\n\
dst_w: destination width.\n\
dst_h: destination height.\n\
");

static PyObject *
raster_scaled_blit8(PyRasterObject *self, PyObject *args)
{
    char *buf;
    UWORD src_w, src_h, dst_x, dst_y, dst_w, dst_h;
    int buf_size;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "s#HHHHHH:ScaledBlit8", &buf, &buf_size,
                          &src_w, &src_h, &dst_x, &dst_y, &dst_w, &dst_h)) /* BR */
        return NULL;

    ScalePixelArray(buf, src_w, src_h, buf_size/src_h, self->rp, dst_x, dst_y, dst_w, dst_h, RECTFMT_RGB);

    Py_RETURN_NONE;
}
//-
//+ raster_scroll
static PyObject *
raster_scroll(PyRasterObject *self, PyObject *args)
{
    LONG dx, dy, minx, maxx, miny, maxy;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "iiiiii:Scroll", &dx, &dy, &minx, &maxx, &miny, &maxy)) /* BR */
        return NULL;

    ScrollRaster(self->rp, dx, dy, minx, maxx, miny, maxy);

    Py_RETURN_NONE;
}
//-
//+ raster_rect
static PyObject *
raster_rect(PyRasterObject *self, PyObject *args)
{
    LONG l, t, r, b;
    UBYTE pen, fill=FALSE;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "Biiii|B:Rect", &pen, &l, &t, &r, &b, &fill)) /* BR */
        return NULL;

    SetAPen(self->rp, pen);
    if (fill)
        RectFill(self->rp, l, t, r, b);
    else {
        Move(self->rp, l, t);
        Draw(self->rp, r, t);
        Draw(self->rp, r, b);
        Draw(self->rp, l, b);
        Draw(self->rp, l, t);
    }

    Py_RETURN_NONE;
}
//-

static struct PyMethodDef raster_methods[] = {
    {"Blit8",       (PyCFunction)raster_blit8,        METH_VARARGS, raster_blit8_doc},
    {"ScaledBlit8", (PyCFunction)raster_scaled_blit8, METH_VARARGS, raster_scaled_blit8_doc},
    {"Scroll",      (PyCFunction)raster_scroll,       METH_VARARGS, NULL},
    {"Rect",        (PyCFunction)raster_rect,         METH_VARARGS, NULL},
    {NULL} /* sentinel */
};

static PyTypeObject PyRasterObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.PyRasterObject",
    tp_basicsize    : sizeof(PyRasterObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    tp_doc          : "Raster Objects",

    tp_dealloc      : (destructor)raster_dealloc,
    tp_methods      : raster_methods,
};


/*******************************************************************************************
** EventHandlerObject_Type
*/

//+ evthandler_new
static PyObject *
evthandler_new(PyTypeObject *type, PyObject *args)
{
    PyEventHandlerObject *self;

    self = (PyEventHandlerObject *)type->tp_alloc(type, 0); /* NR */
    if (NULL != self) {
        self->self = (PyObject *)self;
        return (PyObject *)self;
    }

    return NULL;
}
//-
//+ evthandler_traverse
static int
evthandler_traverse(PyEventHandlerObject *self, visitproc visit, void *arg)
{
    Py_VISIT(self->TabletTagsList);
    Py_VISIT(self->window);
    Py_VISIT(self->target);
    return 0;
}
//-
//+ evthandler_clear
static int
evthandler_clear(PyEventHandlerObject *self)
{
    if (NULL != self->window) {
        Object *mo = PyBOOPSIObject_GET_OBJECT(self->window);

        DPRINT("%s: win=%p\n", __FUNCTION__, mo);
        if (NULL != mo)
            DoMethod(mo, MUIM_Window_RemEventHandler, (ULONG)&self->handler);

    }
 
    Py_CLEAR(self->TabletTagsList);
    Py_CLEAR(self->window);
    Py_CLEAR(self->target);
    return 0;
}
//-
//+ evthandler_dealloc
static void
evthandler_dealloc(PyEventHandlerObject *self)
{
    evthandler_clear(self);
    self->ob_type->tp_free((PyObject *)self);
}
//-
//+ evthandler_install
static PyObject *
evthandler_install(PyEventHandlerObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *pyo_win, *pyo_tgt;
    static CONST_STRPTR kwlist[] = {"target", "idcmp", "flags", "prio", NULL};
    Object *win, *target;

    if (NULL != self->window) {
        PyErr_SetString(PyExc_TypeError, "Already installed handler, remove it before");
        return NULL;
    }

    self->handler.ehn_Flags = 0;
    self->handler.ehn_Priority = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!I|Hb", (char **)kwlist,
            &PyMUIObject_Type, &pyo_tgt,
            &self->handler.ehn_Events,
            &self->handler.ehn_Flags,
            &self->handler.ehn_Priority)) /* BR */
        return NULL;

    target = PyBOOPSIObject_GetObject(pyo_tgt);
    if (NULL == target)
        return NULL;

    win = _win(target);
    if (NULL == win) {
        PyErr_SetString(PyExc_SystemError, "no window found");
        return NULL;
    }

    pyo_win = (PyObject *)muiUserData(win); DPRINT("window py object: %p\n", pyo_win);
    if (!PyBOOPSIObject_IsValid(pyo_win)) {
       PyErr_SetString(PyExc_TypeError, "events handler object must be installed on MUI Window object only");
        return NULL;
    }

    self->window = pyo_win; Py_INCREF(pyo_win);
    self->target = pyo_tgt; Py_INCREF(pyo_tgt);

    self->handler.ehn_Object = target;
    self->handler.ehn_Class = OCLASS(target);

    DPRINT("install handler  %p on win %p: target=%p idcmp=%p, flags=%u, prio=%d\n",
        &self->handler, win, target,
        self->handler.ehn_Events,
        self->handler.ehn_Flags,
        self->handler.ehn_Priority);
    
    DoMethod(win, MUIM_Window_AddEventHandler, (ULONG)&self->handler);

    Py_RETURN_NONE;
}
//-
//+ evthandler_uninstall
static PyObject *
evthandler_uninstall(PyEventHandlerObject *self)
{
    Object *win;

    if (NULL == self->window) {
        PyErr_SetString(PyExc_TypeError, "Not installed handler, install it before!");
        return NULL;
    }

    win = PyBOOPSIObject_GetObject(self->window);
    if (NULL == win)
        return NULL;

    DPRINT("uninstall handler %p on win %p\n", &self->handler, win);
    DoMethod(win, MUIM_Window_RemEventHandler, (ULONG)&self->handler);

    Py_CLEAR(self->window);
    Py_CLEAR(self->target);

    Py_RETURN_NONE;
}
//-
//+ evthandler_readmsg
static PyObject *
evthandler_readmsg(PyEventHandlerObject *self, PyMethodMsgObject *msg_obj)
{
    Object *obj; /* used by _isinobject macro */
    struct MUIP_HandleEvent *msg;

    if (NULL == self->window) {
        PyErr_SetString(PyExc_TypeError, "Not installed handler, install it before!");
        return NULL;
    }

    if (!PyMethodMsgObject_CheckExact(msg_obj)) {
        PyErr_SetString(PyExc_TypeError, "readmsg argument shall the the method msg object");
        return NULL;
    }

    msg = (APTR)msg_obj->mmsg_Msg;
    obj = msg_obj->mmsg_Object;

    /* Sanity check */
    if (msg->ehn != &self->handler) {
        PyErr_SetString(PyExc_RuntimeError, "given message doesn't match to this event handler");
        return NULL;
    }

    CopyMem(msg->imsg, &self->imsg, sizeof(self->imsg));
    self->muikey = msg->muikey;

    self->inobject = _isinobject(msg->imsg->MouseX, msg->imsg->MouseY);
    self->hastablet = NULL != ((struct ExtIntuiMessage *)msg->imsg)->eim_TabletData;

    /* if tablet data, extract tag items */
    if (self->hastablet) {
        PyObject *o_tags;
        struct TagItem *tag, *tags = ((struct ExtIntuiMessage *)msg->imsg)->eim_TabletData->td_TagList;
        int error;

        if (NULL == self->TabletTagsList) {
            self->TabletTagsList = PyDict_New(); /* NR */
            if (NULL == self->TabletTagsList)
                return NULL;
        } else
            PyDict_Clear(self->TabletTagsList);

        o_tags = PyList_New(0); /* NR */
        if (NULL == o_tags)
            return 0;

        while (NULL != (tag = NextTagItem(&tags))) {
            PyObject *item = Py_BuildValue("II", tag->ti_Tag, tag->ti_Data); /* NR */

            if ((NULL == item) || (PyList_Append(o_tags, item) != 0)) {
                Py_XDECREF(item);
                Py_DECREF(o_tags);
                return 0;
            }
        }

        error = PyDict_MergeFromSeq2(self->TabletTagsList, o_tags, TRUE); /* NR */
        Py_DECREF(o_tags);
        if (error)
            return 0;

        self->tabletdata = *((struct ExtIntuiMessage *)msg->imsg)->eim_TabletData;
    } else
        memset(&self->tabletdata, 0, sizeof(self->tabletdata));

    Py_RETURN_NONE;
}
//-
//+ evthandler_get_normtablet
static PyObject *
evthandler_get_normtablet(PyEventHandlerObject *self, void *closure)
{
    if (0 == closure)
        return PyFloat_FromDouble((double)self->tabletdata.td_TabletX / self->tabletdata.td_RangeX);
    else
        return PyFloat_FromDouble((double)self->tabletdata.td_TabletY / self->tabletdata.td_RangeY);
}
//-
//+ evthandler_get_up
static PyObject *
evthandler_get_up(PyEventHandlerObject *self, void *closure)
{
    return PyBool_FromLong((self->imsg.Code & IECODE_UP_PREFIX) == IECODE_UP_PREFIX);
}
//-
//+ evthandler_get_key
static PyObject *
evthandler_get_key(PyEventHandlerObject *self, void *closure)
{
    return PyInt_FromLong(self->imsg.Code & ~IECODE_UP_PREFIX);
}
//-
//+ evthandler_get_handler
static PyObject *
evthandler_get_handler(PyEventHandlerObject *self, void *closure)
{
    return PyLong_FromVoidPtr(&self->handler);
}
//-

static PyGetSetDef evthandler_getseters[] = {
    {"handler", (getter)evthandler_get_handler, NULL, "Address of the MUI_EventHandlerNode", NULL},
    {"Up", (getter)evthandler_get_up, NULL, "True if Code has UP prefix", NULL},
    {"Key", (getter)evthandler_get_key, NULL, "IntuiMessage Code field without UP prefix if exists", NULL},
    {"td_NormTabletX", (getter)evthandler_get_normtablet, NULL, "Normalized tablet X (float [0.0, 1.0])", (APTR)0},
    {"td_NormTabletY", (getter)evthandler_get_normtablet, NULL, "Normalized tablet Y (float [0.0, 1.0])", (APTR)~0},
    {NULL} /* sentinel */
};

static PyMemberDef evthandler_members[] = {
    {"idcmp",        T_ULONG, offsetof(PyEventHandlerObject, handler.ehn_Events), RO, "IDCMP value"},
    {"muikey",       T_LONG, offsetof(PyEventHandlerObject, muikey), RO, NULL},
    {"Class",        T_ULONG, offsetof(PyEventHandlerObject, imsg.Class), RO, NULL},
    {"Code",         T_USHORT, offsetof(PyEventHandlerObject, imsg.Code), RO, NULL},
    {"Qualifier",    T_USHORT, offsetof(PyEventHandlerObject, imsg.Qualifier), RO, NULL},
    {"MouseX",       T_SHORT, offsetof(PyEventHandlerObject, imsg.MouseX), RO, NULL},
    {"MouseY",       T_SHORT, offsetof(PyEventHandlerObject, imsg.MouseY), RO, NULL},
    {"Seconds",      T_ULONG, offsetof(PyEventHandlerObject, imsg.Seconds), RO, NULL},
    {"Micros",       T_ULONG, offsetof(PyEventHandlerObject, imsg.Micros), RO, NULL},
    {"InObject",     T_BYTE, offsetof(PyEventHandlerObject, inobject), RO, NULL},
    {"ValidTD",      T_BYTE, offsetof(PyEventHandlerObject, hastablet), RO, NULL},
    {"td_TabletX",   T_ULONG, offsetof(PyEventHandlerObject, tabletdata.td_TabletX), RO, NULL},
    {"td_TabletY",   T_ULONG, offsetof(PyEventHandlerObject, tabletdata.td_TabletY), RO, NULL},
    {"td_RangeX",    T_ULONG, offsetof(PyEventHandlerObject, tabletdata.td_RangeX), RO, NULL},
    {"td_RangeY",    T_ULONG, offsetof(PyEventHandlerObject, tabletdata.td_RangeY), RO, NULL},
    {"td_XFraction", T_USHORT, offsetof(PyEventHandlerObject, tabletdata.td_XFraction), RO, NULL},
    {"td_YFraction", T_USHORT, offsetof(PyEventHandlerObject, tabletdata.td_YFraction), RO, NULL},
    {"td_Tags",      T_OBJECT, offsetof(PyEventHandlerObject, TabletTagsList), RO, NULL},

    {NULL} /* sentinel */
};

static struct PyMethodDef evthandler_methods[] = {
    {"install",   (PyCFunction)evthandler_install,   METH_VARARGS, NULL},
    {"uninstall", (PyCFunction)evthandler_uninstall, METH_NOARGS, NULL},
    {"readmsg", (PyCFunction)evthandler_readmsg, METH_O, NULL},
    {NULL} /* sentinel */
};

static PyTypeObject PyEventHandlerObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.PyEventHandlerObject",
    tp_basicsize    : sizeof(PyEventHandlerObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    tp_doc          : "Event Handler Objects",

    tp_new          : (newfunc)evthandler_new,
    tp_traverse     : (traverseproc)evthandler_traverse,
    tp_clear        : (inquiry)evthandler_clear,
    tp_dealloc      : (destructor)evthandler_dealloc,
    
    tp_members      : evthandler_members,
    tp_methods      : evthandler_methods,
    tp_getset       : evthandler_getseters,
};


/*******************************************************************************************
** CHookObject_Type
*/

//+ chook_new
static PyObject *
chook_new(PyTypeObject *type, PyObject *args)
{
    CHookObject *self;
    PyObject *v;

    self = (CHookObject *)type->tp_alloc(type, 0); /* NR */
    if (NULL != self) {
        if (PyArg_ParseTuple(args, "O", &v)) {
            DPRINT("HookObject: %p, func: %p-'%s' (callable? %s)\n", self, v, OBJ_TNAME(v), PyCallable_Check(v)?"yes":"no");

            if (PyCallable_Check(v)) {
                self->hook = &self->_hook;
                INIT_HOOK(self->hook, callpython);
                self->callable = v; Py_INCREF(v);
                self->_hook.h_Data = self;
            } else {
                ULONG x;

                if (!py2long(v, &x)) {
                    Py_CLEAR(self);
                    return NULL;
                }

                self->hook = (APTR)x;
            }

            DPRINT("Hook: %p, callable: %p\n", self->hook, self->callable);
            return (PyObject *)self;
        }

        Py_CLEAR(self);
    }

    return NULL;
}
//-
//+ chook_traverse
static int
chook_traverse(CHookObject *self, visitproc visit, void *arg)
{
    Py_VISIT(self->callable);
    return 0;
}
//-
//+ chook_clear
static int
chook_clear(CHookObject *self)
{
    Py_CLEAR(self->callable);
    return 0;
}
//-
//+ chook_dealloc
static void
chook_dealloc(CHookObject *self)
{
    DPRINT("HookObject: %p\n", self);
    chook_clear(self);
    self->ob_type->tp_free((PyObject *)self);
}
//-

static PyMemberDef chook_members[] = {
    {"address", T_ULONG, offsetof(CHookObject, hook), RO, NULL},
    {NULL} /* sentinel */
};

static PyTypeObject CHookObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster._CHook",
    tp_basicsize    : sizeof(CHookObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    tp_doc          : "_CHook Objects",

    tp_new          : (newfunc)chook_new,
    tp_traverse     : (traverseproc)chook_traverse,
    tp_clear        : (inquiry)chook_clear,
    tp_dealloc      : (destructor)chook_dealloc,

    tp_members      : chook_members,
};
 

/*******************************************************************************************
** Module Functions
**
** List of functions exported by this module reside here
*/

//+ _muimaster_mainloop
PyDoc_STRVAR(_muimaster_mainloop_doc,
"mainloop(app) -> None.\n\
\n\
Simple main loop.\n\
The loop exits when the app object received a MUIV_Application_ReturnID_Quit\n\
or by a sending a SIGBREAKF_CTRL_C to the task.\n\
\n\
Notes:\n\
 - SIGBREAKF_CTRL_C signal generates a PyExc_KeyboardInterrupt exception\n\
 - doesn't check if app really contains an application MUI object");

static PyObject *
_muimaster_mainloop(PyObject *self, PyObject *args)
{
    ULONG sigs = 0;
    PyObject *pyapp;
    Object *app;
    
    if (!PyArg_ParseTuple(args, "O!:mainloop", &PyMUIObject_Type, &pyapp))
        return NULL;

    app = PyBOOPSIObject_GetObject((PyObject *)pyapp);
    if (NULL == app)
        return NULL;

    /* This code will not check that the given object is really an Application object;
     * That should be checked by the caller!
     */

    DPRINT("Goes into mainloop...\n");
    gApp = app; Py_INCREF(pyapp);

    for (;;) {
        ULONG id;
        PyThreadState *_save;

        Py_UNBLOCK_THREADS;
        id = DoMethod(app, MUIM_Application_NewInput, (ULONG) &sigs);
        Py_BLOCK_THREADS;

        /* Exception occured or quit requested */
        if ((MUIV_Application_ReturnID_Quit == id) || PyErr_Occurred())
            break;

        if (sigs) {
            Py_UNBLOCK_THREADS;
            sigs = Wait(sigs | SIGBREAKF_CTRL_C);
            Py_BLOCK_THREADS;
        } else
            sigs = SetSignal(0, 0);

        if (sigs & SIGBREAKF_CTRL_C)
            break;
    }

    Py_DECREF(pyapp);
    gApp = NULL;

    if (sigs & SIGBREAKF_CTRL_C) {
        PyErr_SetNone(PyExc_KeyboardInterrupt);
        DPRINT("bye mainloop with Keyboard Interruption...\n");
        return NULL;
    }

    if (PyErr_Occurred()) {
        DPRINT("bye mainloop with error...\n");
        return NULL;
    }

    DPRINT("bye mainloop...\n");
    Py_RETURN_NONE;
}
//-
//+ _muimaster_getfilename
static PyObject *
_muimaster_getfilename(PyObject *self, PyObject *args)
{
    PyBOOPSIObject *pyo;
    Object *mo, *win;
    STRPTR filename, title;
    STRPTR init_drawer = NULL;
    STRPTR init_pat = NULL;
    UBYTE save = FALSE;

    if (!PyArg_ParseTuple(args, "O!s|zzb:getfilename", &PyMUIObject_Type, &pyo, &title, &init_drawer, &init_pat, &save))
        return NULL;

    mo = PyBOOPSIObject_GetObject((PyObject *)pyo);
    if (NULL == mo)
        return NULL;

    win = mo;
    get(mo, MUIA_WindowObject, &win);
    filename = getfilename(win, title, init_drawer, init_pat, save);
    if (NULL == filename)
        Py_RETURN_NONE;

    return PyString_FromString(filename);
}
//-
//+ _muimaster_setwinpointer
static PyObject *
_muimaster_setwinpointer(PyObject *self, PyObject *args)
{
    PyObject *pyo;
    Object *obj;
    struct Window *win;
    ULONG type;

    if (!PyArg_ParseTuple(args, "O!I", &PyMUIObject_Type, &pyo, &type))
        return NULL;

    obj = PyBOOPSIObject_GetObject((PyObject *)pyo);
    if (NULL != obj) {
        /* Try to obtain the system window of the given object */
        win = NULL;
        if (get(obj, MUIA_Window, &win) && (NULL != win)) {
            SetWindowPointer(win, WA_PointerType, type, TAG_DONE); 
            Py_RETURN_NONE;
        }

        PyErr_SetString(PyExc_SystemError, "No window found on this MUI object");
    }

    return NULL;
}
//-
//+ _muimaster_addclipping
static PyObject *
_muimaster_addclipping(PyObject *self, PyObject *args)
{
    PyObject *pyo;
    Object *obj;
    APTR handle;

    if (!PyArg_ParseTuple(args, "O!", &PyMUIObject_Type, &pyo))
        return NULL;

    obj = PyBOOPSIObject_GetObject((PyObject *)pyo);
    if (NULL == obj)
        return NULL;

    handle = MUI_AddClipping(muiRenderInfo(obj), _mleft(obj), _mtop(obj), _mwidth(obj), _mheight(obj));
    return PyLong_FromVoidPtr(handle);
}
//-
//+ _muimaster_removeclipping
static PyObject *
_muimaster_removeclipping(PyObject *self, PyObject *args)
{
    PyObject *pyo;
    Object *obj;
    APTR handle;

    if (!PyArg_ParseTuple(args, "O!k", &PyMUIObject_Type, &pyo, &handle))
        return NULL;

    obj = PyBOOPSIObject_GetObject((PyObject *)pyo);
    if (NULL == obj)
        return NULL;

    MUI_RemoveClipping(muiRenderInfo(obj), handle);

    Py_RETURN_NONE;
}
//-
//+ _muimaster_boopsitopython
static PyObject *
_muimaster_boopsitopython(PyObject *self, PyObject *args)
{
    ULONG value;
    Object *obj;
    PyObject *pyo;

    if (!PyArg_ParseTuple(args, "I", &value))
        return NULL;

    obj = (Object *)value;

    if (NULL != obj) {
        /* Check if the object doesn't contain a valid PyMUI object */
        pyo = (PyObject *)muiUserData(obj); DPRINT("pyo: %p\n", pyo);
        if (PyBOOPSIObject_IsValid(pyo)) {
            Py_INCREF(pyo);
            return pyo;
        }
    }

    pyo = (PyObject *)PyObject_New(PyBOOPSIObject, &PyBOOPSIObject_Type);
    if (NULL != pyo) {
        if (!PyBOOPSIObject_Initialize(pyo, obj, NULL, 0))
            Py_CLEAR(pyo);
    }

    return pyo;
}
//-
//+ _muimaster_aptr2python
static PyObject *
_muimaster_aptr2python(PyObject *self, PyObject *args)
{
    ULONG value;
    PyObject *pyo;

    if (!PyArg_ParseTuple(args, "I", &value))
        return NULL;

    pyo = (PyObject *)value;
    DPRINT("pyo = %p\n", pyo);
    if (NULL == pyo)
        Py_RETURN_NONE;

    /* Small check */
    if (!TypeOfMem(pyo))
        return PyErr_Format(PyExc_ValueError, "value '%x' is not a valid system pointer", (unsigned int)pyo);

    Py_INCREF(pyo);
    return pyo;
}
//-

/* module methods */
static PyMethodDef _muimaster_methods[] = {
    {"mainloop", _muimaster_mainloop, METH_VARARGS, _muimaster_mainloop_doc},
    {"getfilename", _muimaster_getfilename, METH_VARARGS, NULL},
    {"_setwinpointer", _muimaster_setwinpointer, METH_VARARGS, NULL},
    {"_AddClipping", _muimaster_addclipping, METH_VARARGS, NULL},
    {"_RemoveClipping", _muimaster_removeclipping, METH_VARARGS, NULL},
    {"_BOOPSI2Python", _muimaster_boopsitopython, METH_VARARGS, NULL},
    {"_APTR2Python", _muimaster_aptr2python, METH_VARARGS, NULL},
    {NULL, NULL} /* Sentinel */
};


/*
** Public Functions
*/

//+ PyMorphOS_CloseModule
void
PyMorphOS_CloseModule(void) {
    CreatedObjectNode *node;
    CreatedMCCNode *mcc_node;
    APTR next;

    DPRINT("Closing module...\n");

    gClosingModule = TRUE;

    /* Object disposing */
    ForeachNodeSafe(&gCreatedObjectList, node, next) {
        Object *app, *obj = node->n_Object;
        
        if (NULL != obj) {
            /* Zombie object? */
            if (node->n_Flags & CONF_ZOMBIE) {
                DPRINT("Zombie object [%p, node: %p]\n", obj, node);
            } else if (node->n_Flags & CONF_MUI) {
                Object *parent;

                DPRINT("Forgotten object [%p-'%s', node: %p, MCC: %p]\n",
                    obj, OCLASS(obj)->cl_ID?(char *)OCLASS(obj)->cl_ID:(char *)"<MCC>", node, node->n_MCC);

                /* Python is not perfect, PyMUI not also and user design even less :-P
                 * So an object can be here if for any reasons its dealloc function has not been called.
                 * Normally in this case, MUI should not have deleted the object and it remains valid.
                 * But...
                 */
                app = parent = NULL;
                if (get(obj, MUIA_ApplicationObject, &app) && get(obj, MUIA_Parent, &parent)) {
                    /* If Python has not deleted some objects is possible that an object
                     * is detroyed here, but if this objects has some children
                     * and these ones are destroyed after (due to the node order at creation)
                     * the parent, MUIA_Parent/MUIA_ApplicationObject return NULL! That's correct,
                     * but our delete procedure here will fails because we thing that an object without
                     * parent (and app) is a standalone object, safe to destroy ourself.
                     * That's not true as the parent object has disposed its children during its dispose!
                     *
                     * To workaround that we use the recoreded parent during a call to muiobject__cadd().
                     * This not fixing the pb if the PyMUI user doesn't design well his GUI.
                     * In this case MUI will shows an error message!
                     */
                    if (NULL == parent)
                        parent = node->n_Parent;

                    DPRINT("[%p] app=%p, parent=%p\n", obj, app, parent);

                    /* As the Python interpretor doesn't exist remove invalid Python linkage! */
                    if (NULL != node->n_MCC)
                        ((MCCData *)INST_DATA(OCLASS(obj), obj))->PythonObject = NULL;

                    /* Keep the application object disposal for later */
                    if (obj == app) {
                        DPRINT("[%p] Application => disposed later\n", obj);
                        continue;
                    }

                    /* No parent object ? */
                    if ((NULL == parent) && (NULL == app)) {
                        DPRINT("[%p] Disposing a MUI object...\n", obj);
                        MUI_DisposeObject(obj);
                        DPRINT("[%p] Disposed\n", obj);
                    } else
                        DPRINT("[%p] Has a parent!\n", obj);
                } else
                    DPRINT("[%p] Bad object!\n", obj);
            } else {
                DPRINT("[%p] Disposing a BOOPSI object ...\n", obj);
                DisposeObject(obj);
                DPRINT("[%p] Disposed\n", obj);
            }
        }

        free(REMOVE(node));
    }

    /* Second round for the applications objects */
    ForeachNodeSafe(&gCreatedObjectList, node, next) {
        Object *obj = node->n_Object;

        DPRINT("[%p] Disposing application...\n", obj);
        MUI_DisposeObject(obj);
        DPRINT("[%p] Application disposed\n", obj);

        free(node);
    }

    /* MCC disposing */
    ForeachNodeSafe(&gCreatedMCCList, mcc_node, next) {
        DPRINT("Disposing MCC node @ %p (mcc=%p-'%s')\n", mcc_node, mcc_node->n_MCC, mcc_node->n_MCC->mcc_Super->cl_ID);
        MUI_DeleteCustomClass(mcc_node->n_MCC);
        free(mcc_node);
    }

    if (NULL != CyberGfxBase) {
        DPRINT("Closing cybergfx library...\n");
        CloseLibrary(CyberGfxBase);
        CyberGfxBase = NULL;
    }

    if (NULL != LayersBase) {
        DPRINT("Closing layers library...\n");
        CloseLibrary(LayersBase);
        LayersBase = NULL;
    }
 
    if (NULL != MUIMasterBase) {
        DPRINT("Closing muimaster library...\n");
        CloseLibrary(MUIMasterBase);
        MUIMasterBase = NULL;
    }

    DPRINT("Bye\n");
}
//- PyMorphOS_CloseModule
//+ all_ins
static int
all_ins(PyObject *m) {
    INSI(m, "VLatest", (long)MUIMASTER_VLATEST);
    INSS(m, "BUILD_TIME", __TIME__);
    INSS(m, "BUILD_DATE", __DATE__);

    return 0;
}
//- all_ins

//+ INITFUNC()
PyMODINIT_FUNC
INITFUNC(void) {
    PyObject *m;

    INIT_HOOK(&OnAttrChangedHook, OnAttrChanged);
    NEWLIST(&gCreatedObjectList);
    NEWLIST(&gCreatedMCCList);

    MUIMasterBase = OpenLibrary(MUIMASTER_NAME, MUIMASTER_VLATEST);
    if (NULL == MUIMasterBase) {
        DPRINT("Can't open library %s, V%u.\n", MUIMASTER_NAME, MUIMASTER_VLATEST);
        return;
    }

    LayersBase = OpenLibrary("layers.library", 50);
    if (NULL == LayersBase) {
        DPRINT("Can't open library %s, V%u.\n", "layers.library", 50);
        return;
    }

    CyberGfxBase = OpenLibrary("cybergraphics.library", 50);
    if (NULL == CyberGfxBase) {
        DPRINT("Can't open library %s, V%u.\n", "cybergraphics.library", 50);
        return;
    }

    /* New Python types initialization */
    if (PyType_Ready(&PyRasterObject_Type) < 0) return;
    if (PyType_Ready(&PyBOOPSIObject_Type) < 0) return;
    if (PyType_Ready(&PyMUIObject_Type) < 0) return;
    if (PyType_Ready(&PyEventHandlerObject_Type) < 0) return;
    if (PyType_Ready(&CHookObject_Type) < 0) return;
    if (PyType_Ready(&PyMethodMsgObject_Type) < 0) return;

    /* Module creation/initialization */
    m = Py_InitModule3(MODNAME, _muimaster_methods, _muimaster__doc__);
    if (all_ins(m)) return;

    ADD_TYPE(m, "PyBOOPSIObject", &PyBOOPSIObject_Type);
    ADD_TYPE(m, "PyMUIObject", &PyMUIObject_Type);
    ADD_TYPE(m, "EventHandler", &PyEventHandlerObject_Type);
    ADD_TYPE(m, "_CHook", &CHookObject_Type);
    ADD_TYPE(m, "MethodMsg", &PyMethodMsgObject_Type);
}
//-

/* EOF */
