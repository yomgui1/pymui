#!/usr/bin/env python

from distutils.core import setup, Extension

opt = ['-Wall -Wuninitialized -Wstrict-prototypes -Wno-pointer-sign']
libraries = ['syscall']
include_dirs = []

with_cairo = True

if with_cairo:
    opt += ['-DWITH_PYCAIRO']
    include_dirs.append('/usr/local/include/pycairo')
    include_dirs.append('/usr/local/include/cairo')
    libraries += ['cairo', 'pixman-1', 'ft2']

setup(name = 'PyMUI',
      version = '0.6.1',
      author='Guillaume Roguez',
      description = 'Python wrapper for the MUI library',
      url='http://www.yomgui.fr/yiki/doku.php/dev:pymui:start',
      platforms=['morphos'],
      packages = ['pymui', 'pymui.mcc'],
      ext_modules = [Extension('pymui._muimaster',
                               ['src/_muimastermodule.c'],
                               include_dirs=include_dirs,
                               libraries=libraries,
                               extra_compile_args = opt)],
      data_files=[('Docs/PyMUI', ('LICENSE', 'HISTORY'))],
      )
