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

#define PyBOOPSIObject_OBJECT(o) (((PyBOOPSIObject *)(o))->node->n_Object)

#define PyBOOPSIObject_CHECK_OBJ(o) if (NULL == (o)) {                  \
        PyErr_SetString(PyExc_RuntimeError, "no BOOPSI object associated"); \
        return NULL; }

#define _between(a,x,b) ((x)>=(a) && (x)<=(b))
#define _isinobject(x,y) (_between(_mleft(obj),(x),_mright(obj)) && _between(_mtop(obj),(y),_mbottom(obj)))


/*
** Private Types and Structures
*/

typedef struct DoMsg_STRUCT {
    ULONG MethodID;
    ULONG data[0];
} DoMsg;

typedef struct CreatedObjectNode_STRUCT {
    struct MinNode           n_Node;
    Object *                 n_Object;
    BOOL                     n_IsMUI;
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

    CreatedObjectNode * node;
} PyBOOPSIObject;

typedef struct PyMUIObject_STRUCT {
    PyBOOPSIObject   base;
    PyObject *       children;
    PyRasterObject * raster;
} PyMUIObject;

typedef struct PyEventHandlerObject_STRUCT {
    PyObject_HEAD         

    struct MUI_EventHandlerNode * handler;
    PyObject *                    win_pyo;
    LONG                          muikey; /* copied from MUIP_HandleEvent msg */
    struct IntuiMessage           imsg;   /* copied from MUIP_HandleEvent->imsg */
    struct TabletData             tabletdata; /* copied from MUIP_HandleEvent msg */
    BYTE                          inobject;
    BYTE                          hastablet;
} PyEventHandlerObject;

typedef struct MCCData_STRUCT {
    PyObject *PythonObject;
} MCCData;


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
static struct MinList gCreatedObjectList;
static struct MinList gCreatedMCCList;


/*
** Module DocString
*/

//+ _muimaster__doc__
/*! \cond */
PyDoc_STRVAR(_muimaster__doc__,
"This module provides access to muimaster.library functionnalities.\n\
Refer to the library manual and corresponding MorphOS manual entries\n\
for more information on calls.");
/*! \endcond */
//-


/*
** Private Functions
*/

//+ PyMUIObjectFromObject
static PyObject *
PyMUIObjectFromObject(Object *mo)
{
    PyObject *pyo;

    if (NULL == mo)
        Py_RETURN_NONE;

    /* MUI object linked to a PyMUIObject? just incref and return it */
    pyo = (PyObject *)muiUserData(mo);
    if (NULL != pyo) {
        Py_INCREF(pyo);
        return pyo;
    }

    /* Allocate a new PyMUIObject */
    pyo = (PyObject *)PyObject_New(PyMUIObject, &PyMUIObject_Type); /* NR */
    if (NULL == pyo)
        return NULL;

    PyBOOPSIObject_OBJECT(pyo) = mo;
    muiUserData(mo) = (ULONG)pyo;

    return pyo;
}
//-
//+ OnAttrChanged
static void
OnAttrChanged(struct Hook *hook, Object *mo, ULONG *args) {
    PyObject *pyo;
    ULONG attr = args[0];
    ULONG value = args[1];

    pyo = (APTR) muiUserData(mo);

    /* In case of the Python object die before the MUI object */
    if (NULL != pyo){
        PyObject *res;

        Py_INCREF(pyo); /* to prevent that our object was deleted during methods calls */

        DPRINT("{%#lx} Py=%p-%s, MUI=%p, value=(%ld, %lu, %p)\n",
               attr, pyo, OBJ_TNAME_SAFE(pyo), mo, (LONG)value, value, (APTR)value);


        res = PyObject_CallMethod(pyo, "_notify_cb", "II", attr, value); /* NR */
        Py_XDECREF(res);

        Py_DECREF(pyo);
    }
}
//-
//+ python2long
/*
 * /!\ This function doesn't incref the given python object.
 * This one shall be kept valid if a reference is stored by the MUI object,
 * until the object is disposed or if the reference is released.
 */
