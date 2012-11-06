/******************************************************************************
Copyright (c) 2009,2010 Guillaume Roguez

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

// Dev Notes (outdated):
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

/* TODO list:
 * Sem protect the DB access.
 */

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
#include <hardware/atomic.h>
#include <graphics/rpattr.h>

#define __NOLIBBASE__ 1

#include <proto/alib.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/intuition.h>
#include <proto/utility.h>
#include <proto/muimaster.h>
#include <proto/cybergraphics.h>
#include <proto/layers.h>
#include <proto/graphics.h>
#include <proto/keymap.h>

#include <sys/param.h>

#ifdef WITH_PYCAIRO
#include <pycairo.h>
static Pycairo_CAPI_t *Pycairo_CAPI;
#endif

extern void dprintf(char*fmt, ...);
extern struct Library *IntuitionBase;
extern struct Library *DOSBase;
extern struct Library *UtilityBase;
extern struct Library *GfxBase;
extern struct Library *KeymapBase;

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
#define DPRINT(f, x...) ({ dprintf("PYMUI[%4u:%-23s] ", __LINE__, __FUNCTION__); dprintf(f ,##x); })
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

#define PyBOOPSIObject_Check(op) PyObject_TypeCheck(op, &PyBOOPSIObject_Type)
#define PyBOOPSIObject_CheckExact(op) ((op)->ob_type == &PyBOOPSIObject_Type)

#define PyMUIObject_Check(op) PyObject_TypeCheck(op, &PyMUIObject_Type)
#define PyMUIObject_CheckExact(op) ((op)->ob_type == &PyMUIObject_Type)

#define PyMethodMsgObject_CheckExact(op) ((op)->ob_type == &PyMethodMsgObject_Type)

#define PyBOOPSIObject_GET_OBJECT(o) (((PyBOOPSIObject *)(o))->bObject)
#define PyBOOPSIObject_SET_OBJECT(o, x) (((PyBOOPSIObject *)(o))->bObject = (x))
#define PyBOOPSIObject_ADD_FLAGS(o, x) (((PyBOOPSIObject *)(o))->flags |= (x))
#define PyBOOPSIObject_REM_FLAGS(o, x) (((PyBOOPSIObject *)(o))->flags &= ~(x))
#define PyBOOPSIObject_ISOWNER(o) (0 != (((PyBOOPSIObject *)(o))->flags & FLAG_OWNER))
#define PyBOOPSIObject_HAS_FLAGS(o, m) (0 != (((PyBOOPSIObject *)(o))->flags & (m)))
#define PyBOOPSIObject_OVERLOADED_DICT(o) (((PyBOOPSIObject *)(o))->overloaded_dict)

#define PyBOOPSIObject_SET_NODE(o, n) ({ \
    PyBOOPSIObject *_o = (PyBOOPSIObject *)(o); \
    ObjectNode *_n = (ObjectNode *)(n); \
    _o->node = _n; _n->obj = PyBOOPSIObject_GET_OBJECT(_o); })

#define PyBOOPSIObject_FORBID(o) ({ PyBOOPSIObject *_o = (APTR)(o); \
            PyBOOPSIObject_ADD_FLAGS(_o, FLAG_USED); \
            _o->used_cnt++; })
#define PyBOOPSIObject_PERMIT(o) ({ PyBOOPSIObject *_o = (APTR)(o); \
            if (0 == --_o->used_cnt) {                              \
                PyBOOPSIObject_REM_FLAGS(_o, FLAG_USED);            \
                if (PyBOOPSIObject_HAS_FLAGS(_o, FLAG_DISPOSE)      \
                    && PyBOOPSIObject_DisposeObject(_o))            \
                    PyErr_Clear();                                  \
            } })

#ifdef WITH_PYCAIRO
#define CHECK_FOR_PYCAIRO \
    if (NULL == Pycairo_CAPI) return PyErr_Format(PyExc_ImportError, "No PyCairo module found");
#endif

#define _between(a,x,b) ((x)>=(a) && (x)<=(b))
#define _isinobject(x,y) (_between(_mleft(obj),(x),_mright(obj)) && _between(_mtop(obj),(y),_mbottom(obj)))

#define ID_BREAK 0xABADDEAD
#define FLAG_OWNER (1<<0) /* bObject has been created by the PyObject */
#define FLAG_DISPOSE (1<<1) /* The bObject shall be disposed when operator is done */
#define FLAG_USED (1<<2) /* The bObject can't be explicitly disposed when set */

#define NODE_FLAG_MUI (1<<0)

enum {
    PYMUI_DATA_MLEFT  = 0,
    PYMUI_DATA_MRIGHT,
    PYMUI_DATA_MTOP,
    PYMUI_DATA_MBOTTOM,
    PYMUI_DATA_MWIDTH,
    PYMUI_DATA_MHEIGHT
};


/*
** Private Types and Structures
*/

typedef struct ObjectNode_STRUCT {
    struct MinNode node;
    Object *       obj;
    LONG           flags;
} ObjectNode;

typedef struct PyRasterObject_STRUCT {
    PyObject_HEAD

    struct RastPort *rp;
} PyRasterObject;

typedef struct PyBOOPSIObject_STRUCT {
    PyObject_HEAD
    Object *       bObject;
    ObjectNode *   node;
    ULONG          flags;
    ULONG          used_cnt;
    PyObject *     wreflist;
    PyObject *     overloaded_dict;
} PyBOOPSIObject;

typedef struct PyMUIObject_STRUCT {
    PyBOOPSIObject    base;
    PyRasterObject *  raster;    /* cached value, /!\ not always valid */
#ifdef WITH_PYCAIRO
    APTR              cairo_data_pyobj;
    APTR              cairo_data;
    ULONG             cairo_surface_width;
    ULONG             cairo_surface_height;
    ULONG             cairo_surface_stride;
    cairo_rectangle_int_t cairo_paint_area;
    cairo_surface_t * cairo_surface;
    cairo_t *         cairo_context;
    PyObject *        pycairo_obj;
#endif
} PyMUIObject;

typedef struct CHookObject_STRUCT {
    PyObject_HEAD

    struct Hook * hook;
    struct Hook   _hook;
    PyObject *    callable;
} CHookObject;

typedef struct MCCData_STRUCT {
    ULONG dummy;
} MCCData;

typedef struct MCCNode_STRUCT {
    struct MinNode           node;
    struct MUI_CustomClass * mcc;
} MCCNode;

typedef struct PyMethodMsgObject_STRUCT {
    PyObject_HEAD

    PyObject *      mmsg_PyMsg;
    struct IClass * mmsg_Class;
    Object *        mmsg_Object;
    Msg             mmsg_Msg;
    BOOL            mmsg_SuperCalled;
    ULONG           mmsg_SuperResult;
} PyMethodMsgObject;

typedef struct PyEventHandlerObject_STRUCT {
    PyObject_HEAD

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


/*
** Private Variables
*/

struct Library *MUIMasterBase;
struct Library *CyberGfxBase;
struct Library *LayersBase;

static PyTypeObject PyBOOPSIObject_Type;
static PyTypeObject PyMUIObject_Type;
static PyTypeObject CHookObject_Type;
static PyTypeObject PyMethodMsgObject_Type;
static PyTypeObject PyEventHandlerObject_Type;
static PyTypeObject PyRasterObject_Type;

static Object *gApp = NULL; /* Non-NULL if mainloop is running */
static PyObject *gBOOPSI_Objects_Dict = NULL;
static struct MinList gObjectList;
static struct MinList gMCCList;
static struct MinList gToDisposeList;
static struct Hook OnAttrChangedHook;
static APTR gMemPool;


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

/**
 * Python-BOOPSI relations database.
 *
 * Purpose of this DB is to give a way to retrieve which Python objet handles
 * a BOOPSI objet by giving this last.
 * So at each instant, one BOOPSI object is always linked to only one Python object.
 * But at two different moments this Python object can be different.
 * The Python object reference itself is not saved, but only a weak reference of it.
 * In this way the user needs to keep valid the object if it want to save its attributes.
 */

//+ objdb_add
static int objdb_add(Object *bObj, PyObject *pObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj); /* NR */
    PyObject *wref = PyWeakref_NewRef(pObj, NULL); /* NR */
    int res;

    /* BOOPSI -> Python relation */
    DPRINT("bObj: %p => key: %p, pObj: %p => wref: %p\n", bObj, key, pObj, wref);
    if ((NULL != key) && (NULL != wref)) {
        res = PyDict_SetItem(gBOOPSI_Objects_Dict, key, wref);
        DPRINT("PyDict_SetItem() = %d\n", res);
    } else {
        DPRINT("Error: %p\n", PyErr_Occurred());
        res = -1;
    }

    Py_XDECREF(key);
    Py_XDECREF(wref);

    return res;
}
//-
//+ objdb_remove
static void objdb_remove(Object *bObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj); /* NR */

    if (!PyDict_DelItem(gBOOPSI_Objects_Dict, key))
        DPRINT("Removed entry: bObj=%p\n", bObj);
    Py_XDECREF(key);
    //PyErr_Clear();
}
//-
//+ objdb_get
static PyObject *objdb_get(Object *bObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj);
    PyObject *wref, *pyo;

    wref = PyDict_GetItem(gBOOPSI_Objects_Dict, key); /* BR */
    DPRINT("bObj: %p => wref: %p\n", bObj, wref);
    Py_XDECREF(key);

    if (NULL == wref)
        return NULL;

    pyo = PyWeakref_GET_OBJECT(wref); /* BR */
    DPRINT("pyo: %p\n", pyo);

    if (Py_None == pyo)
        return NULL;

    return pyo;
}
//-

/*====================================================================*/

