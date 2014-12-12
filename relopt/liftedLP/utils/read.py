from .. import glpkwrap
import scipy.sparse as sp
import numpy as np

UPPER = 3
LOWER = 2
EQUAL = 5
UNBOUND = 1
GEOMMEAN = 6
EQUILIB = 7


##Calls C++ code which opens a linear Program to solve given problem in specified file
#
#@param fname The path of a specified file, which is subject to solving
#@param format A specified format as how to solve the given LP ?
def openLP(fname,ftype):
    glpkwrap.openLP_Py(fname,ftype)

## Extracts a coordinate matrix from a given n-dimensional array
#Creates a coordinate matrix for the given lpmatrix, by extracting necessary values from the given lpmatrix
#
#@param lpmatrix The four dimensional array with column and row coordinates in the first two rows and data in the third row
#
def extract_matrix(lpmatrix):


    ncols = np.int(lpmatrix[0,0])
    nrows = np.int(lpmatrix[1,0])
    nelms = np.int(lpmatrix[2,0])
    print nelms, ncols, nrows    
    i = np.array(lpmatrix[1,1:(nelms+1)], dtype = np.int) 
    j = np.array(lpmatrix[0,1:(nelms+1)], dtype = np.int) - 1
    d = lpmatrix[2,1:(nelms+1)]
    lb = np.int(lpmatrix[3,0]) + 1
    b = lpmatrix[3,1:lb]
    A = sp.coo_matrix((d, (i,j)), shape=(nrows, ncols))
    return [A, b]

##Computes the Upper Bounds for a given LP and returns it as a multi-dimensional array
#@param scaled  Flag, which indicates a scaled matrix    
def getMatrix_Upper(scaled):
    return glpkwrap.getMatrix_Upper(scaled)

##Computes the Lower Bounds for a given LP and returns it as a multi-dimensional array
#
#@param scaled Flag, which indicates a scaled matrix
def getMatrix_Lower(scaled):
    return glpkwrap.getMatrix_Lower(scaled)

##Computes the Equality constraints of given LP and returns it as a multi-dimensional array
#
#@param scaled Flag, which indicates a scaled matrix 
def getMatrix_Equal(scaled):
    return glpkwrap.getMatrix_Equal(scaled)

##Computes Unbound variables of given LP
#
#@param scaled Flag, which indicates a scaled matrix 
def getMatrix_Unbound(scaled):
    return glpkwrap.getMatrix_Unbound(scaled)

##Calls the function getObjective from glpk2py.cpp and returns the objectives as one-dimensional array (see getObjective.cpp)
#
#@param scaled Flag, which indicates a scaled matrix
def getObjective(scaled):
    return glpkwrap.getObjective_Py(scaled)
def solve():
    glpkwrap.solve_Py()
def doScaling(sctype):
     glpkwrap.doScaling_Py(sctype)
def closeLP():
    glpkwrap.closeLP_Py()