static int
python2long(PyObject *obj, ULONG *value)
{
    Py_ssize_t buffer_len;

    if (PyString_Check(obj) || PyUnicode_Check(obj))
        *value = (ULONG)PyString_AsString(obj);
    else if (PyBOOPSIObject_Check(obj))
        *value = (ULONG)PyBOOPSIObject_OBJECT(obj);
    else if (PyCObject_Check(obj))
        *value = (ULONG)PyCObject_AsVoidPtr(obj);
    else if (PyObject_CheckReadBuffer(obj)) {
        if (PyObject_AsReadBuffer(obj, (const void **)value, &buffer_len) != 0)
            return 0;
    } else {
        PyObject *tmp = PyNumber_Int(obj);

        if (NULL == tmp) {
            PyErr_Format(PyExc_TypeError, "can't convert a %s object into an integer", OBJ_TNAME(obj));
            return 0;
        }

        if (PyLong_CheckExact(tmp))
            *value = PyLong_AsUnsignedLong(tmp);
        else
            *value = PyInt_AS_LONG(tmp);

        Py_DECREF(tmp);
    }

    DPRINT("%s object converted into integer: %ld, %lu, %lx\n", OBJ_TNAME(obj), (LONG)*value, *value, *value);
    return 1;
}
//-
//+ parse_attribute_entry
static int
parse_attribute_entry(PyObject *entry, ULONG *attr, ULONG *value)
{
    PyObject *value_obj;

    if (!PyArg_ParseTuple(entry, "IO:PyBOOPSIObject", attr, &value_obj)) /* BR */
        return FALSE;

    return python2long(value_obj, value);
}
//-
//+ attrs2tags
static struct TagItem *
attrs2tags(PyObject *self, PyObject *attrs)
{
    struct TagItem *tags;
    PyObject *fast;
    Py_ssize_t size;

    DPRINT("attrs: %p (%s)\n", attrs, OBJ_TNAME_SAFE(attrs));
    fast = PySequence_Fast(attrs, "Given object doesn't provide Sequence protocol.");
    if (NULL != fast) {
        size = PySequence_Fast_GET_SIZE(fast);
        tags = PyMem_Malloc(sizeof(struct TagItem) * (size+1));
        if (NULL != tags) {
            Py_ssize_t i;
            struct TagItem *tag;

            for (i=0, tag=tags; i < size; i++, tag++) {
                PyObject *entry = PySequence_Fast_GET_ITEM(fast, i);

                if ((NULL == entry) || !parse_attribute_entry(entry, &tag->ti_Tag, &tag->ti_Data))
                    goto error;

                DPRINT("  #%u: 0x%08x = 0x%08x\n", i, tag->ti_Tag, tag->ti_Data);
            }

            tags[size].ti_Tag = TAG_DONE;
            Py_DECREF(fast);
            return tags;

        error:
            PyMem_Free(tags);
        } else
            PyErr_NoMemory();
    
        Py_DECREF(fast);
    }

    return NULL;
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
                width  = w->Width - w->BorderLeft - w->BorderRight - 4;
                height = w->Height - w->BorderTop - w->BorderBottom - 4;
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


/*******************************************************************************************
** MCC MUI Object
*/

//+ mAskMinMax
static ULONG mAskMinMax(struct IClass *cl, Object *obj, struct MUIP_AskMinMax *msg)
{
    MCCData *data = INST_DATA(cl, obj);  
    PyObject *pyo, *res; 
    WORD minw, defw, maxw, minh, defh, maxh;
    
    DoSuperMethodA(cl, obj, msg);

    pyo = data->PythonObject;
    DPRINT("pyo=%p-%s\n", pyo, OBJ_TNAME(pyo));
    if ((NULL == pyo) || !PyObject_HasAttrString(pyo, "MCC_AskMinMax"))
        return 0;

    Py_INCREF(pyo);
    res = PyObject_CallMethod((PyObject *)pyo, "MCC_AskMinMax", "hhhhhh",
                              msg->MinMaxInfo->MinWidth,
                              msg->MinMaxInfo->DefWidth,
                              msg->MinMaxInfo->MaxWidth,
                              msg->MinMaxInfo->MinHeight,
                              msg->MinMaxInfo->DefHeight,
                              msg->MinMaxInfo->MaxHeight); /* NR */
    Py_DECREF(pyo); 
    
    if (NULL != res) {
        int result = PyArg_ParseTuple(res, "hhhhhh", &minw, &defw, &maxw, &minh, &defh, &maxh);

        Py_DECREF(res); 
        if (!result)
            return 0;
    }

    msg->MinMaxInfo->MinWidth  = minw;
    msg->MinMaxInfo->DefWidth  = defw;
    msg->MinMaxInfo->MaxWidth  = maxw;
    msg->MinMaxInfo->MinHeight = minh;
    msg->MinMaxInfo->DefHeight = defh;
    msg->MinMaxInfo->MaxHeight = maxh;

    return 0;
}
//-
//+ mSetup
static ULONG mSetup(struct IClass *cl, Object *obj, Msg msg)
{
    MCCData *data = INST_DATA(cl, obj);
    PyObject *pyo, *res;
    ULONG result;

    if (!DoSuperMethodA(cl, obj, msg))
        return FALSE;

    pyo = data->PythonObject;
    DPRINT("pyo=%p-%s\n", pyo, OBJ_TNAME(pyo));
    if ((NULL == pyo) || !PyObject_HasAttrString(pyo, "MCC_Setup"))
        return TRUE;

    Py_INCREF(pyo);
    res = PyObject_CallMethod((PyObject *)pyo, "MCC_Setup", NULL); /* NR */
    Py_DECREF(pyo); 
    
    if (NULL != res) {
        result = PyInt_AsLong(res);
        Py_DECREF(res);
    } else
        result = FALSE;

    return result;
}
//-
//+ mCleanup
static ULONG mCleanup(struct IClass *cl, Object *obj, Msg msg)
{
    MCCData *data = INST_DATA(cl, obj);
    PyObject *pyo, *res;

    pyo = data->PythonObject;
    DPRINT("%s: obj=%p, pyo=%p\n", __FUNCTION__, obj, pyo);
    if ((NULL != pyo)  && PyObject_HasAttrString(pyo, "MCC_Cleanup")) {
        Py_INCREF(pyo);
        res = PyObject_CallMethod((PyObject *)pyo, "MCC_Cleanup", NULL); /* NR */
        Py_XDECREF(res);
        Py_DECREF(pyo);
    }

    return DoSuperMethodA(cl, obj, msg);
}
//-
//+ mShow
static ULONG mShow(struct IClass *cl, Object *obj, Msg msg)
{
    MCCData *data = INST_DATA(cl, obj);
    PyObject *pyo, *res;
    ULONG result;

    if (!DoSuperMethodA(cl, obj, msg))
        return FALSE;

    pyo = data->PythonObject;
    DPRINT("pyo=%p\n", pyo);
    if ((NULL == pyo) || !PyObject_HasAttrString(pyo, "MCC_Show"))
        return TRUE;

    Py_INCREF(pyo);
    res = PyObject_CallMethod((PyObject *)pyo, "MCC_Show", NULL); /* NR */
    if (NULL != res)
        result = PyInt_AsLong(res);
    else
        result = TRUE;
    Py_XDECREF(res);
    Py_DECREF(pyo);

    return result;
}
//-
//+ mHide
static ULONG mHide(struct IClass *cl, Object *obj, Msg msg)
{
    MCCData *data = INST_DATA(cl, obj);
    PyObject *pyo, *res;

    pyo = data->PythonObject;
    DPRINT("obj=%p, pyo=%p\n", obj, pyo);
    if ((NULL != pyo)  && PyObject_HasAttrString(pyo, "MCC_Hide")) {
        Py_INCREF(pyo);
        res = PyObject_CallMethod((PyObject *)pyo, "MCC_Hide", NULL); /* NR */
        Py_XDECREF(res);
        Py_DECREF(pyo);
    }

    return DoSuperMethodA(cl, obj, msg);
}
//-
//+ mDraw
static ULONG mDraw(struct IClass *cl, Object *obj, struct MUIP_Draw *msg)
{
    MCCData *data = INST_DATA(cl, obj);
    PyObject *pyo, *res;
    struct Region *region, *oldregion = NULL;

    DoSuperMethodA(cl, obj, msg);

    pyo = data->PythonObject;
    DPRINT("pyo=%p\n", pyo);
    if ((NULL == pyo) || !PyObject_HasAttrString(pyo, "MCC_Draw"))
        return 0;

    if (PyObject_HasAttrString(pyo, "_clip")) {
        region = NewRegion();
        if (NULL != region) {
            struct Rectangle rect = { _left(obj), _mtop(obj), _mright(obj), _bottom(obj) };

            OrRectRegion(region, &rect);
            oldregion = InstallClipRegion(_window(obj)->WLayer, region);
        }
    } else
        region = NULL;

    Py_INCREF(pyo);
    res = PyObject_CallMethod((PyObject *)pyo, "MCC_Draw", "I", msg->flags); /* NR */
    Py_XDECREF(res);
    Py_DECREF(pyo);

    if (NULL != region) {
        InstallClipRegion(_window(obj)->WLayer, oldregion);
        DisposeRegion(region);
    }

    return 0;
}
//-
//+ mHandleEvent
static ULONG mHandleEvent(struct IClass *cl, Object *obj, struct MUIP_HandleEvent *msg)
{
    MCCData *data = INST_DATA(cl, obj);
    PyObject *pyo, *res;
    PyEventHandlerObject *ehn_obj;
    ULONG result;

    DPRINT("obj: %p, ehn: %p\n", obj, msg->ehn);

    pyo = data->PythonObject;
    DPRINT("pyo: %p-%s\n", pyo, OBJ_TNAME(pyo));
    if ((NULL == pyo) || !PyObject_HasAttrString(pyo, "MCC_HandleEvent"))
        return 0;

    ehn_obj = *(PyEventHandlerObject **)(&msg->ehn[1]);
    if (NULL == ehn_obj)
        return 0;

    DPRINT("ehn_obj=%p-%s\n", ehn_obj, OBJ_TNAME_SAFE(ehn_obj));

    if (ehn_obj->handler != msg->ehn) {
        PyErr_SetString(PyExc_TypeError, "mHandlerEvent called with inconsistant event handler!");
        return 0;
    }

    Py_INCREF(ehn_obj);

    /* Make a copy of data */
    ehn_obj->imsg = *msg->imsg;
    ehn_obj->muikey = msg->muikey;
    ehn_obj->inobject = _isinobject(msg->imsg->MouseX, msg->imsg->MouseY);
    ehn_obj->hastablet = NULL != ((struct ExtIntuiMessage *)msg->imsg)->eim_TabletData;

    if (ehn_obj->hastablet)
        ehn_obj->tabletdata = *((struct ExtIntuiMessage *)msg->imsg)->eim_TabletData;
    else
        memset(&ehn_obj->tabletdata, 0, sizeof(ehn_obj->tabletdata));

    Py_INCREF(pyo);
    res = PyObject_CallMethod((PyObject *)pyo, "MCC_HandleEvent", "O", ehn_obj); /* NR */
    if (NULL != res) {
        if (res == Py_None)
            result = 0;
        else
            result = PyLong_AsLong(res);
        Py_DECREF(res);
    } else
        result = 0;
    Py_DECREF(pyo);

    Py_DECREF(ehn_obj);

    return result;
}
//-
//+ MCC Dispatcher
DISPATCHER(mcc)
{
    ULONG result;
    PyObject *exception;

    switch (msg->MethodID) {
        case MUIM_AskMinMax    : result = mAskMinMax  (cl, obj, (APTR)msg); break;
        case MUIM_Setup        : result = mSetup      (cl, obj, (APTR)msg); break;
        case MUIM_Cleanup      : result = mCleanup    (cl, obj, (APTR)msg); break;
        case MUIM_Show         : result = mShow       (cl, obj, (APTR)msg); break;
        case MUIM_Hide         : result = mHide       (cl, obj, (APTR)msg); break;
        case MUIM_Draw         : result = mDraw       (cl, obj, (APTR)msg); break;
        case MUIM_HandleEvent  : result = mHandleEvent(cl, obj, (APTR)msg); break;
        default: result = DoSuperMethodA(cl, obj, msg);
    }

    exception = PyErr_Occurred();
    if (exception) {
        PyErr_WriteUnraisable(exception);
        PyErr_Clear();
    }

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
    CreatedObjectNode *node;

    node = malloc(sizeof(*node));
    if (NULL== node)
        return PyErr_NoMemory();

    self = (APTR)type->tp_alloc(type, 0); /* NR */
    if (NULL != self) {
        self->node = node;
        PyBOOPSIObject_OBJECT(self) = NULL;
        return (PyObject *)self;
    }

    free(node);
    return NULL;
}
//-
//+ boopsi_dealloc
static void
boopsi_dealloc(PyBOOPSIObject *self)
{
    Object *obj;

    obj = PyBOOPSIObject_OBJECT(self);
    DPRINT("self=%p, obj=%p, node=%p\n", self, obj, self->node);

    if (NULL != obj) {
        free(REMOVE(self->node));

        DPRINT("before DisposeObject(%p)\n", obj);
        DisposeObject(obj);
        DPRINT("after DisposeObject(%p)\n", obj);
    }

    ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}
//-
//+ boopsi_repr
static PyObject *
boopsi_repr(PyBOOPSIObject *self) {
    Object *obj;
    
    obj = PyBOOPSIObject_OBJECT(self);
    if (NULL != obj)
        return PyString_FromFormat("<%s at %p, object at %p>", OBJ_TNAME(self), self, obj);
    else
        return PyString_FromFormat("<%s at %p, no object>", OBJ_TNAME(self), self);
}
//-
//+ boopsi__create
static PyObject *
boopsi__create(PyBOOPSIObject *self, PyObject *args)
{
    UBYTE *classid;
    PyObject *attrs=NULL;
    Object *obj;
    struct TagItem *tags;
    STRPTR superid = NULL;
    struct MUI_CustomClass *mcc = NULL;

    if (!PyArg_ParseTuple(args, "sz|O:PyBOOPSIObject", &classid, &superid, &attrs)) /* BR */
        return NULL;

    DPRINT("ClassID: '%s'\n", classid);
    self->node->n_IsMUI = PyMUIObject_Check(self); 

    if (self->node->n_IsMUI) {
        CreatedMCCNode *node = NULL, *next;

        DPRINT("SuperID: '%s'\n", superid);
        if (NULL == classid)
            classid = superid;
        
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
    }

    /* The Python object is needed before convertir the attributes dict into tagitem array */
    if (NULL != attrs) {
        tags = attrs2tags((PyObject *)self, attrs);
        if (NULL != tags) {
            if (self->node->n_IsMUI) {
                if (NULL == mcc)
                    obj = MUI_NewObjectA(classid, tags);
                else
                    obj = NewObjectA(mcc->mcc_Class, NULL, tags);    
            } else
                obj = NewObjectA(NULL, classid, tags);
            
            PyMem_Free(tags);
        } else
            obj = NULL;
    } else if (self->node->n_IsMUI) {
        if (NULL == mcc)
            obj = MUI_NewObject(classid, TAG_DONE);
        else
            obj = NewObject(mcc->mcc_Class, NULL, TAG_DONE); 
    } else
        obj = NewObject(NULL, classid, TAG_DONE);

    if (NULL != obj) {
        DPRINT("New %s object @ %p (self=%p, node=%p, mcc=%p)\n", classid, obj, self, self->node, mcc);
        PyBOOPSIObject_OBJECT(self) = obj;
        ADDTAIL(&gCreatedObjectList, self->node);
        if (self->node->n_IsMUI) {
            muiUserData(obj) = (ULONG)self;
            self->node->n_MCC = mcc;   
            if (NULL != mcc) {
                ((MCCData *)INST_DATA(mcc->mcc_Class, obj))->PythonObject = (APTR)self;
            }
        }
        Py_RETURN_NONE;
    } else
        PyErr_Format(PyExc_SystemError, "NewObjectA() failed on class %s.", classid);

    return NULL;
}
//-
//+ boopsi__get
/*! \cond */
PyDoc_STRVAR(boopsi__get_doc,
"_get(attr, format) -> object\n\
\n\
Try to obtain value of an BOOPSI obejct attribute by calling the BOOPSI function GetAttr().\n\
The value returned by GetAttr() is converted by Py_BuildValue() using given format.");
/*! \endcond */

static PyObject *
boopsi__get(PyBOOPSIObject *self, PyObject *args)
{
    PyObject *format_obj;
    Object *obj;
    ULONG attr;
    ULONG value;
    char format[2];

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);
 
    if (!PyArg_ParseTuple(args, "IO:_get", &attr, &format_obj)) /* BR */
        return NULL;

    DPRINT("MUI=%p (%s - %s), attr=0x%08x\n", obj, OCLASS(obj)->cl_ID, OBJ_TNAME(self), attr);
    if (!GetAttr(attr, obj, &value))
        return PyErr_Format(PyExc_ValueError, "GetAttr(0x%08x) failed", (int)attr);
    DPRINT("value=(%d, %u, 0x%08lx)\n", (LONG)value, value, value);

    /* Format: Convertor class instance or char */
    if (PyString_CheckExact(format_obj) && (PyString_GET_SIZE(format_obj) == 1)) {
        format[0] = PyString_AS_STRING(format_obj)[0];
        
        DPRINT("Converting to format='%c'...\n", format[0]);
        /* Convert value into the right Python object */
        switch (format[0]) {
            case 'M':
                return PyMUIObjectFromObject((Object *)value);

            case 'p':
                return (PyObject *)PyCObject_FromVoidPtr((APTR)value, NULL);

            case 'b':
                if (value) {
                    Py_RETURN_TRUE;
                } else {
                    Py_RETURN_FALSE;
                }
                break;

            case 's':
            case 'z':
            case 'u':
            case 'i':
            case 'I':
            case 'k':
            case 'n':
            case 'c':
                format[1] = '\0';
                return Py_BuildValue(format, value);

            default:
                PyErr_Format(PyExc_ValueError, "Unsupported format: '%c'.", format[0]);
        }

        return NULL;
    } else {
        PyObject *res;      

        /* Array of pointers of fixed size */
        if (PyObject_HasAttrString(format_obj, "pointer_base")) {
            int i, n;
            char *ptr = (APTR)value;
            char format;

            res = PyObject_GetAttrString(format_obj, "pointer_base"); /* NR */
            if (NULL == res)
                return NULL;

            if (!PyString_CheckExact(res) || (PyString_GET_SIZE(res) != 1)) {
                PyErr_SetString(PyExc_TypeError, "convertor.pointer_base shall be a string of one character.");
                return NULL;
            }

            format = PyString_AS_STRING(res)[0];
            Py_DECREF(res);

            if (!PyObject_HasAttrString(format_obj, "size")) {
                PyErr_SetString(PyExc_TypeError, "ArrayOf instance without size attribute!");
                return NULL;
            }

            res = PyObject_GetAttrString(format_obj, "size"); /* NR */
            if (NULL == res)
                return NULL;

            if (!PyInt_CheckExact(res))
                return PyErr_Format(PyExc_TypeError, "convertor.size shall be a int not %s.", OBJ_TNAME(res));

            i = PyInt_AS_LONG(res);
            Py_DECREF(res);

            DPRINT("Converting %u pointer(s) into tuple of %c...\n", i, format);

            res = PyTuple_New(i); /* NR */
            if (NULL == res)
                return NULL;

            for (n=0; n < i; n++) {
                PyObject *o;
                
                switch (format) {
                    case 'I':
                        DPRINT("  %-04u: 0x%08x\n", n, *(ULONG *)ptr);
                        o = PyLong_FromUnsignedLong(*(ULONG *)ptr); /* NR */
                        ptr += sizeof(ULONG);
                        break;
                
                    default:
                        o = NULL;
                }

                if (NULL == o) {
                    Py_DECREF(res);
                    return NULL;
                }

                PyTuple_SET_ITEM(res, n, o); /* Steals a reference */
            }
            
            return res;
        }

        DPRINT("Converting using get method on object at %p\n", format_obj);
        Py_INCREF(format_obj);
        res = PyObject_CallMethod(format_obj, "get", "I", value); /* NR */
        Py_DECREF(format_obj);
        return res;
    }

    PyErr_SetString(PyExc_TypeError, "Format shall be an instance of convertor class or a single character string.");
    return NULL;
}
//-
//+ boopsi__set
/*! \cond */
PyDoc_STRVAR(boopsi__set_doc,
"_set(attr, value) -> None\n\
\n\
Try to set an attribute of the BOOPSI object by calling the BOOPSI function SetAttrs().\n\
Value should be a string, a unicode or something convertible into a int or a long.\n\
Note: No reference kept on the given value object!");
/*! \endcond */