//+ dispose_node
static void dispose_node(PyBOOPSIObject *pObj)
{
    ObjectNode *node = pObj->node;

    pObj->node = NULL;
    FreeMem(REMOVE(node), sizeof(*node));
}
//-
//+ loose
static void loose(PyBOOPSIObject *pObj)
{
    if (PyBOOPSIObject_ISOWNER(pObj)) {
        PyBOOPSIObject_REM_FLAGS(pObj, FLAG_OWNER);

        /* really loose it! */
        dispose_node(pObj);

        DPRINT("PyObj %p-'%s' flags: $%08x\n", pObj, OBJ_TNAME(pObj), pObj->flags);
    }
}
//-
//+ PyBOOPSIObject_GetObject
static Object *
PyBOOPSIObject_GetObject(PyBOOPSIObject *pyo)
{
    Object *bo = PyBOOPSIObject_GET_OBJECT(pyo);

    if (NULL != bo)
        return bo;

    PyErr_SetString(PyExc_TypeError, "no BOOPSI object associated");
    return NULL;
}
//-
//+ PyBOOPSIObject_DisposeObject
// WARNING: this function doesn't check USED flag.
static int
PyBOOPSIObject_DisposeObject(PyBOOPSIObject *pObj)
{
    Object *bObj;
    PyObject *ptype = NULL, *pvalue, *ptb, *err;
    int res;

    err = PyErr_Occurred();
    if (NULL != err)
        PyErr_Fetch(&ptype, &pvalue, &ptb);

    bObj = PyBOOPSIObject_GET_OBJECT(pObj);
    if (NULL == bObj) {
        PyErr_SetString(PyExc_TypeError, "No valid BOOPSI object found");
        res = -1;
        goto bye;
    }

    if (PyBOOPSIObject_HAS_FLAGS(pObj, FLAG_OWNER|FLAG_DISPOSE)) {
        /* In mainloop ? */
        if (NULL != gApp) {
            ObjectNode *node;

            /* don't dispose BOOPSI objects if we're inside the MUIM_Application_NewInput.
             * Put the object in a dispose list, and ask to exit the method to flush the
             * list outside the method.
             */

            node = AllocMem(sizeof(*node), MEMF_PUBLIC | MEMF_CLEAR | MEMF_SEM_PROTECTED);
            if (NULL != node) {
                node->obj = bObj;
                node->flags = PyMUIObject_Check(pObj) ? NODE_FLAG_MUI:0;
                ADDTAIL(&gToDisposeList, node);
                DPRINT("break mainloop\n");
                DoMethod(gApp, MUIM_Application_ReturnID, ID_BREAK);
                DPRINT("break mainloop asked\n");
            } else
                DPRINT("AllocMem(node) failed, oups!\n");
        } else {
            /* BOOPSI/MUI destroy */
            DPRINT("Before DisposeObject(%p) (%p-'%s')\n", bObj, pObj, OBJ_TNAME(pObj));
            if (PyMUIObject_Check(pObj))
                MUI_DisposeObject(bObj);
            else
                DisposeObject(bObj);
            DPRINT("After DisposeObject(%p) (%p-'%s')\n", bObj, pObj, OBJ_TNAME(pObj));
        }

        /* Now delete the attached node */
        if (NULL != pObj->node) /* checked because the OWNER flag may have beem forced */
            dispose_node(pObj);
    } else
        DPRINT("BOOPSI object not disposed (not owner)\n");

    if (bObj == gApp)
        gApp = NULL;

    if (PyMUIObject_Check(pObj))
        Py_CLEAR(((PyMUIObject *)pObj)->raster);

    /* remove BOOPSI object reference from the objects db */
    objdb_remove(bObj);
    PyErr_Clear();

    PyBOOPSIObject_SET_OBJECT(pObj, NULL);
    res = 0;

bye:
    if (NULL != ptype) {
        err = PyErr_Occurred();
        if (NULL != err)
            PyErr_WriteUnraisable(err);

        PyErr_Restore(ptype, pvalue, ptb);
    }

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

    /* A Hook can be called by MUI even when Python interpreter is not available anymore */
    if (!Py_IsInitialized()) {
        dprintf("Warning: PyMUI Hook called without Python initialized.");
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
//+ OnAttrChanged
static void
OnAttrChanged(struct Hook *hook, Object *mo, ULONG *args)
{
    PyObject **wref_storage = (PyObject **)args[0];
    PyObject *pyo;
    PyGILState_STATE gstate;
    ULONG attr = args[1];

    /* 1 - Atttribute value change hook may be called during the module cleanup.
     * 2 - Source python object may be destroyed and/or a previous call
     *     has destroyed the wref object also.
     */
    if (!Py_IsInitialized() || (NULL == *wref_storage))
        return;

    gstate = PyGILState_Ensure();

    /* Don't try to execute python code if we are already in exception */
    if (NULL == PyErr_Occurred())
    {
        /* Is source object valid ? */
        pyo = PyWeakref_GET_OBJECT(*wref_storage); /* BR */
        if (Py_None != pyo)
        {
            PyObject *res;
            ULONG v = args[2];

            DPRINT("{%#lx} pyo=%p-'%s', MUI=%p, value=(%ld, %lu, $%X)\n",
                   attr, pyo, OBJ_TNAME_SAFE(pyo), mo, v, v, (APTR)v);

            Py_INCREF(pyo);

            res = PyObject_CallMethod(pyo, "_notify_cb", "III", attr, v, ~v); /* NR */
            DPRINT("PyObject_CallMethod() resulted with value %p-%s (err=%p)\n", res, OBJ_TNAME_SAFE(res), PyErr_Occurred());

            if (PyErr_Occurred() && (NULL != gApp))
                DoMethod(gApp, MUIM_Application_ReturnID, ID_BREAK);

            Py_XDECREF(res);
            Py_DECREF(pyo);
        }
        else
        {
            /* destroy the weakref and NULLify the pointer (see point 2 on the function first comments) */
            DPRINT("Dead python object for MUI obj %p, attribute $%08x\n", mo, attr);
            Py_CLEAR(*wref_storage);

            /* XXX: can I remove the notification ? */
        }
    }

    PyGILState_Release(gstate);
}
//-
//+ PyMethodMsg_New
static PyMethodMsgObject *
PyMethodMsg_New(struct IClass *cl, Object *obj, Msg msg)
{
    PyMethodMsgObject *self;

    self = PyObject_GC_New(PyMethodMsgObject, &PyMethodMsgObject_Type); /* NR */
    if (NULL != self) {
        self->mmsg_PyMsg       = NULL;
        self->mmsg_Class       = cl;
        self->mmsg_Object      = obj;
        self->mmsg_Msg         = msg;
        self->mmsg_SuperCalled = FALSE;
    }

    return self;
}
//-

//+ IntuiMsgFunc
static void
IntuiMsgFunc(struct Hook *hook, struct FileRequester *req, struct IntuiMessage *imsg)
{
    /* fr_UserData is Application, and its python proxy is already protected against
     * Disposing. So I don't protect it using FORBID/PERMIT pair here.
     */
    if (IDCMP_REFRESHWINDOW == imsg->Class)
        DoMethod(req->fr_UserData, MUIM_Application_CheckRefresh);
}
//-
//+ getfilename
/* Stolen from MUI psi.c demo */
LONG
getfilename(STRPTR **results, Object *win, STRPTR title, STRPTR init_drawer, STRPTR init_pat,
            BOOL save, BOOL multiple)
{
    struct FileRequester *req;
    struct Window *w = NULL;
    static LONG left=-1,top=-1,width=-1,height=-1;
    Object *app = NULL;
    LONG res=0;
    static const struct Hook IntuiMsgHook;

    INIT_HOOK(&IntuiMsgHook, IntuiMsgFunc)

    get(win, MUIA_ApplicationObject, &app);
    if (NULL != app)
    {
        get(win, MUIA_Window_Window, &w);
        if (NULL != win)
        {
            if (-1 == left)
            {
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
                                          //ASLFR_InitialLeftEdge, left,
                                          //ASLFR_InitialTopEdge , top,
                                          //ASLFR_InitialWidth   , width,
                                          //ASLFR_InitialHeight  , height,
                                          ASLFR_InitialDrawer  , (ULONG)init_drawer,
                                          ASLFR_InitialPattern , (ULONG)init_pat,
                                          ASLFR_DoSaveMode     , save,
                                          ASLFR_DoPatterns     , TRUE,
                                          ASLFR_RejectIcons    , TRUE,
                                          ASLFR_UserData       , (ULONG)app,
                                          ASLFR_IntuiMsgFunc   , (ULONG)&IntuiMsgHook,
                                          ASLFR_DoMultiSelect  , multiple,
                                          TAG_DONE);
            if (NULL != req)
            {
                set(app, MUIA_Application_Sleep, TRUE);

                if (MUI_AslRequestTags(req, TAG_DONE))
                {
                    if (multiple && (req->fr_NumArgs > 0))
                    {
                        int i;

                        *results = AllocVec(sizeof(STRPTR) * req->fr_NumArgs,
                                            MEMF_PUBLIC|MEMF_SEM_PROTECTED);
                        if (NULL != *results)
                        {
                            for (i=0; i < req->fr_NumArgs; i++)
                            {
                                BYTE *name = req->fr_ArgList[i].wa_Name;

                                if (NULL != name)
                                {
                                    ULONG size = strlen(req->fr_Drawer) + strlen(name) + 2;
                                    STRPTR str = AllocVec(size, MEMF_PUBLIC|MEMF_SEM_PROTECTED);

                                    if (NULL != str)
                                    {
                                        strncpy(str, req->fr_Drawer, size);
                                        AddPart(str, name, size);
                                        (*results)[i] = str;
                                        res++;
                                    }
                                    else
                                        DPRINT("AllocVec() failed for string copy\n");
                                }
                            }

                            if (0 == res)
                                FreeVec(*results);
                        }
                        else
                            DPRINT("AllocVec() failed for %lu strings\n", req->fr_NumArgs);
                    }
                    else
                    {
                        if (NULL != req->fr_File)
                        {
                            *results = AllocVec(sizeof(STRPTR), MEMF_PUBLIC|MEMF_SEM_PROTECTED);
                            if (NULL != *results)
                            {
                                ULONG size = strlen(req->fr_File) + strlen(req->fr_Drawer) + 2;
                                STRPTR str = AllocVec(size, MEMF_PUBLIC|MEMF_SEM_PROTECTED);

                                if (NULL != str)
                                {
                                    strncpy(str, req->fr_Drawer, size);
                                    AddPart(str, req->fr_File, size);
                                    (*results)[0] = str;
                                    res = 1;
                                }
                                else
                                {
                                    DPRINT("AllocVec() failed for string copy\n");
                                    FreeVec(*results);
                                }
                            }
                            else
                                DPRINT("AllocVec() failed for %lu strings\n", req->fr_NumArgs);
                        }
                    }

                    left   = req->fr_LeftEdge;
                    top    = req->fr_TopEdge;
                    width  = req->fr_Width;
                    height = req->fr_Height;
                }

                MUI_FreeAslRequest(req);
                set(app, MUIA_Application_Sleep, FALSE);
            } else
                PyErr_SetString(PyExc_SystemError, "MUI_AllocAslRequestTags() failed");
        } else
             PyErr_Format(PyExc_SystemError, "no Window for win obj %p", win);
    } else
         PyErr_Format(PyExc_SystemError, "no app for win obj %p", win);

    return res;
}
//-

#ifdef WITH_PYCAIRO
//+ blit_cairo_surface
void blit_cairo_surface(PyMUIObject *pyo, Object *mo)
{
    ULONG doublebuffer = FALSE;
    struct Rectangle r;

    DPRINT("MuiBounds: (%d, %d, %d, %d), ", _mleft(mo), _mright(mo), _mtop(mo), _mbottom(mo));

    if (get(mo, MUIA_DoubleBuffer, &doublebuffer) && !doublebuffer)
    {
        /* Ask for the current drawing area to refresh */
        GetRPAttrs(_rp(mo), RPTAG_DrawBounds, (ULONG)&r, TAG_DONE);
        DPRINT("SysBounds: (%d, %d, %d, %d), ", r.MinX, r.MaxX, r.MinY, r.MaxY);

        if (r.MinX <= r.MaxX)
        {
            /* Clip to the object area and translate to object origin */
            r.MinX = MAX(r.MinX, _mleft(mo))   - _mleft(mo);
            r.MinY = MAX(r.MinY, _mtop(mo))    - _mtop(mo);
            r.MaxX = MIN(r.MaxX, _mright(mo))  - _mleft(mo);
            r.MaxY = MIN(r.MaxY, _mbottom(mo)) - _mtop(mo);
        }
        else
        {
            /* No system clip, use the object area */
            r.MinX = 0;
            r.MinY = 0;
            r.MaxX = _mright(mo)-_mleft(mo);
            r.MaxY = _mbottom(mo)-_mtop(mo);
        }
    }
    else
    {
        /* Use the object area */
        r.MinX = 0;
        r.MinY = 0;
        r.MaxX = _mright(mo)-_mleft(mo);
        r.MaxY = _mbottom(mo)-_mtop(mo);
    }

    DPRINT("(%d, %d, %d, %d), ", r.MinX, r.MaxX, r.MinY, r.MaxY);

    if ((r.MinX > r.MaxX) || (r.MinY > r.MaxY))
        return;

    /* Clip to the user requested area */
    r.MinX = MAX(r.MinX, pyo->cairo_paint_area.x);
    r.MinY = MAX(r.MinY, pyo->cairo_paint_area.y);
    r.MaxX = MIN(r.MaxX, pyo->cairo_paint_area.x+pyo->cairo_paint_area.width-1);
    r.MaxY = MIN(r.MaxY, pyo->cairo_paint_area.y+pyo->cairo_paint_area.height-1);

    DPRINT("FinalBounds: (%d, %d, %d, %d)\n", r.MinX, r.MaxX, r.MinY, r.MaxY);

    /* Sanity checks */
    if ((r.MinX > r.MaxX) || (r.MinY > r.MaxY))
        return;

    cairo_surface_flush(pyo->cairo_surface);

#if 0
    WritePixelArrayAlpha(pyo->cairo_data, r.MinX, r.MinY, pyo->cairo_surface_stride,
                         _rp(mo), _mleft(mo)+r.MinX, _mtop(mo)+r.MinY,
                         r.MaxX-r.MinX+1, r.MaxY-r.MinY+1, 0xffffffff);
#else
    WritePixelArray(pyo->cairo_data, r.MinX, r.MinY, pyo->cairo_surface_stride,
                    _rp(mo), _mleft(mo)+r.MinX, _mtop(mo)+r.MinY,
                    r.MaxX-r.MinX+1, r.MaxY-r.MinY+1, RECTFMT_ARGB);
#endif
}
//-
#endif

/*******************************************************************************************
** MCC MUI Object
*/

//+ mCheckPython
static ULONG
mCheckPython(struct IClass *cl, Object *obj, Msg msg)
{
    PyGILState_STATE gstate;
    PyObject *pyo, *erro;
    ULONG result;
    BOOL callsuper;

    callsuper = TRUE;
    result = 0;

    gstate = PyGILState_Ensure();

    erro = PyErr_Occurred();
    if (NULL == erro)
    {
        /* existing a python object for this MUI object ? */
        pyo = objdb_get(obj); /* BR */
        DPRINT("pyo: %p-'%s', MID=$%08x\n", pyo, OBJ_TNAME_SAFE(pyo), msg->MethodID);
        if (NULL != pyo)
        {
            PyObject *overloaded_dict;

            Py_INCREF(pyo);

            overloaded_dict = PyBOOPSIObject_OVERLOADED_DICT(pyo);
            if (NULL != overloaded_dict)
            {
                Py_INCREF(overloaded_dict);

                PyObject *key = PyLong_FromUnsignedLong(msg->MethodID); /* NR */
                if (NULL != key)
                {
                    PyObject *value = PyDict_GetItem(overloaded_dict, key); /* BR */

                    Py_DECREF(key);

                    if (NULL != value)
                    {
                        PyMethodMsgObject *msg_obj = PyMethodMsg_New(cl, obj, msg); /* NR */
                        if (NULL != msg_obj)
                        {
                            PyObject *o;

                            DPRINT("pyo=%p-%s (MID: 0x%08x, callable: %p, MethodMsg: %p)\n",
                                   pyo, OBJ_TNAME(pyo), msg->MethodID, value, msg_obj);

                            Py_INCREF(value);
                            o = PyObject_CallFunction(value, "OO", pyo, msg_obj);
                            DPRINT("result: %p-%s\n", o, OBJ_TNAME_SAFE(o));
                            Py_DECREF(value);

                            /* No Python errors */
                            if (NULL != o)
                            {
                                py2long(o, &result);
                                Py_DECREF(o);

                                /* let the python code decide if super needs to be called or not */
                                callsuper = FALSE;

#ifdef WITH_PYCAIRO
                                /* Handle cairo surface during draw method */
                                if ((MUIM_Draw == msg->MethodID) &&
                                    (((struct MUIP_Draw *)msg)->flags & MADF_DRAWOBJECT) &&
                                    PyMUIObject_Check(pyo) && (NULL != ((PyMUIObject *)pyo)->pycairo_obj))
                                {
                                    PyMUIObject *muio = (PyMUIObject *)pyo;

                                    /* Delete cairo objects if object size has changed */
                                    if ((muio->cairo_surface_width != _mwidth(obj)) ||
                                        (muio->cairo_surface_height != _mheight(obj)))
                                    {
                                        Py_CLEAR(muio->pycairo_obj);
                                        Py_CLEAR(muio->cairo_data_pyobj);
                                    }
                                    else /* Blit it on object rast port */
                                        blit_cairo_surface((PyMUIObject *)pyo, obj);
                                }
#endif
                            }
                            else if (msg_obj->mmsg_SuperCalled)
                            {
                                callsuper = FALSE;
                                result = msg_obj->mmsg_SuperResult;
                            } /* else callsuper = TRUE */
                            
                            Py_DECREF(msg_obj);
                        }
                    }
                }

                Py_DECREF(overloaded_dict);
            }

            Py_DECREF(pyo);
        }
        else
            DPRINT("No python object for MUI obj %p (method $%08x)\n", obj, msg->MethodID);

        erro = PyErr_Occurred();
    }

    /* Need to pass the msg to the super ? */
    if (callsuper)
    {
        PyObject *type, *value, *tb;

        DPRINT("DoSuper(cl=%p, obj=%p, msg=%p)...\n", cl, obj, msg);

        /* Save/restore exception if needed */
        if (erro) PyErr_Fetch(&type, &value, &tb);

        Py_BEGIN_ALLOW_THREADS
        result = DoSuperMethodA(cl, obj, msg);
        Py_END_ALLOW_THREADS

        if (erro) PyErr_Restore(type, value, tb);
    }

    PyGILState_Release(gstate);

    return result;
}
//-
//+ MCC Dispatcher
DISPATCHER(mcc)
{
    ULONG result;

    DPRINT("meth: %08x %s\n", msg->MethodID, OCLASS(obj)->cl_ID);

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

        default:
            if (Py_IsInitialized())
                result = mCheckPython(cl, obj, (APTR)msg);
            else
                result = DoSuperMethodA(cl, obj, msg);
    }

    DPRINT("meth: %08x result: %08x\n", msg->MethodID, result);
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
        Object *bObj = NULL;

        if (PyArg_ParseTuple(args, "|I", &bObj)) {
            PyBOOPSIObject_SET_OBJECT(self, bObj);
            self->flags = 0;
            self->used_cnt = 0;
            self->node = NULL;
            self->wreflist = NULL;
            self->overloaded_dict = NULL;
        }
    }

    return (PyObject *)self;
}
//-
//+ boopsi_traverse
static int
boopsi_traverse(PyBOOPSIObject *self, visitproc visit, void *arg)
{
    Py_VISIT(self->overloaded_dict);
    return 0;
}
//-
//+ boopsi_clear
static int
boopsi_clear(PyBOOPSIObject *self)
{
    Py_CLEAR(self->overloaded_dict);
    return 0;
}
//-
//+ boopsi_dealloc
static void
boopsi_dealloc(PyBOOPSIObject *self)
{
    DPRINT("self=%p-'%s', bObj=%p\n", self, OBJ_TNAME_SAFE(self), PyBOOPSIObject_GET_OBJECT(self));

    if (NULL != PyBOOPSIObject_GET_OBJECT(self))
        PyBOOPSIObject_DisposeObject(self);

    boopsi_clear(self);

    if (NULL != self->wreflist)
        PyObject_ClearWeakRefs((PyObject *)self);

    ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
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
//+ boopsi__dispose
PyDoc_STRVAR(boopsi__dispose_doc,
"_dispose() -> int\n\
\n\
This method force the BOOPSI object dispose.\n\
If this method is called when the object is in-use (set/get/do,...)\n\
the BOOPSI object is not disposed immediatly, but after the use.\n\
Use it only if you know what you are doing!\n\
This object may be disposed elsewhere, not neccessary by you your code...");

static PyObject *
boopsi__dispose(PyBOOPSIObject *self)
{
    Object *bObj = PyBOOPSIObject_GET_OBJECT(self);
    DPRINT("bObj %p-'%s'\n", bObj, OBJ_TNAME(self));
    if (NULL != bObj) {
        PyBOOPSIObject_ADD_FLAGS(self, FLAG_DISPOSE);

        if (!PyBOOPSIObject_HAS_FLAGS(self, FLAG_USED)) {
            PyBOOPSIObject_DisposeObject(self);
            PyErr_Clear();
        } else
            DPRINT("bObj %p-'%s' is in use, DISPOSE flags set\n", bObj, OBJ_TNAME(self));
    }

    Py_RETURN_NONE;
}
//-
//+ boopsi__loosed
PyDoc_STRVAR(boopsi__loosed_doc,
"_loosed(object) -> int\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__loosed(PyBOOPSIObject *self)
{
    Object *bObj = PyBOOPSIObject_GetObject(self);

    if (NULL == bObj)
        return NULL;

    loose(self);

    Py_RETURN_NONE;
}
//-
//+ boopsi__addchild
PyDoc_STRVAR(boopsi__addchild_doc,
"_addchild(object) -> int\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__addchild(PyBOOPSIObject *self, PyObject *args)
{
    PyObject *ret;
    PyBOOPSIObject *pychild;
    Object *obj, *child;
    int lock = FALSE;

    obj = PyBOOPSIObject_GetObject(self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "O!|i", &PyBOOPSIObject_Type, &pychild, &lock)) /* BR */
        return NULL;

    /* Warning: no reference kept on arg object after return! */
    child = PyBOOPSIObject_GetObject(pychild);
    if (NULL == child)
        return NULL;

    /* Automatic OWNER flag loosing */
    loose(pychild);

    ret = NULL;
    PyBOOPSIObject_FORBID(self);

    if (lock) {
        DPRINT("Lock\n");

        /* This call can execute python code and cause exception */
        DoMethod(obj, MUIM_Group_InitChange);
        if (PyErr_Occurred())
            goto bye;
    }

    DPRINT("OM_ADDMEMBER: parent=%p, child=%p\n", obj, child);
    ret = PyInt_FromLong(DoMethod(obj, OM_ADDMEMBER, (ULONG)child));

    if (lock) {
        PyObject *ptype = NULL, *pvalue, *ptb;

        DPRINT("Unlock\n");

        if (NULL != PyErr_Occurred())
            PyErr_Fetch(&ptype, &pvalue, &ptb);

        /* This call can execute python code and cause exception */
        DoMethod(obj, MUIM_Group_ExitChange);

        if (NULL != ptype) {
            PyObject *err = PyErr_Occurred();

            if (NULL != err)
                PyErr_WriteUnraisable(err);

            PyErr_Restore(ptype, pvalue, ptb);
        }
    }

bye:
    PyBOOPSIObject_PERMIT(self);
    if (PyErr_Occurred())
        return NULL;

    return ret;
}
//-
//+ boopsi__remchild
PyDoc_STRVAR(boopsi__remchild_doc,
"_remchild(object) -> int\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__remchild(PyBOOPSIObject *self, PyObject *args)
{
    PyObject *ret, *pychild;
    Object *obj, *child;
    int lock = FALSE;

    obj = PyBOOPSIObject_GetObject(self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "O!|i", &PyBOOPSIObject_Type, &pychild, &lock)) /* BR */
        return NULL;

    /* Warning: no reference kept on arg object after return! */
    child = PyBOOPSIObject_GetObject((PyBOOPSIObject *)pychild);
    if (NULL == child)
        return NULL;

    ret = NULL;
    PyBOOPSIObject_FORBID(self);

    if (lock) {
        DPRINT("Lock\n");

        /* This call can execute python code and cause exception */
        DoMethod(obj, MUIM_Group_InitChange);
        if (PyErr_Occurred())
            goto bye;
    }

    DPRINT("OM_REMMEMBER: parent=%p, obj=%p\n", obj, child);
    ret = PyInt_FromLong(DoMethod(obj, OM_REMMEMBER, (ULONG)child));

    /* Note: object is not owned anymore!
     * So user should re-attach it immediately or dispose it
     */

    if (lock) {
        PyObject *ptype = NULL, *pvalue, *ptb;

        DPRINT("Unlock\n");

        if (NULL != PyErr_Occurred())
            PyErr_Fetch(&ptype, &pvalue, &ptb);

        /* This call can execute python code and cause exception */
        DoMethod(obj, MUIM_Group_ExitChange);

        if (NULL != ptype) {
            PyObject *err = PyErr_Occurred();

            if (NULL != err)
                PyErr_WriteUnraisable(err);

            PyErr_Restore(ptype, pvalue, ptb);
        }
    }

bye:
    PyBOOPSIObject_PERMIT(self);

    if (PyErr_Occurred())
        return NULL;

    return ret;
}
//-
//+ boopsi__create
PyDoc_STRVAR(boopsi__create_doc,
"_create(object) -> int\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__create(PyBOOPSIObject *self, PyObject *args)
{
    UBYTE *classid;
    PyObject *err=NULL, *fast, *params, *overloaded_dict;
    struct MUI_CustomClass *mcc=NULL;
    struct TagItem *tags;
    Object *bObj;
    ObjectNode *node;
    BOOL isMUI;
    ULONG n;

    /* Protect againts doubles */
    if (NULL != PyBOOPSIObject_GET_OBJECT(self))
    {
        PyErr_SetString(PyExc_RuntimeError, "Already created BOOPSI Object");
        return NULL;
    }

    params = overloaded_dict = NULL;
    if (!PyArg_ParseTuple(args, "s|OO:PyBOOPSIObject", &classid, &params, &overloaded_dict)) /* BR */
        return NULL;

    DPRINT("ClassID: '%s', isMCC: %d\n", classid, NULL!=overloaded_dict);

    isMUI = PyMUIObject_Check(self);
    if (!isMUI && (NULL != overloaded_dict))
    {
        PyErr_SetString(PyExc_TypeError, "MCC feature requested on a non-MUI object");
        return NULL;
    }

    /* Parse params sequence and convert it into tagitem's */
    fast = PySequence_Fast(params, "object tags shall be convertible into tuple or list"); /* NR */
    if (NULL == fast)
        return NULL;

    n = PySequence_Fast_GET_SIZE(fast);
    if (n > 0)
    {
        PyObject **tuples = PySequence_Fast_ITEMS(fast);
        ULONG i;

        tags = PyMem_Malloc(sizeof(struct TagItem) * (n+1));
        if (NULL == tags)
        {
            Py_DECREF(fast);
            return PyErr_NoMemory();
        }

        for (i=0; i < n; i++)
        {
            PyObject *tag_id = PyTuple_GetItem(tuples[i], 0);
            PyObject *tag_value = PyTuple_GetItem(tuples[i], 1);

            if ((NULL == tag_id) || (NULL == tag_value))
                break;

            tags[i].ti_Tag = PyLong_AsUnsignedLongMask(tag_id);
            py2long(tag_value, &(tags[i].ti_Data));

            if (PyErr_Occurred())
                break;

            DPRINT("#  args[%u]: %d, %u, 0x%08x\n", i, (LONG)tags[i].ti_Data, (ULONG)tags[i].ti_Data, tags[i].ti_Data);
        }

        if (PyErr_Occurred())
        {
            Py_DECREF(fast);
            PyMem_Free(tags);
            return NULL;
        }

        tags[n].ti_Tag = TAG_DONE;

        Py_DECREF(fast);
    }
    else
        tags = NULL;
    DPRINT("tags: %p (%lu)\n", tags, n);

    /* Allocated a note to save the object reference.
     * It will be used at module cleanup to flush BOOPSI/MUI.
     * Note: PyMem_xxx() functions are not used here as the python context
     * is not valid during this cleanup stage.
     */
    node = AllocMem(sizeof(ObjectNode), MEMF_PUBLIC | MEMF_CLEAR | MEMF_SEM_PROTECTED);
    if (NULL == node)
    {
        err = PyErr_NoMemory();
        goto bye_err;
    }

    DPRINT("Node created @ %p\n", node);

    /* Need to create a new MCC or a simple MUI object instance ? */
    if (NULL != overloaded_dict)
    {
        MCCNode *mccnode = NULL, *next;

        DPRINT("Search for MCC based on: '%s'\n", classid);

        ForeachNode(&gMCCList, next)
        {
            if ((NULL != next->mcc->mcc_Super->cl_ID) && !strcmp(classid, next->mcc->mcc_Super->cl_ID))
            {
                mccnode = next;
                break;
            }
        }

        if (NULL == mccnode)
        {
            mccnode = AllocMem(sizeof(MCCNode), MEMF_PUBLIC | MEMF_SEM_PROTECTED | MEMF_CLEAR);
            if (NULL == mccnode)
            {
                PyErr_SetString(PyExc_MemoryError, "Not enough memory to create a new MCC for this object");
                goto bye_err;
            }

            mcc = MUI_CreateCustomClass(NULL, classid, NULL, sizeof(MCCData), DISPATCHER_REF(mcc));
            if (NULL == mcc)
            {
                FreeMem(mccnode, sizeof(MCCNode));
                PyErr_Format(PyExc_MemoryError, "MUI_CreateCustomClass() failed with classid %s", classid);
                goto bye_err;
            }

            mccnode->mcc = mcc;
            ADDTAIL(&gMCCList, mccnode);
        }
        else
            mcc = mccnode->mcc;

        DPRINT("MCC: %p (SuperID: '%s')\n", mcc, mccnode->mcc->mcc_Super->cl_ID);
    }

    /* Creating the BOOPSI/MUI object */
    if (isMUI)
    {
        if (NULL != mcc)
            bObj = NewObjectA(mcc->mcc_Class, NULL, tags);
        else
            bObj = MUI_NewObjectA(classid, tags);
        node->flags |= NODE_FLAG_MUI;
    } else if (NULL != mcc)
        bObj = NewObjectA(mcc->mcc_Class, NULL, tags);
    else
        bObj = NewObjectA(NULL, classid, tags);

    if (NULL != tags)
    {
        PyMem_Free(tags);
        tags = NULL;
    }

    if (NULL != bObj)
    {
        DPRINT("New '%s' object @ %p (self=%p-'%s')\n", classid, bObj, self, OBJ_TNAME(self));

        /* Add an entry into the BOOPSI objects database */
        if (objdb_add(bObj, (PyObject *) self))
        {
            if (PyMUIObject_Check(self))
                MUI_DisposeObject(bObj);
            else
                DisposeObject(bObj);

            goto bye_err;
        }

        PyBOOPSIObject_SET_OBJECT(self, bObj);
        PyBOOPSIObject_ADD_FLAGS(self, FLAG_OWNER);
        PyBOOPSIObject_SET_NODE(self, node);
        PyBOOPSIObject_OVERLOADED_DICT(self) = overloaded_dict;
        Py_XINCREF(overloaded_dict);

        ADDTAIL(&gObjectList, node);

        Py_RETURN_NONE;
    }

    err = PyErr_Format(PyExc_SystemError, "Failed to create BOOPSI object of class %s", classid);

bye_err:
    if (NULL != tags)
        PyMem_Free(tags);

    if (NULL == node)
        FreeMem(node, sizeof(*node));

    return err;
}
//-
//+ boopsi__get
PyDoc_STRVAR(boopsi__get_doc,
"_get(id) -> unsigned integer \n\
\n\
Call BOOPSI function GetAttr() on linked BOPPSI object with given attribute id.\n\
Returns the stored value of GetAttr().");

static PyObject *
boopsi__get(PyBOOPSIObject *self, PyObject *attr_o)
{
    Object *obj;
    ULONG attr;
    ULONG value;

    obj = PyBOOPSIObject_GetObject(self);
    if (NULL == obj)
        return NULL;

    attr = PyLong_AsUnsignedLongMask(attr_o);
    if (PyErr_Occurred())
        return NULL;

    DPRINT("_get(0x%08x): Object=%p (%s)\n", attr, obj, OCLASS(obj)->cl_ID);
    value = 0xdeadbeaf; /* be sure that the value is modified */
    if (!GetAttr(attr, obj, &value)) /* I suppose that GetAttr() doesn't call python code */
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

    obj = PyBOOPSIObject_GetObject(self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "IO", &attr, &v_obj)) /* BR */
        return NULL;

    if (!py2long(v_obj, &value))
        return NULL;

    PyBOOPSIObject_FORBID(self);

    DPRINT("+ Attr 0x%lx set to value: %ld %ld %#lx on BOOPSI obj @ %p\n", attr, (LONG)value, value, value, obj);
    set(obj, attr, value); /* may call some python code (notifications) */
    DPRINT("- done\n");

    PyBOOPSIObject_PERMIT(self);

    if (PyErr_Occurred())
        return NULL;

    Py_RETURN_NONE;
}
//-
//+ boopsi__do
PyDoc_STRVAR(boopsi__do_doc,
"_do(msg, *extra_args) -> long\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__do(PyBOOPSIObject *self, PyObject *args) {
    Object *obj;
    ULONG result;
    Msg msg;
    int msg_length;
    PyObject *extra_args = NULL;

    obj = PyBOOPSIObject_GetObject(self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "s#|O:_do", &msg, &msg_length, &extra_args)) /* BR */
        return NULL;

    DPRINT("DoMethod(obj=%p, msg=%p (%u bytes), 0x%08x)\n", obj, msg, msg_length, msg->MethodID);

    #if 0
    {
        int i;
        ULONG *p = (ULONG *)msg;

        for (i=0; i < msg_length/4; i++) {
            DPRINT("msg[%-03lu] = $%08x\n", i, p[i]);
        }
    }
    #endif

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

        PyBOOPSIObject_FORBID(self);
        result = DoMethodA(obj, final_msg);
        PyBOOPSIObject_PERMIT(self);

        PyMem_Free(final_msg);
    } else {
        PyBOOPSIObject_FORBID(self);
        result = DoMethodA(obj, msg);
        PyBOOPSIObject_PERMIT(self);
    }

    DPRINT("DoMethod(obj=%p, 0x%08x) = (%ld, %lu, %lx)\n", obj, msg->MethodID, (LONG)result, result, result);

    /* Methods can call Python code ... check against exception here also */
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
    LONG v1=0, v2=0;

    obj = PyBOOPSIObject_GetObject(self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "I|O&O&", &meth, py2long, &v1, py2long, &v2)) /* BR */
        return NULL;

    PyBOOPSIObject_FORBID(self);
    DPRINT("+ DoMethod(obj=%p, meth=0x%08x, v1=%08x, v2=%08x):\n", obj, meth, v1, v2);
    v1 = DoMethod(obj, meth, v1, v2);
    DPRINT("- done\n");
    PyBOOPSIObject_PERMIT(self);

    if (PyErr_Occurred())
        return NULL;

    return PyLong_FromUnsignedLong(v1);
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
    {"_loosed",   (PyCFunction) boopsi__loosed,   METH_NOARGS,  boopsi__loosed_doc},
    {"_dispose",  (PyCFunction) boopsi__dispose,  METH_NOARGS,  boopsi__dispose_doc},
    {"_addchild", (PyCFunction) boopsi__addchild, METH_VARARGS, boopsi__addchild_doc},
    {"_remchild", (PyCFunction) boopsi__remchild, METH_VARARGS, boopsi__remchild_doc},
    {"_create",   (PyCFunction) boopsi__create,   METH_VARARGS, boopsi__create_doc},
    {"_get",      (PyCFunction) boopsi__get,      METH_O,       boopsi__get_doc},
    {"_set",      (PyCFunction) boopsi__set,      METH_VARARGS, boopsi__set_doc},
    {"_do",       (PyCFunction) boopsi__do,       METH_VARARGS, boopsi__do_doc},
    {"_do1",      (PyCFunction) boopsi__do1,      METH_VARARGS, boopsi__do1_doc},

    {NULL, NULL} /* sentinel */
};

