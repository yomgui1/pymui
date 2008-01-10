#!python

from distutils.core import setup, Extension

module1 = Extension('_muimaster', sources = ['src/_muimastermodule.c'])

setup(name = 'PyMui',
    version = '1.0',
    description = 'This is a test',
    packages = ['pymui'],
    ext_package = 'pymui',
    ext_modules = [module1],
    )
