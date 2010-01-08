from pymui import *

class MyException(Exception):
    pass

args = (c_STRPTR('tutu'), c_STRPTR('toto'), c_STRPTR('titi'))

n = Notify()

def callback(obj, args_ptr):
    # Notify.CallHook method calls the callback with 2 long as arguments.
    # First value is the pointer on the MUI Object that called the hook.
    # Second value is the pointer on the first argument given to CallHook,
    # after the callback argument.

    print "Hello: callback",

    assert isinstance(obj, c_MUIObject)
    assert isinstance(args_ptr, c_APTR._PointerType())
    assert obj.value is n

    # Second argument is a pointer on the first hook argument.
    assert long(args_ptr[0]) == long(args[0])

    # Use this pointer as a string array now
    x = c_pSTRPTR.FromLong(long(args_ptr))
    assert long(x[0]) == long(args[0])
    assert any(a.value == b.value for a, b in zip(args, x))

def bad_callback(*args):
    print "Hello: bad_callback",
    raise MyException('error')

def typed_callback(obj):
    print "Hello: typed_callback",

    assert isinstance(obj, c_pSTRPTR)
    assert len(tuple(obj)) == 3

def complex_callback(args_ptr):
    print "Hello: complex_callback",

    s = c_STRPTR.FromLong(args_ptr[0].value)
    i = c_LONG.FromLong(args_ptr[1].value)
    o = c_PyObject.FromLong(args_ptr[2].value)
    assert s

typed_hook = c_NotifyHook(typed_callback, argstypes=(None, c_pSTRPTR))
complex_hook = c_NotifyHook(complex_callback, argstypes=(None, c_NotifyHook._argtypes_[1]))

# Shall print an exception
try:
    n.CallHook(bad_callback)
except MyException:
    print '[ok]'
else:
    raise AssertionError("MyException exception not raised by the bad hook callback")

# Good example
n.CallHook(callback, *args)
print '[ok]'

# Typed hook
n.CallHook(typed_hook, c_STRPTR('toto'), c_STRPTR('titi'), c_STRPTR('tutu'), 0)
print '[ok]'

# Various arguments types
n.CallHook(complex_hook, c_STRPTR('test'), 42, c_PyObject([1, 2, 3]))
print '[ok]'