static PyTypeObject PyBOOPSIObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.PyBOOPSIObject",
    tp_basicsize    : sizeof(PyBOOPSIObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    tp_doc          : "BOOPSI Objects",

    tp_new          : (newfunc)boopsi_new,
    tp_traverse     : (traverseproc)boopsi_traverse,
    tp_clear        : (inquiry)boopsi_clear,
    tp_dealloc      : (destructor)boopsi_dealloc,
    tp_weaklistoffset : offsetof(PyBOOPSIObject, wreflist),

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
        self->pycairo_obj = NULL;
        self->cairo_data = NULL;
        self->raster = (PyRasterObject *)PyObject_New(PyRasterObject, &PyRasterObject_Type); /* NR */
        if (NULL != self->raster)
            return (PyObject *)self;

        Py_DECREF((PyObject *)self);
    }

    return NULL;
}
//-
//+ muiobject_traverse
static int
muiobject_traverse(PyMUIObject *self, visitproc visit, void *arg)
{
#ifdef WITH_PYCAIRO
    Py_VISIT(self->cairo_data_pyobj);
    Py_VISIT(self->pycairo_obj);
#endif
    Py_VISIT(self->raster);

    return 0;
}
//-
//+ muiobject_clear
static int
muiobject_clear(PyMUIObject *self)
{
    DPRINT("Clearing PyMUIObject: %p [%s]\n", self, OBJ_TNAME(self));

#ifdef WITH_PYCAIRO
    DPRINT("Cairo obj @ %p\n", self->pycairo_obj);
    if (NULL != self->pycairo_obj)
    {
        Py_CLEAR(self->pycairo_obj);
        Py_CLEAR(self->cairo_data_pyobj);
    }
#endif
    Py_CLEAR(self->raster);

    return 0;
}
//-
//+ muiobject_dealloc
static void
muiobject_dealloc(PyMUIObject *self)
{
    muiobject_clear(self);
    boopsi_dealloc((PyBOOPSIObject *)self);
}
//-
//+ muiobject__nnset
PyDoc_STRVAR(muiobject__nnset_doc,
"_nnset(attr, value) -> None\n\
\n\
Like BOOPSIObject._set() but without triggering notification (MUI objects only).");

