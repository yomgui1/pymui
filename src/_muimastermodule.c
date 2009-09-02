/***************************************************************************//**
 *** \file _muimastermodule.c
 *** \author ROGUEZ "Yomgui" Guillaume
 *** \date 2007/06/06
 ***
 *** \brief Python wrapper for muimaster.library
 ***
 *******************************************************************************/

//+ Dev notes
/* Dev notes:

***** Ma vie, mon oeuvre... *****

* "dur dur... tr�s dur!"

Pour faire un 'wrapper' Python pour MUI, tout le probl�me est qu'il faut savoir quand un objet meurt (= OM_DISPOSE).
Car comme l'objet Python va garder une r�f�rence  sur cet objet MUI (ou BOOPSI comme on veut...), il faut donc �tre sur
que si on d�truit ce dernier, l'objet MUI le soit aussi (ca c'est la partie simple: on appel MUI_DisposeObject () durant le dispose
de l'objet python), mais aussi indiquer � l'objet python que l'objet MUI est d�truit si jamais la m�thode OM_DISPOSE de ce dernier
est appel�e (ext�rieurement, pas depuis le wrapper bien-s�r pour ne pas faire une boucle-infinie avec le premier cas).
Evidement c'est ce dernier cas o� tous les probl�mes surgissent...

Pourquoi? Il faut �tre certain d'�tre notifi� (du c�t� python) de l'appel � la m�thode OM_DISPOSE! En effet, les m�thodes pour Python
associ�es vont forcement utiliser cet object MUI, aui doit alors �tre valide.

De quoi dispose t'on alors?

1) Ne cherchons pas du c�t� de la classe Notify. Le syst�me de notification de MUI ne fonctionne que sur des changenents
de valeurs des attributs des objets... pas des m�thodes.

2) BOOPSI? Pouvoir savoir si OM_DISPOSE est appel� � coups-sur serait de contr�ler le code du dispatcher de l'objet MUI.

Comment faire cela? Ils y a plusieurs possibilit�es:

    a) Faire une classe 'wrapper' dont la super-classe serait identique � l'objet BOOPSI o� on aurait le contr�le du dispatcher,
    en particulier de notre m�thode OM_DISPOSE et o� on appelerait CoerceMethod() avec la classe d'origine de l'instance wrapp�e.
    
    => probl�mes: vu que la classe d'origine s'attend � avoir ses donn�es d'instance rattach�s au pointeur associ� il faut donc copier
    ces donn�es juste apr�s la cr�ation donc pendant OM_NEW. Ainsi la classe d'origine n'ira pas taper n'importe o� en m�moire.
    C'est faisable, mais... quand on cr�e l'objet avec notre custom classe on passe les arguments comme si c'�tait la vraie classe, l� c'est ok.
    Mais comment fait-on pour une instance d�j� cr�er, ailleur que par ntore code Python? On ne peut-pas cr�er une instance de notre custom class
    pour contenir cette instance car pour faire cela notre custom classe doit avoir comme super la m�me classe que l'instance d'origine.
    Or on ne connait pas les param�tres qu'il faut employer avec cette super classe! Il est tr�s parfaitement possible d'avoir des param�tres
    obligatoires qu'on ne peut deviner. Ceci nous emp�che alors d'utilis� des instances d'objets BOOPSI (= MUI) cr�es ailleur
    que par notre module Python. Trop restrictif... abandonnons cette solution. Et m�me si on on fait une impasse sur les instances externes
    d'autres probl�mes sont � r�soudre comme des classes qui gardent des pointeurs sur les instances (alors qu'on va justement cr�er une nouvelle
    instance qui wrappe la premi�re...), ce que je soupconne fortement car d'apr�s quelques tests mes instance de classe Window ne veulent pas
    �tres   reconnues par la classe Application (et donc rattach�es...).
    
    b)  Disons qu'on garde alors notre instance qu'on veut embarquer dans une objet Python, on va donc s'attaquer juste au hook du dispatcher
    qui est sauv� dans la structure IClass assoc�e avec l'instance. Rempla�ons donc les fonctions h_Entry et h_SubEntry de fa�on � faire executer
    notre propre dispatcher, qui lui-m�me appelera le dispatcher d'origine qu'on aura pr�alablement sauv� (d'ailleur rien que ce point est un probl�me).
    
    => probl�mes: il faut savoir que l'adresse du hook est l'adresse de la structure IClass puisque la structure Hook y est embarqu�e au d�but.
    C'est pour cela que le prototype du dispatcher commence par struct IClass * et non pas par struct Hook * comme tout hook car en fait
    c'est la m�me chose ici. Le dispatcher �tant tout simplement appel� par CallHook (ou CallHookA). On peut ce dire 'cool! Alors appelons
    dans notre dispatcher custom le dispatcher d'origine!'... Et bah non, car comme on vient de le dire, on n'appel pas la fonction directement
    mais on passe par CallHook, qui s'attend � avoir un pointeur sur un hook. Mais on ne peut pas passer une nouvelle structure hook
    remplie avec les fonctions d'origines, car le pointeur change donc les donn�es qui suivent la structure ne sont plus celle de la structure IClass.
    Donc, soit juste avant d'appeler avec CallHook le "hook-IClass" on revient avec les fonctions d'origines et on remet notre dispatcher
    just apr�s l'appel, et ainsi la classe d'origine n'y voit que du feu (mais cela rajoute du code qui ralentit le dispatcher), soit on appel comme
    un gros cochon la fonction h_Entry "� la main" (avec tout ce que cela implique pour MorphOS = setup des registres 68k,
    appel de la couche �mulation, ...). Alors d�j� c'est franchement plus tr�s propre tout cela mais rajoutons qu'on est en train de modifier le code
    de la structure IClass, qui nous appartient pas du tout et donc on ne g�re rien niveau vie (on retire comment notre disptacher si la classe
    doit  �tre d�truite?). Et c'est pas tout car on touche � des classes �tant quasiement � coups-s�r utilis�es ailleur que par notre module.
    R�sultat si notre module n'est pas 100% robuste on crash tous le syst�me... et quand on quitte python on a int�ret � faire le m�nage proprement!
    Alors solution envisageable mais tr�s peut fiable (et je n'ai m�me pas parl� comment enregistr� les fonctions du hook d'orginine!).

    c) Patcher une fonction:
    - J'ai tent� de patcher DisposeObject() de l'intuition.library. Effectivement cette fonction est bien appel� fr�quement pour d�truire un object.
    Malheureusement cela n'est pas syst�matique, on peut-tr�s bien appeler '� la main' la m�thode OM_DIPOSE et le meilleur (ou pire..) des exemples
    pour cela est la fonction MUI_DiposeObject() de la muimaster.library. Patcher cette derni�re alors (aussi...)? Cela n'arrange en rien
    l'appel '� la main'. Donc on oublis.
    
    d) Il me reste plus comme choix de patcher la rootclass... C'est pas tr�s propre, mais au moins on patch uniquement qu'une seule classe.
    L'id�e est donc de modifier (comme expliqu� en 2)) le hook de la classe root pour appeler notre prope dispatcher, propre � avertir
    le pendant pythonesque de l'objet de la d�cision morbide de l'objet BOOPSI (donc MUI par l'occasion).
    Reste � savoir o� sauver les anciennes valeurs du hook. Sachant de plus qu'il ne faut faire cela qu'une seule fois (on va pas cummuler
    les patches n'est-ce pas...) et vu que notre module peut-�tre initialis� plusieur fois (au moins une fois par t�che utilisant
    la biblioth�que Python), le plus simple est d'externaliser la proc�dure de patch dans un code � part, en attendant que le syst�me
    d'initialisation des modules Python pour MorphOS impl�mente un appel unique (ce que je ne pense pas au passage).
    Maintenant qu'on est d'accord, sur la fa�on de conna�t�re � coup-s�r la mort d'un objet, il faut trouver un moyen de mettre en relation,
    l'objet MUI avec sont pendant Python.
    C�t� Python pas de pb, c'est enregistrer par notre module dans la structure Data de l'objet Python.
    C�t� BOOPSI maintenant... Sauf erreur de ma part, impossible de mettre un pointeur (celui de notre objet Python) quelque part dans l'instance
    de l'object :-( . J'ai v�rif� 20x, rien!
    Unique fa�on restante, utiliser une table de correspondance BOOPSI -> Python. Pour acc�l�rer la recherche dans cette table
    on pourra utiliser une indexation par hachage du pointeur de l'objet BOOPSI. Reste � dimensionner tout cela pour que cela reste
    efficace en terme d'acc�s.
    Dernier point pour la route: comme les modules sont li�s (en terme de donn�es) au process ex�cutant, la table de correspondance
    l'est donc aussi!
    Donc si un process A demande de tuer un objet x et qu'un process B utilisant le module Python poss�de un objet Python y
    li� avec cet objet x, comment allons nous retrouver cette table et comment avertir le process B?
    Il faut donc lier cette table avec le code de notre dispatcher, table qui contiendra des objets Python de diff�rentes instances
    de notre module. Les objets python seront d�li�s de la partie BOOPSI dans le dispatcher. L'acc�s au data du c�t� Python sera
    prot�g�e par l'utilisation d'un s�maphore pour g�rer l'aspect multi-processes. Comme un objet BOOPSI peut-�tre li� � de multiples
    objets Python, on utilisera une liste pour chaque objet BOOPSI, donnant ces objets Python li�s.

- R�-�valutation:
    Due � la complexit� du code g�n�r� par une version o� chaque objet BOOPSI peut-�tre associ� avec plusieurs objets Python
    (cas de plusieurs appli utilisant le module, se partagant un objets BOOPSI), une simplification s'impose...
    
    D�finition des r�gles:
        REG-01: associativit� 1-1 entre BOOPSI et Python.
        REG-02: code non re-entrant (m�me pour la destruction, donc attention!)
        REG-03: pas de communications d'objets entre t�ches.
        REG-04: seulement la t�che ayant associ�e l'object python et l'objet boopsi peut les dissocier.
        
- News du 01/11/07:
    L'impl�mentation du 2-d aurait du fonctionner...  en th�orie. Mais la pratique ne l'est pas du tout! Apr�s une discussion IRC
    avec Stuntzi il s'av�re que MUI ne suit pas les r�gles de BOOPSI, encore moins les appels indirects aux dispatchers des classes internes.
    Ceci expliquant l'impossibilit� de patcher les dispatchers des classes MUI => il ne sont pas appeler par le pointeur dans la structure IClass.
    Devant ce fait il ne reste donc plus qu'une seule fa�on d'op�rer: sous-classer toute classe utilis�e. Cette derni�re implique
    certaines restrictions que je ne souhaitait pas (cela explique que j'en avais pas encore parl�):
        - Le module ne pourra qu'op�rer sur des objets cr�� par lui-m�me. Aucun objet de l'ext�rieur (=d�j� cr��).
        - Impossible de passer un objet X du process l'ayant cr�� vers un autre. MUIM_Application_PushMethod ne peut-�tre utilis�.
        (Ceci n'est pas encore certain... il faudra y r�fl�chir apr�s l'impl�mentation de la phase 1).
        - Pas d'objets 'builtins' => on ne peut pas les sous-classer!

- Autre soucis: quitter Python doit de-allouer tout objets, m�me ceux qui ont encore des ref > 0. Le pb �vident c'est qu'on ne peut pas le faire
dans n'importe quel ordre: si on prend un objet A ayant une r�f�rence sur un objet B, qu'on d�truit l'objet B puis le A, si le A doit op�r�rer
sur l'objet B on est dans le baba! A va acc�der � un objet mort, donc de la m�moire al�atoire => crash.
C'est ce qui arrive en ce moment (20080107) quand je quitte Python: l'objet Application n'est pas d�truit le premier (al�as l'algorythme interne
de Python quand il d�truit tout), mais par exemple un objet Text inclus dans une fen�tre, incluse dans l'appli...

Solution:
=> augmenter le compteur de r�f de l'objet Python ou un autre priv� quand l'objet MUI est "parent�" dans un autre objet MUI, �
l'instar de Python.
=> Je pense que cela sera un compteur priv� (histoire de pas tout m�langer).

3) (News du 01/09/09) Apr�s qq ann�es � r�fl�chir (...) il y a beaucoup plus simple en faite...

- Pour le probl�me de savoir quand on objet MUI est d�truit pour ne plus �tre utilis� du c�t� python:
=> ON S'EN TAPE! (La solution ultime � tous les probl�mes du monde :-D)
On faite c'est tr�s simple, la r�gle est la suivante: un objet MUI ne doit pas �tre 'dispos�' par personne, sauf:
  - Par l'application elle-m�me, quand l'objet y est li�, directement ou non, car l'application est 'dispos�e' par notre module.
  - Par le type Python l'encapsulant, mais seulement si l'objet MUI n'est pas li� (MUA_Parent == NULL),
    exception faite de l'application elle-m�me �videment (car MUIA_Parent(app) == app).
100 ligne de blabla r�solus...

- Reste le probl�me des r�f�rences sur des choses donn�es en param�tres � des fonctions BOOPSI/MUI qui les enregistes.
=> pas solutionnable localement, c'est au programmeur d'en tenire compte!
=> Notes pour la documentation utilisateur:
   Expliquer le pb de garder des r�f�rences des valeurs donn�es.
*/
//-

