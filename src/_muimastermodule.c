/***************************************************************************//**
 *** \file _muimastermodule.c
 *** \author ROGUEZ "Yomgui" Guillaume
 *** \date 2007/06/06
 ***
 *** \brief Python wrapper for muimaster.library
 ***
 *******************************************************************************/

/* Dev notes:

***** Ma vie, mon oeuvre... *****

* "dur dur... très dur!"

Pour faire un 'wrapper' Python pour MUI, tout le problème est qu'il faut savoir quand un objet meurt (= OM_DISPOSE).
Car comme l'objet Python va garder une référence  sur cet objet MUI (ou BOOPSI comme on veut...), il faut donc être sur
que si on détruit ce dernier, l'objet MUI l'est aussi (ca c'est la partie simple: on appel MUI_DisposeObject () durant le dispose
de l'objet python), mais aussi indiquer à l'objet python que l'objet MUI est détruit si jamais la méthode OM_DISPOSE de ce dernier
est appelée (extérieurement, pas depuis le wrapper bien-sûr pour ne pas faire une boucle-infinie avec le premier cas).
Evidement c'est ce dernier cas où tous les problèmes surgissent...

Pourquoi? Car comment être certain d'être notifié (du côté python) de l'appel à la méthode OM_DISPOSE?
De quoi dispose t'on alors?

1) Ne cherchons pas du côté de la classe Notify. Le système de notification de MUI ne fonctionne que sur des changenents
de valeurs des attributs des objets... pas des méthodes.

2) BOOPSI? Pouvoir savoir si OM_DISPOSE est appelé à coups-sur serait de contrôler le code du dispatcher de l'objet MUI.

Comment faire cela? Ils y a plusieurs possibilitées:

    a) Faire une classe 'wrapper' dont la super-classe serait identique à l'objet BOOPSI où on aurait le contrôle du dispatcher,
    en particulier de notre méthode OM_DISPOSE et où on appelerait CoerceMethod() avec la classe d'origine de l'instance wrappée.
    
    => problèmes: vu que la classe d'origine s'attend à avoir ses données d'instance rattachés au pointeur associé il faut donc copier
    ces données juste après la création donc pendant OM_NEW. Ainsi la classe d'origine n'ira pas taper n'importe où en mémoire.
    C'est faisable, mais... quand on crée l'objet avec notre custom classe on passe les arguments comme si c'était la vraie classe, là c'est ok.
    Mais comment fait-on pour une instance déjà créer, ailleur que par ntore code Python? On ne peut-pas créer une instance de notre custom class
    pour contenir cette instance car pour faire cela notre custom classe doit avoir comme super la même classe que l'instance d'origine.
    Or on ne connait pas les paramètres qu'il faut employer avec cette super classe! Il est trés parfaitement possible d'avoir des paramètres
    obligatoires qu'on ne peut deviner. Ceci nous empêche alors d'utilisé des instances d'objets BOOPSI (= MUI) crées ailleur
    que par notre module Python. Trop restrictif... abandonnons cette solution. Et même si on on fait une impasse sur les instances externes
    d'autres problèmes sont à résoudre comme des classes qui gardent des pointeurs sur les instances (alors qu'on va justement créer une nouvelle
    instance qui wrappe la première...), ce que je soupconne fortement car d'après quelques tests mes instance de classe Window ne veulent pas
    êtres   reconnues par la classe Application (et donc rattachées...).
    
    b)  Disons qu'on garde alors notre instance qu'on veut embarquer dans une objet Python, on va donc s'attaquer juste au hook du dispatcher
    qui est sauvé dans la structure IClass assocée avec l'instance. Remplaçons donc les fonctions h_Entry et h_SubEntry de façon à faire executer
    notre propre dispatcher, qui lui-même appelera le dispatcher d'origine qu'on aura préalablement sauvé (d'ailleur rien que ce point est un problème).
    
    => problèmes: il faut savoir que l'adresse du hook est l'adresse de la structure IClass puisque la structure Hook y est embarquée au début.
    C'est pour cela que le prototype du dispatcher commence par struct IClass * et non pas par struct Hook * comme tout hook car en fait
    c'est la même chose ici. Le dispatcher étant tout simplement appelé par CallHook (ou CallHookA). On peut ce dire 'cool! Alors appelons
    dans notre dispatcher custom le dispatcher d'origine!'... Et bah non, car comme on vient de le dire, on n'appel pas la fonction directement
    mais on passe par CallHook, qui s'attend à avoir un pointeur sur un hook. Mais on ne peut pas passer une nouvelle structure hook
    remplie avec les fonctions d'origines, car le pointeur change donc les données qui suivent la structure ne sont plus celle de la structure IClass.
    Donc, soit juste avant d'appeler avec CallHook le "hook-IClass" on revient avec les fonctions d'origines et on remet notre dispatcher
    just après l'appel, et ainsi la classe d'origine n'y voit que du feu (mais cela rajoute du code qui ralentit le dispatcher), soit on appel comme
    un gros cochon la fonction h_Entry "à la main" (avec tout ce que cela implique pour MorphOS = setup des registres 68k,
    appel de la couche émulation, ...). Alors déjà c'est franchement plus très propre tout cela mais rajoutons qu'on est en train de modifier le code
    de la structure IClass, qui nous appartient pas du tout et donc on ne gère rien niveau vie (on retire comment notre disptacher si la classe
    doit  être détruite?). Et c'est pas tout car on touche à des classes étant quasiement à coups-sûr utilisées ailleur que par notre module.
    Résultat si notre module n'est pas 100% robuste on crash tous le système... et quand on quitte python on a intêret à faire le ménage proprement!
    Alors solution envisageable mais très peut fiable (et je n'ai même pas parlé comment enregistré les fonctions du hook d'orginine!).

    c) Patcher une fonction:
    - J'ai tenté de patcher DisposeObject() de l'intuition.library. Effectivement cette fonction est bien appelé fréquement pour détruire un object.
    Malheureusement cela n'est pas systèmatique, on peut-très bien appeler 'à la main' la méthode OM_DIPOSE et le meilleur (ou pire..) des exemples
    pour cela est la fonction MUI_DiposeObject() de la muimaster.library. Patcher cette dernière alors (aussi...)? Cela n'arrange en rien
    l'appel 'à la main'. Donc on oublis.
    
    d) Il me reste plus comme choix de patcher la rootclass... C'est pas très propre, mais au moins on patch uniquement qu'une seule classe.
    L'idée est donc de modifier (comme expliqué en 2)) le hook de la classe root pour appeler notre prope dispatcher, propre à avertir
    le pendant pythonesque de l'objet de la décision morbide de l'objet BOOPSI (donc MUI par l'occasion).
    Reste à savoir où sauver les anciennes valeurs du hook. Sachant de plus qu'il ne faut faire cela qu'une seule fois (on va pas cummuler
    les patches n'est-ce pas...) et vu que notre module peut-être initialisé plusieur fois (au moins une fois par tâche utilisant
    la bibliothèque Python), le plus simple est d'externaliser la procédure de patch dans un code à part, en attendant que le système
    d'initialisation des modules Python pour MorphOS implémente un appel unique (ce que je ne pense pas au passage).
    Maintenant qu'on est d'accord, sur la façon de connaìt§re à coup-sûr la mort d'un objet, il faut trouver un moyen de mettre en relation,
    l'objet MUI avec sont pendant Python.
    Côté Python pas de pb, c'est enregistrer par notre module dans la structure Data de l'objet Python.
    Côté BOOPSI maintenant... Sauf erreur de ma part, impossible de mettre un pointeur (celui de notre objet Python) quelque part dans l'instance
    de l'object :-( . J'ai vérifé 20x, rien!
    Unique façon restante, utiliser une table de correspondance BOOPSI -> Python. Pour accélérer la recherche dans cette table
    on pourra utiliser une indexation par hachage du pointeur de l'objet BOOPSI. Reste à dimensionner tout cela pour que cela reste
    efficace en terme d'accés.
    Dernier point pour la route: comme les modules sont liés (en terme de données) au process exécutant, la table de correspondance
    l'est donc aussi!
    Donc si un process A demande de tuer un objet x et qu'un process B utilisant le module Python posséde un objet Python y
    lié avec cet objet x, comment allons nous retrouver cette table et comment avertir le process B?
    Il faut donc lier cette table avec le code de notre dispatcher, table qui contiendra des objets Python de différentes instances
    de notre module. Les objets python seront déliés de la partie BOOPSI dans le dispatcher. L'accés au data du côté Python sera
    protégée par l'utilisation d'un sémaphore pour gérer l'aspect multi-processes. Comme un objet BOOPSI peut-être lié à de multiples
    objets Python, on utilisera une liste pour chaque objet BOOPSI, donnant ces objets Python liés.
    
3) Ré-évalutation:
    Due à la complexité du code généré par une version où chaque objet BOOPSI peut-être associé avec plusieurs objets Python
    (cas de plusieurs appli utilisant le module, se partagant un objets BOOPSI), une simplification s'impose...
    
    Définition des régles:
        REG-01: associativité 1-1 entre BOOPSI et Python.
        REG-02: code non re-entrant (même pour la destruction, donc attention!)
        REG-03: pas de communications d'objets entre tâches.
        REG-04: seulement la tâche ayant associée l'object python et l'objet boopsi peut les dissocier.
        
4) News du 01/11/07:
    L'implémentation du 2-d aurait du fonctionner...  en théorie. Mais la pratique ne l'est pas du tout! Après une discussion IRC
    avec Stuntzi il s'avère que MUI ne suit pas les règles de BOOPSI, encore moins les appels indirects aux dispatchers des classes internes.
    Ceci expliquant l'impossibilité de patcher les dispatchers des classes MUI => il ne sont pas appeler par le pointeur dans la structure IClass.
    Devant ce fait il ne reste donc plus qu'une seule façon d'opérer: sous-classer toute classe utilisée. Cette dernière implique
    certaines restrictions que je ne souhaitait pas (cela explique que j'en avais pas encore parlé):
        - Le module ne pourra qu'opèrer sur des objets créé par lui-même. Aucun objet de l'extérieur (=déjà créé).
        - Impossible de passer un objet X du process l'ayant créé vers un autre. MUIM_Application_PushMethod ne peut-être utilisé.
        (Ceci n'est pas encore certain... il faudra y réfléchir après l'implémentation de la phase 1).
        - Pas d'objets 'builtins' => on ne peut pas les sous-classer!

Autre soucis: quitter Python doit de-allouer tout objets, même ceux qui ont encore des ref > 0. Le pb évident c'est qu'on ne peut pas le faire
dans n'importe quel ordre: si on prend un objet A ayant une référence sur un objet B, qu'on détruit l'objet B puis le A, si le A doit opérérer
sur l'objet B on est dans le baba! A va accéder à un objet mort, donc de la mémoire aléatoire => crash.
C'est ce qui arrive en ce moment (20080107) quand je quitte Python: l'objet Application n'est pas détruit le premier (aléas l'algorythme interne
de Python quand il détruit tout), mais par exemple un objet Text inclus dans une fenêtre, incluse dans l'appli...

- Solution:
=> augmenter le compteur de réf de l'objet Python ou un autre privé quand l'objet MUI est "parenté" dans un autre objet MUI, à
l'instar de Python.
=> Je pense que cela sera un compteur privé (histoire de pas tout mélanger).

*/

