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
        int size()

#cdef vector[int].iterator iter

cdef extern from "fc.h":
    vector[np.intp_t] equitablePartitionSaucyBipartite(const size_t nrows, const size_t ncols, const size_t medges, const size_t data[], const size_t rowind[], const size_t colind[], const size_t b[], const size_t c[], int cIters, int coarsest);
    vector[itype_t] equitablePartitionSaucyV2(itype_t mvertices, itype_t medges, double data[], itype_t rown[], itype_t coln[], itype_t b[], int cIters, int coarsest);

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
    vector[double] getMatrix(bounds boundquery,int scaled);
    vector[double] getObjective(int scaled);
    void doScaling(scaling sctype);
    void solve();


################################################
#EquitablePartitionSaucyWrapper
#All functions from fc.h are defined below
################################################

def epSaucy(
    np.ndarray[np.double_t,ndim=1] A,
    np.ndarray[itype_t,ndim=1] B,
    np.ndarray[itype_t,ndim=1] C,
    np.ndarray[itype_t,ndim=1] Z,
    cIters = 0,
    coarsest = True):

    # Pass references to c++ function to guarantee correct memory access
    cdef vector[size_t] res = equitablePartitionSaucyV2(Z.shape[0], A.shape[0], &A[0], &B[0], &C[0], &Z[0], cIters, 1 if coarsest else 0)
    
    #Get size of result and copy elements into numpy array
    i = res.size()
    cdef np.ndarray result = np.empty(i)
    for x in range(0,i):
     result[x] = res[x]
   
    
    #Print and return resulting numpy array
    return result

def epSaucyBipartite(
    np.ndarray[itype_t,ndim=1] A,
    np.ndarray[itype_t,ndim=1] rows,
    np.ndarray[itype_t,ndim=1] cols,
    np.ndarray[itype_t,ndim=1] rowcolor,
    np.ndarray[itype_t,ndim=1] colcolor,
    cIters = 0,
    coarsest = True):
    # Pass references to c++ function to guarantee correct memory access
    cdef vector[int] res = equitablePartitionSaucyBipartite(rowcolor.shape[0], colcolor.shape[0], A.shape[0], &A[0], &rows[0], &cols[0], &rowcolor[0], &colcolor[0], cIters, 1 if coarsest else 0)
    
    #Get size of result and copy elements into numpy array
    i = res.size()
    cdef np.ndarray result = np.empty(i)
    for x in range(0,i):
     result[x] = res[x]
   
    
    #Print and return resulting numpy array
    return result

################################################
#GLPK2PY-Wrapper
#All functions from glpk2py.h are defined below
################################################

def openLP_Py(fname,format_):
    openLP(fname,format_)

def closeLP_Py():
    closeLP()

def getMatrix_Upper(scaled):

    cdef vector[double] res
    res = getMatrix(UPPER,scaled)
    
    i = res.size()
    d = i/4
    cdef np.ndarray result = np.zeros([4,i/4],dtype=np.double)

    for x in range(0,d):
        result[0,x] = res[x]
        result[1,x] = res[x+d]
        result[2,x] = res[x+d*2]
        result[3,x] = res[x+d*3]

    return result

def getMatrix_Lower(scaled):

    cdef vector[double] res
    res = getMatrix(LOWER,scaled)

    i = res.size()
    d = i/4
    cdef np.ndarray result = np.zeros([4,i/4],dtype=np.double)

    for x in range(0,d):
        result[0,x] = res[x]
        result[1,x] = res[x+d]
        result[2,x] = res[x+d*2]
        result[3,x] = res[x+d*3]

    return result

def getMatrix_Equal(scaled):

    cdef vector[double] res
    res = getMatrix(EQUAL,scaled)

    i = res.size()
    d = i/4
    cdef np.ndarray result = np.zeros([4,i/4],dtype=np.double)

    for x in range(0,d):
        result[0,x] = res[x]
        result[1,x] = res[x+d]
        result[2,x] = res[x+d*2]
        result[3,x] = res[x+d*3]

    return result

def getMatrix_Unbound(scaled):

    cdef vector[double] res
    res = getMatrix(UNBOUND,scaled)

    i = res.size()
    d = i/4
    cdef np.ndarray result = np.zeros([4,i/4],dtype=np.double)

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
