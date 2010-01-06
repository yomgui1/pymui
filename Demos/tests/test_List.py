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
    def __init__(self):
        List.__init__(self, Background='ListBack', Format="BAR,")
        self.entries = {}

        self.ConstructHook = self.Constructor
        self.DestructHook = self.Destructor
        self.DisplayHook = self.Display

    def Constructor(self, pool, entry):
        # make a copy of entry string
        v = c_STRPTR(entry).value

        # If the line is identical twice or more, the entry value can be identical multiple times also.
        # Becarefull with that during the Destruct hook call!

        res = c_STRPTR(v)
        self.entries.setdefault(long(res), v)

        # because v is a c_STRPTR it's convertible into long!
        return res

    def Destructor(self, pool, value):
        try:
            del self.entries[value]
        except:
            pass

    def Display(self, str_array, entry):
        str_array = c_pSTRPTR._asobj(str_array-c_APTR.c_size())
        str_array[1] = str(long(str_array[0])+1)
        str_array[2] = entry

mylist = MyList()

f = open(sys.argv[1], 'Ur')
lines = f.readlines()
f.close()

lines = ''.join(colorize(MyReadline(lines)))

for line in lines.split('\n'):
    mylist.InsertSingleString(line, MUIV_List_Insert_Bottom)

top = HGroup(Child=mylist)

win = Window('PyMUI Test - More Complexe List Test', RootObject=top, CloseOnReq=True)
win.Notify('CloseRequest', True, lambda e: e.Source.KillApp())

app = Application(Base="PyMUITest_ComplexList", Author="Guillaume ROGUEZ", Copyright="Guillaume ROGUEZ - MIT license")
app.AddChild(win)

win.OpenWindow()
app.Run()
