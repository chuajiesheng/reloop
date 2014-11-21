
# f.pyx: numpy arrays -> extern from "glpk2py.h"
# 3 steps:
# cython glpk2py-wrapper.pyx  -> glpk2py-wrapper.c
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
        void assign(size_t, T&) nogil
        void assign[input_iterator](input_iterator,input_iterator)
        int size()

cdef extern from "glpk2py.h":
 
    cdef enum bounds:      
        UPPER
        LOWER
        EQUAL
        UNBOUND

    cdef enum scaling:     
        GEOMMEAN
        EQUILIB

    void openLP(const char* fname, int format_);
    void closeLP();
    vector[double] getMatrix(bounds boundquery, int scaled);
    vector[double] getObjective(int scaled);
    void doScaling(scaling sctype);
    void solve();


#cdef vector[int].iterator iter

def openLP_Py(fname,format_):
    openLP(fname,format_)

def closeLP_Py():
    closeLP()

def getMatrix_Py(boundquery,scaled):
    # Time needed for one call =~ 0,015s
    #TODO : Split getMatrix into four functions as soon as it is confirmed as working properly
    cdef vector[double] res
    print"MatrixGeneration"
    if boundquery == UPPER:
        res = getMatrix(UPPER,scaled) 
    elif boundquery == LOWER:
        res = getMatrix(LOWER,scaled) 
    elif boundquery == EQUAL:
        res = getMatrix(EQUAL,scaled) 
    elif boundquery == UNBOUND:
        res = getMatrix(UNBOUND,scaled) 
    
    i = res.size()
    d = i/4
    cdef np.ndarray result = np.zeros([4,i/4],dtype=np.double)
  
    #More dynamic version for copying the resulting vector. Should be better for general solutions
    #   
    #for x in range(0,result.shape[0]):
    #    for y in range(0,result.shape[1]):
    #        result[x,y] = res[x*result.shape[1]+y]
    
    
    # Parallelized copying : We know that we have exactly for rows so we can copy them more efficient.
    for x in range(0,d):
        result[0,x] = res[x]
        result[1,x] = res[x+d]
        result[2,x] = res[x+d*2]
        result[3,x] = res[x+d*3]

    return result

def getObjective_Py(scaled):

    cdef vector[double] res = getObjective(scaled)
    #Instantiate numpy Array and get size of objective
    i = res.size()
    cdef np.ndarray result = np.empty(i)

    for x in range(0,i):
     result[x] = res[x]
  
    return result

def doScaling_Py(sctype):
    if sctype == 7:
        doScaling(EQUILIB)
    else:
        doScaling(GEOMMEAN)

def solve_Py():
    solve()


   