/*
** Project Includes
*/

#include <Python.h>


/*
** System Includes
*/

#include <clib/debug_protos.h>

#include <proto/alib.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/intuition.h>
#include <proto/utility.h>
#include <proto/muimaster.h>

extern struct Library *PythonBase;
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
#define DPRINT(f, x...) ({ dprintf("\033[32m[%4u] %-25s: \033[0m", __LINE__, __FUNCTION__); dprintf(f ,##x); })
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

#define PyBOOPSIObject_OBJECT(o) (((PyBOOPSIObject *)(o))->boopsi)

#define PyBOOPSIObject_CHECK_OBJ(o) if (NULL == (o)) {                  \
        PyErr_SetString(PyExc_RuntimeError, "no BOOPSI object associated"); \
        return NULL; }

/*
** Private Types and Structures
*/

typedef struct DoMsg_STRUCT {
    ULONG MethodID;
    ULONG data[0];
} DoMsg;

typedef struct PyBOOPSIObject_STRUCT {
    PyObject_HEAD

    Object * boopsi;
} PyBOOPSIObject;


typedef struct PyMUIObject_STRUCT {
    PyBOOPSIObject base;
} PyMUIObject;


/*
** Private Variables
*/

static struct Hook OnAttrChangedHook;
static PyTypeObject PyBOOPSIObject_Type;
static PyTypeObject PyMUIObject_Type;


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
** Private Functions
*/

