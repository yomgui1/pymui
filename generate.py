import os, sys, re
from pprint import pprint

muia_match = re.compile('.*(MUIA_\w+).*(0x[0-9a-fA-F]+).*').match
muim_match = re.compile('.*(MUIM_\w+).*(0x[0-9a-fA-F]+).*').match
muiv_match = re.compile('.*(MUIV_\w+)[ \t]+(.*)').match
muii_match = re.compile('.*(MUII_\w+)[ \t]+(.*)').match

vars_to_change = { 'MUIV_Application_Save_ENV':      0,
                   'MUIV_Application_Save_ENVARC':   -1,
                   'MUIV_Application_Load_ENV':      0,
                   'MUIV_Application_Load_ENVARC':   -1,
                   'MUIV_Textinput_NoMark':          -1,
                   }

def parse(lines):
    attrs = []
    vars = []
    methods = []
    integers = []
    
    for line in lines:
        ma = muia_match(line)
        mm = muim_match(line)
        mv = muiv_match(line)
        mi = muii_match(line)
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
        if mi:
            n = mi.group(1)
            v = re.sub('/\*.*\*/', '', mi.group(2))
            integers.append((n, v))

    return methods, attrs, vars, integers
            
incdir = sys.argv[1]
incfile = "libraries/mui.h"
output = "pymui/defines.py"

fd = open(os.path.join(incdir, incfile))
try:
    m,a,v,i = parse(fd.xreadlines())
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
    for t in i:
        fd.write("%-40s = %s\n" % t)
except:
    fd.close()
    os.remove(output)
    raise
else:
    fd.close()