/* Notes pour la documentation utilisateur

- Expliquer le pb de garder des références des valeurs données (_set/_nnset le font automatiquement, pas _do ou tout
autre méthodes de classe.).

*/

/*
** Project Includes
*/

#include <Python.h>


/*
** System Includes
*/

#include <emul/emulregs.h>
#include <clib/debug_protos.h>

#include <proto/alib.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/intuition.h>
#include <proto/utility.h>
#include <proto/muimaster.h>

#define NDEBUG

#define USE_PYAMIGA_HELP_MACROS
#include <pyamiga/_coremod.h>


/*
** Private Macros and Definitions
*/

#ifndef MODNAME
#define MODNAME "_muimaster"
#endif

#ifndef INITFUNC
#define INITFUNC init_muimaster
#endif

#if defined __GNUC__
    #define ASM
    #define SAVEDS
#else
    #define ASM    __asm
    #define SAVEDS __saveds
#endif

#define CHECK_OBJ(o) if (NULL == (o)) {                                 \
        PyErr_SetString(PyExc_RuntimeError, "no MUI object associated"); \
        return NULL; }

#define MUIObject_Check(op) PyObject_TypeCheck(op, &MUIObject_Type)
#define MUIObject_CheckExact(op) ((op)->ob_type == &MUIObject_Type)

/* Class dispatcher helpers */

#define DISPATCHER(Name) \
    static ULONG DSP_##Name(void); \
    struct EmulLibEntry GATE_DSP_##Name = { TRAP_LIB, 0, (void (*)(void)) DSP_##Name }; \
    static ULONG DSP_##Name(void) { struct IClass *cl=(struct IClass*)REG_A0; Msg msg=(Msg)REG_A1; Object *obj=(Object*)REG_A2;