static PyObject *
muiobject__nnset(PyMUIObject *self, PyObject *args)
{
    Object *obj;
    ULONG attr;
    LONG value;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;

    if (!PyArg_ParseTuple(args, "IO&", &attr, py2long, &value)) /* BR */
        return NULL;

    PyBOOPSIObject_FORBID(self);

    DPRINT("+ Attr 0x%lx set to value: %ld %ld %#lx on MUI obj @ %p\n", attr, (LONG)value, value, value, obj);
    nnset(obj, attr, value);
    DPRINT("- done\n");

    PyBOOPSIObject_PERMIT(self);

    if (PyErr_Occurred())
        return NULL;

    Py_RETURN_NONE;
}
//-
//+ muiobject__redraw
PyDoc_STRVAR(muiobject__redraw_doc,
"_redraw(flags) -> None\n\
\n\
Just direct call to MUI_Redraw(flags).");

static PyObject *
muiobject__redraw(PyMUIObject *self, PyObject *args)
{
    Object *obj;
    ULONG flags = MADF_DRAWOBJECT;

    if (!PyArg_ParseTuple(args, "|I", &flags))
        return NULL;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;

    PyBOOPSIObject_FORBID(self);
    MUI_Redraw(obj, flags);
    PyBOOPSIObject_PERMIT(self);

    if (PyErr_Occurred())
        return NULL;

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
    ULONG trigattr;
    Object *mo;
    PyObject **wref_storage;

    mo = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == mo)
        return NULL;

    if (!PyArg_ParseTuple(args, "I", &trigattr)) /* BR */
        return NULL;

    /* The hook will be called using a weakref on the python object.
     * So if the python object is destroyed the weakref gives NULL.
     *
     * In this last case the hook shall destroy also the weakref itself.
     * But we can't give directly to the hook this weakref as parameter
     * as it will be invalid, so we use a mempool to store this ptr.
     * The storage will be NULLed when weakref die.
     * The storage memory is freed globaly by using a mempool.
     */

    wref_storage = AllocPooled(gMemPool, sizeof(*wref_storage));
    if (NULL == wref_storage)
        return PyErr_NoMemory();

    *wref_storage = PyWeakref_NewRef((PyObject *)self, NULL); /* NR */
    if (NULL == *wref_storage) {
        FreePooled(gMemPool, wref_storage, sizeof(*wref_storage));
        return NULL;
    }

    PyBOOPSIObject_FORBID(self);

    DPRINT("+ MO: %p, WRef ptr: %p on %p-'%s', trigattr: %#lx\n",
           mo, wref_storage, self, OBJ_TNAME(self), trigattr);
    DoMethod(mo, MUIM_Notify, trigattr, MUIV_EveryTime,
             MUIV_Notify_Self, 5,
             MUIM_CallHook, (ULONG)&OnAttrChangedHook, (ULONG) wref_storage, trigattr, MUIV_TriggerValue);
    DPRINT("- done\n");

    PyBOOPSIObject_PERMIT(self);

    if (PyErr_Occurred())
        return NULL;

    Py_RETURN_NONE;
}
//-

