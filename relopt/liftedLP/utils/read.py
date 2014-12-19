import glpkwrap
import scipy.sparse as sp
import numpy as np

UPPER = 3
LOWER = 2
EQUAL = 5
UNBOUND = 1
GEOMMEAN = 6
EQUILIB = 7

def openLP(fname,ftype):
    """
    Calls C++ code which opens a linear Program to solve given problem in specified file.
    
    :param fname: The path of a specified file, which is subject to solving
    :type fname: str.
    :param ftype: A specified format as how to solve the given LP
    :type ftype: int.
    """
    glpkwrap.openLP_Py(fname,ftype)

def extract_matrix(lpmatrix):
    """
    Extracts a coordinate matrix from a given array with exactly 4 rows

    :param lpmatrix: An array with four rows. The first two rows being the row and column coordinates of the matrix to be extracted and the third row being the data for the respective coordinates. Fourth Row TODO

    :returns: a tuple (A,b)

            A -- The matrix extracted from lpmatrix!
            b -- the corresponding data vector.

    This function is heavily dependant on the number of the rows of given lpmatrix. Four rows are necessary for this function to be properly executed.

    >>> print extract_matrix(lpmatrix)
    A,b
    """


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
 
def getMatrix_Upper(scaled):
    """
    Computes the Upper Bounds for a given LP and returns it as a multi-dimensional array
        Ax > b

    :param scaled: Flag, which indicates a scaled LP   
    :type scaled: int.

    :returns:
    """
    return glpkwrap.getMatrix_Upper(scaled)

def getMatrix_Lower(scaled):
    """
    Computes the Lower Bounds for a given LP and returns it as a multi-dimensional array
        Ax < b

    :param scaled: Flag, which indicates a scaled LP   
    :type scaled: int.

    :returns:
    """
    return glpkwrap.getMatrix_Lower(scaled)

def getMatrix_Equal(scaled):
    """
    TODO
        Ax = b

    :param scaled: Flag, which indicates a scaled LP   
    :type scaled: int.

    :returns:
    """

    return glpkwrap.getMatrix_Equal(scaled)

def getMatrix_Unbound(scaled):
    """
    Computes Unbound variables of given LP
        Ax < 0

    :param scaled: Flag, which indicates a scaled LP   
    :type scaled: int.

    :returns:
    """
    return glpkwrap.getMatrix_Unbound(scaled)

def getObjective(scaled):
    """
    Calls the function getObjective from glpk2py.cpp and returns the objectives as one-dimensional array (see getObjective.cpp)

    :param scaled: Flag, which indicates a scaled LP   
    :type scaled: int.

    :returns: The objective of a given lp as numpy array
    """
    return glpkwrap.getObjective_Py(scaled)
def solve():
    glpkwrap.solve_Py()
def doScaling(sctype):
     glpkwrap.doScaling_Py(sctype)
def closeLP():
    glpkwrap.closeLP_Py()