#define DISPATCHER_REF(Name) &GATE_DSP_##Name
#define DISPATCHER_END }

/* attributes */
#define TAG_PYMOD (TAG_USER | (0xCAFE << 16))
#define MUIA_PyMod_PyObject (TAG_PYMOD | 0x100) /* i.g */
#define MUIM_PyMod_CallHook (TAG_PYMOD | 0x000)

/*
** Private Types and Structures
*/

typedef struct DoMsg_STRUCT {
    ULONG MethodID;
    long data[0];
} DoMsg;

typedef struct OnAttrChangedMsg_STRUCT {
    PyObject *  py_obj;
    ULONG       attr;
    ULONG       value;
} OnAttrChangedMsg;

typedef struct MUIObject_STRUCT {
    CPointer    base;
    PyObject *  refdict; // -> GC mandatory. Used for attributes [REQ-04-B]
    ULONG       refcnt;  // Reference counter like in Python but between MUI objects [REQ-04-C]
} MUIObject;

typedef struct PyModMCCData_STRUCT {
    PyObject *pmd_PyObject;
} PyModMCCData;

typedef struct MCCNode_STRUCT {
    struct MinNode              mn_Node;
    struct MUI_CustomClass *    mn_MCC;
} MCCNode;


/*
** Private Variables
*/

static struct Hook OnAttrChangedHook;
static PyTypeObject MUIObject_Type;
static struct MinList classes;

PYAMIGA_CORE_DECL_TYPES;
PYAMIGA_CORE_DECL_API;


/*
** Public Variables
*/

struct Library *MUIMasterBase;


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
** PyMod MCC: methods and dispatcher
*/

//+ PyModMCC_New
static ULONG
PyModMCC_New(struct IClass *cl, Object *obj, struct opSet *msg) {
    PyModMCCData *data;
    struct TagItem *tstate, *tag;
    PyObject *pyo = NULL;
    
    /* MUI object creation */
    obj = (Object *) DoSuperMethodA(cl, obj, msg);
    if (!obj) return 0;
    
    /* Parse tags */
    tstate = msg->ops_AttrList;
    while (NULL != (tag = NextTagItem(&tstate))) {
        switch (tag->ti_Tag) {
            case MUIA_PyMod_PyObject:
                pyo = (PyObject *) tag->ti_Data;
                break;
        }
    }

    DPRINT("Link PyObject @ %p\n", pyo);

    /* Check defaults */
    if (NULL == pyo)
        return CoerceMethod(cl, obj, OM_DISPOSE);
    
    /* Setup instance data */
    data = INST_DATA(cl, obj);
    data->pmd_PyObject = pyo;

    return (ULONG) obj;
}
//- PyModMCC_New
//+ PyModMCC_Dispose
static ULONG
PyModMCC_Dispose(struct IClass *cl, Object *obj, Msg msg) {
    PyModMCCData *data = INST_DATA(cl, obj);
    PyObject *pyo = data->pmd_PyObject;

    DPRINT("MUI=%p, PyObj=%p\n", obj, pyo);
    
    // The python object may has been already unlinked
    if (NULL != pyo) {
        CPointer_SET_ADDR(pyo, NULL);
        data->pmd_PyObject = NULL;
    }

    return DoSuperMethodA(cl, obj, msg);
}
//- PyModMCC_Dispose
//+ PyModMCC_Get
static ULONG
PyModMCC_Get(struct IClass *cl, Object *obj, struct opGet *msg) {
    PyModMCCData *data = INST_DATA(cl, obj);

    if (MUIA_PyMod_PyObject == msg->opg_AttrID) {
        *(msg->opg_Storage) = (ULONG) data->pmd_PyObject;
        return TRUE;
    }

    return DoSuperMethodA(cl, obj, msg);
}
//- PyModMCC_Get
//+ PyMod MCC Dispatcher
DISPATCHER(PyModMCC) {
    PyModMCCData *data;
    PyObject *pyobj;

    //DPRINT("cl=%p, obj=%p, method=%#x\n", cl, obj, msg->MethodID);
    
    switch (msg->MethodID) {
    case OM_NEW:     return PyModMCC_New(cl, obj, (APTR) msg);
    case OM_DISPOSE: return PyModMCC_Dispose(cl, obj, (APTR) msg);
    case OM_GET:     return PyModMCC_Get(cl, obj, (APTR) msg);

        /* following methods should never be handled by a Python user method */
    case MUIM_Notify:
    case MUIM_CallHook:
    case MUIM_Application_NewInput:
    case 0x80428910:
    case 0x8042295f:
    case 0x80426688:
        return DoSuperMethodA(cl, obj, msg);
        
    }

    /* Try to call Python a method for this BOOPSI method, if exists */
    if (msg->MethodID & TAG_USER) {
        data = INST_DATA(cl, obj);
        pyobj = data->pmd_PyObject;
        if (NULL != pyobj) {
            PyObject *result_obj;

            Py_INCREF(pyobj); // because a bad method can destroy this object
            result_obj = PyObject_CallMethod(pyobj, "_OnBoopsiMethod", "kk", msg->MethodID, (ULONG)(msg + 1));
            Py_DECREF(pyobj);

            if (NULL != result_obj) {
                LONG res;

                /* Do not call super ? */
                if (result_obj != Py_None)
                    res = PyLong_AsUnsignedLong(result_obj);
                else
                    res = DoSuperMethodA(cl, obj, msg);

                Py_DECREF(result_obj);
                return res;
            } else
                return 0;
        }
    }
    
    return DoSuperMethodA(cl, obj, msg);
}
DISPATCHER_END
//- PxMod MCC Dispatcher


/*
** Private Functions
*/

