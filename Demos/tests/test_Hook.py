###############################################################################
#   Copyright(c) 2009-2014 Guillaume Roguez
#
#   This file is part of PyMUI.
#
#   PyMUI is free software: you can redistribute it and/or modify it under
#   the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PyMUI is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with PyMUI. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from pymui import *

class MyException(Exception):
    pass

test_args = [ c_STRPTR(x) for x in ('tutu', 'toto', 'titi') ]

n = Notify()

def callback(obj, args):
    # Notify.CallHook method calls the callback with 2 long as arguments.
    # First value is the pointer on the MUI Object that called the hook.
    # Second value is the pointer on the first argument given to CallHook,
    # after the callback argument.

    print "Hello: callback",

    assert isinstance(obj, c_pMUIObject)
    assert isinstance(args, c_APTR.PointerType())
    assert obj.object is n

    # Second argument is a pointer on the first hook argument.
    assert long(args[0]) == long(test_args[0])

    # Use this pointer as a string array now
    x = c_pSTRPTR.from_value(long(args))
    assert long(x[0]) == long(test_args[0])
    assert any(a.value == b.value for a, b in zip(test_args, x))

def bad_callback(*args):
    print "Hello: bad_callback",
    raise MyException('error')

def typed_callback(obj):
    print "Hello: typed_callback",

    assert isinstance(obj, c_pSTRPTR)
    assert len(obj[:3]) == 3
    assert long(obj[2]) != 0
    assert long(obj[3]) == 0

def complex_callback(args_ptr):
    print "Hello: complex_callback",

    s = c_STRPTR.from_value(args_ptr[0].value)
    i = c_LONG.from_value(args_ptr[1].value)
    o = c_PyObject.from_value(args_ptr[2].value)
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
n.CallHook(callback, *test_args)
print '[ok]'

# Typed hook
n.CallHook(typed_hook, c_STRPTR('toto'), c_STRPTR('titi'), c_STRPTR('tutu'), 0)
print '[ok]'

# Various arguments types
n.CallHook(complex_hook, c_STRPTR('test'), 42, c_PyObject([1, 2, 3]))
print '[ok]'
