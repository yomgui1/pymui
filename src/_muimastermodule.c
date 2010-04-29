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

#define PyBOOPSIObject_Check(op) PyObject_TypeCheck(op, &PyBOOPSIObject_Type)
#define PyBOOPSIObject_CheckExact(op) ((op)->ob_type == &PyBOOPSIObject_Type)

#define PyMUIObject_Check(op) PyObject_TypeCheck(op, &PyMUIObject_Type)
#define PyMUIObject_CheckExact(op) ((op)->ob_type == &PyMUIObject_Type)

#define PyBOOPSIObject_GET_OBJECT(o) (((PyBOOPSIObject *)(o))->bObject)
#define PyBOOPSIObject_SET_OBJECT(o, x) (((PyBOOPSIObject *)(o))->bObject = (x))
#define PyBOOPSIObject_ADD_FLAGS(o, x) (((PyBOOPSIObject *)(o))->flags |= (x))
#define PyBOOPSIObject_REM_FLAGS(o, x) (((PyBOOPSIObject *)(o))->flags &= ~(x))
#define PyBOOPSIObject_ISOWNER(o) (0 != (((PyBOOPSIObject *)(o))->flags & FLAG_OWNER))

#define PyBOOPSIObject_SET_NODE(o, n) ({ \
    PyBOOPSIObject *_o = (PyBOOPSIObject *)(o); \
    ObjectNode *_n = (ObjectNode *)(n); \
    _o->node = _n; _n->obj = PyBOOPSIObject_GET_OBJECT(_o); })

#define _between(a,x,b) ((x)>=(a) && (x)<=(b))
#define _isinobject(x,y) (_between(_mleft(obj),(x),_mright(obj)) && _between(_mtop(obj),(y),_mbottom(obj)))

#define ID_BREAK 0xABADDEAD
#define FLAG_OWNER (1<<0) /* bObject has been created by the PyObject */

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
    Object * obj;
    LONG flags;
} ObjectNode;

typedef struct PyBOOPSIObject_STRUCT {
    PyObject_HEAD
    Object *       bObject;
    ObjectNode *   node;
    ULONG          flags;
} PyBOOPSIObject;

typedef struct PyMUIObject_STRUCT {
    PyBOOPSIObject base;
} PyMUIObject;

typedef struct CHookObject_STRUCT {
    PyObject_HEAD

    struct Hook * hook;
    struct Hook   _hook;
    PyObject *    callable;
} CHookObject;


/*
** Private Variables
*/

static struct Library *MUIMasterBase;
static struct Library *CyberGfxBase;
static struct Library *LayersBase;

static PyTypeObject PyBOOPSIObject_Type;
static PyTypeObject PyMUIObject_Type;
static PyTypeObject CHookObject_Type;

static ULONG gModuleIsValid = FALSE; /* TRUE when module is valid and used */
static Object *gApp = NULL; /* Non-NULL if mainloop is running */
static PyObject *gBOOPSI_Objects_Dict = NULL;
static struct MinList gObjectList;


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