#ifdef WITH_PYCAIRO
//+ muiobject_blit_cairo_context
PyDoc_STRVAR(muiobject_blit_cairo_context_doc,
"BlitCairoContext() -> None\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
muiobject_blit_cairo_context(PyMUIObject *self, PyObject *args)
{
    Object *mo;

    mo = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == mo)
        return NULL;

    if (NULL == self->pycairo_obj)
        return PyErr_Format(PyExc_TypeError, "No cairo context found on this object");

    blit_cairo_surface(self, mo);

    Py_RETURN_NONE;
}
//-
//+ muiobject_clip_cairo_paint_area
PyDoc_STRVAR(muiobject_clip_cairo_paint_area_doc,
"ClipCairoPaintArea() -> None\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
muiobject_clip_cairo_paint_area(PyMUIObject *self, PyObject *args)
{
    cairo_rectangle_int_t clip;
    int x2, y2;

    if (NULL == self->pycairo_obj)
        return PyErr_Format(PyExc_TypeError, "No cairo context found on this object");

    if (PyArg_ParseTuple(args, "iiii", &clip.x, &clip.y, &clip.width, &clip.height) < 0)
        return NULL;

    x2 = self->cairo_paint_area.x + self->cairo_paint_area.width - 1;
    x2 = MIN(x2, MAX(0, clip.x + clip.width - 1));
    y2 = self->cairo_paint_area.y + self->cairo_paint_area.height - 1;
    y2 = MIN(y2, MAX(0, clip.y + clip.height - 1));

    self->cairo_paint_area.x = MAX(self->cairo_paint_area.x, MIN(x2, clip.x));
    self->cairo_paint_area.y = MAX(self->cairo_paint_area.y, MIN(y2, clip.y));
    self->cairo_paint_area.width = x2 - self->cairo_paint_area.x + 1;
    self->cairo_paint_area.height = y2 - self->cairo_paint_area.y + 1;

    Py_RETURN_NONE;
}
//-
//+ muiobject_add_cairo_paint_area
PyDoc_STRVAR(muiobject_add_cairo_paint_area_doc,
"AddCairoPaintArea() -> None\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
muiobject_add_cairo_paint_area(PyMUIObject *self, PyObject *args)
{
    cairo_rectangle_int_t clip;
    int x2, y2;

    if (NULL == self->pycairo_obj)
        return PyErr_Format(PyExc_TypeError, "No cairo context found on this object");

    if (PyArg_ParseTuple(args, "iiii", &clip.x, &clip.y, &clip.width, &clip.height) < 0)
        return NULL;

    x2 = self->cairo_paint_area.x + self->cairo_paint_area.width;
    y2 = self->cairo_paint_area.y + self->cairo_paint_area.height;
    
    self->cairo_paint_area.x = MIN(self->cairo_paint_area.x, clip.x);
    self->cairo_paint_area.y = MIN(self->cairo_paint_area.y, clip.y);
    
    clip.x += clip.width;
    clip.y += clip.height;
    self->cairo_paint_area.width = MAX(x2, clip.x) - self->cairo_paint_area.x;
    self->cairo_paint_area.height = MAX(y2, clip.y) - self->cairo_paint_area.y;

    Py_RETURN_NONE;
}
//-
#endif

//+ muiobject_get_data
static PyObject *
muiobject_get_data(PyMUIObject *self, void *closure)
{
    Object *obj;
    LONG data;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;

    switch ((int)closure) {
        case PYMUI_DATA_MLEFT:   data = _mleft(obj); break;
        case PYMUI_DATA_MRIGHT:  data = _mright(obj); break;
        case PYMUI_DATA_MTOP:    data = _mtop(obj); break;
        case PYMUI_DATA_MBOTTOM: data = _mbottom(obj); break;
        case PYMUI_DATA_MWIDTH:  data = _mwidth(obj); break;
        case PYMUI_DATA_MHEIGHT: data = _mheight(obj); break;

        default:
            return PyErr_Format(PyExc_SystemError, "[INTERNAL ERROR] bad closure given to muiobject_get_data()");
    }

    return PyInt_FromLong(data);
}
//-
//+ muiobject_get_mbox
static PyObject *
muiobject_get_mbox(PyMUIObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;

    return Py_BuildValue("HHHH", _mleft(obj), _mtop(obj), _mright(obj), _mbottom(obj));
}
//-
//+ muiobject_get_sdim
static PyObject *
muiobject_get_sdim(PyMUIObject *self, void *closure)
{
    Object *obj;
    struct Screen *scr;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
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
muiobject_get_srange(PyMUIObject *self, void *closure)
{
    Object *obj;
    struct Screen *scr;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
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
static PyObject *
muiobject_get_drawbounds(PyMUIObject *self, void *closure)
{
    struct Rectangle r;
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;

    if (NULL == _rp(obj))
        Py_RETURN_NONE;

    GetRPAttrs(_rp(obj), RPTAG_DrawBounds, (ULONG)&r, TAG_DONE);

    return Py_BuildValue("HHHH",
                         MAX(r.MinX-_mleft(obj), 0),
                         MAX(r.MinY-_mtop(obj), 0),
                         MIN(r.MaxX-r.MinX+1, _mwidth(obj)),
                         MIN(r.MaxY-r.MinY+1, _mheight(obj)));
}
static PyObject *
muiobject_get_rp(PyMUIObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;

    self->raster->rp = _rp(obj);
    Py_INCREF((PyObject *)self->raster);

    return (PyObject *)self->raster;
}
static PyObject *
muiobject_get_font_ysize(PyMUIObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;
    
    if (!_font(obj))
        Py_RETURN_NONE;
            
    return Py_BuildValue("i", _font(obj)->tf_YSize);
}
#ifdef WITH_PYCAIRO
//+ muiobject_get_cairo_context
static PyObject *
muiobject_get_cairo_context(PyMUIObject *self, void *closure)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;

    CHECK_FOR_PYCAIRO;

    /* Destroy context if object size changed */
    if ((NULL != self->pycairo_obj) &&
        ((self->cairo_surface_width != _mwidth(obj)) ||
         (self->cairo_surface_height != _mheight(obj))))
    {
        Py_CLEAR(self->pycairo_obj);
        Py_CLEAR(self->cairo_data_pyobj);
    }

    if (NULL == self->pycairo_obj)
    {
        int stride;

        stride = cairo_format_stride_for_width (CAIRO_FORMAT_ARGB32, _mwidth(obj));
        self->cairo_data_pyobj = PyBuffer_New(stride * _mheight(obj));
        if (NULL != self->cairo_data_pyobj)
        {
            PycairoSurface *pyo;
            Py_ssize_t size;

            PyObject_AsWriteBuffer(self->cairo_data_pyobj, &self->cairo_data, &size);
            bzero(self->cairo_data, size);

            pyo = (PycairoSurface *)PyObject_CallMethod((PyObject *)&PycairoImageSurface_Type, "create_for_data",
                                                          "OIIII", (ULONG)self->cairo_data_pyobj,
                                                          CAIRO_FORMAT_ARGB32,
                                                          _mwidth(obj), _mheight(obj), stride); /* NR */
            if (NULL != pyo)
            {
                self->cairo_surface = pyo->surface;
                self->pycairo_obj = PyObject_CallFunction((PyObject *)&PycairoContext_Type, "N", pyo); /* NR */
                self->cairo_surface_width = _mwidth(obj);
                self->cairo_surface_height = _mheight(obj);
                self->cairo_surface_stride = stride;

                /*self->cairo_surface = cairo_image_surface_create_for_data(self->cairo_data, CAIRO_FORMAT_ARGB32,
                                                                          _mwidth(obj), _mheight(obj), stride);
                self->cairo_context = cairo_create(self->cairo_surface);
                self->pycairo_obj = PycairoContext_FromContext(self->cairo_context, &PycairoContext_Type, NULL); */

                if (NULL != self->pycairo_obj)
                {
                    self->cairo_context = ((PycairoContext *)self->pycairo_obj)->ctx;
                    Py_INCREF(self->pycairo_obj);
                }
                else
                    self->cairo_data = NULL;
            }
            else
                self->cairo_data = NULL;

            if (NULL == self->cairo_data)
                Py_CLEAR(self->cairo_data_pyobj);
        }
        else
            PyErr_SetString(PyExc_MemoryError, "Failed to allocate cairo data buffer");
    }
    else
        Py_INCREF(self->pycairo_obj);

    /* Reset the paint area to the full surface */
    if (NULL != self->pycairo_obj)
    {
        self->cairo_paint_area.x = 0;
        self->cairo_paint_area.y = 0;
        self->cairo_paint_area.width = self->cairo_surface_width;
        self->cairo_paint_area.height = self->cairo_surface_height;
    }

    return self->pycairo_obj;
}
//-
//+ muiobject_fill_cairo_context
static PyObject *
muiobject_fill_cairo_context(PyMUIObject *self)
{
    Object *obj;

    obj = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self);
    if (NULL == obj)
        return NULL;

    CHECK_FOR_PYCAIRO;

    ReadPixelArray(self->cairo_data, 0, 0, self->cairo_surface_stride,
                   _rp(obj), _mleft(obj), _mtop(obj),
                   self->cairo_surface_width, self->cairo_surface_height,
                   RECTFMT_ARGB);

    Py_RETURN_NONE;
}
//-
#endif

static PyGetSetDef muiobject_getseters[] = {
    {"MLeft",   (getter)muiobject_get_data, NULL, "_mleft(obj)",   (APTR) PYMUI_DATA_MLEFT},
    {"MRight",  (getter)muiobject_get_data, NULL, "_mright(obj)",  (APTR) PYMUI_DATA_MRIGHT},
    {"MTop",    (getter)muiobject_get_data, NULL, "_mtop(obj)",    (APTR) PYMUI_DATA_MTOP},
    {"MBottom", (getter)muiobject_get_data, NULL, "_mbottom(obj)", (APTR) PYMUI_DATA_MBOTTOM},
    {"MWidth",  (getter)muiobject_get_data, NULL, "_mwidth(obj)",  (APTR) PYMUI_DATA_MWIDTH},
    {"MHeight", (getter)muiobject_get_data, NULL, "_mheight(obj)", (APTR) PYMUI_DATA_MHEIGHT},
    {"MBox",    (getter)muiobject_get_mbox,    NULL, "4-Tuple of the bounded box object values", NULL},
    {"SWidth",  (getter)muiobject_get_sdim,    NULL, "Screen Width",   (APTR) 0},
    {"SHeight", (getter)muiobject_get_sdim,    NULL, "Screen Height",  (APTR)~0},
    {"SRangeX", (getter)muiobject_get_srange,  NULL, "Screen X range", (APTR) 0},
    {"SRangeY", (getter)muiobject_get_srange,  NULL, "Screen Y range", (APTR)~0},
    {"DrawBounds", (getter)muiobject_get_drawbounds, NULL, "RastPort draw bounds", (APTR)~0},
    {"_rp",     (getter)muiobject_get_rp,      NULL, "RastPort", NULL},
    {"FontYSize", (getter)muiobject_get_font_ysize, NULL, "Font YSize (works only with instance of Area, or subclasses)", NULL},
#ifdef WITH_PYCAIRO
    {"cairo_context", (getter)muiobject_get_cairo_context, NULL, "Cairo context", NULL},
#endif
    {NULL} /* sentinel */
};

static struct PyMethodDef muiobject_methods[] = {
    {"_notify", (PyCFunction) muiobject__notify, METH_VARARGS, muiobject__notify_doc},
    {"_nnset",  (PyCFunction) muiobject__nnset,  METH_VARARGS, muiobject__nnset_doc},
    {"Redraw",  (PyCFunction) muiobject__redraw, METH_VARARGS, muiobject__redraw_doc},
#ifdef WITH_PYCAIRO
    {"BlitCairoContext",  (PyCFunction) muiobject_blit_cairo_context, METH_VARARGS, muiobject_blit_cairo_context_doc},
    {"ClipCairoPaintArea",  (PyCFunction) muiobject_clip_cairo_paint_area, METH_VARARGS, muiobject_clip_cairo_paint_area_doc},
    {"AddCairoPaintArea",  (PyCFunction) muiobject_add_cairo_paint_area, METH_VARARGS, muiobject_add_cairo_paint_area_doc},
    {"FillCairoContext", (PyCFunction) muiobject_fill_cairo_context, METH_NOARGS, "Copy rastport on cairo"},
#endif
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
    //tp_members      : muiobject_members,
    tp_getset       : muiobject_getseters,
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
** MethodMsg_Type
*/

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
    self->mmsg_PyMsg = PyObject_CallFunction(callable, "k", (ULONG)self->mmsg_Msg); /* NR */
    if (NULL == self->mmsg_PyMsg)
        return NULL;

    Py_INCREF(self);
    return (PyObject *)self;
}

static int
mmsg_traverse(PyMethodMsgObject *self, visitproc visit, void *arg)
{
    Py_VISIT(self->mmsg_PyMsg);
    return 0;
}

static int
mmsg_clear(PyMethodMsgObject *self)
{
    Py_CLEAR(self->mmsg_PyMsg);
    return 0;
}

static void
mmsg_dealloc(PyMethodMsgObject *self)
{
    mmsg_clear(self);
    self->ob_type->tp_free((PyObject *)self);
}

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
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
    tp_doc          : "Method Message Objects",

    tp_new          : (newfunc)PyType_GenericNew,
    tp_traverse     : (traverseproc)mmsg_traverse,
    tp_clear        : (inquiry)mmsg_clear,
    tp_dealloc      : (destructor)mmsg_dealloc,
    tp_getattro     : (getattrofunc)mmsg_getattro,
    tp_methods      : mmsg_methods,
};

/*******************************************************************************************
** EventHandlerObject_Type
*/

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

        DPRINT("win=%p\n", mo);
        if (NULL != mo) {
            PyBOOPSIObject_FORBID(self->window);
            DoMethod(mo, MUIM_Window_RemEventHandler, (ULONG)&self->handler);
            PyBOOPSIObject_PERMIT(self->window);
            PyErr_Clear(); /* Silent exceptions during DoMethod or PERMIT */
        }
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

    target = PyBOOPSIObject_GetObject((PyBOOPSIObject *)pyo_tgt);
    if (NULL == target)
        return NULL;

    win = _win(target);
    DPRINT("window obj: %p\n", win);
    if (NULL == win) {
        PyErr_SetString(PyExc_SystemError, "no window found");
        return NULL;
    }

    pyo_win = objdb_get(win);
    DPRINT("window py obj: %p\n", pyo_win);
    if (NULL == pyo_win) {
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

    PyBOOPSIObject_FORBID(pyo_tgt);
    DoMethod(win, MUIM_Window_AddEventHandler, (ULONG)&self->handler);
    PyBOOPSIObject_PERMIT(pyo_tgt);

    if (PyErr_Occurred())
        return NULL;

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

    win = PyBOOPSIObject_GetObject((PyBOOPSIObject *)self->window);
    if (NULL == win)
        return NULL;

    PyBOOPSIObject_FORBID(self->window);
    DPRINT("uninstall handler %p on win %p\n", &self->handler, win);
    DoMethod(win, MUIM_Window_RemEventHandler, (ULONG)&self->handler);
    PyBOOPSIObject_PERMIT(self->window);

    Py_CLEAR(self->window);
    Py_CLEAR(self->target);

    if (PyErr_Occurred())
        return NULL;

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
            return NULL;

        while (NULL != (tag = NextTagItem(&tags))) {
            PyObject *item = Py_BuildValue("II", tag->ti_Tag, tag->ti_Data); /* NR */

            if ((NULL == item) || (PyList_Append(o_tags, item) != 0)) {
                Py_XDECREF(item);
                Py_DECREF(o_tags);
                return NULL;
            }
            
            Py_DECREF(item);
        }

        error = PyDict_MergeFromSeq2(self->TabletTagsList, o_tags, TRUE); /* NR */
        Py_DECREF(o_tags);
        if (error)
            return NULL;

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
static PyObject *
evthandler_get_up(PyEventHandlerObject *self, void *closure)
{
    return PyBool_FromLong((self->imsg.Code & IECODE_UP_PREFIX) == IECODE_UP_PREFIX);
}

static PyObject *
evthandler_get_rawkey(PyEventHandlerObject *self, void *closure)
{
    return PyInt_FromLong(self->imsg.Code & ~IECODE_UP_PREFIX);
}

static PyObject *
evthandler_get_key(PyEventHandlerObject *self, void *closure)
{
    struct InputEvent ie;

    if (IDCMP_RAWKEY == self->imsg.Class)
    {
        int len;
        char c[4];

        ie.ie_Class        = IECLASS_RAWKEY;
        ie.ie_SubClass     = 0;
        ie.ie_Code         = self->imsg.Code & ~IECODE_UP_PREFIX;
        ie.ie_Qualifier    = self->imsg.Qualifier & (ULONG)closure;
        ie.ie_EventAddress = (APTR *)*((ULONG *)self->imsg.IAddress);

        len = MapRawKey(&ie, c, sizeof(c), NULL);
        if (len > 0)
            return PyString_FromStringAndSize(c, len);
    }

    Py_RETURN_NONE;
}

static PyObject *
evthandler_get_handler(PyEventHandlerObject *self, void *closure)
{
    return PyLong_FromVoidPtr(&self->handler);
}

static PyGetSetDef evthandler_getseters[] = {
    {"handler", (getter)evthandler_get_handler, NULL, "Address of the MUI_EventHandlerNode", NULL},
    {"Up", (getter)evthandler_get_up, NULL, "True if Code has UP prefix", NULL},
    {"RawKey", (getter)evthandler_get_rawkey, NULL, "IntuiMessage Code field without UP prefix if exists", NULL},
    {"Key", (getter)evthandler_get_key, NULL, "Mapped key using the rawkey (None if Class is not IDCMP_RAWKEY)", (void*)0xFFF},
    {"SimpleKey", (getter)evthandler_get_key, NULL, "Mapped key using the rawkey without qualifiers (None if Class is not IDCMP_RAWKEY)", (void*)0xFF00},
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

    tp_new          : PyType_GenericNew,
    tp_traverse     : (traverseproc)evthandler_traverse,
    tp_clear        : (inquiry)evthandler_clear,
    tp_dealloc      : (destructor)evthandler_dealloc,

    tp_members      : evthandler_members,
    tp_methods      : evthandler_methods,
    tp_getset       : evthandler_getseters,
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
Blit given ARGB8 buffer on the raster.\n\
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
    unsigned int buf_size, stride, use_alpha=0;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "s#kHHHH|HHI:Blit8", &buf, &buf_size, &stride,
                          &dst_x, &dst_y, &src_w, &src_h, &src_x, &src_y, &use_alpha)) /* BR */
        return NULL;

    if (use_alpha)
        WritePixelArrayAlpha(buf, src_x, src_y, stride, self->rp, dst_x, dst_y, src_w, src_h, 0xffffffff);
    else
        WritePixelArray(buf, src_x, src_y, stride, self->rp, dst_x, dst_y, src_w, src_h, RECTFMT_ARGB);

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
    unsigned int buf_size, stride;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "s#kHHHHHH:ScaledBlit8", &buf, &buf_size, &stride,
                          &src_w, &src_h, &dst_x, &dst_y, &dst_w, &dst_h)) /* BR */
        return NULL;

    ScalePixelArray(buf, src_w, src_h, stride, self->rp, dst_x, dst_y, dst_w, dst_h, RECTFMT_RGB);

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
//+ raster_get_apen
static PyObject *
raster_get_apen(PyRasterObject *self, APTR closure)
{
    return PyInt_FromLong(GetAPen(self->rp));
}
//-
//+ raster_set_apen
static int
raster_set_apen(PyRasterObject *self, PyObject *value, APTR closure)
{
    if (NULL != value)
    {
        ULONG pen = PyInt_AsLong(value);

        if (PyErr_Occurred())
            return 1;

        SetAPen(self->rp, pen);
    }

    return 0;
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
//+ raster_move
static PyObject *
raster_move(PyRasterObject *self, PyObject *args)
{
    LONG x, y;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "ii:Move", &x, &y)) /* BR */
        return NULL;

    Move(self->rp, x, y);

    Py_RETURN_NONE;
}
//-
//+ raster_draw
static PyObject *
raster_draw(PyRasterObject *self, PyObject *args)
{
    LONG x, y;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "ii:Draw", &x, &y)) /* BR */
        return NULL;

    Draw(self->rp, x, y);

    Py_RETURN_NONE;
}
static PyObject *
raster_text(PyRasterObject *self, PyObject *args)
{
    char *text;
    int length, x, y;
    
    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "iis#", &x, &y, &text, &length)) /* BR */
        return NULL;

    Move(self->rp, x, y);
    Text(self->rp, text, length);

    Py_RETURN_NONE;
}

