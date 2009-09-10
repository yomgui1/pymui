#!/usr/bin/env python

import os, sys, re
from pprint import pprint

muia_match = re.compile('.*(MUIA_\w+).*(0x[0-9a-fA-F]+).*').match
muim_match = re.compile('.*(MUIM_\w+).*(0x[0-9a-fA-F]+).*').match
muix_match = re.compile('.*(MUI[VXIC]_\w+)[ \t]+(.*)').match

vars_to_change = { 'MUIV_Application_Save_ENV':      0,
                   'MUIV_Application_Save_ENVARC':   -1,
                   'MUIV_Application_Load_ENV':      0,
                   'MUIV_Application_Load_ENVARC':   -1,
                   'MUIV_Textinput_NoMark':          -1,
                   }
to_add = """
MADF_DRAWOBJECT = (1<< 0) # completely redraw yourself
MADF_DRAWUPDATE = (1<< 1) # only update yourself

IDCMP_SIZEVERIFY        = 0x00000001
IDCMP_NEWSIZE           = 0x00000002
IDCMP_REFRESHWINDOW     = 0x00000004
IDCMP_MOUSEBUTTONS      = 0x00000008
IDCMP_MOUSEMOVE         = 0x00000010
IDCMP_GADGETDOWN        = 0x00000020
IDCMP_GADGETUP          = 0x00000040
IDCMP_REQSET            = 0x00000080
IDCMP_MENUPICK          = 0x00000100
IDCMP_CLOSEWINDOW       = 0x00000200
IDCMP_RAWKEY            = 0x00000400
IDCMP_REQVERIFY         = 0x00000800
IDCMP_REQCLEAR          = 0x00001000
IDCMP_MENUVERIFY        = 0x00002000
IDCMP_NEWPREFS          = 0x00004000
IDCMP_DISKINSERTED      = 0x00008000
IDCMP_DISKREMOVED       = 0x00010000
IDCMP_WBENCHMESSAGE     = 0x00020000
IDCMP_ACTIVEWINDOW      = 0x00040000
IDCMP_INACTIVEWINDOW    = 0x00080000
IDCMP_DELTAMOVE         = 0x00100000
IDCMP_VANILLAKEY        = 0x00200000
IDCMP_INTUITICKS        = 0x00400000
IDCMP_IDCMPUPDATE       = 0x00800000
IDCMP_MENUHELP          = 0x01000000
IDCMP_CHANGEWINDOW      = 0x02000000
IDCMP_GADGETHELP        = 0x04000000
IDCMP_MOUSEHOVER        = 0x08000000 # v50
IDCMP_MOUSEOBJECTMUI    = 0x40000000 # special idcmp message created by MUI
IDCMP_LONELYMESSAGE     = 0x80000000
"""

def parse(lines):
    attrs = []
    vars = []
    methods = []
    
    for line in lines:
        ma = muia_match(line)
        mm = muim_match(line)
        mv = muix_match(line)
        if ma:
            attrs.append(ma.groups())
        if mv:
            n = mv.group(1)
            if n in vars_to_change:
                v = vars_to_change[n]
            else:
                v = re.sub('/\*.*\*/', '', mv.group(2))
            vars.append((n, v))
        if mm:
            methods.append(mm.groups())

    return methods, attrs, vars
            
incdir = sys.argv[1]
incfile = "libraries/mui.h"
output = "pymui/defines.py"

fd = open(os.path.join(incdir, incfile))
try:
    m,a,v = parse(fd.xreadlines())
finally:
    fd.close()

fd = open(output, 'w')
try:
    fd.write("TAG_USER = 1 << 31\n\n")
    for t in m:
        fd.write("%-40s = %s\n" % t)
    for t in a:
        fd.write("%-40s = %s\n" % t)
    for t in v:
        fd.write("%-40s = %s\n" % t)
    fd.write(to_add);
except:
    fd.close()
    os.remove(output)
    raise
else:
    fd.close()
