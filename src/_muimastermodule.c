/***************************************************************************//**
 *** @file _muimastermodule.c
 *** @author ROGUEZ "Yomgui" Guillaume
 *** @date 2007/06/06
 ***
 *** @brief Python wrapper for muimaster.library
 ***
  ******************************************************************************/

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

//#define NDEBUG

/*
** Private Macros and Definitions
*/

#ifndef MODNAME
#define MODNAME "_muimaster"
#endif

#ifndef INITFUNC
#define INITFUNC init_muimaster
#endif

#define NDEBUG

#ifndef NDEBUG
#define DPRINT(x...) ({ PyObject *o = module?PyObject_GetAttrString(module, "stddebug"):NULL; \
         if ((NULL == o) || !PyInt_AS_LONG(o)) {                         \
             KPrintF("%s:%u: ", __FUNCTION__, __LINE__); KPrintF(##x);  \
         } else {                                                       \
             printf("%s:%u: ", __FUNCTION__, __LINE__); printf(##x);    \
         } })
#else
#define DPRINT(x...)
#endif

#if defined __GNUC__
    #define ASM
    #define SAVEDS
#else
    #define ASM    __asm
    #define SAVEDS __saveds
#endif

#define ADD_TYPE(m, s, t) {Py_INCREF(t); PyModule_AddObject(m, s, (PyObject *)(t));}

#define GET_ADDRESS(o) (((CPointer *)(o))->address)
#define SET_ADDRESS(o, v) (((CPointer *)(o))->address = (APTR)(v)) 

#define CHECK_OBJ(o) if (NULL == (o)) { \
        PyErr_SetString(PyExc_RuntimeError, "no MUI object associated"); \
        return NULL; }

#define CPointer_Check(op) PyObject_TypeCheck(op, &CPointer_Type)
#define CPointer_CheckExact(op) ((op)->ob_type == &CPointer_Type)

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

typedef struct CPointer_STRUCT {
    PyObject_HEAD
    APTR address;
} CPointer;

typedef struct OnAttrChangedMsg_STRUCT {
    PyObject *  py_obj;
    ULONG       attr;
    ULONG       value;
} OnAttrChangedMsg;

typedef struct MUIObject_STRUCT {
    CPointer    base;
    PyObject *  refdict; // -> GC mandatory. Used for attributes [REQ-04-B]
    ULONG       refcnt; // Reference counter like in Python but between MUI objects [REQ-04-C]
} MUIObject;

typedef struct PyModMCCData_STRUCT {
    PyObject *pmd_PyObject;
} PyModMCCData;

typedef struct MCCNode_STRUCT {
    struct MinNode              mn_Node;
    struct MUI_CustomClass *    mn_MCC;
} MCCNode;


/*
** Private Prototypes
*/


/*
** Private Variables
*/

static struct Hook OnAttrChangedHook;
static PyTypeObject CPointer_Type;
static PyTypeObject MUIObject_Type;
static ULONG id_counter;
static Object *global_app;
static struct MinList classes;

#ifndef NDEBUG
static PyObject *module; /* only used in debugging */
#endif


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
static void
PyModMCC_Dispose(struct IClass *cl, Object *obj) {
    PyModMCCData *data = INST_DATA(cl, obj);
    PyObject *pyo = data->pmd_PyObject;

    DPRINT("MUI=%p, PyObj=%p\n", obj, pyo);
    
    if (NULL != pyo) {
        SET_ADDRESS(pyo, NULL);
    }
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
    //DPRINT("cl=%p, obj=%p, method=%#x\n", cl, obj, msg->MethodID);
    
    switch (msg->MethodID) {
        case OM_NEW: return PyModMCC_New(cl, obj, (APTR) msg);
        case OM_DISPOSE: PyModMCC_Dispose(cl, obj); break;
        case OM_GET: return PyModMCC_Get(cl, obj, (APTR) msg);
    }
    
    return DoSuperMethodA(cl, obj, msg);
}
DISPATCHER_END
//- PxMod MCC Dispatcher


/*
** Private Functions
*/

