#!/usr/bin/env python

from distutils.core import setup, Extension

opt = ['-Wall -Wuninitialized -Wstrict-prototypes -Wno-pointer-sign']

setup(name = 'PyMUI',
      version = '0.4',
      author='Guillaume Roguez',
      description = 'Python wrapper for the MUI library',
      url='http://www.yomgui.fr/yiki/doku.php/dev:pymui:start',
      platforms=['morphos'],
      packages = ['pymui', 'pymui.mcc'],
      ext_modules = [Extension('pymui._muimaster',
                               ['src/_muimastermodule.c'],
                               libraries = ['syscall'],
                               extra_compile_args = opt)],
      data_files=[('Docs/PyMUI', ('LICENSE', 'HISTORY'))],
      )
