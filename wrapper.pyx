# f.pyx: numpy arrays -> extern from "fc.h"
# 3 steps:
# cython f.pyx  -> f.c
# link: python f-setup.py build_ext --inplace  -> f.so, a dynamic library
# py test-f.py: import f gets f.so, f.fpy below calls fc()

from cython.operator cimport preincrement as inc
import numpy as np
cimport numpy as np

#there is a bug with typing certain variables. To circumvent it we need to define our own type and pass it to the compiler otherwise the function will pass garbage to the c++ function
ctypedef np.uintp_t itype_t

#Defining std::vector to process the return type of fc
cdef extern from "<vector>" namespace "std":
    cdef cppclass vector[T]:
        cppclass iterator:
            T operator*()
            iterator operator++()
            bint operator==(iterator)
            bint operator!=(iterator)
        vector()
        void push_back(T&)
        T& operator[](int)
        T& at(int)
        iterator begin()
        iterator end()

cdef vector[int].iterator iter

cdef extern from "fc.h": 
    vector[itype_t] equitablePartitionSaucyV2(itype_t mvertices, itype_t medges, double data[], itype_t rown[], itype_t coln[], itype_t b[], int cIters, int coarsest);


def epSaucy(
    np.ndarray[np.double_t,ndim=1] A,
    np.ndarray[itype_t,ndim=1] B,
    np.ndarray[itype_t,ndim=1] C,
    np.ndarray[itype_t,ndim=1] Z,
    cIters = 0,
    coarsest = True):

    # Pass references to c++ function to guarantee correct memory access
    cdef vector[size_t] res = equitablePartitionSaucyV2(Z.shape[0], A.shape[0], &A[0], &B[0], &C[0], &Z[0], cIters, 1 if coarsest else 0)
    
    #Instantiate Iterator and iterate over returned c++ vector and assign values to numpy array
    iter = res.begin()
    i = 0 
    while iter != res.end():
     i = i + 1
     inc(iter)
    cdef np.ndarray result = np.empty(i)
    for x in range(0,i):
     result[x] = res[x]
   
    
    #Print and return resulting numpy array
    return result