static PyGetSetDef raster_getseters[] = {
    {"APen", (getter)raster_get_apen, (setter)raster_set_apen, "RastPort APen value", NULL},
    {NULL} /* sentinel */
};

static struct PyMethodDef raster_methods[] = {
    {"Blit8",       (PyCFunction)raster_blit8,        METH_VARARGS, raster_blit8_doc},
    {"ScaledBlit8", (PyCFunction)raster_scaled_blit8, METH_VARARGS, raster_scaled_blit8_doc},
    {"Scroll",      (PyCFunction)raster_scroll,       METH_VARARGS, NULL},
    {"Rect",        (PyCFunction)raster_rect,         METH_VARARGS, NULL},
    {"Move",        (PyCFunction)raster_move,         METH_VARARGS, NULL},
    {"Draw",        (PyCFunction)raster_draw,         METH_VARARGS, NULL},
    {"Text",        (PyCFunction)raster_text,         METH_VARARGS, NULL},
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
    tp_getset       : raster_getseters,
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

    app = PyBOOPSIObject_GetObject((PyBOOPSIObject *)pyapp);
    if (NULL == app)
        return NULL;

    /* This code will not check that the given object is really an Application object;
     * That should be checked by the caller!
     */

    DPRINT("Goes into mainloop... (app=%p)\n", app);
    gApp = app; Py_INCREF(pyapp);
    PyBOOPSIObject_FORBID(pyapp);

