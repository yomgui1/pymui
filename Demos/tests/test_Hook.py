from pymui import *

class MyException(Exception):
    pass

args = (c_STRPTR('toto'), c_STRPTR('titi'), c_STRPTR('tutu'), c_STRPTR(0))

n = Notify()

def callback(a2, a1):
    print "A1 = %x" % a1
    print "A2 = %x" % a2

    # First argument is the MUI object that call the hook
    o = c_MUIObject._asobj(a2)
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

hook = c_Hook(callback)
badhook = c_Hook(bad_callback)

# Shall print an exception
n.CallHook(badhook)

# Good example
n.CallHook(hook, *args)