//+ PyMUIObjectFromObject
static PyMUIObject *
PyMUIObjectFromObject(Object *mo)
{
    PyMUIObject *pyo;

    /* MUI object linked to a PyMUIObject? just incref and return it */
    pyo = (PyMUIObject *)muiUserData(mo);
    if (NULL != pyo) {
        Py_INCREF((PyObject *)pyo);
        return pyo;
    }

    /* Allocate a new PyMUIObject */
    pyo = PyObject_New(PyMUIObject, &PyMUIObject_Type); /* NR */
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

        DPRINT("Attribute %#lx set: PyObject %p, MUI=%p, value: %ld, %lu, %p\n",
               attr, pyo, mo, (LONG)value, value, (APTR)value);


        res = PyObject_CallMethod(pyo, "_notify_cb", "II", attr, value); /* NR */
        Py_XDECREF(res);

        Py_DECREF(pyo);
    }

    /* in case of Python exception, the PyErr_Occurred() in the mainloop will catch it */
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

/*******************************************************************************************
** PyBOOPSIObject_Type
*/

//+ boopsi_new
static PyObject *
boopsi_new(PyTypeObject *type, PyObject *args)
{
    PyBOOPSIObject *self;
    UBYTE *class;
    PyObject *attrs=NULL;
    Object *obj;
    struct TagItem *tags;

    if (!PyArg_ParseTuple(args, "s|O:PyBOOPSIObject", &class, &attrs))
        return NULL;

    /* The Python object is needed before convertir the attributes dict into tagitem array */
    self = (APTR)type->tp_alloc(type, 0);
    if (NULL != self) {
        if (NULL != attrs) {
            tags = attrs2tags((PyObject *)self, attrs);
            if (NULL != tags) {
                if (PyMUIObject_Check(self))
                    obj = MUI_NewObjectA(class, tags);
                else
                    obj = NewObjectA(NULL, class, tags);
                PyMem_Free(tags);
            } else
                obj = NULL;
        } else if (PyMUIObject_Check(self))
            obj = MUI_NewObject(class, TAG_DONE);
        else
            obj = NewObject(NULL, class, TAG_DONE);
        
        if (NULL != obj) {
            DPRINT("New %s object @ %p (self=%p)\n", class, obj, self);
            PyBOOPSIObject_OBJECT(self) = obj;
            if (PyMUIObject_Check(self))
                muiUserData(obj) = (ULONG)self;
            return (PyObject *)self;
        } else
            PyErr_Format(PyExc_SystemError, "NewObjectA() failed on class %s.", class);
        
        Py_CLEAR(self);
    }
    
    return NULL;
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
    Object *obj;
    ULONG attr;
    ULONG value;
    char format[2];

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);
 
    if (!PyArg_ParseTuple(args, "Ic:_get", &attr, &format[0]))
        return NULL;

    DPRINT("attr: 0x%08x, format='%c'\n", attr, format[0]);

    if (!GetAttr(attr, obj, &value))
        return PyErr_Format(PyExc_ValueError, "GetAttr(0x%08lx) failed", attr);

    DPRINT("value: %d %u 0x%08lx\n", (LONG)value, value, value);

    /* Convert value into the right Python object */
    switch (format[0]) {
        case 'M':
            return (PyObject *)PyMUIObjectFromObject((Object *)value);

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
}
//-
//+ boopsi__set
/*! \cond */
PyDoc_STRVAR(boopsi__set_doc,
"_set(attr, value) -> int\n\
\n\
Try to set an attribute of the BOOPSI object by calling the BOOPSI function SetAttrs().\n\
Value should be a string, a unicode or something convertible into a int or a long.\n\
Note: No reference kept on the given value object!");
/*! \endcond */

