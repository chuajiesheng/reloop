# python f-setup.py build_ext --inplace
#   cython wrapper.pyx -> wrapper.cpp
#   g++ -c wrapper.cpp -> wrapper.o
#   g++ -c fc.cpp -> fc.o
#   link wrapper.o fc.o -> wrapper.so

# distutils uses the Makefile distutils.sysconfig.get_makefile_filename()
# for compiling and linking: a sea of options.

# http://docs.python.org/distutils/introduction.html
# http://docs.python.org/distutils/apiref.html  20 pages ...
# http://stackoverflow.com/questions/tagged/distutils+python

import numpy
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import os
# from Cython.Build import cythonize

os.environ["CC"] = "g++" 

ext_modules = [Extension(
    name="wrapper",
    sources=["wrapper.pyx", "fc.cpp", "saucy.c", "main.c", "saucyio.c", "util.c","glpk2py.cpp"],
        # extra_objects=["fc.o"],  # if you compile fc.cpp separately
    include_dirs = [numpy.get_include(),"./libs/"],  # .../site-packages/numpy/core/include
    language="c++",
    libraries= ["glpk"],
    library_dirs = ["./libs/"],
    extra_compile_args = "-ansi -fpermissive -Wall -O0 -ggdb -fPIC".split(),
        # extra_link_args = "...".split()
    )]

setup(
    name = 'wrapper',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,
        # ext_modules = cythonize(ext_modules)  ? not in 0.14.1
    # version=
    # description=
    # author=
    # author_email=
    )

# test: import f
