from distutils.core import setup, Extension

module1 = Extension('_muimaster', sources=['src/_muimastermodule.c'])

setup(name = 'PyMui',
    version = '1.0',
    description = 'Python wrapper for the MUI library',
    packages = ['pymui'],
    ext_package = 'pymui',
    ext_modules = [module1],
    )
