from pymui import *

class MyException(Exception):
    pass

args = ('tutu', 'toto', 'titi')

n = Notify()

def callback(hook_ptr, args_ptr):
    # Notify.CallHook method calls the callback with 2 long as arguments.
    # First value is the pointer on a Hook C structure
    # Second value is the pointer on the first argument given to CallHook,
    # after the callback argument.
    
    assert isinstance(hook_ptr, long)
    assert isinstance(args_ptr, long)
    
    # First argument is the MUI object that call the hook
    o = c_MUIObject.(a2)
    assert o.contents is n

    # Second argument is a pointer on hook arguments array.
    x = c_APTR.from_address(a1)
    assert x.value == long(args[0])

    x = c_pSTRPTR._asobj(a1)
    assert long(x[0]) == long(args[0])

    print tuple(o.contents for o in x)
    return 0

def bad_callback(*args):
    raise MyException('error')

def typed_callback(obj):
    assert isinstance(obj, c_pSTRPTR)
    print tuple(obj)

g_str = 'coucou'
def complex_hook(args_ptr):
    s = c_STRPTR.FromLong(args_ptr[0].value)
    i = c_LONG.FromLong(args_ptr[1].value)
    o = c_PyObject.FromLong(args_ptr[2].value)
    print s, i, o

    # note: We can't use a str object here, because this one
    # will be valable until this callback returns (local variable).
    # So when the CallHook() returns, the integer value will be a pointer
    # on a deallocated object!! Crashes...
    # So we reply using a global variable.
    return c_PyObject(g_str)

hook = c_Hook(callback)
badhook = c_Hook(bad_callback)
typed_hook = c_Hook(new_callback, argtypes=(None, c_pSTRPTR))
complex_hook = c_Hook(complex_callback, argtypes=(None, c_APTR._PointerType()))

# Shall print an exception
n.CallHook(badhook)

# Good example
print n.CallHook(hook, *args)

# Typed hook
n.CallHook(typed_hook, c_STRPTR('toto'), c_STRPTR('titi'), c_STRPTR('tutu'), 0)

# Various arguments types and non integer return value
ret = n.CallHook(complex_hook, c_STRPTR('test'), 42, c_PyObject([1,2 3]))
print ret
assert c_PyObject(ret).value is g_str