    for (;;)
    {
        ULONG id;
        //PyThreadState *_save;
        ObjectNode *node, *next;

        Py_BEGIN_ALLOW_THREADS
        id = DoMethod(app, MUIM_Application_NewInput, (ULONG) &sigs);
        Py_END_ALLOW_THREADS

        ForeachNodeSafe(&gToDisposeList, node, next)
        {
            Object *bObj = node->obj;

            /* BOOPSI/MUI destroy */
            DPRINT("Before DisposeObject(%p)\n", bObj);
            if (node->flags & NODE_FLAG_MUI)
                MUI_DisposeObject(bObj);
            else
                DisposeObject(bObj);
            DPRINT("After DisposeObject(%p)\n", bObj);

            FreeMem(REMOVE(node), sizeof(*node));
        }

        /* Exception occured or quit requested */
        if ((MUIV_Application_ReturnID_Quit == id) || PyErr_Occurred())
            break;

        if (sigs)
        {
            Py_BEGIN_ALLOW_THREADS
            sigs = Wait(sigs | SIGBREAKF_CTRL_C);
            Py_END_ALLOW_THREADS
        }
        else
            sigs = SetSignal(0, 0);

        if (sigs & SIGBREAKF_CTRL_C)
            break;
    }

    PyBOOPSIObject_PERMIT(pyapp);

    Py_DECREF(pyapp);
    gApp = NULL;

    if (sigs & SIGBREAKF_CTRL_C)
    {
        PyErr_SetNone(PyExc_KeyboardInterrupt);
        DPRINT("bye mainloop with Keyboard Interruption...\n");
        return NULL;
    }

    if (PyErr_Occurred())
    {
        DPRINT("bye mainloop with error...\n");
        return NULL;
    }

    DPRINT("bye mainloop...\n");
    Py_RETURN_NONE;
}
//-
//+ _muimaster_pyobjfromptr
static PyObject *
_muimaster_pyobjfromptr(PyObject *self, PyObject *args)
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
//+ _muimaster_ptr2pyboopsi
static PyObject *
_muimaster_ptr2pyboopsi(PyObject *self, PyObject *args)
{
    ULONG value;
    Object *bObj;
    PyObject *pObj;

    if (!PyArg_ParseTuple(args, "I", &value))
        return NULL;

    bObj = (Object *)value;
    DPRINT("bObj: %p\n", bObj);
    if (NULL != bObj) {
        /* Check if this BOOPSI object is already known */
        pObj = objdb_get(bObj);
        DPRINT("pObj: %p\n", pObj);
        if (NULL != pObj) {
            if (!TypeOfMem(pObj))
                return PyErr_Format(PyExc_ValueError, "value '%x' is not a valid system pointer", (unsigned int)pObj);

            Py_INCREF(pObj);
            return pObj;
        }
    }

    /* New PyBOOPSIObject */
    pObj = (PyObject *)PyObject_GC_New(PyBOOPSIObject, &PyBOOPSIObject_Type); /* NR */
    PyBOOPSIObject_SET_OBJECT(pObj, bObj);
    ((PyBOOPSIObject *)pObj)->flags = 0;
    ((PyBOOPSIObject *)pObj)->node = NULL;
    ((PyBOOPSIObject *)pObj)->used_cnt = NULL;
    ((PyBOOPSIObject *)pObj)->wreflist = NULL;
    ((PyBOOPSIObject *)pObj)->overloaded_dict = NULL;

    /* record this new PyBOOPSIObject into the DB (Empty also) */
    if (objdb_add(bObj, pObj))
        Py_CLEAR(pObj);

    return pObj;
}
//-
//+ _muimaster_ptr2pymui
static PyObject *
_muimaster_ptr2pymui(PyObject *self, PyObject *args)
{
    ULONG value;
    Object *bObj;
    PyObject *pObj;

    if (!PyArg_ParseTuple(args, "I", &value))
        return NULL;

    bObj = (Object *)value;
    DPRINT("bObj: %p\n", bObj);
    if (NULL != bObj) {
        /* Check if the object is owned by a valid PyMUIObject object */
        pObj = objdb_get(bObj); /* BR */
        DPRINT("pObj: %p\n", pObj);
        if (NULL != pObj) {
            if (!TypeOfMem(pObj))
                return PyErr_Format(PyExc_ValueError, "value '%x' is not a valid system pointer", (unsigned int)pObj);
            if (!PyMUIObject_Check(pObj))
                return PyErr_Format(PyExc_TypeError, "value '%x' doesn't refer to a PyMUIObject instance", (unsigned int)pObj);

            Py_INCREF(pObj);
            return pObj;
        }
    }

    /* New PyMUIObject */
    pObj = (PyObject *)PyObject_GC_New(PyMUIObject, &PyMUIObject_Type); /* NR */
    if (NULL == pObj)
        return NULL;

    DPRINT("New PyObject created @ %p for bObj %p\n", pObj, bObj);
    PyBOOPSIObject_SET_OBJECT(pObj, bObj);
    ((PyBOOPSIObject *)pObj)->flags = 0;
    ((PyBOOPSIObject *)pObj)->node = NULL;
    ((PyBOOPSIObject *)pObj)->used_cnt = NULL;
    ((PyBOOPSIObject *)pObj)->wreflist = NULL;
    ((PyBOOPSIObject *)pObj)->overloaded_dict = NULL;

    ((PyMUIObject *)pObj)->pycairo_obj = NULL;
    ((PyMUIObject *)pObj)->cairo_data = NULL;
    ((PyMUIObject *)pObj)->raster = NULL;

    if (objdb_add(bObj, pObj)) /* record this new PyBOOPSIObject into the DB (Empty also) */
        Py_CLEAR(pObj);

    return pObj;
}
//-
//+ _muimaster_getfilename
static PyObject *
_muimaster_getfilename(PyObject *self, PyObject *args)
{
    PyBOOPSIObject *pyo;
    PyObject *res;
    Object *mo, *win;
    STRPTR *results, title;
    STRPTR init_drawer = NULL;
    STRPTR init_pat = NULL;
    UBYTE save = FALSE, multiple = FALSE;
    ULONG dummy, i, count;

    if (!PyArg_ParseTuple(args, "Os|zzbb:getfilename", &pyo, &title, &init_drawer, &init_pat, &save, &multiple))
        return NULL;

    if (!PyMUIObject_Check(pyo))
        return PyErr_Format(PyExc_TypeError,
            "first parameter should be a MUI Window object, not %s\n",
            OBJ_TNAME(pyo));

    mo = PyBOOPSIObject_GetObject(pyo);
    if (NULL == mo)
        return NULL;

    if (get(mo, MUIA_Window_Window, &dummy))
        win = mo;
    else
        win = _win(mo);

    DPRINT("Obj %p-'%s' (mo=%p, win=%p)\n", pyo, OBJ_TNAME(pyo), mo, win);
    count = getfilename(&results, win, title, init_drawer, init_pat, save, multiple);
    if (count == 0)
        Py_RETURN_NONE;

    res = PyTuple_New(count);
    if (NULL != res)
    {
        for (i=0; i < count; i++)
            PyTuple_SET_ITEM(res, i, PyString_FromString(results[i]));
    }

    for (i=0; i < count; i++)
        FreeVec(results[i]);
    FreeVec(results);

    return res;
}
//-
//+ _muimaster_request
static PyObject *
_muimaster_request(PyObject *self, PyObject *args)
{
    char *gadgets, *contents;
    char *title;
    PyObject *win_py;
    Object *app, *win;
    LONGBITS flags = 0;
    LONG result;

    if (!PyArg_ParseTuple(args, "O&Ozss|l", py2long, &app, &win_py, &title, &gadgets, &contents, &flags))
        return NULL;

    if (!py2long(win_py, (LONG *)&win))
        return NULL;

    PyBOOPSIObject_FORBID(win_py);
    result = MUI_RequestA(app, win, flags, title, gadgets, contents, NULL);
    PyBOOPSIObject_PERMIT(win_py);

    if (PyErr_Occurred())
        return NULL;

    return PyInt_FromLong(result);
}
//-
//+ _muimaster_addclipping
static PyObject *
_muimaster_addclipping(PyObject *self, PyObject *args)
{
    PyBOOPSIObject *pyo;
    ULONG w,h;
    LONG x,y;
    Object *obj;
    APTR handle;

    if (!PyArg_ParseTuple(args, "O!|iiII", &PyMUIObject_Type, &pyo, &x, &y, &w, &h))
        return NULL;

    obj = PyBOOPSIObject_GetObject(pyo);
    if (NULL == obj)
        return NULL;

    handle = MUI_AddClipping(muiRenderInfo(obj), x,y, w, h);
    return PyLong_FromVoidPtr(handle);
}
//-
//+ _muimaster_removeclipping
static PyObject *
_muimaster_removeclipping(PyObject *self, PyObject *args)
{
    PyBOOPSIObject *pyo;
    Object *obj;
    APTR handle;

    if (!PyArg_ParseTuple(args, "O!k", &PyMUIObject_Type, &pyo, &handle))
        return NULL;

    obj = PyBOOPSIObject_GetObject(pyo);
    if (NULL == obj)
        return NULL;

    MUI_RemoveClipping(muiRenderInfo(obj), handle);

    Py_RETURN_NONE;
}
//-
//+ _muimaster_setwinpointer
static PyObject *
_muimaster_setwinpointer(PyObject *self, PyObject *args)
{
    PyBOOPSIObject *pyo;
    Object *obj;
    struct Window *win;
    ULONG type;

    /* The given object is not necessary a window object.
     * It could be any MUI object with a window object as parent.
     */
    if (!PyArg_ParseTuple(args, "O!I", &PyMUIObject_Type, &pyo, &type))
        return NULL;

    obj = PyBOOPSIObject_GetObject(pyo);
    if (NULL == obj)
        return NULL;

    /* Catch the window parent object */
    win = NULL; /* protection against bugged OM_GET implementations */
    if (!get(obj, MUIA_Window, &win) || (NULL == win))
    {
        PyErr_SetString(PyExc_TypeError, "Unable to obtain attached Window object");
        return NULL;
    }

    SetWindowPointer(win, WA_PointerType, type, TAG_DONE);
    Py_RETURN_NONE;
}
static PyObject *
_muimaster_setwindowbox(PyObject *self, PyObject *args)
{
    PyBOOPSIObject *pyo;
    Object *obj;
    struct Window *win;
    LONG left, top, width, height;

    /* The given object is not necessary a window object.
     * It could be any MUI object with a window object as parent.
     */
    if (!PyArg_ParseTuple(args, "O!IIII", &PyMUIObject_Type, &pyo, &left, &top, &width, &height))
        return NULL;

    obj = PyBOOPSIObject_GetObject(pyo);
    if (NULL == obj)
        return NULL;

    win = NULL; /* protection against bugged OM_GET implementations */
    if (!get(obj, MUIA_Window_Window, &win) || (NULL == win))
    {
        PyErr_SetString(PyExc_TypeError, "Unable to obtain the system Window pointer");
        return NULL;
    }

    ChangeWindowBox(win, left, top, width, height);
    Py_RETURN_NONE;
}
//-


