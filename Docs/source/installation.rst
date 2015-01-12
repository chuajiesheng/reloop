.. _installation:

============
Installation
============
Hello and thank you for your interest in our program. We are constantly making improvements to performance and adding features. If you want to help developing or just want to try out our program you first need to install some required packages. So to get started right away you will need to follow these steps to be able to run the code and develop new features.

Setup
=====


For Users
*********

To be able to run RLP properly you will need to install some packages, which are being used by our program.

    **SciPy**

    First you will need to install SciPy, which provides data structures like arrays and matrices for Python in an efficient way.
    The best way to install SciPy is to follow the installation instructions on the official SciPy homepage, which can be found here : `SciPy <http://scipy.org>`_

    The easiest way to install SciPy, if you have the admin permissions to do so, is to run::

        $ sudo apt-get install python-numpy python-scipy python-matplotlib ipython ipython-notebook python-pandas python-sympy python-nose
    
    for Linux Users.

    **GNU glpk**

    The GNU glpk is necessary in order to actually solve the calculated LP. You can follow the installation guide on the GLPK wikibooks if you like : `glpk <http://en.wikibooks.org/wiki/GLPK/Linux_OS>`_ 

    After you have successfully installed the packages you might need to adjust your library paths, because your system might not yet know where to find the new files. To do that as a superuser you can just run::

        $ sudo ldconfig

    If you do not have the permission to execute the above command you will need to adjust your library path manually by using::

        $ export LD_LIBRARY_PATH="/path/to/the/sharedlibaries/of/glpk"

    In case you do not want to set a permanent path to the shared library we suggest to create a make file, which has to be executed before running the actual program. This will keep the shared libraries seperated from your system.    

    **Z-LIB**

    The zlib1g-dev package is also necessary to run the program. It is installed by running::

        $ sudo apt-get install zlib1g-dev

    **Picos**

    To install Picos you need to download it first and the install it in the python environment or via pip. A tutorial on how to install Picos can be found here: `Picos <http://picos.zib.de/intro.html#installation>`_

For Developers
**************

    **Cython**

    Cython is necessary, because it links the python code with our C++ code. It allows to call C++ functions from our python framework. As soon as you change C++ or C code in our program you will need Cython to recompile the whole code. If you have pip installed on your OS you can simply run::

        $ pip install cython

    Otherwise you can download the tarball and install it using python, by unpacking the tarball and running::

        $python setup.py install

    in the specified folder. For more information about how to install cython see the `Cython_Documentation <http://docs.cython.org/src/quickstart/install.html>`_


Troubleshooting
===============


FAQ
===