//+ insi
static int
insi(PyObject *module, char *symbol, long value) {
    return PyModule_AddIntConstant(module, symbol, value);
}//-
//+ inss
static int
inss(PyObject *module, char *symbol, char *string) {
    return PyModule_AddStringConstant(module, symbol, string);
}//-
//+ all_ins
static int
all_ins(PyObject *m) {
    if (insi(m, "VLatest", (long)MUIMASTER_VLATEST)) return -1;
    if (inss(m, "TIME", __TIME__)) return -1; 

    /* BOOPSI general methods */

    /* ClassID */
    if (inss(m, "MUIC_Aboutmui", MUIC_Aboutmui)) return -1;
    if (inss(m, "MUIC_Application", MUIC_Application)) return -1;
    if (inss(m, "MUIC_Applist", MUIC_Applist)) return -1;
    if (inss(m, "MUIC_Area", MUIC_Area)) return -1;
    if (inss(m, "MUIC_Balance", MUIC_Balance)) return -1;
    if (inss(m, "MUIC_Bitmap", MUIC_Bitmap)) return -1;
    if (inss(m, "MUIC_Bodychunk", MUIC_Bodychunk)) return -1;
    if (inss(m, "MUIC_Boopsi", MUIC_Boopsi)) return -1;
    if (inss(m, "MUIC_Coloradjust", MUIC_Coloradjust)) return -1;
    if (inss(m, "MUIC_Colorfield", MUIC_Colorfield)) return -1;
    if (inss(m, "MUIC_Configdata", MUIC_Configdata)) return -1;
    if (inss(m, "MUIC_Cycle", MUIC_Cycle)) return -1;
    if (inss(m, "MUIC_Dataspace", MUIC_Dataspace)) return -1;
    if (inss(m, "MUIC_Dirlist", MUIC_Dirlist)) return -1;
    if (inss(m, "MUIC_Dtpic", MUIC_Dtpic)) return -1;
    if (inss(m, "MUIC_Family", MUIC_Family)) return -1;
    if (inss(m, "MUIC_Floattext", MUIC_Floattext)) return -1;
    if (inss(m, "MUIC_Frameadjust", MUIC_Frameadjust)) return -1;
    if (inss(m, "MUIC_Framedisplay", MUIC_Framedisplay)) return -1;
    if (inss(m, "MUIC_Gadget", MUIC_Gadget)) return -1;
    if (inss(m, "MUIC_Gauge", MUIC_Gauge)) return -1;
    if (inss(m, "MUIC_Group", MUIC_Group)) return -1;
    if (inss(m, "MUIC_Image", MUIC_Image)) return -1;
    if (inss(m, "MUIC_Imageadjust", MUIC_Imageadjust)) return -1;
    if (inss(m, "MUIC_Imagedisplay", MUIC_Imagedisplay)) return -1;
    if (inss(m, "MUIC_Knob", MUIC_Knob)) return -1;
    if (inss(m, "MUIC_Levelmeter", MUIC_Levelmeter)) return -1;
    if (inss(m, "MUIC_List", MUIC_List)) return -1;
    if (inss(m, "MUIC_Listview", MUIC_Listview)) return -1;
    if (inss(m, "MUIC_Mccprefs", MUIC_Mccprefs)) return -1;
    if (inss(m, "MUIC_Menu", MUIC_Menu)) return -1;
    if (inss(m, "MUIC_Menuitem", MUIC_Menuitem)) return -1;
    if (inss(m, "MUIC_Menustrip", MUIC_Menustrip)) return -1;
    if (inss(m, "MUIC_Notify", MUIC_Notify)) return -1;
    if (inss(m, "MUIC_Numeric", MUIC_Numeric)) return -1;
    if (inss(m, "MUIC_Numericbutton", MUIC_Numericbutton)) return -1;
    if (inss(m, "MUIC_Palette", MUIC_Palette)) return -1;
    if (inss(m, "MUIC_Penadjust", MUIC_Penadjust)) return -1;
    if (inss(m, "MUIC_Pendisplay", MUIC_Pendisplay)) return -1;
    if (inss(m, "MUIC_Popasl", MUIC_Popasl)) return -1;
    if (inss(m, "MUIC_Popframe", MUIC_Popframe)) return -1;
    if (inss(m, "MUIC_Popimage", MUIC_Popimage)) return -1;
    if (inss(m, "MUIC_Poplist", MUIC_Poplist)) return -1;
    if (inss(m, "MUIC_Popobject", MUIC_Popobject)) return -1;
    if (inss(m, "MUIC_Poppen", MUIC_Poppen)) return -1;
    if (inss(m, "MUIC_Popscreen", MUIC_Popscreen)) return -1;
    if (inss(m, "MUIC_Popstring", MUIC_Popstring)) return -1;
    if (inss(m, "MUIC_Prop", MUIC_Prop)) return -1;
    if (inss(m, "MUIC_Radio", MUIC_Radio)) return -1;
    if (inss(m, "MUIC_Rectangle", MUIC_Rectangle)) return -1;
    if (inss(m, "MUIC_Register", MUIC_Register)) return -1;
    if (inss(m, "MUIC_Scale", MUIC_Scale)) return -1;
    if (inss(m, "MUIC_Scrmodelist", MUIC_Scrmodelist)) return -1;
    if (inss(m, "MUIC_Scrollbar", MUIC_Scrollbar)) return -1;
    if (inss(m, "MUIC_Scrollgroup", MUIC_Scrollgroup)) return -1;
    if (inss(m, "MUIC_Semaphore", MUIC_Semaphore)) return -1;
    if (inss(m, "MUIC_Settings", MUIC_Settings)) return -1;
    if (inss(m, "MUIC_Settingsgroup", MUIC_Settingsgroup)) return -1;
    if (inss(m, "MUIC_Slider", MUIC_Slider)) return -1;
    if (inss(m, "MUIC_String", MUIC_String)) return -1;
    if (inss(m, "MUIC_Text", MUIC_Text)) return -1;
    if (inss(m, "MUIC_Virtgroup", MUIC_Virtgroup)) return -1;
    if (inss(m, "MUIC_Volumelist", MUIC_Volumelist)) return -1;
    if (inss(m, "MUIC_Window", MUIC_Window)) return -1;

    return 0;
}
//-
//+ convertFromPython
static LONG
convertFromPython(PyObject *obj, long *value) {
    DPRINT("value @ %p\n", value);

    if (PyString_Check(obj)) {
        *value = (LONG) PyString_AS_STRING(obj);
    } else if (CPointer_Check(obj)) {
        *value = (LONG) GET_ADDRESS(obj);
    } else {
        PyObject *o = PyNumber_Int(obj);

        if (NULL == o) {
            PyErr_Format(PyExc_TypeError, "can't convert a %s object into an integer", obj->ob_type->tp_name);
            return -1;
        }

        if (PyLong_CheckExact(o)) {
            *value = PyLong_AsUnsignedLong(o);
        } else {
            *value = PyInt_AS_LONG(o);
        }

        Py_DECREF(o);
    }

    DPRINT("%s object converted into integer: %ld %lu %lx\n", obj->ob_type->tp_name,
           (LONG) *value, (ULONG) *value, (ULONG) *value);

    return 0;
}
//-
//+ convertToPython
/*
** Convert a given value into the right Python type object
*/
static PyObject *
convertToPython(PyTypeObject *type, long value) {   
    DPRINT("type: %p (%s), value: %ld %lu %#lx\n", type, type->tp_name, (ULONG) value, value, (ULONG) value);

    if (type == &PyString_Type) {
        if (NULL != value) return PyString_FromString((char *)value);
        Py_RETURN_NONE;
    } else if (type == &PyBool_Type) {
        return PyBool_FromLong(value);
    } else if (PyType_IsSubtype(type, &MUIObject_Type)) {
        PyObject *v;
        Object *obj;

        if (NULL == value) Py_RETURN_NONE;

        obj = (Object *) value;
        if (!get(obj, MUIA_PyMod_PyObject, &v)) {
            PyErr_SetString(PyExc_RuntimeError, "not handled given object");
            return NULL;
        }
        
        if (NULL != v) {
            Py_INCREF(v);
        } else {
            PyErr_SetString(PyExc_RuntimeError, "linked Python object is NULL");
            return NULL;
        }
        
        return v;
    } else if (PyType_IsSubtype(type, &CPointer_Type)) {
        PyObject *v, *args;
        
        args = PyTuple_Pack(1, value);
        if (NULL == args) return NULL;
        v = PyType_GenericNew(&CPointer_Type, args, NULL);
        Py_DECREF(args);

        return v;
    }
    else if (type == &PyInt_Type)
        return PyInt_FromLong(value);
    else if (type == &PyLong_Type)
        return PyLong_FromUnsignedLong(value);

    PyErr_SetString(PyExc_TypeError, "unsupported convert type");
    return NULL;
}
//-
//+ OnAttrChanged
static void
OnAttrChanged(struct Hook *hook, Object *obj, OnAttrChangedMsg *msg)  { 
    PyObject *res, *attr_obj, *value_obj;
    LONG value = msg->value;

    DPRINT("Attribute %#lx Changed for PyMCC object @ %p (MUI=%p) to %ld %lu %p\n",
           msg->attr, msg->py_obj, obj, value, (ULONG) value, (APTR) value);

    /* Get the attribute type */
    attr_obj = Py_BuildValue("I", msg->attr);
    if (NULL == attr_obj) return;

    DPRINT("Calling _GetAttrType(attr_obj = %p)...\n", attr_obj);
    res = PyObject_CallMethod(msg->py_obj, "_GetAttrType", "O", attr_obj);
    if ((NULL == res) || (res == Py_None)) {
        Py_DECREF(attr_obj);
        Py_XDECREF(res);
        PyErr_Format(PyExc_RuntimeError, "can't determinate type for attribute %#x", msg->attr);
        return;
    }

    /* Converting this attribute into right Python object */
    value_obj = convertToPython((PyTypeObject *)res, value);
    Py_DECREF(res);
    if (NULL == value_obj) {
        Py_DECREF(attr_obj);
        return;
    }
    
    /* Call the high-level notify method */
    DPRINT("Calling OnAttrChanged(attr_obj = %p, value_obj = %p)...\n", attr_obj, value_obj);
    PyObject_CallMethod(msg->py_obj, "_OnAttrChanged", "OO", attr_obj, value_obj);

    // nothing to do more... so don't take care about result of this call
    
    Py_DECREF(attr_obj);
    Py_DECREF(value_obj);
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

    DPRINT("value (%s): %ld %ld %#lx\n", keep?"saved":"not saved", *value, *value, *value);

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
        if (node->mn_MCC->mcc_Super->cl_ID == id) {
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
** CPointer_Type
*/

//+ cpointer_init
static int
cpointer_init(CPointer *self, PyObject *args) {
    ULONG value = 0;

    if ((NULL != args) && !PyArg_ParseTuple(args, "|I", &value))
        return -1;

    self->address = (APTR) value;

    DPRINT("CPointer.init(self=%p, address=%p)\n", self, self->address);

    return 0;

}
//- cpointer_init
//+ cpointer_repr
static PyObject *
cpointer_repr(CPointer *self) {
    return PyString_FromFormat("<CPointer at %p, address=%p>", self, self->address);
}
//- cpointer_repr
//+ cpointer_long
static PyObject *
cpointer_long(CPointer *self) {
    return PyLong_FromVoidPtr(self->address);
}
//- cpointer_long
//+ cpointer_int
static PyObject *
cpointer_int(CPointer *self) {
    return PyInt_FromLong((long) self->address);
}
//- cpointer_int
//+ cpointer_nonzero
static int
cpointer_nonzero(CPointer *self) {
    return self->address != NULL;
}
//- cpointer_nonzero

//+ CPointer_Type
static PyMemberDef cpointer_members[] = {
    {"address", T_ULONG, offsetof(CPointer, address), RO, "Address"},
    {NULL}  /* Sentinel */
};

static PyNumberMethods cpointer_as_number = {
    nb_long         : (unaryfunc)cpointer_long,
    nb_int          : (unaryfunc)cpointer_int,
    nb_nonzero      : (inquiry)cpointer_nonzero,
};
 
static PyTypeObject CPointer_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.CPointer",
    tp_basicsize    : sizeof(CPointer),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    tp_doc          : "CPointer Objects",     

    tp_new          : PyType_GenericNew,   
    tp_init         : (initproc)cpointer_init,

    tp_members      : cpointer_members,  
    tp_repr         : (reprfunc)cpointer_repr,
    tp_as_number    : &cpointer_as_number,
};
//- CPointer_Type


/*******************************************************************************************
** MUIObject_Type
*/

//+ muiobject_init
static int
muiobject_init(MUIObject *self) {
    if (CPointer_Type.tp_init((PyObject *)self, NULL, NULL) < 0)
        return -1;

    self->refdict = PyDict_New();
    if (NULL == self->refdict)
        return -1;

    self->refcnt = 0;
        
    DPRINT("MUIObject.init(self=%p)\n", self);

    return 0;
}
//- muiobject_init
//+ muiobject_dealloc()
static void
muiobject_dealloc(MUIObject *self) {
    Object *obj;
    
    obj = GET_ADDRESS(self);
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
    ((PyObject *) self)->ob_type->tp_free((PyObject *)self);
}
//-
//+ muiobject_repr()
static PyObject *
muiobject_repr(MUIObject *self) {
    Object *obj;
    
    obj = GET_ADDRESS(self);
    if (NULL != obj)
        return PyString_FromFormat("<MUIObject at %p, MUI object at %p>", self, obj);
    else
        return PyString_FromFormat("<MUIObject at %p, MUI object disposed>", self);
}
//- muiobject_repr()
//+ muiobject_traverse()
static int
muiobject_traverse(MUIObject *self, visitproc visit, void *arg) {
    return visit(self->refdict, arg);
}
//-muiobject_traverse()
//+ muiobject_clear()
static int
muiobject_clear(MUIObject *self) {
    PyDict_Clear(self->refdict);
    return 0;
}
//- muiobject_clear()
//+ muiobject__incref()
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
    obj = GET_ADDRESS(self);
    CHECK_OBJ(obj);

    assert(self->refcnt < ULONG_MAX);

    // We keep alive the Python objet if some MUI refs exists.
    if (0 == self->refcnt) {
        Py_INCREF((PyObject *)self);
    }

    self->refcnt++;

    Py_RETURN_NONE;
}
//- muiobject__incref()
//+ muiobject__decref()
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
    obj = GET_ADDRESS(self);
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
//- muiobject__decref()
//+ muiobject__create()
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
    mui_obj = GET_ADDRESS(self);
    if (NULL != mui_obj) {
        PyErr_SetString(PyExc_RuntimeError, "the MUI object is already created");
        return NULL;
    }

    data = NULL;
    tags = NULL;
    if (!PyArg_ParseTuple(args, "s|O!:_create", &cl, &PyDict_Type, &data))
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

    mui_obj = myMUI_NewObject(self, cl, tags);
    DPRINT("MUI_NewObject(\"%s\") = %p\n", cl, mui_obj);
    
    PyMem_Free(tags);
    
    if (NULL == mui_obj) {
        PyErr_SetString(PyExc_RuntimeError, "can't create a new MUI object");
        return NULL;
    }

    SET_ADDRESS(self, mui_obj);
    Py_RETURN_TRUE;
}
//-
//+ muiobject__dispose()
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

    obj = GET_ADDRESS(self);
    CHECK_OBJ(obj);

    DPRINT("PyObj: %p, MUI obj: %p, refcnt=%lu\n", self, obj, self->refcnt);

    if (self->refcnt) {
        DPRINT("not disposed: refcnt > 0\n");
        Py_RETURN_FALSE;
    }
    
    MUI_DisposeObject(obj);
    SET_ADDRESS(self, NULL);

    Py_RETURN_TRUE;
}
//-
//+ muiobject__init()
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
//-
//+ muiobject__get()
/*! \cond */
PyDoc_STRVAR(muiobject__get_doc,
"_get(attr, attr_type, array=False) -> object\n\
\n\
Try to obtain the attribute value of the MUI object by calling \n\
the BOOPSI function GetAttr().");
/*! \endcond */

