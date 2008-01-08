#!python

from distutils.core import setup, Extension

module1 = Extension('_muimaster', sources = ['_muimastermodule.c'])

setup(name = 'PackageName',
    version = '1.0',
    description = 'This is a test',
    ext_modules = [module1])
