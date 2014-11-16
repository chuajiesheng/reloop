# python f-setup.py build_ext --inplace
#   cython glpk2py-wrapper.pyx -> glpk2py-wrapper.cpp
#   g++ -c glpk2py-wrapper.cpp -> glpk2py-wrapper.o
#   g++ -c glpk2py.cpp -> glpk2py.o
#   link glpk2py-wrapper.o glpk2py.o -> glpk2py-wrapper.so

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
    name="glpkwrapper",
    sources=["glpk2py_wrapper.pyx", "glpk2py.cpp"],  #"saucy.c", "main.c", "saucyio.c", "util.c"
    #extra_objects=["~/glpk/glpk-4.47/src/glpapi04.c"],  # if you compile fc.cpp separately
    include_dirs = [numpy.get_include(),"./libs/"],  # .../site-packages/numpy/core/include
    libraries=["glpk"],
    language="c++",
    library_dirs = ["./libs/"],
    extra_compile_args = "-ansi -fpermissive -Wall -O0 -ggdb -fPIC".split(),
        # extra_link_args = "...".split()
    )]

setup(
    name = 'glpkwrapper',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,
        # ext_modules = cythonize(ext_modules)  ? not in 0.14.1
    # version=
    # description=
    # author=
    # author_email=
    )

# test: import f