static PyObject *
boopsi__set(PyBOOPSIObject *self, PyObject *args) {
    Object *obj;
    PyObject *value_obj, *convertor = NULL;
    ULONG attr;
    ULONG value;

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "IO|O:_set", &attr, &value_obj, &convertor)) /* BR */
        return NULL;
    
    if (NULL == convertor) {
        if (!python2long((PyObject *)value_obj, &value))
            return NULL;

        DPRINT("Attr 0x%lx set to value: %ld %ld %#lx on BOOPSI obj @ %p\n", attr, (LONG)value, value, value, obj);
        set(obj, attr, value);
    } else  {
        PyObject *res;
        
        Py_INCREF(value_obj);
        res = PyObject_CallMethod(convertor, "set", "(O)", value_obj); /* NR */
        Py_DECREF(value_obj);

        if (NULL == res)
            return res;

        if (!python2long((PyObject *)res, &value))
            return NULL;

        DPRINT("Attr 0x%lx set to pointer %p on BOOPSI obj @ %p\n", attr, value, obj);
        set(obj, attr, value);
  
        Py_DECREF(res);
    }

    DPRINT("done\n");
    
    /* We handle Python exception here because set an attribute can call a notification
       that will raise an exception. In this case the set fails also. */
    if (PyErr_Occurred())
        return NULL;

    Py_RETURN_NONE;
}
//-
//+ boopsi__do
/*! \cond */
PyDoc_STRVAR(boopsi__do_doc,
"_do(method, args) -> int\n\
\n\
Sorry, Not documented yet :-(");
/*! \endcond */

