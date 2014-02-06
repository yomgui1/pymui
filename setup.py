#!/usr/bin/env python

###############################################################################
#   Copyright(c) 2009-2014 Guillaume Roguez
#
#   This file is part of PyMUI.
#
#   PyMUI is free software: you can redistribute it and/or modify it under
#   the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   PyMUI is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with PyMUI. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

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
      version = '0.7.0',
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