static PyObject *
boopsi__set(PyBOOPSIObject *self, PyObject *args) {
    Object *obj;
    PyObject *value_obj;
    ULONG attr;
    ULONG value;

    obj = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(obj);

    if (!PyArg_ParseTuple(args, "IO:_set", &attr, &value_obj)) /* BR */
        return NULL;
    
    if (!python2long((PyObject *)value_obj, &value))
        return NULL;

    DPRINT("Attr 0x%lx set to value: %ld %ld %#lx on BOOPSI obj @ %p\n", attr, (LONG)value, value, value, obj);
    set(obj, attr, value);  
    
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
"_do(method, args)\n\
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
    DPRINT("  Data size = %d\n", n);
    msg = (DoMsg *) PyMem_Malloc(sizeof(DoMsg) + sizeof(ULONG) * n);
    if (NULL == msg)
        return PyErr_NoMemory();

    for (i = 0; i < n; i++) {
        PyObject *o = PyTuple_GET_ITEM(meth_data, i);
        ULONG *ptr = (ULONG *) &msg->data[i];

        if (python2long(o, ptr)) {
            PyMem_Free(msg);
            return NULL;
        }

        DPRINT("  args[%u]: %d, %u, 0x%08x\n", i, (LONG)*ptr, *ptr, *ptr);
    }

    /* Notes: objects given to the object dispatcher should remains alive during the call of the method,
     * even if this call cause some Python code to be executed causing a DECREF of these objects.
     * This is protected by the fact that objects have their ref counter increased until they remains
     * inside the argument tuple of this function.
     * So here there is no need to INCREF argument python objects.
     */

    msg->MethodID = meth;
    ret = PyInt_FromLong(DoMethodA(obj, (Msg) msg));
    PyMem_Free(msg);

    if (PyErr_Occurred())
        return NULL;

    return ret;
}
//-