static PyObject *
boopsi__do(PyBOOPSIObject *self, PyObject *args) {
    PyObject *ret, *meth_data;
    Object *obj;
    DoMsg *msg;
    int meth, i, n;

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "IO!:_do", &meth, &PyTuple_Type, &meth_data)) /* BR */
        return NULL;

    DPRINT("DoMethod(obj=%p, meth=0x%08x):\n", obj, meth);

    n = PyTuple_GET_SIZE(meth_data);
    DPRINT("#  Data size = %d\n", n);
    msg = (DoMsg *) PyMem_Malloc(sizeof(DoMsg) + sizeof(ULONG) * n);
    if (NULL == msg)
        return PyErr_NoMemory();

    for (i = 0; i < n; i++) {
        PyObject *o = PyTuple_GET_ITEM(meth_data, i);
        ULONG *ptr = (ULONG *) &msg->data[i];

        if (!python2long(o, ptr)) {
            PyMem_Free(msg);
            return NULL;
        }

        DPRINT("#  args[%u]: %d, %u, 0x%08x\n", i, (LONG)*ptr, *ptr, *ptr);
    }

    /* Notes: objects given to the object dispatcher should remains alive during the call of the method,
     * even if this call cause some Python code to be executed causing a DECREF of these objects.
     * This is protected by the fact that objects have their ref counter increased until they remains
     * inside the argument tuple of this function.
     * So here there is no need to INCREF argument python objects.
     */

    msg->MethodID = meth;
    ret = PyInt_FromLong(DoMethodA(obj, (Msg) msg));
    DPRINT("done\n");
    
    return ret;
}
//-
//+ boopsi__do1
/*! \cond */
PyDoc_STRVAR(boopsi__do1_doc,
"_do1(method, arg) -> int\n\
\n\
Sorry, Not documented yet :-(");
/*! \endcond */