//+ convertFromPython
static LONG
convertFromPython(PyObject *obj, long *value) {
    DPRINT("value @ %p\n", value);

    if (PyString_Check(obj)) {
        *value = (LONG) PyString_AS_STRING(obj);
    } else if (CPointer_Check(obj)) {
        *value = (LONG) CPointer_GET_ADDR(obj);
    } else {
        PyObject *o = PyNumber_Int(obj);

        if (NULL == o) {
            PyErr_Format(PyExc_TypeError, "can't convert a %s object into an integer", OBJ_TNAME(obj));
            return -1;
        }

        if (PyLong_CheckExact(o)) {
            *value = PyLong_AsUnsignedLong(o);
        } else {
            *value = PyInt_AS_LONG(o);
        }

        Py_DECREF(o);
    }

    DPRINT("%s object converted into integer: %ld %lu %lx\n", OBJ_TNAME(obj),
           (LONG) *value, (ULONG) *value, (ULONG) *value);

    return 0;
}
//-
//+ OnAttrChanged
static void
OnAttrChanged(struct Hook *hook, Object *obj, OnAttrChangedMsg *msg) {
    PyObject *res, *pyo_attr, *pyo_value;
    LONG value = msg->value;

    DPRINT("Attribute %#lx Changed for PyMCC object @ %p (MUI=%p) to %ld %lu %p\n",
           msg->attr, msg->py_obj, obj, value, (ULONG) value, (APTR) value);
    
    Py_INCREF(msg->py_obj); // to prevent that our object was deleted during methods calls.

    /* Get the attribute object */
    DPRINT("Calling py_obj.GetAttribute(id=0x%08x)...\n", msg->attr);
    pyo_attr = PyObject_CallMethod(msg->py_obj, "GetAttribute", "k", msg->attr);
    if (NULL != pyo_attr) {
        DPRINT("attr found: %p\n", pyo_attr);

        /* Convert the integer value into its Python representation */
        DPRINT("Get attr.format...\n");
        res = PyObject_GetAttrString(pyo_attr, "format");
        if (NULL != res) {
            char *format = PyString_AS_STRING(res);
            DPRINT("format: '%s'\n", format);

            /* Converting this attribute into right Python object */
            pyo_value = Py_BuildValue(format, value);
            Py_DECREF(res);
            if (NULL != pyo_value) {
                /* Call the high-level notify method */
                DPRINT("Calling OnAttrChanged(pyo_attr: %p, pyo_value: %p)...\n", pyo_attr, pyo_value);
                PyObject_CallMethod(msg->py_obj, "_OnAttrChanged", "OO", pyo_attr, pyo_value);

                Py_DECREF(pyo_value);
            }
        }
        Py_DECREF(pyo_attr);
    }
    Py_DECREF(msg->py_obj);
    return;
}
//-
//+ _keep_ref
static int
_keep_ref(MUIObject *obj, ULONG attr, PyObject *value)
{
    PyObject *key;

    DPRINT("keep ref on object @ %p (type=%s)\n", value, value->ob_type->tp_name);

    key = PyInt_FromLong(attr);
    if (NULL == key) {
        PyErr_SetString(PyExc_RuntimeError, "Can't create key for the internal reference");
        return -1;
    }

    return PyDict_SetItem(obj->refdict, key, value);
}
//-
//+ _set_base
static LONG
_set_base(MUIObject *obj, PyObject *args, ULONG *attr, LONG *value) {
    PyObject *v;
    char keep;

    if (!PyArg_ParseTuple(args, "IOb:_set_base", attr, &v, &keep))
        return -1;
    
    if (convertFromPython(v, value))
        return -1;

    DPRINT("Attr \033[32m0x%lx\033[0m set to value (%s): %ld %ld %#lx on obj @ \033[32m0x%p\033[0m\n",
           *attr, keep?"saved":"not saved", *value, *value, *value, CPointer_GET_ADDR(obj));

    if (keep)
        return _keep_ref(obj, *attr, v);
    
    return 0;
}
//-
//+ myMUI_NewObject
static Object *
myMUI_NewObject(MUIObject *pyo, ClassID id, struct TagItem *tags) {
    MCCNode *node;
    struct MUI_CustomClass *mcc = NULL;
    
    /* First check if this ClassID wasn't sub-classed before */
    DPRINT("Searching for ClassID '%s'\n", id);
    ForeachNode(&classes, node) {
        if (!strcmp(id, node->mn_MCC->mcc_Super->cl_ID)) {
            mcc = node->mn_MCC;
            break;
        }
    }
    
    if (NULL == mcc) {
        /* Create a new MCC for this ClassID */
        DPRINT("No MCC found, sub-classing...\n");
        
        /* Creating a new MCC node */
        node = (MCCNode *) malloc(sizeof(MCCNode));
        if (NULL == node) return NULL;
        
        mcc = MUI_CreateCustomClass(NULL, id, NULL,
                                    sizeof(PyModMCCData),
                                    DISPATCHER_REF(PyModMCC));
        DPRINT("New MCC @ %p\n", mcc);
        if (NULL == mcc) {
            free(node);
            return NULL;
        }
        
        node->mn_MCC = mcc;
        ADDTAIL(&classes, node);
        DPRINT("Node %p: MCC @ %p\n", node, node->mn_MCC);
    } else {
        /* Already sub-classed */
        DPRINT("MCC already sub-classed\n");
    }
    
    /* Create the MUI object now with the right MCC */
    DPRINT("Creating object with mcc=%p (super id='%s')...\n", mcc, id);
    if (NULL != tags) {
        return (Object *) NewObject(mcc->mcc_Class, NULL,
                                    MUIA_PyMod_PyObject, (ULONG) pyo,
                                    TAG_MORE, tags);
    } else {
        return (Object *) NewObject(mcc->mcc_Class, NULL,
                                    MUIA_PyMod_PyObject, (ULONG) pyo);
    }
}
//- myMUI_NewObject


/*******************************************************************************************
** MUIObject_Type
*/