static PyObject *
muiobject__get(MUIObject *self, PyObject *args) {
    PyTypeObject *type;
    Object *obj;
    ULONG attr;
    ULONG value;

    obj = GET_ADDRESS(self);
    CHECK_OBJ(obj);
 
    if (!PyArg_ParseTuple(args, "O!I:_get", &PyType_Type, &type, &attr))
        return NULL;

    DPRINT("type: %s, attr: 0x%08x\n", type->tp_name, attr);

    if (get(obj, attr, &value) == 0)
        return PyErr_Format(PyExc_ValueError,
            "attribute 0x%08x can't be get", attr);

    DPRINT("value: %d %u 0x%08x\n", (LONG)value, value, (APTR) value);

    /* Convert value into the right Python object */
    return convertToPython(type, value);
}
//-
//+ muiobject__set()
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

    obj = GET_ADDRESS(self);
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
//-
//+ muiobject__nnset()
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

    obj = GET_ADDRESS(self);
    CHECK_OBJ(obj);

    if (_set_base(self, args, &attr, &value))
        return NULL;

    nnset(obj, attr, value);

    Py_RETURN_NONE;
}
//-
//+ muiobject__notify()
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

    obj = GET_ADDRESS(self);
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

    /* Not needed to increment self reference because notifications
       are destroyed in the same time as the MUI object */
 
    DoMethod(obj, MUIM_Notify, trigattr, trigvalue,
        MUIV_Notify_Self, 5,
        MUIM_CallHook, (ULONG) &OnAttrChangedHook, (ULONG) self, trigattr, value);

    Py_RETURN_NONE;
}
//-
//+ muiobject__do()
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

    obj = GET_ADDRESS(self);
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

    msg->MethodID = meth;
    ret = PyInt_FromLong(DoMethodA(obj, (Msg) msg));

    free(msg);
    return ret;
}//-
//+ muiobject__addmember
static PyObject *
muiobject__addmember(MUIObject *self, PyObject *args) {
    MUIObject *child;
    Object *obj, *child_obj;

    obj = GET_ADDRESS(self);
    CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "O!", &MUIObject_Type, &child))
        return NULL;

    child_obj = GET_ADDRESS(child);
    if (NULL == child_obj) {
        PyErr_SetString(PyExc_ValueError, "given MUI object is died!");
        return NULL;
    }

    DoMethod(obj, OM_ADDMEMBER, (ULONG) child_obj);
    if (NULL == muiobject__incref(child))
        return NULL;

    Py_RETURN_TRUE;
}
//- muiobject__addmember
//+ muiobject__remmember
static PyObject *
muiobject__remmember(MUIObject *self, PyObject *args) {
    MUIObject *child;
    Object *obj, *child_obj;

    obj = GET_ADDRESS(self);
    CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "O!", &MUIObject_Type, &child))
        return NULL;

    child_obj = GET_ADDRESS(child);
    if (NULL == child_obj) {
        PyErr_SetString(PyExc_ValueError, "given MUI object is died!");
        return NULL;
    }

    if (NULL == muiobject__decref(child))
        return NULL;

    DoMethod(obj, OM_REMMEMBER, (ULONG) child_obj);

    Py_RETURN_TRUE;
}
//- muiobject__remmember