static struct PyMethodDef boopsi_methods[] = {
    {"_get", (PyCFunction) boopsi__get, METH_VARARGS, boopsi__get_doc},
    {"_set", (PyCFunction) boopsi__set, METH_VARARGS, boopsi__set_doc},
    {"_do",  (PyCFunction) boopsi__do,  METH_VARARGS, boopsi__do_doc},
    {NULL, NULL} /* sentinel */
};

static PyTypeObject PyBOOPSIObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "_muimaster.PyBOOPSIObject",
    tp_basicsize    : sizeof(PyBOOPSIObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    tp_doc          : "BOOPSI Objects",
    
    tp_new          : (newfunc)boopsi_new,
    
    tp_repr         : (reprfunc)boopsi_repr,
    tp_methods      : boopsi_methods,
};

/*******************************************************************************************
** MUIObject_Type
*/

//+ muiobject_dealloc
static void
muiobject_dealloc(PyMUIObject *self)
{
    Object *mo, *app, *parent;
    
    mo = PyBOOPSIObject_OBJECT(self);
    DPRINT("self=%p, obj=%p\n", self, mo);

    if (NULL != mo) {
        if (!get(mo, MUIA_ApplicationObject, &app) || !get(mo, MUIA_Parent, &parent)) {
            DPRINT("unable to free object %p!\n", mo);
            return;
        }
        
        /* Destroy only the Application object or not used objects */
        if ((mo == app) || ((NULL == app) && (NULL == parent))) {
            DPRINT("before MUI_DisposeObject(%p)\n", mo);
            MUI_DisposeObject(mo);
            DPRINT("after MUI_DisposeObject(%p)\n", mo);
        } else {
            DPRINT("Object %p not disposed (used): app=%p, parent=%p\n", mo, app, parent);

            /* Just unlink it */
            muiUserData(mo) = NULL;
        }
    }

    ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}
