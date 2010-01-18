from pymui import *
from sys import getrefcount as rc

load_btn = SimpleButton('.', ShowMe=False)
print load_btn, rc(load_btn)
path_str = String(Frame='String', MaxLen=256)
print path_str, rc(path_str)

popasl = Popasl(Type='FileRequest', Button=load_btn, String=path_str)
print popasl, rc(popasl)
print [(hex(k), v) for k,v in popasl._keep_dict.iteritems()]

print rc(popasl), rc(load_btn), rc(path_str)