//+ muiobject_new
static PyObject *
muiobject_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    MUIObject *self;
    PyObject *obj = NULL;
    APTR address = NULL;
    char *keys[] = {"address", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O:PyMuiObject", keys, &obj))
        return NULL;

    if (NULL != obj) {
        if (MUIObject_Check(obj)) {
            DPRINT("direct MUIObject @ %p (type='%s')\n", obj, OBJ_TNAME(obj));
            Py_INCREF((PyObject *) self);
            return (PyObject *) self; /* WARNING: the init method of the 'self' type may be called after
                                       * return if 'type' is a subclass of MUIObject_Type.
                                       */
        }

        /* Now try to obtain an address from the given object */
        if (!CPointer_Convert((PyObject *) obj, &address))
            return NULL;

        if (NULL == address) Py_RETURN_NONE;

        /* obtain from the Object the associated PyMuiObject and returns it */
        if (!get(address, MUIA_PyMod_PyObject, &self) || (NULL == self))
            return PyErr_Format(PyExc_RuntimeError, "Object @ %p doesn't seem to be associated with a PyMuiObject.", address);

        DPRINT("Associated object to %p: %p\n", address, self);

        Py_INCREF((PyObject *) self);
        return (PyObject *) self; /* WARNING: the init method of the 'self' type may be called after
                                   * return if 'type' is a subclass of MUIObject_Type.
                                   */
    }

    self = (MUIObject *) type->tp_alloc(type, 0);
    if ((NULL == self) || CPointer_Init((PyObject *) self, (APTR)-1, NULL, NULL))
        Py_CLEAR(self);
    else {
        CPointer_SET_ADDR(self, NULL);

        self->refdict = PyDict_New();
        if (NULL != self->refdict)
            self->refcnt = 0;
        else
            Py_CLEAR(self);
    }

    DPRINT("MUIObject.init(self=%p)\n", self);

    return (PyObject *) self;
}
//- muiobject_new
//+ muiobject_dealloc
static void
muiobject_dealloc(MUIObject *self) {
    Object *obj;
    
    obj = CPointer_GET_ADDR(self);
    DPRINT("MUIObject.dealloc(self=%p, refcnt=%lu, MUI=%p)\n", self, self->refcnt, obj);

    if (NULL != obj) {        
        /* Note: using get() on MUIA_Parent doesn't work for Window objets for example.
         * => The parent of a window isn't the application object!
         */
    
        assert(0 == self->refcnt);

        DPRINT("before MUI_DisposeObject(%p)\n", obj);
        MUI_DisposeObject(obj);
        DPRINT("after MUI_DisposeObject(%p)\n", obj);
    }

    Py_XDECREF(self->refdict);
    CPointer_Type.tp_dealloc((PyObject *) self);
}
//- muiobject_dealloc
//+ muiobject_repr
static PyObject *
muiobject_repr(MUIObject *self) {
    Object *obj;
    
    obj = CPointer_GET_ADDR(self);
    if (NULL != obj)
        return PyString_FromFormat("<%s at %p, MUI object at %p>", OBJ_TNAME(self), self, obj);
    else
        return PyString_FromFormat("<%s at %p, MUI object disposed>", OBJ_TNAME(self), self);
}
//- muiobject_repr
//+ muiobject_traverse
static int
muiobject_traverse(MUIObject *self, visitproc visit, void *arg) {
    return visit(self->refdict, arg);
}
//- muiobject_traverse
//+ muiobject_clear
static int
muiobject_clear(MUIObject *self) {
    PyDict_Clear(self->refdict);
    return 0;
}
//- muiobject_clear
//+ muiobject__incref
/*! \cond */
PyDoc_STRVAR(muiobject__incref_doc,
"_incref() -> None\n\
\n\
Use this function to increment the internal MUI reference counter.\n\
When this counter reach 0, the object can be deallocated by the garbage collector of Python.\n\
See also method _decref().");
/*! \endcond */

static PyObject *
muiobject__incref(MUIObject *self)
{
    Object *obj;
    
    // Increment the MUI reference counter only if a MUI object exists.
    obj = CPointer_GET_ADDR(self);
    CHECK_OBJ(obj);

    assert(self->refcnt < ULONG_MAX);

    // We keep alive the Python objet if some MUI refs exists.
    if (0 == self->refcnt) {
        Py_INCREF((PyObject *)self);
    }

    self->refcnt++;

    Py_RETURN_NONE;
}
//- muiobject__incref
//+ muiobject__decref
/*! \cond */
PyDoc_STRVAR(muiobject__decref_doc,
"_decref() -> None\n\
\n\
Use this function to decrement the internal MUI reference counter.\n\
When this counter reach 0, the object can be deallocated by the garbage collector of Python.\n\
See also method _incref().");
/*! \endcond */

static PyObject *
muiobject__decref(MUIObject *self)
{
    Object *obj;
    
    // Decrement the MUI reference counter only if a MUI object exists.
    obj = CPointer_GET_ADDR(self);
    CHECK_OBJ(obj);

    if (self->refcnt) {
        self->refcnt--;
        
        // Permit the Python object to die
        if (0 == self->refcnt) {
            Py_DECREF((PyObject *)self);
        }
    }

    Py_RETURN_NONE;
}
//- muiobject__decref
//+ muiobject__create
/*! \cond */
PyDoc_STRVAR(muiobject__create_doc,
"_create(ClassID [, data]) -> bool\n\
\n\
Calling this function create the MUI object using the giben class ID\n\
and an optional tags dictionary. This object is linked to the Python object.\n\
When a MUI object is created with this function you can create a new one\n\
with the same Python object. Call _dispose() on it before, to do that.");
/*! \endcond */

static PyObject *
muiobject__create(MUIObject *self, PyObject *args) {
    Object *mui_obj;
    char *cl;
    PyObject *data;
    struct TagItem *tags;

    /* Checking that no MUI object is already linked */
    mui_obj = CPointer_GET_ADDR(self);
    if (NULL != mui_obj) {
        PyErr_SetString(PyExc_RuntimeError, "the MUI object is already created");
        return NULL;
    }

    data = NULL;
    tags = NULL;
    if (!PyArg_ParseTuple(args, "s|O!", &cl, &PyDict_Type, &data))
        return NULL;

    if (NULL != data) {
        PyObject *k, *v;
        int n, p, i;

        n = PyDict_Size(data);
        DPRINT("Data size = %d\n", n);
        tags = (struct TagItem *) PyMem_New(struct TagItem, n+1);
        if (NULL == tags) return PyErr_NoMemory();

        for (p=i=0; i < n; i++) {
            struct TagItem *tag = &tags[i];
        
            if (!PyDict_Next(data, &p, &k, &v)) break;

            k = PyNumber_Int(k);
            if (NULL == k) {
                PyMem_Free(tags);  
                PyErr_SetString(PyExc_TypeError, "data's key should be coercable into an integer object");
                return NULL;
            }
        
            if (PyLong_CheckExact(k))
                tag->ti_Tag = PyLong_AsUnsignedLong(k);
            else
                tag->ti_Tag = PyInt_AS_LONG(k);    

            if (0 == tag->ti_Tag) {
                PyMem_Free(tags);        
                PyErr_SetString(PyExc_ValueError, "attribute can't be zero");
                return NULL;
            }

            if (convertFromPython(v, &tag->ti_Data)) {
                PyMem_Free(tags);
                return NULL;
            }

            Py_DECREF(k); 

            DPRINT("tag: 0x%08lx, data: %ld %lu %p\n", tag->ti_Tag, (LONG) tag->ti_Data, tag->ti_Data, (APTR) tag->ti_Data);
        }

        tags[i].ti_Tag = TAG_DONE;
    }

    /* Notes: Here, Python objects passed througth function argument have their references increased
     * case by case depending on flags of each attributes defined in mui_attribute dict of the class.
     * But a call to the _init method should be done to handle that before calling _create.
     */

    mui_obj = myMUI_NewObject(self, cl, tags);
    DPRINT("MUI_NewObject(\"%s\") = \033[32m%p\033[0m\n", cl, mui_obj);
    
    PyMem_Free(tags);
    
    if (NULL == mui_obj) {
        PyErr_SetString(PyExc_RuntimeError, "can't create a new MUI object");
        return NULL;
    }

    CPointer_SET_ADDR(self, mui_obj);
    Py_RETURN_TRUE;
}
//- muiobject__create
//+ muiobject__dispose
/*! \cond */
PyDoc_STRVAR(muiobject__dispose_doc,
"_dispose() -> bool\n\
\n\
Dispose the underlaying MUI object if MUI internal reference counter is 0.\n\
If not, nothing is done.\n\
Note: Disposing a MUI object can dispose some other linked MUI objects too.");
/*! \endcond */

