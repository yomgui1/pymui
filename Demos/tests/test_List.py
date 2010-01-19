import os, sys
from pymui import *

import tokenize, token
from keyword import kwlist
import sys, cStringIO

normal = "\033n\0332"
bold = "\033b"
underline = "\033u"
tcolor = lambda n: "\033%u" % (2+n)

colors = {
    tokenize.NL: normal,
    tokenize.COMMENT: tcolor(1),
    tokenize.NAME: normal,
    tokenize.OP: tcolor(2),
    tokenize.STRING: tcolor(5),
    }

def colorize(readline):
    lcol = 0
    colname = False
    dot = False
    for tnum, tval, spos, epos, _ in tokenize.generate_tokens(readline):
        if tnum != token.ENDMARKER:
            spaces = ' '*(spos[1] - lcol)
            lcol = epos[1]
            if tnum == token.NAME:
                if tval in kwlist:
                    col = tcolor(3)
                    if tval in ('def', 'class'):
                        colname = True
                elif not dot and tval in __builtins__.__dict__:
                    col = bold + tcolor(5)
                else:
                    if colname:
                        col = bold + tcolor(1)
                        colname = False
                    else:
                        col = colors.get(tnum, '')
                dot = False
            else:
                dot = tval == '.'
                col = colors.get(tnum, '')
            
            if tval.endswith('\n'):
                tval = tval[:-1]+normal+'\n'
                lcol = 0
            if tnum == tokenize.NL:
                lcol = 0

            yield spaces + col + tval

class MyReadline(object):
    def __init__(self, lines, row=0):
        self.lines = lines
        self.row = row
        self.need_stop = False

    def setrow(self, n):
        self.row = n

    def stop(self):
        self.need_stop = True

    def __call__(self):
        if self.need_stop:
            raise StopIteration()
        try:
            line = self.lines[self.row]
            self.row += 1
            return line
        except IndexError:
            raise StopIteration()

class MyList(List):
    MCC = True

    def __init__(self):
        List.__init__(self, Background='ListBack', Format='BAR,', Title=True)
        self.entries = {}

    @muimethod(MUIM_List_Construct)
    def MyConstruct(self, msg):
        # entry is a string handled by a str Python object.
        # So we need to keep alive this object to keep valid the string pointer.

        # Converting the entry c_APTR into a Python string object
        v = c_STRPTR(msg.entry.value)

        # store the python object into a dict to keep valid the string
        if v.value in self.entries:
            print "double: '%s'" % v.value
        v = self.entries.setdefault(v.value, v) # we use setdefault and the string as key
                                                # to keep only one time equal strings.

        # because v is a c_STRPTR it's convertible into long!
        return v

    @muimethod(MUIM_List_Destruct)
    def Destructor(self, msg):
        print long(msg)

    @muimethod(MUIM_List_Display)
    def Display(self, msg):
        # here entry is NULL for title strings or a pointer on a C string, the one keep in self.entries.
        if msg.entry.value:
            msg.array[0] = str(long(msg.array[-1])+1)
            msg.array[1] = msg.entry.value
        else:
            msg.array[0] = 'Line #'
            msg.array[1] = 'Text'

mylist = MyList()

f = open(sys.argv[1], 'Ur')
lines = f.readlines()
f.close()

lines = ''.join(colorize(MyReadline(lines))).split('\n')
for line in lines:
    mylist.InsertSingleString(line)

top = HGroup(Child=mylist)

win = Window('PyMUI Test - More Complexe List Test', RootObject=top, CloseOnReq=True)
win.Notify('CloseRequest', True, lambda e: e.Source.KillApp())

app = Application(Base="PyMUITest_ComplexList", Author="Guillaume ROGUEZ", Copyright="Guillaume ROGUEZ - MIT license")
app.AddChild(win)

win.OpenWindow()
app.Run()
