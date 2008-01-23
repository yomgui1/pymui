from distutils.core import setup, Extension

opt = ['-Wall -Wuninitialized -Wstrict-prototypes']
module1 = Extension('_muimaster',
                    sources=['src/_muimastermodule.c'],
                    extra_compile_args = opt)

setup(name = 'PyMui',
    version = '1.0',
    description = 'Python wrapper for the MUI library',
    packages = ['pymui'],
    ext_package = 'pymui',
    ext_modules = [module1],
    )