//-
//+ muiobject__nnset
/*! \cond */
PyDoc_STRVAR(muiobject__nnset_doc,
"_nnset(attr, value, keep) -> int\n\
\n\
Like BOOPSIObject._set() but without triggering notification on MUI object.");
/*! \endcond */

static PyObject *
muiobject__nnset(PyMUIObject *self, PyObject *args) {
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

    Py_RETURN_NONE;
}
//-
//+ muiobject__notify
/*! \cond */
PyDoc_STRVAR(muiobject__notify_doc,
"_notify(trigattr, trigvalue)\n\
\n\
Sorry, Not documented yet :-(");
/*! \endcond */

static PyObject *
muiobject__notify(PyMUIObject *self, PyObject *args) {
    PyObject *value_obj;
    ULONG trigattr, trigvalue, value;
    Object *mo;

    mo = PyBOOPSIObject_OBJECT(self);
    PyBOOPSIObject_CHECK_OBJ(mo);

    if (!PyArg_ParseTuple(args, "IO:_notify", &trigattr, &value_obj)) /* BR */
        return NULL;

    if (!python2long(value_obj, &trigvalue))
        return NULL;

    DPRINT("MO: %p, trigattr: %#lx, trigvalue('%s'): %ld, %lu, %#lx\n",
           mo, trigattr, OBJ_TNAME(value_obj), (LONG)trigvalue, trigvalue, trigvalue);

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
             MUIV_Notify_Self, 5,
             MUIM_CallHook, (ULONG)&OnAttrChangedHook, trigattr, value);

    Py_RETURN_NONE;
}
//- muiobject__notify

static struct PyMethodDef muiobject_methods[] = {
    {"_nnset",  (PyCFunction) muiobject__nnset,  METH_VARARGS, muiobject__nnset_doc},
    {"_notify", (PyCFunction) muiobject__notify, METH_VARARGS, muiobject__notify_doc},
    {NULL, NULL} /* sentinel */
};

static PyTypeObject PyMUIObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_base         : &PyBOOPSIObject_Type,
    tp_name         : "_muimaster.PyMUIObject",
    tp_basicsize    : sizeof(PyMUIObject),
    tp_flags        : Py_TPFLAGS_DEFAULT,
    tp_doc          : "MUI Objects",

    tp_dealloc      : (destructor)muiobject_dealloc,
    tp_methods      : muiobject_methods,
};


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
 - doesn't check if app really contains an application MUI object");
/*! \endcond */

static PyObject *
_muimaster_mainloop(PyObject *self, PyObject *args)
{
    ULONG sigs = 0;
    PyObject *pyapp;
    Object *app;
    
    if (!PyArg_ParseTuple(args, "O!", &PyMUIObject_Type, &pyapp))
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

        if (PyErr_Occurred())
            return NULL;
    }

    DPRINT("bye mainloop...\n");
    Py_RETURN_NONE;
}
//- _muimaster_mainloop

/* module methods */
static PyMethodDef _muimaster_methods[] = {
    {"_mainloop", _muimaster_mainloop, METH_VARARGS, _muimaster_mainloop_doc},
    {NULL, NULL} /* Sentinel */
};


/*
** Public Functions
*/

//+ PyMorphOS_CloseModule
void
PyMorphOS_CloseModule(void) {
    DPRINT("Closing module...\n");

    if (NULL != MUIMasterBase) {
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

    INIT_HOOK(&OnAttrChangedHook, OnAttrChanged);

    MUIMasterBase = OpenLibrary(MUIMASTER_NAME, MUIMASTER_VLATEST);
    if (NULL == MUIMasterBase) return;

    /* New Python types initialization */
    if (PyType_Ready(&PyBOOPSIObject_Type) < 0) return;
    if (PyType_Ready(&PyMUIObject_Type) < 0) return;

    /* Module creation/initialization */
    m = Py_InitModule3(MODNAME, _muimaster_methods, _muimaster__doc__);
    if (all_ins(m)) return;

    ADD_TYPE(m, "PyBOOPSIObject", &PyBOOPSIObject_Type);
    ADD_TYPE(m, "PyMUIObject", &PyMUIObject_Type);
}
//-

/* EOF */
