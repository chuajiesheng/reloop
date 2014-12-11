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

ext_modules = [
    Extension(
    name="liftedLP.saucywrap",
    sources=["liftedLP/saucy/saucywrap.pyx",\
             "liftedLP/saucy/fc.cpp", \
             "liftedLP/saucy/saucy.c",\
             "liftedLP/saucy/main.c",\
             "liftedLP/saucy/saucyio.c",\
             "liftedLP/saucy/util.c"],
    include_dirs = [numpy.get_include()],  # .../site-packages/numpy/core/include
    language="c++",
    extra_compile_args = "-ansi -fpermissive -Wall -O0 -ggdb -fPIC".split(),
        # extra_link_args = "...".split()
    ),
    Extension(
    name="liftedLP.glpkwrap",
    sources=["liftedLP/utils/glpkwrap.pyx",\
             "liftedLP/utils/glpk2py.cpp"],
    include_dirs = [numpy.get_include()],  # .../site-packages/numpy/core/include
    libraries=["glpk"],
    language="c++",
    extra_compile_args = "-ansi -fpermissive -Wall -O0 -ggdb -fPIC".split(),
        # extra_link_args = "...".split()
    )

]

setup(
    name = 'liftedLP',
    version = "0.0",
    package_dir={'liftedLP':'liftedLP'},
    packages = ['liftedLP', 'liftedLP.utils'],
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,
        # ext_modules = cythonize(ext_modules)  ? not in 0.14.1
    # version=
    # description=
    # author=
    # author_email=
    )

# test: import f