static PyObject *
boopsi__do1(PyBOOPSIObject *self, PyObject *args) {
    PyObject *ret;
    Object *obj;
    LONG meth, data;

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "IO&:_do", &meth, python2long, &data)) /* BR */
        return NULL;

    DPRINT("DoMethod(obj=%p, meth=0x%08x, data=0x%08x):\n", obj, meth, data);
    ret = PyInt_FromLong(DoMethod(obj, meth, data));
    DPRINT("done\n");

    return ret;
}
//-
//+ boopsi__add
/*! \cond */
PyDoc_STRVAR(boopsi__add_doc,
"_add(object) -> int\n\
\n\
Sorry, Not documented yet :-(");
/*! \endcond */

static PyObject *
boopsi__add(PyBOOPSIObject *self, PyObject *args) {
    PyObject *ret, *pychild;
    Object *obj, *child;
    int lock = FALSE;

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "O!|i:_add", &PyBOOPSIObject_Type, &pychild, &lock)) /* BR */
        return NULL;

    child = PyBOOPSIObject_OBJECT(pychild);
    PyBOOPSIObject_CHECK_OBJ(child);

    /* Warning: no reference kept on arg object after return ! */

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
/*! \cond */
PyDoc_STRVAR(boopsi__rem_doc,
"_rem(object, lock=False) -> int\n\
\n\
Sorry, Not documented yet :-(");
/*! \endcond */

static PyObject *
boopsi__rem(PyBOOPSIObject *self, PyObject *args) {
    PyObject *ret, *pychild;
    Object *obj, *child;
    int lock = FALSE;

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "O!|i:_rem", &PyBOOPSIObject_Type, &pychild, &lock)) /* BR */
        return NULL;

    child = PyBOOPSIObject_OBJECT(pychild);
    PyBOOPSIObject_CHECK_OBJ(child);

    DPRINT("OM_REMMEMBER: parent=%p, obj=%p\n", obj, child);

    /* Warning: no reference kept on arg object after return ! */

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
//+ boopsi_get_mo
static PyObject *
boopsi_get_mo(PyBOOPSIObject *self, void *closure)
{
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    return PyLong_FromVoidPtr(mo);
}
//-

static PyGetSetDef boopsi_getseters[] = {
    {"_mo",   (getter)boopsi_get_mo, NULL, "MUI object address", NULL},
    {NULL} /* sentinel */
};

