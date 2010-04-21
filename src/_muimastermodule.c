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


#define _between(a,x,b) ((x)>=(a) && (x)<=(b))
#define _isinobject(x,y) (_between(_mleft(obj),(x),_mright(obj)) && _between(_mtop(obj),(y),_mbottom(obj)))

#define ID_BREAK 0xABADDEAD
#define FLAG_OWNER (1<<0) /* bObject has been created by the PyObject */


/*
** Private Types and Structures
*/

typedef struct PyBOOPSIObject_STRUCT {
    PyObject_HEAD
    Object *       bObject;
    ULONG          flags;
} PyBOOPSIObject;

typedef struct PyMUIObject_STRUCT {
    PyBOOPSIObject base;
} PyMUIObject;


/*
** Private Variables
*/

static struct Library *MUIMasterBase;
static struct Library *CyberGfxBase;
static struct Library *LayersBase;

static PyTypeObject PyBOOPSIObject_Type;
static PyTypeObject PyMUIObject_Type;

static ULONG gModuleIsValid = FALSE; /* TRUE when module is valid and used */
static Object *gApp = NULL; /* Non-NULL if mainloop is running */
static PyObject *gBOOPSI_Objects_Dict = NULL;


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

static int objdb_add(Object *bObj, PyObject *pObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj); /* NR */
    PyObject *wref = PyWeakref_NewRef(pObj, NULL); /* NR */
    int res;

    res = PyDict_SetItem(gBOOPSI_Objects_Dict, key, wref);
    Py_XDECREF(wref);

    return res;
}

static void objdb_remove(Object *bObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj);

    PyDict_DelItem(gBOOPSI_Objects_Dict, key);
    Py_XDECREF(key);
}

static PyObject *objdb_get(Object *bObj)
{
    PyObject *key = PyLong_FromVoidPtr(bObj);
    PyObject *wref;

    wref = PyDict_GetItem(gBOOPSI_Objects_Dict, key); /* BR */
    Py_XDECREF(key);

    return PyWeakref_GetObject(wref);
}

//+ PyBOOPSIObject_GetObject
static Object *
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

//+ PyBOOPSIObject_DisposeObject
static int
PyBOOPSIObject_DisposeObject(PyObject *pObj)
{
    Object *bObj = PyBOOPSIObject_GetObject(pObj);

    if (NULL != bObj)
        return -1;
    
    /* remove from BOOPSI objects db */
    objdb_remove(bObj);

    /* BOOPSI/MUI destroy */
    DPRINT("Before DisposeObject(%p) (%p-'%s')\n", bObj, self, OBJ_TNAME(self));
    if (PyMUIObject_Check(self))
        MUI_DisposeObject(bObj);
    else
        DisposeObject(bObj);
    DPRINT("After DisposeObject(%p) (%p-'%s')\n", bObj, self, OBJ_TNAME(self));

    return 0;
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

    return self;
}
//-
//+ boopsi_dealloc
static void
boopsi_dealloc(PyBOOPSIObject *self)
{
    Object *bObj = PyBOOPSIObject_GET_OBJECT(obj);

    DPRINT("self=%p, bObj=%p\n", self, bObj);

    if ((NULL != bObj) && PyBOOPSIObject_ISOWNER(self))
        PyBOOPSIObject_DisposeObject(self);

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
Sorry, Not documented yet :-(");

static PyObject *
boopsi__dispose(PyBOOPSIObject *self)
{
    if (PyBOOPSIObject_DisposeObject(self))
        return NULL;

    Py_RETURN_NONE;
}
//-
//+ boopsi__loosed
static PyObject *
boopsi__loosed(PyBOOPSIObject *self)
{
    if (PyBOOPSIObject_ISOWNER(pychild))
        objdb_remove(child);

    PyBOOPSIObject_REM_FLAGS(self, FLAG_OWNER);

    Py_RETURN_NONE;
}
//-
//+ boopsi__add
PyDoc_STRVAR(boopsi__addchild_doc,
"_addchild(object) -> int\n\
\n\
Sorry, Not documented yet :-(");

static PyObject *
boopsi__addchild(PyBOOPSIObject *self, PyObject *args)
{
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

    if (PyBOOPSIObject_ISOWNER(pychild))
        objdb_remove(child);

    PyBOOPSIObject_REM_FLAGS(self, FLAG_OWNER);

    if (lock) {
        DPRINT("Lock\n");    
        DoMethod(obj, MUIM_Group_InitChange);
    }

    DPRINT("OM_ADDMEMBER: parent=%p, obj=%p\n", obj, child);         
    ret = PyInt_FromLong(DoMethod(obj, OM_ADDMEMBER, (ULONG)child));
    
    if (lock) {
        DPRINT("Unlock\n");        
        DoMethod(obj, MUIM_Group_ExitChange);
    }

    return ret;
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
    {"_loosed", (PyCFunction) boopsi__loosed, METH_NOARGS, NULL},

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

    return self;
}
//-

//+ muiobject_dealloc
static void
muiobject_dealloc(PyMUIObject *self)
{
    boopsi_dealloc((PyBOOPSIObject *)self);
}
//-

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
    
    //tp_methods      : muiobject_methods,
    //tp_members      : muiobject_members,
    //tp_getset       : muiobject_getseters,
};

/*******************************************************************************************
** Module Functions
**
** List of functions exported by this module reside here
*/

#if 0
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
#endif

/* module methods */
static PyMethodDef _muimaster_methods[] = {
    //{"mainloop", _muimaster_mainloop, METH_VARARGS, _muimaster_mainloop_doc},
    {NULL, NULL} /* Sentinel */
};


/*
** Public Functions
*/

//+ PyMorphOS_CloseModule
void
PyMorphOS_CloseModule(void) {

    DPRINT("Closing module...\n");

    ATOMIC_STORE(&gModuleIsValid, FALSE);

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

    MUIMasterBase = OpenLibrary(MUIMASTER_NAME, MUIMASTER_VLATEST);
    if (NULL != MUIMasterBase) {
        LayersBase = OpenLibrary("layers.library", 50);
        if (NULL != LayersBase) {
            CyberGfxBase = OpenLibrary("cybergraphics.library", 50);
            if (NULL != CyberGfxBase) {
                /* object -> pyobject database */
                d = PyDict_New(); /* NR */
                if (NULL != d) {
                    /* New Python types initialization */
                    if (!PyType_Ready(&PyBOOPSIObject_Type)) {
                        if (!PyType_Ready(&PyMUIObject_Type)) {
                            /* Module creation/initialization */
                            m = Py_InitModule3(MODNAME, _muimaster_methods, _muimaster__doc__);
                            if (!all_ins(m)) {
                                ADD_TYPE(m, "PyBOOPSIObject", &PyBOOPSIObject_Type);
                                ADD_TYPE(m, "PyMUIObject", &PyMUIObject_Type);
                                PyModule_AddObject(m, "_obj_dict", d);
                                
                                gBOOPSI_Objects_Dict = d;
                                gModuleIsValid = TRUE;
                                return;
                            }
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
