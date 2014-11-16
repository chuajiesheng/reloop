
# f.pyx: numpy arrays -> extern from "glpk2py.h"
# 3 steps:
# cython glpk2py-wrapper.pyx  -> glpk2py-wrapper.c
# link: python f-setup.py build_ext --inplace  -> f.so, a dynamic library
# py test-f.py: import f gets f.so, f.fpy below calls fc()

from cython.operator cimport preincrement as inc
import numpy as np
cimport numpy as np
#cimport glpk


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
   

cdef vector[int].iterator iter
cdef vector[int].iterator itera

cdef extern from "glpk.h":
    pass
cdef extern from "glpk2py.h":
    cdef enum filetype:
      pass
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


    

def openLP_Py(fname,format_):
    openLP(fname,format_)

def closeLP_Py():
    closeLP()

def getMatrix_Py(boundquery,scaled):
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

   
    iter = res.begin()
    i = 0
    while iter != res.end():
        i = i + 1
        inc(iter)
    cdef np.ndarray result = np.zeros([4,i/4],dtype=np.double)
  
    for x in range(0,result.shape[0]):
        for y in range(0,result.shape[1]):
            result[x,y] = res[x*result.shape[1]+y]

    return result

def getObjective_Py(scaled):
    #TODO : Returning Object might not be fully compatible with symLPExperiments

    cdef vector[double] res = getObjective(scaled)
    #Instantiate Iterator and iterate over returned c++ vector and assign values to numpy array
    itera = res.begin()
    i = 0 
    while itera != res.end():
     i = i + 1
     inc(itera)
    cdef np.ndarray result = np.empty(i)
    for x in range(0,i):
     result[x] = res[x]
   
    
    #Print and return resulting numpy array
    return result

def doScaling_Py(sctype):
    if sctype == 7:
        doScaling(EQUILIB)
    else:
        doScaling(GEOMMEAN)

def solve_Py():
    solve()


   