static struct PyMethodDef boopsi_methods[] = {
    {"_create", (PyCFunction) boopsi__create, METH_VARARGS, NULL},
    {"_get",    (PyCFunction) boopsi__get,    METH_VARARGS, boopsi__get_doc},
    {"_set",    (PyCFunction) boopsi__set,    METH_VARARGS, boopsi__set_doc},
    {"_do",     (PyCFunction) boopsi__do,     METH_VARARGS, boopsi__do_doc},
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
        self->children = PyList_New(0); /* NR */
        if (NULL != self->children) {
            self->raster = (PyRasterObject *)PyObject_New(PyRasterObject, &PyRasterObject_Type); /* NR */
            if (NULL != self->raster)
                return (PyObject *)self;
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
    Py_VISIT(self->children);
    Py_VISIT(self->raster);
    return 0;
}
//-
//+ muiobject_clear
static int
muiobject_clear(PyMUIObject *self)
{
    Py_CLEAR(self->children);
    Py_CLEAR(self->raster);
    return 0;
}
//-
//+ muiobject_dealloc
static void
muiobject_dealloc(PyMUIObject *self)
{
    Object *mo, *app, *parent;
    CreatedObjectNode *node;
    
    mo = PyBOOPSIObject_OBJECT(self);
    node = ((PyBOOPSIObject *)self)->node;
    DPRINT("self=%p (%s): clear()\n", self, OBJ_TNAME(self));

    muiobject_clear(self);

    DPRINT("self=%p (%s), obj=%p, node=%p: MUI dealloc\n", self, OBJ_TNAME(self), mo, node);
    if (NULL != mo) {
        if (!get(mo, MUIA_ApplicationObject, &app) || !get(mo, MUIA_Parent, &parent)) {
            DPRINT("unable to free object %p!\n", mo);
            goto end;
        }

        DPRINT("Object %p: app=%p, parent=%p\n", mo, app, parent);
        
        /* Destroy only the Application object or not used objects */
        if ((mo == app) || ((NULL == app) && (NULL == parent))) {
            DPRINT("before MUI_DisposeObject(%p)\n", mo);
            MUI_DisposeObject(mo);
            DPRINT("after MUI_DisposeObject(%p)\n", mo);
        } else {
            DPRINT("  => not disposed (used)\n");

            /* Just unlink it */
            muiUserData(mo) = NULL;
            if (NULL != node->n_MCC)
                ((MCCData *)INST_DATA(OCLASS(mo), mo))->PythonObject = NULL;
        }

        free(REMOVE(node));    
    }

end:
    ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}
//-
//+ muiobject__nnset
/*! \cond */
PyDoc_STRVAR(muiobject__nnset_doc,
"_nnset(attr, value) -> None\n\
\n\
Like BOOPSIObject._set() but without triggering notification on MUI object.");
/*! \endcond */

static PyObject *
muiobject__nnset(PyMUIObject *self, PyObject *args)
{
    Object *obj;
    PyObject *value_obj;
    ULONG attr;
    LONG value;

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "IO:_nnset", &attr, &value_obj)) /* BR */
        return NULL;
    
    if (!python2long((PyObject *)value_obj, &value))
        return NULL;

    DPRINT("Attr 0x%lx set to value: %ld %ld %#lx on MUI obj @ %p\n", attr, (LONG)value, value, value, obj);
    nnset(obj, attr, value);
    DPRINT("done\n");

    Py_RETURN_NONE;
}
//-
//+ muiobject__notify
/*! \cond */
PyDoc_STRVAR(muiobject__notify_doc,
"_notify(trigattr, trigvalue) -> None\n\
\n\
Sorry, Not documented yet :-(");
/*! \endcond */

static PyObject *
muiobject__notify(PyMUIObject *self, PyObject *args)
{
    PyObject *trigvalue_obj;
    ULONG trigattr, trigvalue, value;
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    if (!PyArg_ParseTuple(args, "IO:_notify", &trigattr, &trigvalue_obj)) /* BR */
        return NULL;

    if (!python2long(trigvalue_obj, &trigvalue))
        return NULL;

    DPRINT("MO: %p, trigattr: %#lx, trigvalue('%s'): %ld, %lu, %#lx\n",
           mo, trigattr, OBJ_TNAME(trigvalue_obj), (LONG)trigvalue, trigvalue, trigvalue);

    if (MUIV_EveryTime == trigvalue)
        value = MUIV_TriggerValue;
    else
        value = trigvalue;

    /* If the object is already linked, take this link as the self object */
    if (0 != muiUserData(mo))
        self = (PyMUIObject *)muiUserData(mo);
    else
        muiUserData(mo) = (ULONG)self;

    DoMethod(mo, MUIM_Notify, trigattr, trigvalue,
             MUIV_Notify_Self, 4,
             MUIM_CallHook, (ULONG)&OnAttrChangedHook, trigattr, value);

    DPRINT("done\n");

    Py_RETURN_NONE;
}
//-
//+ muiobject_redraw
/*! \cond */
PyDoc_STRVAR(muiobject_redraw_doc,
"_redraw(flags) -> None\n\
\n\
Just direct call to MUI_Redraw(flags).");
/*! \endcond */

static PyObject *
muiobject_redraw(PyMUIObject *self, PyObject *args)
{
    Object *mo;
    ULONG flags;

    if (!PyArg_ParseTuple(args, "I:Redraw", &flags))
        return NULL;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    MUI_Redraw(mo, flags);

    Py_RETURN_NONE;
}
//- muiobject__notify
//+ muiobject_get_mleft
static PyObject *
muiobject_get_mleft(PyObject *self, void *closure)
{
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    return PyInt_FromLong(_mleft(mo));
}
//-
//+ muiobject_get_mright
static PyObject *
muiobject_get_mright(PyObject *self, void *closure)
{
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    return PyInt_FromLong(_mright(mo));
}
//-
//+ muiobject_get_mtop
static PyObject *
muiobject_get_mtop(PyObject *self, void *closure)
{
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    return PyInt_FromLong(_mtop(mo));
}
//-
//+ muiobject_get_mbottom
static PyObject *
muiobject_get_mbottom(PyObject *self, void *closure)
{
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    return PyInt_FromLong(_mbottom(mo));
}
//-
//+ muiobject_get_mdim
static PyObject *
muiobject_get_mdim(PyObject *self, void *closure)
{
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    if (0 == closure)
        return PyInt_FromLong(_mwidth(mo));
    else
        return PyInt_FromLong(_mheight(mo));
}
//-
//+ muiobject_get_mbox
static PyObject *
muiobject_get_mbox(PyObject *self, void *closure)
{
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    return Py_BuildValue("(HHHH)", _mleft(mo), _mtop(mo), _mright(mo), _mbottom(mo));
}
//-
//+ muiobject_get_sdim
static PyObject *
muiobject_get_sdim(PyObject *self, void *closure)
{
    Object *mo;
    struct Screen *scr;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    scr = _screen(mo);
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
    Object *mo;
    struct Screen *scr;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    scr = _screen(mo);
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
    Object *mo;
    ClassID id;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    id = OCLASS(mo)->cl_Super->cl_ID;
    if (NULL != id)
        return PyString_FromString(id);

    Py_RETURN_NONE;
}
//-
//+ muiobject_get__children
static PyObject *
muiobject_get__children(PyMUIObject *self, void *closure)
{
    Py_INCREF(self->children);
    return self->children;
}
//-
//+ muiobject_set__children
static int
muiobject_set__children(PyMUIObject *self, PyObject *value, void *closure)
{
    if (NULL != value) {
        PyErr_SetString(PyExc_TypeError, "This attribute can't be set");
        return -1;
    }

    Py_DECREF(self->children);
    self->children = PyList_New(0); /* NR */
    return NULL == self->children;
}
//-
//+ muiobject_get_rp
static PyObject *
muiobject_get_rp(PyMUIObject *self, void *closure)
{
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    self->raster->rp = _rp(mo);
    Py_INCREF((PyObject *)self->raster);

    return (PyObject *)self->raster;
}
//-

