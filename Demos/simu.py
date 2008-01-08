class _m:
    _idcnt = 0
    MUIC_Notify = "Notify.mui"

    class CPointer(object):
        def __init__(self, address=0):
            object.__init__(self)
            self.__addr = long(address)

        def __long__(self):
            return self.__addr

        def __int__(self):
            return int(self.__addr__)

        def __repr__(self):
            return "<CPointer at %p, address=%p>" % (id(self), self.__addr)

        def __nonzero__(self):
            return self.__addr != 0

        address = property(fget=lambda self: self.__address)

        def _setAddr(self, v):
            self.__addr = v

    # Abstraction for testings on non-Amiga systems
    class MUIObject(CPointer):
        def __init__(self):
            super(_m.MUIObject, self).__init__()
            self.__attrd = {}

        def _get(self, type, attr):
            assert isinstance(attr, (int, long))
            print "\033[032m** _get: attr=0x%x, type=%s\033[0m" % (attr, type.__name__)
            if attr in self.__attrd:
                return type(self.__attrd[attr])
            return type(0)

        def _set(self, attr, value, save=False):
            assert isinstance(attr, (int, long))
            print "\033[032m** _set: attr=0x%x, value=%d (%u, %x), save=%s\033[0m" % (attr, value, value, value, bool(save))
            self.__attrd[attr] = value

        def _create(self, clID, data):
            assert type(data) == dict and type(clID) == str
            print "\033[032m** _create: clID=%s, data.keys()=%s\033[0m" % (clID, sorted(data.keys()))
            self._setAddr(0xADEADB0A)
            return True

    @classmethod
    def newid(cl):
        cl._idcnt += 1
        return cl._idcnt