//+ dispose_node
static void dispose_node(PyBOOPSIObject *pObj)
{
    ObjectNode *node = pObj->node;

    pObj->node = NULL;
    FreeMem(REMOVE(node), sizeof(*node));
}
//-
//+ objdb_add
static int objdb_add(Object *bObj, PyObject *pObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj); /* NR */
    PyObject *wref = PyWeakref_NewRef(pObj, NULL); /* NR */
    int res;

    /* BOOPSI -> Python relation */
    res = PyDict_SetItem(gBOOPSI_Objects_Dict, key, wref);
    Py_XDECREF(wref);

    return res;
}
//-
//+ objdb_remove
static void objdb_remove(Object *bObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj);

    PyDict_DelItem(gBOOPSI_Objects_Dict, key);
    Py_XDECREF(key);
}
//-
//+ objdb_get
static PyObject *objdb_get(Object *bObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj);
    PyObject *wref;

    wref = PyDict_GetItem(gBOOPSI_Objects_Dict, key); /* BR */
    Py_XDECREF(key);

    return PyWeakref_GetObject(wref);
}
//-
//+ loose
static void loose(PyBOOPSIObject *pObj)
{
    Object *bObj = PyBOOPSIObject_GET_OBJECT(pObj);

    if (PyBOOPSIObject_ISOWNER(pObj)) {
        PyBOOPSIObject_REM_FLAGS(pObj, FLAG_OWNER);

        objdb_remove(bObj);
        PyErr_Clear();

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
static int
PyBOOPSIObject_DisposeObject(PyBOOPSIObject *pObj)
{
    Object *bObj = PyBOOPSIObject_GetObject(pObj);

    if (NULL == bObj) {
        PyErr_SetString(PyExc_TypeError, "No valid BOOPSI object found");
        return -1;
    }

    /* remove from BOOPSI objects db */
    objdb_remove(bObj);
    PyErr_Clear();

    if (PyBOOPSIObject_ISOWNER(pObj)) {
        /* BOOPSI/MUI destroy */
        DPRINT("Before DisposeObject(%p) (%p-'%s')\n", bObj, pObj, OBJ_TNAME(pObj));
        if (PyMUIObject_Check(pObj))
            MUI_DisposeObject(bObj);
        else
            DisposeObject(bObj);
        DPRINT("After DisposeObject(%p) (%p-'%s')\n", bObj, pObj, OBJ_TNAME(pObj));

        /* Now delete the attached node */
        if (NULL != pObj->node) /* checked because the OWNER flag may have beem forced */
            dispose_node(pObj);
    } else
        DPRINT("BOOPSI object not disposed (not owner)\n");

    PyBOOPSIObject_SET_OBJECT(pObj, NULL);

    return 0;
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

    if (!gModuleIsValid) {
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
        }
    }

    return (PyObject *)self;
}
//-
//+ boopsi_dealloc
static void
boopsi_dealloc(PyBOOPSIObject *self)
{
    Object *bObj = PyBOOPSIObject_GET_OBJECT(self);

    DPRINT("self=%p-'%s', bObj=%p\n", self, OBJ_TNAME_SAFE(self), bObj);

    PyBOOPSIObject_DisposeObject(self);
    PyErr_Clear(); /* Silent errors */

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
Use it only if you know what you are doing!\n\
This object may be disposed elsewhere, not neccessary by you your code...");

static PyObject *
boopsi__dispose(PyBOOPSIObject *self)
{
    /* Force the OWNER flag (removed during the disposing) */
    PyBOOPSIObject_ADD_FLAGS(self, FLAG_OWNER);

    if (PyBOOPSIObject_DisposeObject(self))
        return NULL;

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

    if (lock) {
        DPRINT("Lock\n");    
        DoMethod(obj, MUIM_Group_InitChange);
    }

    DPRINT("OM_ADDMEMBER: parent=%p, child=%p\n", obj, child);
    ret = PyInt_FromLong(DoMethod(obj, OM_ADDMEMBER, (ULONG)child));

    if (lock) {
        DPRINT("Unlock\n");        
        DoMethod(obj, MUIM_Group_ExitChange);
    }

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

    if (lock) {
        DPRINT("Lock\n");    
        DoMethod(obj, MUIM_Group_InitChange);
    }

    DPRINT("OM_REMMEMBER: parent=%p, obj=%p\n", obj, child);         
    ret = PyInt_FromLong(DoMethod(obj, OM_REMMEMBER, (ULONG)child));
    
    if (lock) {
        DPRINT("Unlock\n");        
        DoMethod(obj, MUIM_Group_ExitChange);
    }

    /* Note: object is not owned anymore! So user should re-attach it immediately or dispose it */

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
    LONG isMCC = FALSE;
    PyObject *fast, *params = NULL;
    PyObject *overloaded_dict = NULL;
    struct TagItem *tags;
    ULONG n;
    Object *bObj;
    ObjectNode *node;

    /* Protect againts doubles */
    if (NULL != PyBOOPSIObject_GET_OBJECT(self)) {
        PyErr_SetString(PyExc_RuntimeError, "Already created BOOPSI Object");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "s|OiO!:PyBOOPSIObject", &classid, &params, &isMCC, &PyDict_Type, &overloaded_dict)) /* BR */
        return NULL;

    DPRINT("ClassID: '%s', isMCC: %d\n", classid, isMCC);

    /* Parse params sequence and convert it into tagitem's */
    fast = PySequence_Fast(params, "object tags shall be convertible into tuple or list"); /* NR */
    if (NULL == fast)
        return NULL;

    n = PySequence_Fast_GET_SIZE(fast);
    if (n > 0) {
        PyObject **tuples = PySequence_Fast_ITEMS(fast);
        ULONG i;

        tags = PyMem_Malloc(sizeof(struct TagItem) * n);
        if (NULL == tags) {
            Py_DECREF(fast);
            return PyErr_NoMemory();
        }

        for (i=0; i < n; i++) {
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
        
        if (PyErr_Occurred()) {
            Py_DECREF(fast);
            PyMem_Free(tags);
            return NULL;
        }
        
        Py_DECREF(fast);
    } else
        tags = NULL;

    /* Allocated a note to save the object reference.
     * It will be used at module cleanup to flush BOOPSI/MUI.
     * Note: PyMem_xxx() functions are not used here as the python context
     * is not valid during this cleanup stage.
     */
    node = AllocMem(sizeof(ObjectNode), MEMF_PUBLIC | MEMF_CLEAR | MEMF_SEM_PROTECTED);
    if (NULL == node) {
        if (NULL != tags)
            PyMem_Free(tags);
        return PyErr_NoMemory();
    }

    DPRINT("Node created @ %p\n", node);

    /* Creating the BOOPSI/MUI object */
    if (PyMUIObject_Check(self)) {
        bObj = MUI_NewObjectA(classid, tags);
        node->flags |= NODE_FLAG_MUI;
    } else
        bObj = NewObjectA(NULL, classid, tags);

    if (NULL != tags)
        PyMem_Free(tags);

    if (NULL != bObj) {
        DPRINT("New '%s' object @ %p (self=%p-'%s')\n", classid, bObj, self, OBJ_TNAME(self));

        /* Add to the BOOPSI objects database */
        if (objdb_add(bObj, (PyObject *) self)) {
            if (PyMUIObject_Check(self))
                MUI_DisposeObject(bObj);
            else
                DisposeObject(bObj);

            FreeMem(node, sizeof(*node));
            return NULL;
        }

        PyBOOPSIObject_SET_OBJECT(self, bObj);
        PyBOOPSIObject_ADD_FLAGS(self, FLAG_OWNER);
        PyBOOPSIObject_SET_NODE(self, node);

        ADDTAIL(&gObjectList, node);

        Py_RETURN_NONE;
    }

    FreeMem(node, sizeof(*node));
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

    obj = PyBOOPSIObject_GetObject(self);
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

    obj = PyBOOPSIObject_GetObject(self);
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

static PyGetSetDef boopsi_getseters[] = {
    {"_object", (getter)boopsi_get_object, NULL, "BOOPSI object address", NULL},
    {NULL} /* sentinel */
};

static PyNumberMethods boopsi_as_number = {
    nb_nonzero : (inquiry)boopsi_nonzero,
};

static struct PyMethodDef boopsi_methods[] = {
    {"_loosed", (PyCFunction) boopsi__loosed, METH_NOARGS, boopsi__loosed_doc},
    {"_dispose", (PyCFunction) boopsi__dispose, METH_NOARGS, boopsi__dispose_doc},
    {"_addchild", (PyCFunction) boopsi__addchild, METH_VARARGS, boopsi__addchild_doc},
    {"_remchild", (PyCFunction) boopsi__remchild, METH_VARARGS, boopsi__remchild_doc},
    {"_create", (PyCFunction) boopsi__create, METH_VARARGS, boopsi__create_doc},
    {"_get",    (PyCFunction) boopsi__get,    METH_VARARGS, boopsi__get_doc},
    {"_set", (PyCFunction) boopsi__set, METH_VARARGS, boopsi__set_doc},
    {"_do",     (PyCFunction) boopsi__do, METH_VARARGS, boopsi__do_doc},
    {"_do1",    (PyCFunction) boopsi__do1,    METH_VARARGS, boopsi__do1_doc},

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
        /**/
    }

    return (PyObject *)self;
}
//-
//+ muiobject_dealloc
static void
muiobject_dealloc(PyMUIObject *self)
{
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
//+ muiobject_get_data
static PyObject *
muiobject_get_data(PyObject *self, void *closure)
{
    Object *obj;
    LONG data;

    obj = PyBOOPSIObject_GetObject((PyObject *)self);
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
            return PyErr_Format(PyErr_SystemError, "[INTERNAL ERROR] bad closure given to muiobject_get_data()");
    }
    
    return PyInt_FromLong(data);
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
    {NULL} /* sentinel */
};

static struct PyMethodDef muiobject_methods[] = {
    {"_nnset", (PyCFunction) muiobject__nnset, METH_VARARGS, muiobject__nnset_doc},
    {"Redraw", (PyCFunction) muiobject_redraw, METH_O, muiobject_redraw_doc},
    {NULL} /* sentinel */
};

static PyTypeObject PyMUIObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_base         : &PyBOOPSIObject_Type,
    tp_name         : "_muimaster.PyMUIObject",
    tp_basicsize    : sizeof(PyMUIObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    tp_doc          : "MUI Objects",

    tp_new          : (newfunc)muiobject_new,
    //tp_traverse     : (traverseproc)muiobject_traverse,
    //tp_clear        : (inquiry)muiobject_clear,
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
        /* Check if the object is owned by a valid PyBOOPSIObject object */
        pObj = objdb_get(bObj);
        DPRINT("pObj: %p\n", pObj);
        if (NULL != pObj) {
            if (!TypeOfMem(pObj))
                return PyErr_Format(PyExc_ValueError, "value '%x' is not a valid system pointer", (unsigned int)pObj);
            return pObj;
        }
    }

    /* NULL Object or owner not known */
    pObj = (PyObject *)PyObject_New(PyBOOPSIObject, &PyBOOPSIObject_Type);
    if (NULL != pObj) {
        PyBOOPSIObject_SET_OBJECT(pObj, bObj);
        ((PyBOOPSIObject *)pObj)->flags = 0;
    }

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

    /* NULL Object or owner not known */
    pObj = (PyObject *)PyObject_New(PyMUIObject, &PyMUIObject_Type);
    if (NULL != pObj) {
        PyBOOPSIObject_SET_OBJECT(pObj, bObj);
        ((PyBOOPSIObject *)pObj)->flags = 0;
        ((PyBOOPSIObject *)pObj)->node = NULL;
    }

    return pObj;
}
//-

/* module methods */
static PyMethodDef _muimaster_methods[] = {
    {"mainloop", _muimaster_mainloop, METH_VARARGS, _muimaster_mainloop_doc},
    {"_ptr2pyobj", _muimaster_pyobjfromptr, METH_VARARGS, NULL},
    {"_ptr2pyboopsi", _muimaster_ptr2pyboopsi, METH_VARARGS, NULL},
    {"_ptr2pymui", _muimaster_ptr2pymui, METH_VARARGS, NULL},
    {NULL, NULL} /* Sentinel */
};


/*
** Public Functions
*/

//+ PyMorphOS_CloseModule
void
PyMorphOS_CloseModule(void)
{
    ObjectNode *node;
    APTR next;

    DPRINT("Closing module...\n");

    ATOMIC_STORE(&gModuleIsValid, FALSE);

    ForeachNodeSafe(&gObjectList, node, next) {
        Object *app, *obj = node->obj;

        if (NULL != obj) {
            /* Python is not perfect, PyMUI not also and user design even less :-P
             * If PyMUI user has forgotten to 'loose' the owner flag or if Python hasn't
             * disposed all Python objects when module is cleaned, the object node is here.
             * In anycase, the BOOPSI object is considered as owned and diposable.
             * But for MUIA_Parentobject, we can check if the object is really a child or not.
             * If it's a child, the object is not disposed.
             */
            if (node->flags & NODE_FLAG_MUI) {
                Object *parent;

                DPRINT("Forgotten object [%p-'%s', node: %p]\n",
                    obj, OCLASS(obj)->cl_ID?(char *)OCLASS(obj)->cl_ID:(char *)"<MCC>", node);

                app = parent = NULL;
                if (get(obj, MUIA_ApplicationObject, &app) && get(obj, MUIA_Parent, &parent)) {
                    DPRINT("[%p] app=%p, parent=%p\n", obj, app, parent);

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
                        DPRINT("[%p] Has a parent, let it dispose the object\n", obj);
                } else
                    DPRINT("[%p] Bad object!\n", obj);
            } else {
                DPRINT("[%p] Disposing a BOOPSI object ...\n", obj);
                DisposeObject(obj);
                DPRINT("[%p] Disposed\n", obj);
            }
        }

        FreeMem(REMOVE(node), sizeof(*node));
    }

    /* Second round for applications objects */
    ForeachNodeSafe(&gObjectList, node, next) {
        Object *obj = node->obj;

        DPRINT("[%p] Disposing application...\n", obj);
        MUI_DisposeObject(obj);
        DPRINT("[%p] Application disposed\n", obj);

        FreeMem(node, sizeof(*node));
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
    PyObject *m, *d;

    NEWLIST((struct List *)&gObjectList);

    MUIMasterBase = OpenLibrary(MUIMASTER_NAME, MUIMASTER_VLATEST);
    if (NULL != MUIMasterBase) {
        LayersBase = OpenLibrary("layers.library", 50);
        if (NULL != LayersBase) {
            CyberGfxBase = OpenLibrary("cybergraphics.library", 50);
            if (NULL != CyberGfxBase) {
                /* object -> pyobject database */
                d = PyDict_New(); /* NR */
                if (NULL != d) {
                    int error = 0;

                    /* New Python types initialization */
                    error |= PyType_Ready(&PyBOOPSIObject_Type);
                    error |= PyType_Ready(&PyMUIObject_Type);
                    error |= PyType_Ready(&CHookObject_Type);

                    if (!error) {
                        /* Module creation/initialization */
                        m = Py_InitModule3(MODNAME, _muimaster_methods, _muimaster__doc__);
                        if (NULL != m) {
                            error = all_ins(m);
                            if (!error) {
                                ADD_TYPE(m, "PyBOOPSIObject", &PyBOOPSIObject_Type);
                                ADD_TYPE(m, "PyMUIObject", &PyMUIObject_Type);
                                ADD_TYPE(m, "_CHook", &CHookObject_Type);
                        
                                PyModule_AddObject(m, "_obj_dict", d);
                        
                                gBOOPSI_Objects_Dict = d;
                                gModuleIsValid = TRUE;
                                return;
                            }

                            Py_DECREF(m);
                        }
                    }

                    Py_DECREF(d);
                } else
                    DPRINT("Failed to create object->pyobject dict\n");

                CloseLibrary(CyberGfxBase);
                CyberGfxBase = NULL;
            } else
                DPRINT("Can't open library %s, V%u.\n", "cybergraphics.library", 50);

            CloseLibrary(LayersBase);
            LayersBase = NULL;
        } else
            DPRINT("Can't open library %s, V%u.\n", "layers.library", 50);

        CloseLibrary(MUIMasterBase);
        MUIMasterBase = NULL;
    } else
        DPRINT("Can't open library %s, V%u.\n", MUIMASTER_NAME, MUIMASTER_VLATEST);
}
//-

/* EOF */