static PyGetSetDef muiobject_getseters[] = {
    {"MLeft",   (getter)muiobject_get_mleft,   NULL, "_mleft(obj)",   NULL},
    {"MRight",  (getter)muiobject_get_mright,  NULL, "_mright(obj)",  NULL},
    {"MTop",    (getter)muiobject_get_mtop,    NULL, "_mtop(obj)",    NULL},
    {"MBottom", (getter)muiobject_get_mbottom, NULL, "_mbottom(obj)", NULL},
    {"MHidth",  (getter)muiobject_get_mdim,    NULL, "_mwidth(obj)",   (APTR) 0},
    {"MHeight", (getter)muiobject_get_mdim,    NULL, "_mheight(obj)",  (APTR)~0},
    {"MBox",    (getter)muiobject_get_mbox,    NULL, "4-Tuple of the bounded box object values", NULL},
    {"SWidth",  (getter)muiobject_get_sdim,    NULL, "Screen Width",   (APTR) 0},
    {"SHeight", (getter)muiobject_get_sdim,    NULL, "Screen Height",  (APTR)~0},
    {"SRangeX", (getter)muiobject_get_srange,  NULL, "Screen X range", (APTR) 0},
    {"SRangeY", (getter)muiobject_get_srange,  NULL, "Screen Y range", (APTR)~0},
    {"_rp",     (getter)muiobject_get_rp,      NULL, "Object RastPort", NULL},
    {"_superid", (getter)muiobject_get__superid, NULL, "MUI SuperID", NULL},
    {"_children", (getter)muiobject_get__children, (setter)muiobject_set__children, "PRIVATE, DON'T TOUCH!", NULL},
    {NULL} /* sentinel */
};

static struct PyMethodDef muiobject_methods[] = {
    {"_nnset",      (PyCFunction) muiobject__nnset,      METH_VARARGS, muiobject__nnset_doc},
    {"_notify",     (PyCFunction) muiobject__notify,     METH_VARARGS, muiobject__notify_doc},
    {"Redraw",      (PyCFunction) muiobject_redraw,      METH_VARARGS, muiobject_redraw_doc},
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
    tp_getset       : muiobject_getseters,
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
//+ raster_scaled_blit8
/*! \cond */
PyDoc_STRVAR(raster_scaled_blit8_doc,
"ScaleBlit8(buffer, src_w, src_h, dst_x, dst_y, dst_w, dst_h)\n\
\n\
Blit given ARGB8 buffer on the raster. If src and dst size are different,\n\
performs a scaling before blitting at given raster position.\n\
\n\
src_w: source rectangle width.\n\
src_h: source rectangle height.\n\
dst_x: destination position on X-axis in the raster.\n\
dst_y: destination position on Y-axis in the raster.\n\
dst_w: destination width.\n\
dst_h: destination height.\n\
");
/*! \endcond */

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

    ScalePixelArray(buf, src_w, src_h, buf_size/src_h, self->rp, dst_x, dst_y, dst_w, dst_h, RECTFMT_ARGB);

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
    LONG l, t, w, h;
    UBYTE pen;

    if (NULL == self->rp) {
        PyErr_SetString(PyExc_TypeError, "Uninitialized raster object.");
        return NULL;
    }

    if (!PyArg_ParseTuple(args, "Biiii:Rect", &pen, &l, &t, &w, &h)) /* BR */
        return NULL;

    SetAPen(self->rp, pen);
    Move(self->rp, l, t);
    Draw(self->rp, l+w-1, t);
    Draw(self->rp, l+w-1, t+h-1);
    Draw(self->rp, l, t+h-1);
    Draw(self->rp, l, t);

    Py_RETURN_NONE;
}
//-

static struct PyMethodDef raster_methods[] = {
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
        self->handler = PyMem_Malloc(sizeof(*self->handler) + sizeof(APTR));
        if (NULL != self->handler) {
            *(PyEventHandlerObject **)(&self->handler[1]) = self;
            return (PyObject *)self;
        }

        Py_DECREF((PyObject *)self);
    }

    return NULL;
}
//-
//+ evthandler_traverse
static int
evthandler_traverse(PyEventHandlerObject *self, visitproc visit, void *arg)
{
    Py_VISIT(self->win_pyo);
    return 0;
}
//-
//+ evthandler_clear
static int
evthandler_clear(PyEventHandlerObject *self)
{
    if (NULL != self->win_pyo) {
        Object *mo = PyBOOPSIObject_OBJECT(self->win_pyo);

        DPRINT("%s: mo=%p\n", __FUNCTION__, mo);
        if (NULL != mo)
            DoMethod(mo, MUIM_Window_RemEventHandler, (ULONG)self->handler);
    }
 
    Py_CLEAR(self->win_pyo);
    return 0;
}
//-
//+ evthandler_dealloc
static void
evthandler_dealloc(PyEventHandlerObject *self)
{
    evthandler_clear(self);
    
    PyMem_Free(self->handler);
    
    self->ob_type->tp_free((PyObject *)self);
}
//-
//+ evthandler_install
static PyObject *
evthandler_install(PyEventHandlerObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *pyo;
    static CONST_STRPTR kwlist[] = {"object", "idcmp", "flags", "prio", NULL};
    Object *mo, *win;

    if (NULL != self->win_pyo) {
        PyErr_SetString(PyExc_TypeError, "Already installed handler, remove it before!");
        return NULL;
    }

    self->handler->ehn_Flags = 0;
    self->handler->ehn_Priority = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!I|Hb", (char **)kwlist,
            &PyMUIObject_Type, &pyo,
            &self->handler->ehn_Events,
            &self->handler->ehn_Flags,
            &self->handler->ehn_Priority)) /* BR */
        return NULL;

    mo = PyBOOPSIObject_OBJECT(pyo);
    PyBOOPSIObject_CHECK_OBJ(mo);

    win = _win(mo);
    if (NULL == win) {
        PyErr_SetString(PyExc_TypeError, "No Window MUI object found!");
        return NULL;
    }

    pyo = (PyObject *)muiUserData(win);
    if (NULL == pyo) {
        PyErr_SetString(PyExc_TypeError, "No Python object found for the attached MUI window");
        return NULL;
    }

    win = PyBOOPSIObject_OBJECT(pyo);
    PyBOOPSIObject_CHECK_OBJ(win);

    self->handler->ehn_Object = mo;
    self->handler->ehn_Class = OCLASS(mo);

    DPRINT("install handler  %p on win %p: idcmp=0x%lx, flags=%u, prio=%d\n", self->handler, win,
        self->handler->ehn_Events,
        self->handler->ehn_Flags,
        self->handler->ehn_Priority);

    Py_INCREF(pyo);
    self->win_pyo = pyo;
    DoMethod(win, MUIM_Window_AddEventHandler, (ULONG)self->handler);

    Py_RETURN_NONE;
}
//-
//+ evthandler_uninstall
static PyObject *
evthandler_uninstall(PyEventHandlerObject *self)
{
    Object *win;

    if (NULL == self->win_pyo) {
        PyErr_SetString(PyExc_TypeError, "Not installed handler, install it before!");
        return NULL;
    }

    win = PyBOOPSIObject_OBJECT(self->win_pyo);
    PyBOOPSIObject_CHECK_OBJ(win);

    DPRINT("uninstall handler %p on win %p\n", self->handler, win);
    DoMethod(win, MUIM_Window_RemEventHandler, (ULONG)self->handler);
    Py_CLEAR(self->win_pyo);   

    Py_RETURN_NONE;
}
//-
//+ evthandler_get_idcmp
static PyObject *
evthandler_get_idcmp(PyEventHandlerObject *self, void *closure)
{
    return PyLong_FromUnsignedLong(self->handler->ehn_Events);
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
    return PyBool_FromLong(self->imsg.Code & IECODE_UP_PREFIX);
}
//-
//+ evthandler_get_code
static PyObject *
evthandler_get_code(PyEventHandlerObject *self, void *closure)
{
    return PyInt_FromLong(self->imsg.Code & ~IECODE_UP_PREFIX);
}
//-