static PyObject *
muiobject__dispose(MUIObject *self) {
    Object *obj;

    obj = CPointer_GET_ADDR(self);
    CHECK_OBJ(obj);

    DPRINT("PyObj: %p, MUI obj: %p, refcnt=%lu\n", self, obj, self->refcnt);

    if (self->refcnt) {
        DPRINT("not disposed: refcnt > 0\n");
        Py_RETURN_FALSE;
    }
    
    MUI_DisposeObject(obj); // should not call any Python code (done by PyModMCC).
    CPointer_SET_ADDR(self, NULL);

    Py_RETURN_TRUE;
}
//- muiobject__dispose
//+ muiobject__init
/*! \cond */
PyDoc_STRVAR(muiobject__init_doc,
"_init(attr, value, keep) -> int\n\
\n\
");
/*! \endcond */
static PyObject *
muiobject__init(MUIObject *self, PyObject *args) {
    PyObject *obj;
    ULONG attr;
    char keep;

    if (!PyArg_ParseTuple(args, "IOb", &attr, &obj, &keep))
        return NULL;

    if (keep && _keep_ref(self, attr, obj))
        return NULL;

    Py_RETURN_NONE;
}
//- muiobject__init
//+ muiobject__get
/*! \cond */
PyDoc_STRVAR(muiobject__get_doc,
"_get(attr, format) -> object\n\
\n\
Try to obtain the attribute value of the MUI object by calling \n\
the BOOPSI function GetAttr().
The value returned by GetAttr() is converted by Py_BuildValue() using format.");
/*! \endcond */

static PyObject *
muiobject__get(MUIObject *self, PyObject *args)
{
    Object *obj;
    ULONG attr;
    ULONG value;
    char *format;

    obj = CPointer_GET_ADDR(self);
    CHECK_OBJ(obj);
 
    if (!PyArg_ParseTuple(args, "Is", &attr, &format))
        return NULL;

    DPRINT("attr: 0x%08x, format='%s'\n", attr, format);

    if (get(obj, attr, &value) == 0)
        return PyErr_Format(PyExc_ValueError,
            "attribute 0x%08lx can't be get", attr);

    DPRINT("value: %d %u 0x%08lx\n", (LONG)value, value, (APTR) value);

    /* Convert value into the right Python object */
    return Py_BuildValue(format, value);
}
//- muiobject__get
//+ muiobject__set
/*! \cond */
PyDoc_STRVAR(muiobject__set_doc,
"_set(attr, value, keep) -> int\n\
\n\
Try to set an attribute of the MUI object by calling the BOOPSI OM_SET.\n\
Value should be an instance of CPointer or a int or a long.\n\
Note: object reference is keep only if keep = True!");
/*! \endcond */

static PyObject *
muiobject__set(MUIObject *self, PyObject *args) {
    Object *obj;
    ULONG attr;
    LONG value;

    obj = CPointer_GET_ADDR(self);
    CHECK_OBJ(obj);
 
    if (_set_base(self, args, &attr, &value))
        return NULL;

    value = set(obj, attr, value);  
    
    /* We handle Python exception here because set an attribute can call a notification
       that will raise an exception. In this case the set fails also. */
    if (PyErr_Occurred())
        return NULL;

    Py_RETURN_NONE;
}
//- muiobject__set
//+ muiobject__nnset
/*! \cond */
PyDoc_STRVAR(muiobject__nnset_doc,
"_nnset(attr, value, keep) -> int\n\
\n\
Like _set() but without triggering notification.");
/*! \endcond */

static PyObject *
muiobject__nnset(MUIObject *self, PyObject *args) {
    Object *obj;
    ULONG attr;
    LONG value;

    obj = CPointer_GET_ADDR(self);
    CHECK_OBJ(obj);

    if (_set_base(self, args, &attr, &value))
        return NULL;

    nnset(obj, attr, value);

    Py_RETURN_NONE;
}
//- muiobject__nnset
//+ muiobject__notify
/*! \cond */
PyDoc_STRVAR(muiobject__notify_doc,
"_notify(trigattr, trigvalue)\n\
\n\
Sorry, Not documented yet :-(");
/*! \endcond */

static PyObject *
muiobject__notify(MUIObject *self, PyObject *args) {
    PyObject *v;
    LONG trigattr, trigvalue, value;
    Object *obj;

    obj = CPointer_GET_ADDR(self);
    CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "IO", &trigattr, &v))
        return NULL;

    if (convertFromPython(v, &trigvalue))
        return NULL;

    DPRINT("obj: %p, trigattr: %#lx, trigvalue('%s'): %ld %lu %#lx\n",
           obj, trigattr, v->ob_type->tp_name, trigvalue, trigvalue, trigvalue);
    
    if (MUIV_EveryTime == trigvalue)
        value = MUIV_TriggerValue;
    else
        value = trigvalue;

    /* Notes: Like in _do, the hook OnAttrChangedHook cannot be called
     * if the Python object self is deallocated (except by a bad design inside a MUI class, that does
     * some DoMethod on died MUI obejcts... but I can't do anything for that here :-p).
     * Because if self is deallocated, muiobject_dealloc() will call MUI_DisposeObject on self!
     * And as calls are synchrones, calling _notify will raise an exception during the CHECK_OBJ().
     */
 
    DoMethod(obj, MUIM_Notify, trigattr, trigvalue,
        MUIV_Notify_Self, 5,
        MUIM_CallHook, (ULONG) &OnAttrChangedHook, (ULONG) self, trigattr, value);

    Py_RETURN_NONE;
}
//- muiobject__notify
//+ muiobject__do
/*! \cond */
PyDoc_STRVAR(muiobject__do_doc,
"_do(method, args)\n\
\n\
Sorry, Not documented yet :-(");
/*! \endcond */