//+ MUIObject_Type
static PyMemberDef muiobject_members[] = {
    {"_refcnt", T_ULONG, offsetof(MUIObject, refcnt), RO, "MUI internal reference counter."},
    {"_pyrefcnt", T_ULONG, offsetof(PyObject, ob_refcnt), RO, "Python internal reference counter."},
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
    {"_addmember",  (PyCFunction) muiobject__addmember, METH_VARARGS, NULL},
    {"_remmember",  (PyCFunction) muiobject__remmember, METH_VARARGS, NULL},
    {NULL, NULL}    /* sentinel */
};

static PyTypeObject MUIObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.MUIObject",
    tp_basicsize    : sizeof(MUIObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    tp_doc          : "MUI Objects",
    
    tp_base         : &CPointer_Type,
    tp_init         : (initproc)muiobject_init,
    tp_dealloc      : (destructor)muiobject_dealloc,
    
    tp_traverse     : (traverseproc)muiobject_traverse,
    tp_clear        : (inquiry)muiobject_clear,

    tp_repr         : (reprfunc)muiobject_repr,
    tp_methods      : muiobject_methods,
    tp_members      : muiobject_members,
};
//-

 
/*
** Module Functions
**
** List of functions exported by this module reside here
*/

//+ _muimaster_mainloop()
/*! \cond */
PyDoc_STRVAR(_muimaster_mainloop_doc,
"mainloop().\n\
\n\
Simple main loop.\n\
The loop exits when the app object received a MUIV_Application_ReturnID_Quit\n\
or by a sending a SIGBREAKF_CTRL_C to the task.\n\
\n\
Notes:\n\
 - SIGBREAKF_CTRL_C signal generates a PyExc_KeyboardInterrupt exception\n\
 - no checks if app is really an application MUI object");
