###
## \file _core2.py
## \author ROGUEZ "Yomgui" Guillaume
##

# ABOUT METHODS:
#
# MUI knows methods only by an integer id
# PyMUI should make the link between this id and
# a Python method.
#
# MUI methods permit to pass basic C variables,
# but also pointers, so reference on some possible
# Python objects.
# For some methods, these references are used
# only during the call to DoMethod() and not saved.
# For this kind of methods, no issues.
# But some other records for some internal usage
# these references, so when the call to DoMethod()
# returns we need to make sure that the refered
# data block will not be freed as in the case of
# a temporary Python objects.
# Unforntunatly, there are no ways to know if a
# method will keep references or not, except to belive
# methods documentations... if it's written :-(
# So we need a way to mark if a method argument is
# keep or not.
# Now the side effect is a kept argument should be
# untracked after a known time!
# The safe way is to track marked objects in a list
# owned by the object executing the method.
# And when this object is destroyed, deleting this list.
#

# ABOUT CUSTOM MUI CLASSES IN PYTHON:
#
# To be able to create MCC using Python, this PyMCC is defined
# as a classic Python class, with a base class defined here as
# first class.
# So when MUI want to call a method, the custom dispatcher
# of PyMuiObject is called and a corresponding Python method
# is searched for this MUI MethodId. MUI method data are
# transformed into Python objects using definition given and
# finally the Python method is called with these arguments.
#
# The reverse is done also (if the MCC developper uses METHODS
# arrays to define methods or call super methods correctly)
# because methods defined in METHODS list are automatically created
# with a C core that transform arguments in MUI suitable form and
# call the DoMethod() as well.
#
# Types:
#   i/h/c = int/short/char (LONG/WORD/BYTE)
#   I/H/C = unsigned int (ULONG/UWORD/UBYTE)
#   v = void pointer object (APTR)
#   s = string (STRPTR)
#   b = bool (for unsigned int with values 0 or -1/other)
#   f = float (FLOAT, only usable with arrays)
#   d = double (DOUBLE, only usable with arrays)
#   m = a PyMuiObject object
#   p = any Python object
#   t = see structures case.
#
# - Dimensionned arrays results in tuples, format is xn,
# where x is a previous type and n the tuple dimension.
# - Undimensionned arrays results in iterators, format is x*,
# where x is a previous type. These iterators never stop,
# so it's the user responsability to know how many times
# the methods next() can be called.
# - Special case of undimensionned arrays but finished by
# a zero value is possible, format is x#, where x is
# a previous type.
#
# METHODS dict entries format : id: (name, format [, structures, ...])
# name = string name of Python method
# id = MUI MethodID integer
# format = string name defining MUI method arguments,
#   None possible if no arguments.
#
# Note: MethodID argument should not be included in the format string.
#
# If an argument should be tracked during the life of
# the object, append a dot '.' at the end of argument format
# IMPORTANT NOTE: this tracking can only store one argument object
# for one method argument at once.
#

class Notify(PyMuiObject):
    pass

class MinMaxStruct(StructObject):
    _fields_ = (('MinWidth',  t_WORD),
                ('MinHeight', t_WORD),
                ('MaxWidth',  t_WORD),
                ('MaxHeight', t_WORD),
                ('DefWidth',  t_WORD),
                ('DefHeight', t_WORD))

class Area(Notify):
    CLASSID = _m.MUIC_Area
    HEADER = None

    METHODS = {
        0x80423874: ('AskMinMax',           "t,", MinMaxStruct),
        0x8042cac0: ('Cleanup',             None),
        # NODOC: 0x8042df9e: ('ContextMenuAdd',      "miii*i*,"),
        0x80429d2e: ('ContextMenuBuild',    "ii,m"),
        0x80420f0e: ('ContextMenuChoice',   "m,"),
        0x80421c41: ('CreateBubble',        "iis.I,"),
        0x80428e93: ('CreateShortHelp',     "ii,"),
        0x804211af: ('DeleteBubble',        "v,"),
        0x8042d35a: ('DeleteShortHelp',     "s,"),
        0x804216bb: ('DoDrag',              "iiI,"),
        0x8042c03a: ('DragBegin',           "m,"),
        0x8042c555: ('DragDrop',            "miiI,"),
        0x804251f0: ('DragFinish',          "mi,"),
        0x80420261: ('DragQuery',           "m,"),
        0x8042edad: ('DragReport',          "miiiI,"),
        0x80426f3f: ('Draw',                "I,"),
        0x804238ca: ('DrawBackground',      "iiiiiii,"),
        0x80426d66: ('HandleEvent',         "viv,"),
        0x80422a1a: ('HandleInput',         "vi,"),
        0x8042f20f: ('Hide',                None),
        0x80428354: ('Setup',               "v,"),
        0x8042cc84: ('Show',                "v,"),
        # NODOC: 0x8042b0a9: ('UpdateConfig',        "Iiv64C64,")
        }

    def __init__(self):
        #self._menustrips = set()
        pass

    def AskMinMax(self, *args):
        """Custom Class implementation.

        Called by MUI to known min-max-default size of the area.
        """
        return self._mui_AskMinMax(*args)