static PyObject *
muiobject__do(MUIObject *self, PyObject *args) {
    PyObject *ret, *meth_data;
    Object *obj;
    DoMsg *msg;
    int meth, i, n;

    obj = CPointer_GET_ADDR(self);
    CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "IO!", &meth, &PyTuple_Type, &meth_data))
        return NULL;

    DPRINT("DoMethod(obj=%p, meth=0x%08x):\n", obj, meth);

    n = PyTuple_GET_SIZE(meth_data);
    DPRINT("Data size = %d\n", n);
    msg = (DoMsg *) malloc(sizeof(DoMsg) + sizeof(long) * n);
    if (NULL == msg) return PyErr_NoMemory();

    for (i = 0; i < n; i++) {
        PyObject *o = PyTuple_GET_ITEM(meth_data, i);
        LONG *ptr = (LONG *) &msg->data[i];

        if (convertFromPython(o, ptr)) {
            free(msg);
            return NULL;
        }

        DPRINT("  args[%u]: %d %u 0x%08x\n", i, *ptr, (ULONG) *ptr, *ptr);
    }

    /* Notes: objects given to the object dispatcher should remains alive during the call of the method,
     * even if this call cause some Python code to be executed causing a DECREF of these objects.
     * This is protected by the fact that objects have their ref counter increased until they remains
     * inside the argument tuple of this function.
     * So here there is no need to INCREF argument python objects.
     */

    msg->MethodID = meth;
    ret = PyInt_FromLong(DoMethodA(obj, (Msg) msg));
    free(msg);

    if (PyErr_Occurred())
        return NULL;

    return ret;
}//- muiobject__do

//+ MUIObject_Type
static PyMemberDef muiobject_members[] = {
    {"_refcnt", T_ULONG, offsetof(MUIObject, refcnt), RO, "MUI internal reference cunter."},
    {NULL}  /* Sentinel */
};

static struct PyMethodDef muiobject_methods[] = {
    {"_incref",     (PyCFunction) muiobject__incref,    METH_NOARGS,  muiobject__incref_doc},
    {"_decref",     (PyCFunction) muiobject__decref,    METH_NOARGS,  muiobject__decref_doc},
    {"_create",     (PyCFunction) muiobject__create,    METH_VARARGS, muiobject__create_doc},
    {"_dispose",    (PyCFunction) muiobject__dispose,   METH_NOARGS,  muiobject__dispose_doc},
    {"_init",       (PyCFunction) muiobject__init,      METH_VARARGS, muiobject__init_doc},
    {"_get",        (PyCFunction) muiobject__get,       METH_VARARGS, muiobject__get_doc},
    {"_set",        (PyCFunction) muiobject__set,       METH_VARARGS, muiobject__set_doc},
    {"_nnset",      (PyCFunction) muiobject__nnset,     METH_VARARGS, muiobject__nnset_doc},
    {"_notify",     (PyCFunction) muiobject__notify,    METH_VARARGS, muiobject__notify_doc},
    {"_do",         (PyCFunction) muiobject__do,        METH_VARARGS, muiobject__do_doc},
    {NULL, NULL}    /* sentinel */
};

static PyTypeObject MUIObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.MUIObject",
    tp_basicsize    : sizeof(MUIObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    tp_doc          : "MUI Objects",
    
    tp_new          : (newfunc)muiobject_new,
    tp_dealloc      : (destructor)muiobject_dealloc,
    
    tp_traverse     : (traverseproc)muiobject_traverse,
    tp_clear        : (inquiry)muiobject_clear,

    tp_repr         : (reprfunc)muiobject_repr,
    tp_methods      : muiobject_methods,
    tp_members      : muiobject_members,
};
//- MUIObject_Type

 
/*
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
 - doesn't check if app is really an application MUI object");
/*! \endcond */

static PyObject *
_muimaster_mainloop(PyObject *self, PyObject *args) {
    ULONG sigs = 0;
    PyObject *pyapp;
    Object *app;
    
    if (!PyArg_ParseTuple(args, "O!", &MUIObject_Type, &pyapp))
        return NULL;

    app = CPointer_GET_ADDR(pyapp);
    CHECK_OBJ(app);

    /* This code will not check that the given object is really an Application object;
     * That should be checked by the caller!
     */

    DPRINT("Goes into mainloop...\n");
    while (DoMethod(app, MUIM_Application_NewInput, (ULONG) &sigs) != MUIV_Application_ReturnID_Quit) {
        //DPRINT("sigs=%x\n", sigs);
        if (sigs)
            sigs = Wait(sigs | SIGBREAKF_CTRL_C);
        else
            sigs = SetSignal(0, 0);

        if (sigs & SIGBREAKF_CTRL_C) {
            PyErr_SetNone(PyExc_KeyboardInterrupt);
            return NULL;
        }

        if (PyErr_Occurred())
            return NULL;
    }

    DPRINT("bye mainloop...\n");
    
    Py_RETURN_NONE;
}
//- _muimaster_mainloop
//+ _muimaster_newinput
static PyObject *
_muimaster_newinput(PyObject *self, PyObject *args) {
    ULONG sigs;
    PyObject *pyapp;
    Object *app;
    LONG res;
    
    if (!PyArg_ParseTuple(args, "O!i", &MUIObject_Type, &pyapp, &sigs))
        return NULL;

    app = CPointer_GET_ADDR(pyapp);
    CHECK_OBJ(app);

    res = DoMethod(app, MUIM_Application_NewInput, (ULONG) &sigs);
    return Py_BuildValue("(ii)", sigs, res);
}
//- _muimaster_newinput
  

/* module methods */
static PyMethodDef _muimaster_methods[] = {
    {"mainloop", (PyCFunction) _muimaster_mainloop, METH_VARARGS, _muimaster_mainloop_doc},
    {"newinput", (PyCFunction) _muimaster_newinput, METH_VARARGS, NULL},
    {NULL, NULL} /* Sentinel */
};


/*
** Public Functions
*/