/* module methods */
static PyMethodDef _muimaster_methods[] = {
    {"mainloop", _muimaster_mainloop, METH_VARARGS, _muimaster_mainloop_doc},
    {"_ptr2pyobj", _muimaster_pyobjfromptr, METH_VARARGS, NULL},
    {"_ptr2pyboopsi", _muimaster_ptr2pyboopsi, METH_VARARGS, NULL},
    {"_ptr2pymui", _muimaster_ptr2pymui, METH_VARARGS, NULL},
    {"getfilename", _muimaster_getfilename, METH_VARARGS, NULL},
    {"request", _muimaster_request, METH_VARARGS, NULL},
    {"_AddClipping", _muimaster_addclipping, METH_VARARGS, NULL},
    {"_RemoveClipping", _muimaster_removeclipping, METH_VARARGS, NULL},
    {"_setwinptr", _muimaster_setwinpointer, METH_VARARGS, NULL},
    {"_setwindowbox", _muimaster_setwindowbox, METH_VARARGS, NULL},
    {NULL, NULL} /* Sentinel */
};


/*
** Public Functions
*/

//+ PyMorphOS_TermModule
void
PyMorphOS_TermModule(void)
{
    ObjectNode *node;
    MCCNode *mcc_node;
    APTR next;

    DPRINT("Closing module...\n");

    ForeachNodeSafe(&gObjectList, node, next)
    {
        Object *app, *obj = node->obj;

        if (NULL != obj)
        {
            /* Python is not perfect, PyMUI not also and user design even less :-P
             * If PyMUI user has forgotten to 'loose' the owner flag or if Python hasn't
             * disposed all Python objects when module is cleaned, the object node is here.
             * In anycase, the BOOPSI object is considered as owned and diposable.
             * But for MUIA_Parentobject, we can check if the object is really a child or not.
             * If it's a child, the object is not disposed.
             */
            if (node->flags & NODE_FLAG_MUI)
            {
                Object *parent;

                DPRINT("Forgotten object [%p-'%s', node: %p]\n",
                    obj, OCLASS(obj)->cl_ID?(char *)OCLASS(obj)->cl_ID:(char *)"<MCC>", node);

                app = parent = NULL;
                if (get(obj, MUIA_ApplicationObject, &app) && get(obj, MUIA_Parent, &parent))
                {
                    DPRINT("[%p] app=%p, parent=%p\n", obj, app, parent);

                    /* Keep the application object disposal for later */
                    if (obj == app)
                    {
                        DPRINT("[%p] Application => disposed later\n", obj);
                        continue;
                    }

                    /* No parents ? */
                    if (!TypeOfMem(app) && !TypeOfMem(parent))
                    {
                        DPRINT("[%p] Disposing a MUI object...\n", obj);
                        MUI_DisposeObject(obj);
                        DPRINT("[%p] Disposed\n", obj);
                    }
                    else
                        DPRINT("[%p] Has a parent, let it dispose the object\n", obj);
                }
                else
                    DPRINT("[%p] Bad object!\n", obj);
            }
            else
            {
                DPRINT("[%p] Disposing a BOOPSI object ...\n", obj);
                DisposeObject(obj);
                DPRINT("[%p] Disposed\n", obj);
            }
        }

        FreeMem(REMOVE(node), sizeof(*node));
    }

    /* Second round for applications objects */
    ForeachNodeSafe(&gObjectList, node, next)
    {
        Object *obj = node->obj;

        DPRINT("[%p] Disposing application...\n", obj);
        MUI_DisposeObject(obj);
        DPRINT("[%p] Application disposed\n", obj);

        FreeMem(node, sizeof(*node));
    }

    /* MCC disposing */
    ForeachNodeSafe(&gMCCList, mcc_node, next)
    {
        DPRINT("Disposing MCC node @ %p (mcc=%p-'%s')\n", mcc_node, mcc_node->mcc, mcc_node->mcc->mcc_Super->cl_ID);
        MUI_DeleteCustomClass(mcc_node->mcc);
        FreeMem(mcc_node, sizeof(*mcc_node));
    }

    if (NULL != CyberGfxBase)
    {
        DPRINT("Closing cybergfx library...\n");
        CloseLibrary(CyberGfxBase);
        CyberGfxBase = NULL;
    }

    if (NULL != LayersBase)
    {
        DPRINT("Closing layers library...\n");
        CloseLibrary(LayersBase);
        LayersBase = NULL;
    }

    if (NULL != MUIMasterBase)
    {
        DPRINT("Closing muimaster library...\n");
        CloseLibrary(MUIMasterBase);
        MUIMasterBase = NULL;
    }

    if (NULL != gMemPool)
    {
        DeletePool(gMemPool);
        gMemPool = NULL;
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
    PyObject *m, *d;

    NEWLIST((struct List *)&gObjectList);
    NEWLIST(&gMCCList);
    NEWLIST(&gToDisposeList);
    INIT_HOOK(&OnAttrChangedHook, OnAttrChanged);

    gMemPool = CreatePool(MEMF_PUBLIC|MEMF_SEM_PROTECTED, 1024, 512);
    if (NULL != gMemPool)
    {
        MUIMasterBase = OpenLibrary(MUIMASTER_NAME, MUIMASTER_VLATEST);
        if (NULL != MUIMasterBase)
        {
            LayersBase = OpenLibrary("layers.library", 50);
            if (NULL != LayersBase)
            {
                CyberGfxBase = OpenLibrary("cybergraphics.library", 50);
                if (NULL != CyberGfxBase)
                {
                    /* object -> pyobject database */
                    d = PyDict_New(); /* NR */
                    if (NULL != d)
                    {
                        int error = 0;

                        /* New Python types initialization */
                        error |= PyType_Ready(&PyRasterObject_Type);
                        error |= PyType_Ready(&PyBOOPSIObject_Type);
                        error |= PyType_Ready(&PyMUIObject_Type);
                        error |= PyType_Ready(&CHookObject_Type);
                        error |= PyType_Ready(&PyMethodMsgObject_Type);
                        error |= PyType_Ready(&PyEventHandlerObject_Type);

                        if (!error)
                        {
                            /* Module creation/initialization */
                            m = Py_InitModule3(MODNAME, _muimaster_methods, _muimaster__doc__);
                            if (NULL != m)
                            {
                                error = all_ins(m);
                                if (!error)
                                {
                                    ADD_TYPE(m, "PyBOOPSIObject", &PyBOOPSIObject_Type);
                                    ADD_TYPE(m, "PyMUIObject", &PyMUIObject_Type);
                                    ADD_TYPE(m, "_CHook", &CHookObject_Type);
                                    ADD_TYPE(m, "EventHandler", &PyEventHandlerObject_Type);

                                    PyModule_AddObject(m, "_obj_dict", d);
                                    gBOOPSI_Objects_Dict = d;

#ifdef WITH_PYCAIRO
                                    if (PyErr_Occurred())
                                        return;

                                    Pycairo_IMPORT;
                                    PyErr_Clear();
#endif

                                    return;
                                }

                                Py_DECREF(m);
                            }
                        }

                        Py_DECREF(d);
                    }
                    else
                        DPRINT("Failed to create object->pyobject dict\n");

                    CloseLibrary(CyberGfxBase);
                    CyberGfxBase = NULL;
                }
                else
                    DPRINT("Can't open library %s, V%u.\n", "cybergraphics.library", 50);

                CloseLibrary(LayersBase);
                LayersBase = NULL;
            }
            else
                DPRINT("Can't open library %s, V%u.\n", "layers.library", 50);

            CloseLibrary(MUIMasterBase);
            MUIMasterBase = NULL;
        }
        else
            DPRINT("Can't open library %s, V%u.\n", MUIMASTER_NAME, MUIMASTER_VLATEST);
    }
    else
        DPRINT("Failed to create a global memory pool\n");
}
//-

/* EOF */
