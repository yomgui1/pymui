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