//+ PyMorphOS_CloseModule
void
PyMorphOS_CloseModule(void) {
    MCCNode *node;

    DPRINT("Closing module...\n");

    /* Destroy all PyMod classes */
    while (NULL != (node = (MCCNode *) REMTAIL(&classes))) {
        ULONG n = node->mn_MCC->mcc_Class->cl_ObjectCount;
        DPRINT("Node %p: MCC @ %p, obj cnt = %lu\n", node, node->mn_MCC, n);
        if (0 == n)
            MUI_DeleteCustomClass(node->mn_MCC);
        else
            DPRINT("Object count > 0, can't close the MCC @%p\n", node->mn_MCC);
        free(node);
    }
    
    if (NULL != MUIMasterBase) {
        PyMorphOS_CloseLibrary(MUIMasterBase);
        MUIMasterBase = NULL;
    }

    DPRINT("Bye\n");
}
//- PyMorphOS_CloseModule
//+ all_ins
static int
all_ins(PyObject *m) {
    INSI(m, "VLatest", (long)MUIMASTER_VLATEST);
    INSS(m, "TIME", __TIME__); 

    /* BOOPSI general methods */
    INSI(m, "OM_ADDMEMBER", OM_ADDMEMBER);
    INSI(m, "OM_REMMEMBER", OM_REMMEMBER);

    /* ClassID */
    INSS(m, "MUIC_Aboutmui", MUIC_Aboutmui);
    INSS(m, "MUIC_Application", MUIC_Application);
    INSS(m, "MUIC_Applist", MUIC_Applist);
    INSS(m, "MUIC_Area", MUIC_Area);
    INSS(m, "MUIC_Balance", MUIC_Balance);
    INSS(m, "MUIC_Bitmap", MUIC_Bitmap);
    INSS(m, "MUIC_Bodychunk", MUIC_Bodychunk);
    INSS(m, "MUIC_Boopsi", MUIC_Boopsi);
    INSS(m, "MUIC_Coloradjust", MUIC_Coloradjust);
    INSS(m, "MUIC_Colorfield", MUIC_Colorfield);
    INSS(m, "MUIC_Configdata", MUIC_Configdata);
    INSS(m, "MUIC_Cycle", MUIC_Cycle);
    INSS(m, "MUIC_Dataspace", MUIC_Dataspace);
    INSS(m, "MUIC_Dirlist", MUIC_Dirlist);
    INSS(m, "MUIC_Dtpic", MUIC_Dtpic);
    INSS(m, "MUIC_Family", MUIC_Family);
    INSS(m, "MUIC_Floattext", MUIC_Floattext);
    INSS(m, "MUIC_Frameadjust", MUIC_Frameadjust);
    INSS(m, "MUIC_Framedisplay", MUIC_Framedisplay);
    INSS(m, "MUIC_Gadget", MUIC_Gadget);
    INSS(m, "MUIC_Gauge", MUIC_Gauge);
    INSS(m, "MUIC_Group", MUIC_Group);
    INSS(m, "MUIC_Image", MUIC_Image);
    INSS(m, "MUIC_Imageadjust", MUIC_Imageadjust);
    INSS(m, "MUIC_Imagedisplay", MUIC_Imagedisplay);
    INSS(m, "MUIC_Knob", MUIC_Knob);
    INSS(m, "MUIC_Levelmeter", MUIC_Levelmeter);
    INSS(m, "MUIC_List", MUIC_List);
    INSS(m, "MUIC_Listview", MUIC_Listview);
    INSS(m, "MUIC_Mccprefs", MUIC_Mccprefs);
    INSS(m, "MUIC_Menu", MUIC_Menu);
    INSS(m, "MUIC_Menuitem", MUIC_Menuitem);
    INSS(m, "MUIC_Menustrip", MUIC_Menustrip);
    INSS(m, "MUIC_Notify", MUIC_Notify);
    INSS(m, "MUIC_Numeric", MUIC_Numeric);
    INSS(m, "MUIC_Numericbutton", MUIC_Numericbutton);
    INSS(m, "MUIC_Palette", MUIC_Palette);
    INSS(m, "MUIC_Penadjust", MUIC_Penadjust);
    INSS(m, "MUIC_Pendisplay", MUIC_Pendisplay);
    INSS(m, "MUIC_Popasl", MUIC_Popasl);
    INSS(m, "MUIC_Popframe", MUIC_Popframe);
    INSS(m, "MUIC_Popimage", MUIC_Popimage);
    INSS(m, "MUIC_Poplist", MUIC_Poplist);
    INSS(m, "MUIC_Popobject", MUIC_Popobject);
    INSS(m, "MUIC_Poppen", MUIC_Poppen);
    INSS(m, "MUIC_Popscreen", MUIC_Popscreen);
    INSS(m, "MUIC_Popstring", MUIC_Popstring);
    INSS(m, "MUIC_Prop", MUIC_Prop);
    INSS(m, "MUIC_Radio", MUIC_Radio);
    INSS(m, "MUIC_Rectangle", MUIC_Rectangle);
    INSS(m, "MUIC_Register", MUIC_Register);
    INSS(m, "MUIC_Scale", MUIC_Scale);
    INSS(m, "MUIC_Scrmodelist", MUIC_Scrmodelist);
    INSS(m, "MUIC_Scrollbar", MUIC_Scrollbar);
    INSS(m, "MUIC_Scrollgroup", MUIC_Scrollgroup);
    INSS(m, "MUIC_Semaphore", MUIC_Semaphore);
    INSS(m, "MUIC_Settings", MUIC_Settings);
    INSS(m, "MUIC_Settingsgroup", MUIC_Settingsgroup);
    INSS(m, "MUIC_Slider", MUIC_Slider);
    INSS(m, "MUIC_String", MUIC_String);
    INSS(m, "MUIC_Text", MUIC_Text);
    INSS(m, "MUIC_Virtgroup", MUIC_Virtgroup);
    INSS(m, "MUIC_Volumelist", MUIC_Volumelist);
    INSS(m, "MUIC_Window", MUIC_Window);

    return 0;
}
//- all_ins

//+ INITFUNC()
PyMODINIT_FUNC
INITFUNC(void) {
    PyObject *m;

    MUIMasterBase = PyMorphOS_OpenLibrary(MUIMASTER_NAME, MUIMASTER_VLATEST);
    if (!MUIMasterBase) return;

    if (import__core() < 0) return;

    NEWLIST(&classes);

    /* Notification hook initialization */
    OnAttrChangedHook.h_Entry = (HOOKFUNC) &HookEntry; 
    OnAttrChangedHook.h_SubEntry = (HOOKFUNC) &OnAttrChanged; 
    
    /* New Python types initialization */
    MUIObject_Type.tp_base = &CPointer_Type;
    if (PyType_Ready(&MUIObject_Type) < 0) return;

    /* Module creation/initialization */
    m = Py_InitModule3(MODNAME, _muimaster_methods, _muimaster__doc__);

    ADD_TYPE(m, "PyMuiObject", &MUIObject_Type);

    if (all_ins(m)) return;
}
//-

/* EOF */
