import pymui

# PyMUI 0.6.dev crashes with this code
grp = pymui.Group()
obj = pymui.Rectangle()
print obj, hex(obj._object)

grp.AddHead(obj)
grp.MoveMember(obj, 0)