static PyGetSetDef evthandler_getseters[] = {
    {"idcmp", (getter)evthandler_get_idcmp, NULL, "IDCMP value", NULL},
    {"Up", (getter)evthandler_get_up, NULL, "True if Code has UP prefix", NULL},
    {"Code", (getter)evthandler_get_code, NULL, "IntuiMessage Code field (without UP prefix if exists)", NULL},
    {"td_NormTabletX", (getter)evthandler_get_normtablet, NULL, "Normalized tablet X (float [0.0, 1.0])", (APTR)0},
    {"td_NormTabletY", (getter)evthandler_get_normtablet, NULL, "Normalized tablet Y (float [0.0, 1.0])", (APTR)~0},
    {NULL} /* sentinel */
};

static PyMemberDef evthandler_members[] = {
    {"muikey",       T_LONG, offsetof(PyEventHandlerObject, muikey), RO, NULL},
    {"Class",        T_ULONG, offsetof(PyEventHandlerObject, imsg.Class), RO, NULL},
    {"RawCode",      T_USHORT, offsetof(PyEventHandlerObject, imsg.Code), RO, NULL},
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

    {NULL} /* sentinel */
};

static struct PyMethodDef evthandler_methods[] = {
    {"install",   (PyCFunction)evthandler_install,   METH_VARARGS, NULL},
    {"uninstall", (PyCFunction)evthandler_uninstall, METH_NOARGS, NULL},
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
** Module Functions
**
** List of functions exported by this module reside here
*/

//+ _muimaster_mainloop
/*! \cond */
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
/*! \endcond */

static PyObject *
_muimaster_mainloop(PyObject *self, PyObject *args)
{
    ULONG sigs = 0;
    PyObject *pyapp;
    Object *app;
    
    if (!PyArg_ParseTuple(args, "O!:mainloop", &PyMUIObject_Type, &pyapp))
        return NULL;

    app = PyBOOPSIObject_OBJECT(pyapp);
    PyBOOPSIObject_CHECK_OBJ(app);

    /* This code will not check that the given object is really an Application object;
     * That should be checked by the caller!
     */

    DPRINT("Goes into mainloop...\n");
    while (DoMethod(app, MUIM_Application_NewInput, (ULONG) &sigs) != MUIV_Application_ReturnID_Quit) {
        if (sigs)
            sigs = Wait(sigs | SIGBREAKF_CTRL_C);
        else
            sigs = SetSignal(0, 0);

        if (sigs & SIGBREAKF_CTRL_C) {
            PyErr_SetNone(PyExc_KeyboardInterrupt);
            return NULL;
        }

        if (PyErr_Occurred()) {
            DPRINT("bye mainloop with error...\n");
            return NULL;
        }
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

    if (!PyArg_ParseTuple(args, "O!s|zzb:mainloop", &PyMUIObject_Type, &pyo, &title, &init_drawer, &init_pat, &save))
        return NULL;

    mo = PyBOOPSIObject_OBJECT(pyo);
    PyBOOPSIObject_CHECK_OBJ(mo);

    win = mo;
    get(mo, MUIA_WindowObject, &win);
    filename = getfilename(win, title, init_drawer, init_pat, save);
    if (NULL == filename)
        Py_RETURN_NONE;

    return PyString_FromString(filename);
}
//-

/* module methods */
static PyMethodDef _muimaster_methods[] = {
    {"mainloop", _muimaster_mainloop, METH_VARARGS, _muimaster_mainloop_doc},
    {"getfilename", _muimaster_getfilename, METH_VARARGS, NULL},
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
    Object* keep_app = NULL;

    DPRINT("Closing module...\n");

    ForeachNodeSafe(&gCreatedObjectList, node, next) {
        Object *obj = node->n_Object;
        
        DPRINT("Lost object: %p, (node=%p)\n", obj, node);
        if (NULL != obj) {
            if (node->n_IsMUI) {
                Object *app, *parent;

                /* Remove invalid Python linkage! */
                if (NULL != node->n_MCC)
                    ((MCCData *)INST_DATA(OCLASS(obj), obj))->PythonObject = NULL;

                if (get(obj, MUIA_ApplicationObject, &app) && get(obj, MUIA_Parent, &parent)) {
                    DPRINT("  app=%p, parent=%p\n", app, parent);
                    if (obj == app)
                        keep_app = app;
                    else {
                        if ((NULL == app) && (NULL == parent)) {
                            DPRINT("  Disposing...\n");
                            MUI_DisposeObject(obj);
                        } else
                            DPRINT("  Used!\n");
                    }
                } else
                    DPRINT("  dad object!\n");
            } else {
                DPRINT("  Disposing...\n");
                DisposeObject(obj);
            }
        }

        free(node);
    }

    if (NULL != keep_app) {
        DPRINT("Disposing application...\n");
        MUI_DisposeObject(keep_app);
    }

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

    /* Module creation/initialization */
    m = Py_InitModule3(MODNAME, _muimaster_methods, _muimaster__doc__);
    if (all_ins(m)) return;

    ADD_TYPE(m, "PyBOOPSIObject", &PyBOOPSIObject_Type);
    ADD_TYPE(m, "PyMUIObject", &PyMUIObject_Type);
    ADD_TYPE(m, "EventHandler", &PyEventHandlerObject_Type);
}
//-

/* EOF */