/*! \endcond */

static PyObject *
_muimaster_mainloop(PyObject *self) {
    ULONG sigs = 0;
    
    DPRINT("global_app = %p\n", global_app);

    if (NULL == global_app) {
        PyErr_SetString(PyExc_RuntimeError, "No Application created");
        return NULL;
    }

    DPRINT("Goes into mainloop...\n");
    while (DoMethod(global_app, MUIM_Application_NewInput, (ULONG) &sigs) != MUIV_Application_ReturnID_Quit) {
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
//-
//+ _muimaster_newid()
/*! \cond */
PyDoc_STRVAR(_muimaster_newid_doc,
"newid() -> long.\n\
\n\
Return a long integer, unique per process.");
/*! \endcond */

static PyObject *
_muimaster_newid(PyObject *self) {
    return PyLong_FromUnsignedLong(++id_counter);
}
//-
//+ _muimaster__initapp()
static PyObject *
_muimaster__initapp(PyObject *self, PyObject *args) {
    PyObject *mo;
    Object *obj;

    if (!PyArg_ParseTuple(args, "O!:_initapp", &MUIObject_Type, &mo))
        return NULL;

    obj = GET_ADDRESS(mo);
    CHECK_OBJ(obj);

    /* don't assign global_app directly with return of GET_ADDRESS,
    ** as CHECK_OBJ() can cause a return of this function.
    */

    global_app = obj; 
    DPRINT("App obj = %p now\n", obj);

    Py_RETURN_NONE;
}
//-

/* module methods */
static PyMethodDef _muimaster_methods[] = {
    {"mainloop", (PyCFunction) _muimaster_mainloop, METH_NOARGS, _muimaster_mainloop_doc},
    {"newid", (PyCFunction) _muimaster_newid, METH_NOARGS, _muimaster_newid_doc},
    {"_initapp", (PyCFunction) _muimaster__initapp, METH_VARARGS, NULL},
    {NULL, NULL} /* Sentinel */
};


/*
** Public Functions
*/

//+ PyMorphOS_CloseModule()
void
PyMorphOS_CloseModule(void) {
    MCCNode *node;

    #ifndef NDEBUG
    module = NULL;
    #endif
    
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
//-

//+ INITFUNC()
PyMODINIT_FUNC
INITFUNC(void) {
    PyObject *m;

    MUIMasterBase = PyMorphOS_OpenLibrary(MUIMASTER_NAME, MUIMASTER_VLATEST);
    if (!MUIMasterBase) return;

    id_counter = 0;
    global_app = NULL;
    NEWLIST(&classes);

    /* Notification hook initialization */
    OnAttrChangedHook.h_Entry = (HOOKFUNC) &HookEntry; 
    OnAttrChangedHook.h_SubEntry = (HOOKFUNC) &OnAttrChanged; 
    
    /* New Python types initialization */
    if (PyType_Ready(&CPointer_Type) < 0) return;
    if (PyType_Ready(&MUIObject_Type) < 0) return;

    /* Module creation/initialization */
    m = Py_InitModule3(MODNAME, _muimaster_methods, _muimaster__doc__);

    ADD_TYPE(m, "CPointer", &CPointer_Type);
    ADD_TYPE(m, "MUIObject", &MUIObject_Type);

    if (all_ins(m)) return;

#ifndef NDEBUG
    /* Debugging */
    module = m;
    PyModule_AddObject(m, "stddebug", PyInt_FromLong(FALSE));
#endif
}
//-

/* EOF */
