#!/usr/bin/env python

from distutils.core import setup, Extension

opt = ['-Wall -Wuninitialized -Wstrict-prototypes']

setup(name = 'PyMui',
      version = '1.0',
      author='Guillaume Roguez',
      description = 'Python wrapper for the MUI library',
      url='http://www.yomgui.fr/yiki/doku.php/dev:pymui:start',
      platforms=['morphos'],
      packages = ['pymui'],
      ext_modules = [Extension('pymui._muimaster',
                               ['src/_muimastermodule.c'],
                               extra_compile_args = opt)],
      )
